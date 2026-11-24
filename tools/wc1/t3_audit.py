"""Read-only bulk audit of T4 reference C under Watcom 10.0a (toward T3).

usage: python3 -m wc1.t3_audit [--dry-run] [--limit N] [--addr HEX ...]
                               [--jobs N] [--include-unverified] [--output DIR]

For every in-scope function whose reference C is verified (wc1.progress
`c_status == "T4"`: `ref =` plus `ref_verified_by = "difftest:..."`) the
`ref` file is recompiled with Watcom 10.0a (wc1.oldcc), first with the flags
it declares (its codegen-flags header, else the default) and then with the
other 10.0a presets of wc1.permuter, and compared with the original by
wc1.match (match_module for the exact verdict, diff_function for the metrics).
A function's first exact match ends its search; an attempt under which the
whole object matches is then checked for in-place buildability
(wc1.build.check_t3_buildable).

Nothing under src/ or analysis/ is written: the flags go through the `cflags`
argument of match.compile_c (no header is edited), objects go to
<output>/obj/ (removed at the end), the reports to <output>/ (default
build/t3_audit/, git-ignored): report.json (a checkpoint after every ref
file), report.md, report.csv.  Promoting a function stays a manual step.

Per-function status:
  MATCH_BUILDABLE    the function and every other row of its object match
                     under one 10.0a flag set, and check_t3_buildable passes
  MATCH_UNBUILDABLE  the function matches exactly, but the file cannot become
                     `src =` as it stands (reason kept: other functions or
                     data of the file differ, legacy layout, anchors, ...)
  MISMATCH           compiled but never matched: best flags (lowest
                     diff_function score), first difference, counts
  COMPILE_ERROR      no attempt compiled
  TOOLCHAIN_ERROR    a compile timed out (stuck Wine): no evidence either way;
                     the run stops (exit 78, as wc1.match / batch_driver)
  SKIPPED            not audited: invalid entry, ambiguous mapping (one link
                     name claimed by several entries), link name not in the
                     compiled object, or the run stopped first (or, after a
                     parallel timeout, its evidence was discarded)
"""
import argparse
import csv
import datetime
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

from . import analysis, build, match, path, permuter, progress, symbols

SCHEMA = 1
CC = "10.0a"
STATUSES = ("MATCH_BUILDABLE", "MATCH_UNBUILDABLE", "MISMATCH", "COMPILE_ERROR",
            "TOOLCHAIN_ERROR", "SKIPPED")
REPORT_FILES = ("report.json", "report.md", "report.csv")
EXIT_USAGE = 2
EXIT_TOOLCHAIN = 78         # as wc1.match / wc1.batch_driver
EXIT_INTERRUPTED = 130
NEAR_MISS_TOP = 30          # rows in the Markdown near-miss table (the JSON has all)
NOT_REACHED = "not audited: the run stopped before this ref file"
DISCARDED = ("not audited: a compile of this ref file failed while a parallel compile timed "
             "out (the wineserver kill may have caused it); results discarded")
RANKING_NOTE = ("Near misses are ordered by wc1.match.diff_function's score tuple "
                "(opcode/structure differences, then immediates, then registers, "
                "then instruction-count and byte-length differences), lowest first. "
                "Unresolved operands are reported separately, not counted as numeric differences; "
                "a zero score does not prove a match. "
                "This is a heuristic ordering of how far the compiled code is from "
                "the original, not a probability that the function can be matched.")


class ToolchainAbort(Exception):
    """A compile timed out: the toolchain (Wine) is stuck, stop the run.
    `results` holds the TOOLCHAIN_ERROR rows of the unit it happened in."""

    def __init__(self, msg, results=()):
        super().__init__(msg)
        self.results = list(results)


# --- discovery ---------------------------------------------------------------

def _canon(short):
    return " ".join((short or "").split())


def short_flags(cflags):
    """The part of a full compile command line after match.BASE_CFLAGS."""
    base = match.BASE_CFLAGS
    return _canon(cflags[len(base):] if cflags.startswith(base) else cflags)


def attempt_plan(declared_short):
    """[(label, flags without BASE_CFLAGS)] to try under 10.0a: the declared
    flags first, then wc1.permuter's 10.0a presets in order, without repeats."""
    plan, seen = [("declared", _canon(declared_short))], {_canon(declared_short)}
    for cc, short in permuter.FLAG_PRESETS:
        if cc == CC and _canon(short) not in seen:
            seen.add(_canon(short))
            plan.append(("preset", _canon(short)))
    return plan


def discover(funcs, rows, include_unverified=False):
    """Candidates from the symbol database (`funcs`, symbols.load) and the
    progress classification (`rows`, progress.classify).

    Returns (candidates sorted by address, discovery issues).  A candidate
    that cannot be audited keeps a `skip_reason` (it is reported SKIPPED)."""
    issues = []
    seen = {r["addr"] for r in rows}
    for a, e in sorted(funcs.items()):
        if e.get("ref") and a not in seen:
            issues.append(f"{a:#x} {e.get('name')}: has ref {e['ref']!r} but is not a "
                          f"discovered function start ({e.get('_file')}); not audited")
    cands = []
    for r in rows:
        if r["scope"] != "in":
            continue
        if r["c"] == "T4":
            tier = "T4"
        elif r["c"] == "ref" and include_unverified:
            tier = "ref"
        else:
            continue
        e = funcs[r["addr"]]
        raw = e.get("ref")
        ref = os.path.normpath(raw).replace("\\", "/") if isinstance(raw, str) and raw else None
        c = {"addr": r["addr"], "addr_hex": f"{r['addr']:#x}", "name": e.get("name"),
             "link_name": e.get("link_name") or "", "module": e.get("module"),
             "area": r.get("module"), "toml": e.get("_file"), "ref": ref, "tier": tier,
             "diagnostic_only": tier != "T4", "ref_verified_by": e.get("ref_verified_by"),
             "t3_blocker": e.get("t3_blocker"), "declared_cc": None,
             "declared_cflags": None, "skip_reason": None}
        if not ref or not ref.endswith(".c") or ref.startswith("../") or os.path.isabs(ref):
            c["skip_reason"] = f"invalid entry: ref {raw!r} is not a repository .c path"
        elif not os.path.isfile(path(ref)):
            c["skip_reason"] = f"invalid entry: ref file {ref} does not exist"
        elif not c["link_name"]:
            c["skip_reason"] = "invalid entry: no link name"
        else:
            try:
                c["declared_cc"] = match.file_cc(path(ref))
                c["declared_cflags"] = short_flags(match.file_cflags(path(ref)))
            except SystemExit as ex:         # unknown codegen-compiler header
                c["skip_reason"] = f"invalid entry: {ex}"
        if c["skip_reason"]:
            issues.append(f"{c['addr_hex']} {c['name']}: {c['skip_reason']}")
        cands.append(c)
    users = {}
    for a, e in funcs.items():
        if e.get("link_name"):
            users.setdefault(e["link_name"], []).append(a)
    for c in cands:
        us = users.get(c["link_name"], [])
        if not c["skip_reason"] and len(us) > 1:   # wc1.match maps a link name to one address
            c["skip_reason"] = (f"ambiguous mapping: link name {c['link_name']} is used by "
                                + ", ".join(f"{x:#x}" for x in sorted(us)))
            issues.append(f"{c['addr_hex']} {c['name']}: {c['skip_reason']}")
    links = {}
    for c in cands:
        if not c["skip_reason"]:
            links.setdefault((c["ref"], c["link_name"]), []).append(c)
    for (ref, link), cs in sorted(links.items()):
        if len(cs) > 1:                      # one public, several entries: ambiguous
            for c in cs:
                c["skip_reason"] = (f"ambiguous mapping: link name {link} of {ref} is claimed by "
                                    + ", ".join(x["addr_hex"] for x in cs))
            issues.append(cs[0]["skip_reason"])
    cands.sort(key=lambda c: c["addr"])
    return cands, issues


def select(cands, addrs=(), limit=None):
    """Apply --addr and --limit; returns (selected, errors)."""
    errors = []
    if addrs:
        have = {c["addr"] for c in cands}
        errors = [f"{a:#x} is not an in-scope T4 function"
                  f"{' (nor ref-only)' if any(c['tier'] == 'ref' for c in cands) else ''}"
                  for a in addrs if a not in have]
        want = set(addrs)
        cands = [c for c in cands if c["addr"] in want]
    if limit is not None:
        cands = cands[:limit]
    return cands, errors


def group_units(cands):
    """Candidates sharing a ref file form one unit, compiled once per flag set."""
    units = {}
    for c in cands:
        if not c["skip_reason"]:
            units.setdefault(c["ref"], []).append(c)
    return [{"ref": ref, "cands": cs} for ref, cs in sorted(units.items(), key=lambda kv: kv[1][0]["addr"])]


# --- one ref file ------------------------------------------------------------

class Ctx:
    """What auditing a unit needs; the tests replace the callables."""

    def __init__(self, p, funcs, by_link, objdir, timeout=None):
        self.p, self.funcs, self.by_link = p, funcs, by_link
        self.objdir = objdir
        self.timeout = timeout                 # None: match.compile_c's default
        self.lock = threading.Lock()           # analysis-side work (shared program)
        self.abort = threading.Event()
        self.compile_c = match.compile_c
        self.match_module = match.match_module
        self.diff_function = match.diff_function
        self.check_buildable = build.check_t3_buildable
        self.compiles = 0
        self._n = threading.Lock()


def _first_lines(s, n=6):
    return "\n".join(str(s).strip().splitlines()[:n])


def _unlink(obj):
    for f in (obj, obj + ".log", obj + ".err"):
        try:
            os.unlink(f)
        except OSError:
            pass


def audit_unit(ctx, unit):
    """Compile one ref file under the attempt plan until every candidate in
    it matched (and, when they matched under different flags, until one flag
    set matches the whole object or the plan runs out); classify each.
    Raises ToolchainAbort on a compile timeout."""
    ref, cands = unit["ref"], unit["cands"]
    full = path(ref)
    plan = attempt_plan(cands[0]["declared_cflags"])
    st = {c["addr"]: {"attempts": [], "match": None, "best": None} for c in cands}
    whole = None                       # (k, obj, mod): first attempt whose object matches whole
    partial = {}                       # k -> problems of the object at a matching attempt
    try:
        for k, (label, short) in enumerate(plan):
            pending = [c for c in cands if st[c["addr"]]["match"] is None]
            if whole or ctx.abort.is_set():
                break
            if not pending and len({st[c["addr"]]["match"] for c in cands}) == 1:
                break      # all matched under one flag set that is not whole: flags will not fix it
            obj = os.path.join(ctx.objdir, f"a{k}", os.path.basename(match.unique_obj(full)))
            os.makedirs(os.path.dirname(obj), exist_ok=True)
            att = {"index": k, "label": label, "cc": CC, "cflags": short}
            with ctx._n:
                ctx.compiles += 1
            try:
                mod = ctx.compile_c(full, f"{match.BASE_CFLAGS} {short}", obj, cc=CC,
                                    includes=(os.path.dirname(full),), timeout=ctx.timeout,
                                    quiet=True)
            except match.CompileTimeout as ex:
                _unlink(obj)
                rows = []
                for c in cands:
                    s = st[c["addr"]]
                    s["attempts"].append(dict(att, result="TOOLCHAIN_ERROR", detail=_first_lines(ex)))
                    rows.append(dict(c, attempts=s["attempts"], status="TOOLCHAIN_ERROR",
                                     reason=f"compile timed out under [{short}]: {_first_lines(ex, 2)}",
                                     best=None, audited=False))
                ctx.abort.set()
                raise ToolchainAbort(f"{ref} [{short}]: {_first_lines(ex, 2)}", rows) from ex
            except SystemExit as ex:
                _unlink(obj)
                for c in pending:
                    st[c["addr"]]["attempts"].append(dict(att, result="COMPILE_ERROR",
                                                          detail=_first_lines(ex)))
                continue
            keep = False
            with ctx.lock:
                rows = ctx.match_module(ctx.p, mod, ctx.by_link)
                fn = {n: (s, pr) for n, s, pr in rows if not n.startswith("[")}
                bad = [f"{n}: {s}" + (f" ({pr[0]})" if pr else "")
                       for n, s, pr in rows if s != "MATCH"]
                for c in pending:
                    s = st[c["addr"]]
                    row = fn.get(c["link_name"])
                    if row is None:
                        s["attempts"].append(dict(att, result="UNMAPPED",
                                                  detail=f"{c['link_name']} is not a function of the "
                                                         f"compiled _TEXT ({', '.join(sorted(fn)) or 'none'})"))
                        continue
                    if row[0] == "MATCH":
                        s["attempts"].append(dict(att, result="MATCH", object_ok=not bad,
                                                  object_problems=bad[:8]))
                        s["match"] = k
                        keep = True
                        continue
                    dd = ctx.diff_function(ctx.p, mod, ctx.by_link, name=c["link_name"],
                                           orig_addr=c["addr"])
                    a = dict(att, result="MISMATCH", score=list(dd.get("score") or ()),
                             counts=dd.get("counts"),
                             first_diff=dd.get("first_diff") or (row[1][0] if row[1] else None),
                             problems=list(row[1][:3]), unresolved=dd.get("unresolved", []),
                             diff=list((dd.get("lines") or [])[:40]))
                    s["attempts"].append(a)
                    if s["best"] is None or tuple(a["score"]) < tuple(s["best"]["score"]):
                        s["best"] = a
            if not bad and all(c["link_name"] in fn for c in cands):
                whole = (k, obj, mod)
                keep = True
            else:
                if keep:
                    partial[k] = bad
                _unlink(obj)
        bcheck = None
        if whole:
            try:
                bcheck = _buildable(ctx, ref, whole[1], whole[2])
            except ToolchainAbort as ex:
                ctx.abort.set()
                rows = [dict(c, attempts=st[c["addr"]]["attempts"], status="TOOLCHAIN_ERROR",
                             reason=str(ex), best=None, audited=False) for c in cands]
                raise ToolchainAbort(str(ex), rows) from ex
        out = []
        for c in cands:
            s = st[c["addr"]]
            r = dict(c, attempts=s["attempts"], status=None, reason=None, best=None, audited=True)
            if s["match"] is not None:
                k = whole[0] if whole else s["match"]
                r["match_flags"] = plan[k][1]
                r["match_label"] = plan[k][0]
                r["flags_change"] = plan[k][1] != _canon(c["declared_cflags"]) or c["declared_cc"] != CC
                if whole:
                    ok, why = bcheck
                    r["status"] = "MATCH_BUILDABLE" if ok else "MATCH_UNBUILDABLE"
                    r["reason"] = None if ok else f"check_t3_buildable: {why}"
                else:
                    r["status"] = "MATCH_UNBUILDABLE"
                    r["reason"] = ("no flag set matches the whole object (src = needs every function "
                                   f"and its data to match); under [{plan[k][1]}]: "
                                   + "; ".join(partial.get(k, [])[:4]))
            elif s["best"] is not None:
                r["status"], r["best"] = "MISMATCH", s["best"]
            elif any(a["result"] == "UNMAPPED" for a in s["attempts"]):
                r["status"] = "SKIPPED"
                r["reason"] = "link name not in object: " + next(a["detail"] for a in s["attempts"]
                                                                 if a["result"] == "UNMAPPED")
            else:
                r["status"] = "COMPILE_ERROR"
                errs = [a["detail"] for a in s["attempts"] if a["result"] == "COMPILE_ERROR"]
                r["reason"] = errs[0] if errs else "no attempt ran"
            out.append(r)
        return out
    finally:
        if whole:
            _unlink(whole[1])


def _buildable(ctx, ref, obj, mod):
    """wc1.build.check_t3_buildable for the whole object: every DB function
    its _TEXT exports, as `src =` would provide them."""
    ti, text = mod.seg("_TEXT")
    entries = []
    for n, (si, _off) in sorted(mod.publics.items(), key=lambda kv: kv[1][1]):
        if si != ti:
            continue
        e = ctx.by_link.get(n)
        if e is None or e.get("_kind") != "func":
            return False, f"{n} in _TEXT has no function entry"
        entries.append(e)
    if not entries:
        return False, "no public function in _TEXT"
    try:
        with ctx.lock:
            return ctx.check_buildable(ctx.p, ctx.funcs, ref, obj, entries)
    except match.CompileTimeout as ex:
        raise ToolchainAbort(f"{ref}: buildability check: {_first_lines(ex, 2)}") from ex
    except (SystemExit, Exception) as ex:      # as wc1.batch_driver: a failed check is "no"
        return False, f"check failed: {_first_lines(ex, 2)}"


# --- reports -----------------------------------------------------------------

def _git(*args):
    try:
        r = subprocess.run(["git", *args], capture_output=True, text=True, cwd=path(), timeout=30)
        return r.stdout.strip() if r.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def toolchain_id():
    from . import oldcc
    tid = {"compiler": f"Watcom {oldcc.NAME}", "root": oldcc.root()}
    try:
        with open(oldcc.MANIFEST, "rb") as fh:
            tid["manifest_sha256"] = hashlib.sha256(fh.read()).hexdigest()
        tid["manifest_problems"] = oldcc.check()
    except OSError as ex:
        tid["manifest_problems"] = [f"manifest unreadable: {ex}"]
    return tid


def _skipped(c, reason):
    return dict(c, attempts=[], status="SKIPPED", reason=reason, best=None, audited=False)


def summarize(results):
    s = {"total": len(results), "attempts": sum(len(r["attempts"]) for r in results)}
    for tier in ("T4", "ref"):
        rs = [r for r in results if r["tier"] == tier]
        if rs or tier == "T4":
            s[tier] = {st: sum(1 for r in rs if r["status"] == st) for st in STATUSES}
            s[tier]["total"] = len(rs)
            for label, attempts in (
                    ("best", lambda r: [r.get("best") or {}]),
                    ("any_attempt", lambda r: r["attempts"])):
                refs = [{u["symbol"] for a in attempts(r) for u in a.get("unresolved", ())}
                        for r in rs]
                s[tier][f"unresolved_{label}"] = {
                    "functions": sum(bool(syms) for syms in refs),
                    "symbols": len(set().union(*refs))}
    return s


def promotion_candidates(results):
    """T4 functions matching exactly and buildable in place, by ref file then
    address (a file becomes `src =` as a whole); then the exact matches that
    do not build yet."""
    t4 = [r for r in results if r["tier"] == "T4"]
    key = lambda r: (r["ref"], r["addr"])
    return (sorted((r for r in t4 if r["status"] == "MATCH_BUILDABLE"), key=key),
            sorted((r for r in t4 if r["status"] == "MATCH_UNBUILDABLE"), key=key))


def near_misses(results):
    rs = [r for r in results if r["tier"] == "T4" and r["status"] == "MISMATCH" and r.get("best")]
    return sorted(rs, key=lambda r: (tuple(r["best"]["score"]), r["addr"]))


def _brief(r):
    b = {k: r.get(k) for k in ("addr_hex", "name", "module", "ref", "toml", "status",
                               "declared_cflags", "match_flags", "flags_change", "reason")}
    if r.get("best"):
        b.update(best_flags=r["best"]["cflags"], score=r["best"]["score"],
                 counts=r["best"].get("counts"), first_diff=r["best"].get("first_diff"))
    return {k: v for k, v in b.items() if v is not None}


def build_report(meta, results, issues):
    results = sorted(results, key=lambda r: r["addr"])
    builds, unbuilds = promotion_candidates(results)
    return {"schema": SCHEMA, "meta": meta, "stats": summarize(results),
            "ranking_note": RANKING_NOTE,
            "promotion_candidates": [_brief(r) for r in builds],
            "unbuildable_matches": [_brief(r) for r in unbuilds],
            "near_misses": [_brief(r) for r in near_misses(results)],
            "discovery_issues": sorted(issues), "results": results}


def render_csv(report):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["addr", "name", "module", "tier", "status", "ref", "toml", "declared_cc",
                "declared_cflags", "match_flags", "best_flags", "score", "first_diff",
                "reason", "t3_blocker"])
    for r in report["results"]:
        b = r.get("best") or {}
        w.writerow([r["addr_hex"], r["name"], r.get("module") or "", r["tier"], r["status"],
                    r.get("ref") or "", r.get("toml") or "", r.get("declared_cc") or "",
                    r.get("declared_cflags") or "", r.get("match_flags") or "",
                    b.get("cflags", ""), " ".join(map(str, b.get("score", []))),
                    b.get("first_diff") or "", r.get("reason") or "", r.get("t3_blocker") or ""])
    return buf.getvalue()


def _md(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


def render_md(report):
    m, s = report["meta"], report["stats"]
    comp, tc = m["completion"], m["toolchain"]
    L = ["# wc1.t3_audit report", ""]
    if comp["status"] != "complete":
        L += [f"**INCOMPLETE RUN ({comp['status']})**: {comp['audited']} of {comp['selected']} "
              f"selected functions audited. {comp.get('note') or ''}", ""]
    if not m["scope"]["full_scope"]:
        L += [f"**SUBSET**: filtered by {_md(json.dumps(m['scope']['filters'], sort_keys=True))}; "
              "the counts cover only the selected functions.", ""]
    L += [f"- commit: `{m['git_commit']}`" + (" (src/analysis/tools/tests dirty)" if m.get("git_dirty") else ""),
          f"- toolchain: {tc.get('compiler')} at `{tc.get('root')}`, manifest sha256 "
          f"`{(tc.get('manifest_sha256') or '?')[:16]}`, problems: {len(tc.get('manifest_problems') or [])}",
          f"- invocation: `{' '.join(m['invocation'])}`",
          f"- started {m['started']}, finished {m.get('finished') or '-'}; {m.get('compiles', 0)} compiles",
          f"- completion: {comp['status']} ({comp['audited']}/{comp['selected']} audited; "
          f"{m['scope']['in_scope_t4']} in-scope T4 in the database)", ""]
    ref = "ref" in s
    L += ["## Counts", "", "| status | T4 |" + (" ref (diagnostic) |" if ref else ""),
          "|---|---|" + ("---|" if ref else "")]
    for st in STATUSES + ("total",):
        L.append(f"| {st} | {s['T4'][st]} |" + (f" {s['ref'][st]} |" if ref else ""))
    L += ["", "Unresolved external relocations in T4 function attempts (all occurrences in JSON):"]
    for label, key in (("best attempts", "best"), ("any attempt", "any_attempt")):
        counts = s["T4"][f"unresolved_{key}"]
        L.append(f"- {label}: {counts['functions']} functions, {counts['symbols']} distinct symbols")
    if ref:
        L += ["", "`ref` rows (--include-unverified) are diagnostics only: their reference C is "
                  "not difftest-verified, so they are never promotion candidates."]
    L += ["", "## Promotion candidates (exact match, buildable in place)", "",
          "By ref file: a file becomes `src =` as a whole. Promotion is manual (ref -> src, "
          "codegen headers set to the matching flags, ref_verified_by/t3_blocker dropped, "
          "`make verify`).", ""]
    if report["promotion_candidates"]:
        L += ["| addr | name | ref | flags | flags change |", "|---|---|---|---|---|"]
        L += [f"| {r['addr_hex']} | {r['name']} | {r['ref']} | `{r['match_flags']}` | "
              f"{'yes' if r.get('flags_change') else 'no'} |" for r in report["promotion_candidates"]]
    else:
        L.append("None.")
    L += ["", "## Exact matches that do not build in place yet", ""]
    if report["unbuildable_matches"]:
        L += ["| addr | name | ref | flags | reason |", "|---|---|---|---|---|"]
        L += [f"| {r['addr_hex']} | {r['name']} | {r['ref']} | `{r['match_flags']}` | "
              f"{_md(r.get('reason') or '')} |" for r in report["unbuildable_matches"]]
    else:
        L.append("None.")
    nm = report["near_misses"]
    L += ["", f"## Near misses (top {min(NEAR_MISS_TOP, len(nm))} of {len(nm)})", "",
          report["ranking_note"], ""]
    if nm:
        L += ["| addr | name | best flags | score | first difference |", "|---|---|---|---|---|"]
        L += [f"| {r['addr_hex']} | {r['name']} | `{r['best_flags']}` | "
              f"{','.join(map(str, r['score']))} | {_md(r.get('first_diff') or '')} |"
              for r in nm[:NEAR_MISS_TOP]]
    else:
        L.append("None.")
    errs = [r for r in report["results"] if r["status"] in ("COMPILE_ERROR", "TOOLCHAIN_ERROR", "SKIPPED")]
    L += ["", "## Errors and skipped", ""]
    if errs:
        L += ["| addr | name | status | reason |", "|---|---|---|---|"]
        L += [f"| {r['addr_hex']} | {r['name']} | {r['status']} | {_md((r.get('reason') or '')[:240])} |"
              for r in errs]
    else:
        L.append("None.")
    if report["discovery_issues"]:
        L += ["", "## Discovery issues", ""] + [f"- {_md(i)}" for i in report["discovery_issues"]]
    return "\n".join(L) + "\n"


def _atomic_write(fn, text):
    tmp = f"{fn}.tmp.{os.getpid()}"
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    os.replace(tmp, fn)


def write_reports(outdir, report, final):
    """report.json always (a checkpoint); report.md/.csv when the run ends."""
    _atomic_write(os.path.join(outdir, "report.json"),
                  json.dumps(report, indent=1, sort_keys=True) + "\n")
    if final:
        _atomic_write(os.path.join(outdir, "report.md"), render_md(report))
        _atomic_write(os.path.join(outdir, "report.csv"), render_csv(report))


# --- driver ------------------------------------------------------------------

def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def _hex(s):
    try:
        return int(s, 16)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a hex address: {s!r}")


def check_output(outdir):
    """The audit never writes into the project's sources or metadata."""
    a = os.path.realpath(outdir)
    if a == os.path.realpath(path()):
        raise SystemExit("--output: refusing to write into the repository root")
    for d in ("src", "analysis", "asm", "tests", "tools", "docs", "original"):
        root = os.path.realpath(path(d))
        if a == root or a.startswith(root + os.sep):
            raise SystemExit(f"--output {outdir}: refusing to write under {d}/ (use build/...)")


def parse_args(argv):
    ap = argparse.ArgumentParser(prog="python3 -m wc1.t3_audit",
                                 description="Read-only audit of T4 reference C under Watcom 10.0a.")
    ap.add_argument("--dry-run", action="store_true",
                    help="list the selection and attempt plans; compile and write nothing")
    ap.add_argument("--limit", type=int, default=None, metavar="N",
                    help="only the first N selected functions (by address)")
    ap.add_argument("--addr", type=_hex, action="append", default=[], metavar="HEX",
                    help="only this function (repeatable)")
    ap.add_argument("--jobs", type=int, default=1, metavar="N",
                    help="ref files audited in parallel (default 1: a compile timeout "
                         "kills the shared wineserver)")
    ap.add_argument("--include-unverified", action="store_true",
                    help="also audit ref-only entries (no difftest), as diagnostics only")
    ap.add_argument("--output", default=None, metavar="DIR",
                    help="report directory (default build/t3_audit)")
    a = ap.parse_args(argv)
    if a.limit is not None and a.limit < 1:
        ap.error("--limit must be >= 1")
    if a.jobs < 1:
        ap.error("--jobs must be >= 1")
    return a


def load_inputs():
    funcs, datas, errors = symbols.load(strict=False)
    p = analysis.run()
    rows = progress.classify([f["start"] for f in p.functions], funcs, progress.load_modules())
    by_link = {e["link_name"]: e for t in (funcs, datas) for e in t.values() if e.get("link_name")}
    return p, funcs, by_link, rows, [f"symbols: {x}" for x in (errors or [])]


def run(a, argv, inputs=None, log=print, ctx_hook=None):
    """The audit; returns the exit code.  Tests pass `inputs` (instead of
    load_inputs()) and `ctx_hook` (to fake the compiler and the comparison)."""
    outdir = os.path.abspath(a.output or path("build", "t3_audit"))
    check_output(outdir)
    p, funcs, by_link, rows, issues = inputs or load_inputs()
    cands, d_issues = discover(funcs, rows, a.include_unverified)
    issues = list(issues) + d_issues
    sel, errs = select(cands, a.addr, a.limit)
    if errs:
        for e in errs:
            log(f"error: {e}")
        return EXIT_USAGE
    units = group_units(sel)
    if a.dry_run:
        for c in sel:
            head = (f"{c['addr_hex']:>9} {c['name']:32} {c['tier']:3} {c['ref'] or '-'} "
                    f"[{c['declared_cc']}: {c['declared_cflags']}]")
            if c["skip_reason"]:
                log(f"{head}  SKIP: {c['skip_reason']}")
            else:
                log(f"{head}\n{'':10}plan: " + " | ".join(s for _l, s in attempt_plan(c["declared_cflags"])))
        log(f"{len(sel)} selected ({sum(1 for c in sel if c['tier'] == 'T4')} T4) in "
            f"{len(units)} ref files; dry run: nothing compiled or written")
        return 0

    os.makedirs(outdir, exist_ok=True)
    for f in REPORT_FILES:                     # never leave a stale report beside this run
        try:
            os.unlink(os.path.join(outdir, f))
        except FileNotFoundError:
            pass
    objdir = os.path.join(outdir, "obj")
    shutil.rmtree(objdir, ignore_errors=True)
    filters = {}
    if a.addr:
        filters["addr"] = [f"{x:#x}" for x in a.addr]
    if a.limit is not None:
        filters["limit"] = a.limit
    meta = {"tool": "wc1.t3_audit", "started": _now(), "finished": None,
            "git_commit": _git("rev-parse", "HEAD"),
            "git_dirty": bool(_git("status", "--porcelain", "--", "src", "analysis", "tools", "tests")),
            "toolchain": toolchain_id(),
            "invocation": ["python3", "-m", "wc1.t3_audit"] + list(argv),
            "options": {"jobs": a.jobs, "include_unverified": a.include_unverified, "cc": CC,
                        "plan": "declared flags, then wc1.permuter 10.0a presets"},
            "scope": {"tiers": ["T4", "ref"] if a.include_unverified else ["T4"],
                      "in_scope_t4": sum(1 for c in cands if c["tier"] == "T4"),
                      "filters": filters, "full_scope": not filters},
            "completion": {"status": "running", "selected": len(sel), "audited": 0, "note": None},
            "compiles": 0}
    results = {c["addr"]: _skipped(c, c["skip_reason"]) for c in sel if c["skip_reason"]}
    ctx = Ctx(p, funcs, by_link, objdir)
    if ctx_hook:
        ctx_hook(ctx)
    lock = threading.Lock()

    def checkpoint():
        meta["completion"]["audited"] = sum(1 for r in results.values() if r["audited"])
        meta["compiles"] = ctx.compiles
        write_reports(outdir, build_report(meta, list(results.values()), issues), final=False)

    def one(unit):
        if ctx.abort.is_set():
            return
        try:
            rs = audit_unit(ctx, unit)
        except ToolchainAbort as ex:
            with lock:
                for r in ex.results:
                    results[r["addr"]] = r
            raise
        with lock:
            if ctx.abort.is_set():
                return     # finished beside a timeout: the wineserver kill may have hit it
            for r in rs:
                results[r["addr"]] = r
                log(f"{r['addr_hex']:>9} {r['name']:32} {r['status']:17} "
                    f"{r.get('match_flags') or (r.get('best') or {}).get('cflags') or r.get('reason') or ''}")
            checkpoint()

    with lock:
        checkpoint()
    code, status, note = 0, "complete", None
    ex = ThreadPoolExecutor(a.jobs) if a.jobs > 1 else None
    try:
        if ex is None:
            for u in units:
                one(u)
        else:
            futs = [ex.submit(one, u) for u in units]
            first = None
            for f in futs:
                try:
                    f.result()
                except ToolchainAbort as e:
                    first = first or e
            if first:
                raise first
    except ToolchainAbort as e:
        code, status = EXIT_TOOLCHAIN, "aborted"
        note = (f"[TOOLCHAIN ERROR] {e}: a compile timed out; nothing after it is evidence of a "
                "(non-)match. Fix the toolchain and rerun.")
        log(note)
    except KeyboardInterrupt:
        ctx.abort.set()
        code, status, note = EXIT_INTERRUPTED, "interrupted", "interrupted by the user"
        log(note)
    finally:
        if ex is not None:
            ex.shutdown(wait=True, cancel_futures=True)
        shutil.rmtree(objdir, ignore_errors=True)
    if status == "aborted" and a.jobs > 1:
        # A wineserver kill after a timeout fails the compiles running beside it:
        # a COMPILE_ERROR from another file is then no evidence. Matches and
        # mismatches came from finished compiles and stay.
        for u in units:
            rs = [results.get(c["addr"]) for c in u["cands"]]
            if any(r and r["status"] != "TOOLCHAIN_ERROR"
                   and any(x["result"] == "COMPILE_ERROR" for x in r["attempts"]) for r in rs):
                for c in u["cands"]:
                    results[c["addr"]] = _skipped(c, DISCARDED)
    for u in units:
        for c in u["cands"]:
            if c["addr"] not in results:
                results[c["addr"]] = _skipped(c, NOT_REACHED)
    if status == "complete" and any(r["reason"] == NOT_REACHED for r in results.values()):
        status = "incomplete"                      # cannot happen; never report it complete
    meta["completion"].update(status=status, note=note)
    meta["finished"] = _now()
    with lock:
        checkpoint()
    report = build_report(meta, list(results.values()), issues)
    write_reports(outdir, report, final=True)
    t4 = report["stats"]["T4"]
    log(f"{status}: {t4['total']} T4: " + ", ".join(f"{k} {t4[k]}" for k in STATUSES)
        + f"; reports in {os.path.relpath(outdir, path())}/")
    return code


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    a = parse_args(argv)
    if not a.dry_run:
        from . import oldcc
        try:
            oldcc.require()
        except oldcc.OldCCError as ex:
            print(f"[TOOLCHAIN ERROR] {ex}", file=sys.stderr)
            return EXIT_TOOLCHAIN
    return run(a, argv)


if __name__ == "__main__":
    sys.exit(main())
