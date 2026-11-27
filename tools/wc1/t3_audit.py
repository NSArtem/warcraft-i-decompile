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
import re
import shutil
import struct
import subprocess
import sys
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

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


def current_presets():
    """The deduplicated 10.0a preset short flags of wc1.permuter, in order.

    Recorded in report.json meta.options so consumers can tell whether an audit
    predates a preset change (wave4.load_report / wave4a staleness checks)."""
    out, seen = [], set()
    for cc, short in permuter.FLAG_PRESETS:
        s = _canon(short)
        if cc == CC and s not in seen:
            seen.add(s)
            out.append(s)
    return out


_current_presets = current_presets       # kept for is_improved_record_fresh's kwarg shadowing


def compiler_root(repo_root=None):
    """The Watcom 10.0a tree of `repo_root` (no silent fallback elsewhere).

    `WC1_WATCOM10A` (the same explicit override `oldcc.root()` honours) wins;
    otherwise the checkout's own `original/watcom/<oldcc.NAME>`.  With
    `repo_root=None` and no override this equals `oldcc.root()`."""
    from . import oldcc
    env = os.environ.get("WC1_WATCOM10A")
    if env:
        return os.path.abspath(env)
    root = Path(repo_root) if repo_root else Path(path())
    return os.path.abspath(str(root / "original" / "watcom" / oldcc.NAME))


def _tool_sig(repo_root=None):
    """`wave4_fp.tool_signature()` (war.exe + wcc386 identity), fail-open None.

    The identity is rooted at `repo_root` (default: the active checkout) and
    the Watcom tree `compiler_root(repo_root)` — never the active checkout's
    when an explicit root is given.  Imported lazily: wc1.wave4_fp imports
    wc1.t3_audit at module level."""
    try:
        from . import wave4_fp
        root = repo_root or path()
        return wave4_fp.tool_signature(repo_root=root,
                                       compiler_root=compiler_root(root))
    except Exception:              # absent/partial toolchain, mocked tests
        return None


_HOST_PATH_OPT_PREFIXES = ("-i", "-I", "-fo", "-fr", "-fi", "-fh", "-d")


def _default_system_headers(repo_root):
    """The `h/` directory of that checkout's Watcom 10.0a tree."""
    return Path(compiler_root(repo_root)) / "h"


def _valid_ref(ref):
    """A portable repository-relative C path (rule: plain, relative, no `..`)."""
    if not isinstance(ref, str) or not ref or os.path.isabs(ref):
        return False
    return ".." not in Path(ref).parts


def portable_source_digest(ref, *, repo_root=None, system_headers=None):
    """Checkout-location-independent digest of `ref` and its recursive includes.

    `wave4_fp.source_inputs()` keys its hashes by resolved absolute paths, so
    its digest changes when the repository is checked out elsewhere.  Here every
    resolved dependency is mapped to a logical key first:

      * `sys:<path relative to system_headers>` for the Watcom header tree,
      * `repo:<path relative to repo_root>` for repository files.

    The system header tree is classified first: `original/` is a symlink to the
    main checkout in a worktree, so resolving `system_headers` identifies the
    same real `h/` directory (and therefore the same `sys:` keys) whether
    `original/` is a real directory or a symlink.  A dependency that resolves
    outside both roots is a hard failure (returns None): an absolute host path
    must never leak into a digest.

    `ref` must be a non-empty repository-relative path without a `..`
    component; anything else is a hard failure (returns None).

    Returns the SHA-256 hex digest, or None on any unresolvable dependency or
    unreadable file (fail closed)."""
    if not _valid_ref(ref):
        return None
    try:
        from . import wave4_fp
        root = Path(repo_root or path()).resolve()
        sys_headers = Path(system_headers if system_headers is not None
                           else _default_system_headers(root)).resolve()
        src = (root / ref).resolve()
        inc_dirs = [src.parent, root / "src" / "include", sys_headers]
        hashes = wave4_fp.source_inputs(src, inc_dirs)
    except Exception:
        return None
    portable = {}
    for name, digest in hashes.items():
        p = Path(name).resolve()
        try:
            rel = p.relative_to(sys_headers)
        except ValueError:
            try:
                rel = p.relative_to(root)
            except ValueError:
                return None            # outside the repository and the compiler tree
            key = f"repo:{rel.as_posix()}"
        else:
            key = f"sys:{rel.as_posix()}"
        portable[key] = digest
    return hashlib.sha256(json.dumps(portable, sort_keys=True).encode()).hexdigest()


def _source_digest(ref):
    """`portable_source_digest()` for `ref`, fail-open None.

    Imported lazily (circular-import avoidance) and fail-open so an unreadable
    include tree or a mocked test environment never fails the audit."""
    try:
        return portable_source_digest(ref, repo_root=path())
    except Exception:
        return None


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


def extract_omf_deps(mod):
    """Extract exact external relocations (resolved + unresolved) and _TEXT
    symbols from a real compiled OMF module (`wc1.omf.Module`).

    Returns None when `mod` does not carry full OMF relocation metadata (e.g.
    lightweight test fakes), so callers never mistake missing metadata for an
    object with zero external dependencies.
    """
    if (mod is None or not hasattr(mod, "seg") or not hasattr(mod, "externs")
            or not hasattr(mod, "segments") or not hasattr(mod, "publics")):
        return None
    ti, text = mod.seg("_TEXT")
    if text is not None and not hasattr(text, "fixups"):
        return None
    text_syms = set()
    if ti is not None:
        for tbl in (getattr(mod, "publics", None) or {}, getattr(mod, "statics", None) or {}):
            for n, (si, _off) in tbl.items():
                if si == ti:
                    text_syms.add(n)
    ext_syms = {s for s in (getattr(mod, "externs", None) or ()) if isinstance(s, str) and s}
    seen_rel = set()
    ext_relocs = []
    if text is not None:
        tdata = getattr(text, "data", b"") or b""
        for fu in getattr(text, "fixups", None) or ():
            if fu.target_kind == "ext" and isinstance(fu.target, str) and fu.target:
                ext_syms.add(fu.target)
                addend = None
                if fu.loc == 9 and fu.offset + 4 <= len(tdata):
                    addend = struct.unpack_from("<i", tdata, fu.offset)[0] + fu.disp
                key = (fu.target, bool(fu.self_rel), fu.loc, addend)
                if key not in seen_rel:
                    seen_rel.add(key)
                    ext_relocs.append({
                        "symbol": fu.target,
                        "self_relative": bool(fu.self_rel),
                        "loc": fu.loc,
                        "addend": addend,
                    })
    has_data_anchors = False
    for seg in getattr(mod, "segments", None) or ():
        if getattr(seg, "cls", None) in ("DATA", "BSS") and getattr(seg, "length", 0):
            has_data_anchors = True
        if getattr(seg, "name", None) != "_TEXT":
            for fu in getattr(seg, "fixups", None) or ():
                if fu.target_kind == "ext" and isinstance(fu.target, str) and fu.target:
                    ext_syms.add(fu.target)
    ext_relocs.sort(key=lambda r: (
        r["symbol"], r["self_relative"], r["loc"] or 0,
        r["addend"] if r["addend"] is not None else 0,
    ))
    return {
        "external_symbols": sorted(ext_syms),
        "text_symbols": sorted(text_syms),
        "external_relocs": ext_relocs,
        "has_data_anchors": has_data_anchors,
    }


def merge_omf_deps(items, *, complete=True):
    """Merge per-attempt `extract_omf_deps` dicts across a translation unit."""
    ext_syms = set()
    text_syms = set()
    seen_rel = set()
    ext_relocs = []
    has_data_anchors = False
    for d in items or ():
        if not isinstance(d, dict):
            continue
        ext_syms.update(d.get("external_symbols") or ())
        text_syms.update(d.get("text_symbols") or ())
        has_data_anchors = has_data_anchors or bool(d.get("has_data_anchors"))
        for r in d.get("external_relocs") or ():
            k = (r.get("symbol"), bool(r.get("self_relative")), r.get("loc"), r.get("addend"))
            if k not in seen_rel:
                seen_rel.add(k)
                ext_relocs.append({
                    "symbol": r.get("symbol"),
                    "self_relative": bool(r.get("self_relative")),
                    "loc": r.get("loc"),
                    "addend": r.get("addend"),
                })
    ext_relocs.sort(key=lambda r: (
        r["symbol"] or "", r["self_relative"], r["loc"] or 0,
        r["addend"] if r["addend"] is not None else 0,
    ))
    return {
        "complete": bool(complete),
        "external_symbols": sorted(ext_syms),
        "text_symbols": sorted(text_syms),
        "external_relocs": ext_relocs,
        "has_data_anchors": has_data_anchors,
    }


def audit_unit(ctx, unit):
    """Compile one ref file under the attempt plan until every candidate in
    it matched (and, when they matched under different flags, until one flag
    set matches the whole object or the plan runs out); classify each.
    Raises ToolchainAbort on a compile timeout."""
    ref, cands = unit["ref"], unit["cands"]
    full = path(ref)
    src_digest = _source_digest(ref)
    plan = attempt_plan(cands[0]["declared_cflags"])
    st = {c["addr"]: {"attempts": [], "match": None, "best": None} for c in cands}
    whole = None                       # (k, obj, mod): first attempt whose object matches whole
    partial = {}                       # k -> problems of the object at a matching attempt
    attempt_omfs = []
    had_compile_err = False
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
                had_compile_err = True
                for c in pending:
                    st[c["addr"]]["attempts"].append(dict(att, result="COMPILE_ERROR",
                                                          detail=_first_lines(ex)))
                continue
            attempt_omfs.append(extract_omf_deps(mod))
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
                             problems=list(row[1][:3]),
                             diff=list((dd.get("lines") or [])[:40]))
                    if "unresolved" in dd:
                        a["unresolved"] = dd["unresolved"]
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
        omf_evidence = {}
        if attempt_omfs:
            complete = not had_compile_err and None not in attempt_omfs and not ctx.abort.is_set()
            unit_omf = merge_omf_deps(attempt_omfs, complete=complete)
            # Use the symbol table that resolved fixups during the audit.
            symbol_addrs = {name: _symbol_addr(ctx.by_link, name)
                            for name in sorted(_omf_names(unit_omf))}
            omf_evidence = {"omf_deps": unit_omf, "omf_symbol_addrs": symbol_addrs,
                            "omf_evidence_sha256": _omf_evidence_digest(unit_omf, symbol_addrs)}
        out = []
        for c in cands:
            s = st[c["addr"]]
            r = dict(c, attempts=s["attempts"], status=None, reason=None, best=None, audited=True,
                     source_digest=src_digest, **omf_evidence)
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
                if omf_evidence:
                    declared = s["attempts"][0]  # attempt_plan starts with the declared flags
                    r["row_evidence_sha256"] = _row_evidence_digest(
                        r, declared, s["best"], unit_omf, symbol_addrs)
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


# --- provenance-checked improved-T4 snapshot (Wave 4B input) -------------------

# Checks detect staleness against the live checkout's sources and headers,
# toolchain, presets and flags, and symbol DB. They also detect malformed
# evidence, edits that leave any bound digest unreproduced, and mixed rows or
# records that disagree with their bound evidence. Every report row carries a
# `row_sha256` over the whole row and the report header fields it depends on
# (git state, toolchain identity, options), checked before any eligibility
# decision, so a single edited field of a saved report is caught.  Only the
# final report carries `meta.results_sha256` over the whole report document
# (meta incl. completion and scope, stats, near misses, rows), so a checkpoint, an
# edited header/scope/stat or a report with added/removed rows has no
# provenance.  A snapshot carries `snapshot_sha256` over the whole document.
# The record-set digest
# detects missing, duplicated or substituted snapshot records. A deliberate
# rewrite can reproduce every digest consistently. If in doubt, run a fresh audit.

IMPROVED_SCHEMA = 1
IMPROVED_DESCRIPTION = (
    "Residual T4 MISMATCH functions whose best Watcom 10.0a attempt under the "
    "recorded preset list strictly beats the score of their declared flags. Each "
    "record is provenance-checked (portable source + recursive include digest, "
    "compiler/binary tool_sig, preset list/base flags, declared cflags, OMF symbol "
    "addresses) by wc1.t3_audit.is_improved_record_fresh before a future Wave 4B "
    "run may use it.")


_OMF_KEYS = ("complete", "external_symbols", "text_symbols",
             "external_relocs", "has_data_anchors")
_SYMBOL_NAME = re.compile(r"[A-Za-z_$@?][A-Za-z0-9_$@?]*")


def _valid_symbol_name(name):
    return isinstance(name, str) and _SYMBOL_NAME.fullmatch(name) is not None


def _omf_names(deps):
    return set(deps["external_symbols"]) | set(deps["text_symbols"])


def _symbol_addr(by_link, name):
    entry = by_link.get(name)
    return entry.get("addr") if isinstance(entry, dict) else None


def _valid_symbol_addrs(addrs):
    return isinstance(addrs, dict) and all(
        _valid_symbol_name(name) and (addr is None or _is_int(addr))
        for name, addr in addrs.items())


def _changed_symbols(recorded, by_link):
    changed = []
    for name, addr in recorded.items():
        live_addr = _symbol_addr(by_link, name)
        if name in by_link:
            matches = _is_int(live_addr) and live_addr == addr
        else:
            matches = addr is None
        if not matches:
            changed.append(name)
    return changed


def _normalized_omf_deps(d):
    """The fields hashed for a complete, well-formed OMF summary, else None."""
    if not isinstance(d, dict) or d.get("complete") is not True:
        return None
    ext, text = d.get("external_symbols"), d.get("text_symbols")
    relocs, anchors = d.get("external_relocs"), d.get("has_data_anchors")
    if not isinstance(ext, list) or not all(_valid_symbol_name(s) for s in ext):
        return None
    if not isinstance(text, list) or not text or not all(_valid_symbol_name(s) for s in text):
        return None
    ext_names = set(ext)
    if not isinstance(relocs, list) or not all(
            isinstance(r, dict) and _valid_symbol_name(r.get("symbol")) and r["symbol"] in ext_names
            for r in relocs):
        return None
    if not isinstance(anchors, bool):
        return None
    return {k: d[k] for k in _OMF_KEYS}


def _canonical_json_digest(value):
    try:
        return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()
    except (TypeError, ValueError, RecursionError):
        return None


def _omf_deps_digest(d):
    """Digest a valid summary using the legacy key set and JSON encoding."""
    keep = _normalized_omf_deps(d)
    return _canonical_json_digest(keep) if keep is not None else None


def _omf_evidence_digest(deps, addrs):
    """Bind a normalized OMF summary to its audit-time address stamp."""
    return _canonical_json_digest({"omf_deps": deps, "omf_symbol_addrs": addrs})


def _row_evidence_digest(row, declared, best, deps, addrs):
    """Bind candidate and attempt fields using whitespace-canonical short flags
    in both audit rows and records. Scores are JSON arrays."""
    return _canonical_json_digest({
        **{field: row.get(field) for field in ("addr", "link_name", "ref", "source_digest")},
        "declared": {"cflags": _canon(declared["cflags"]), "score": declared.get("score")},
        "best": {"cflags": _canon(best["cflags"]), "score": best["score"],
                 "unresolved": best.get("unresolved")},
        "omf_deps": deps, "omf_symbol_addrs": addrs,
    })


def _record_digest(rec):
    return _canonical_json_digest({k: v for k, v in rec.items() if k != "record_sha256"})


def _valid_unresolved_fixup(fixup):
    """Validate the two entry shapes produced by match._record_unresolved."""
    fields = {"symbol", "offset", "loc", "self_relative", "addend", "original_candidate"}
    if not isinstance(fixup, dict) or not fields <= fixup.keys():
        return False
    if (not _valid_symbol_name(fixup["symbol"])
            or not _is_int(fixup["offset"]) or fixup["offset"] < 0
            or not _is_int(fixup["loc"]) or not isinstance(fixup["self_relative"], bool)):
        return False
    addend, candidate = fixup["addend"], fixup["original_candidate"]
    if fixup.keys() == fields:
        return addend is None and candidate is None
    return (fixup.keys() == fields | {"instruction_offset", "operand"}
            and _is_int(fixup["instruction_offset"]) and fixup["instruction_offset"] >= 0
            and fixup["operand"] in ("imm", "disp")
            and _is_int(addend) and (candidate is None or _is_int(candidate)))


def _valid_unresolved(value):
    return isinstance(value, list) and all(_valid_unresolved_fixup(fixup) for fixup in value)


def _matches_omf_fixup(fixup, deps, addrs):
    symbol, addend = fixup["symbol"], fixup["addend"]
    # Undecoded operands have no addend even when OMF extraction found one.
    return symbol in deps["external_symbols"] and addrs[symbol] is None and any(
        r["symbol"] == symbol and r.get("self_relative") is fixup["self_relative"]
        and _is_int(r.get("loc")) and r["loc"] == fixup["loc"]
        and (addend is None or r.get("addend") is None
             or (_is_int(r["addend"]) and r["addend"] == addend))
        for r in deps["external_relocs"])


def _report_provenance(report):
    """`(presets, base_flags)` of a completed, clean audit report, else None.

    Fail closed: a report without a reproducing `meta.results_sha256` (a
    checkpoint, an edited completion record, or added/removed/reordered rows),
    a report that is still running/aborted/interrupted, was made
    from a dirty or unknown src/analysis/tools/tests tree, lacks a 40-hex
    `git_commit`, or does not carry a valid `options.presets` /
    `options.base_flags` cannot mint provenance records.  A malformed report
    (not a dict, non-dict meta/completion/options) is None, never an exception.
    The values are read from the report itself and never from the current
    environment, so an old-preset report can never be laundered."""
    if not isinstance(report, dict):
        return None
    meta = report.get("meta")
    if not isinstance(meta, dict):
        return None
    completion = meta.get("completion")
    if not isinstance(completion, dict) or completion.get("status") != "complete":
        return None
    seal = meta.get("results_sha256")      # final reports only (see seal_final_report)
    if not _is_sha256_hex(seal) or seal != _results_sha256(report):
        return None
    if meta.get("git_dirty") is not False:
        return None
    if not _is_git_hex(meta.get("git_commit")):
        return None
    opts = meta.get("options")
    if not isinstance(opts, dict):
        return None
    presets = opts.get("presets")
    base_flags = opts.get("base_flags")
    if (not isinstance(presets, list) or not presets
            or not all(isinstance(p, str) and p for p in presets)):
        return None
    if not isinstance(base_flags, str) or not base_flags:
        return None
    return list(presets), base_flags


def _score_tuple(value):
    """`value` as a comparable score tuple, or None unless it is a non-empty
    list/tuple of non-negative integers (bool excluded)."""
    if not isinstance(value, (list, tuple)) or not value:
        return None
    if not all(_is_int(v) and v >= 0 for v in value):
        return None
    return tuple(value)


def improved_t4_records(report, by_link=None):
    """Minimal machine-readable provenance records for residual T4 near misses.

    Only `MISMATCH` T4 rows of a completed, clean report (see
    `_report_provenance`) whose best attempt score strictly beats the score of
    the flags the ref file declares, and whose best flags differ from those, are
    kept: those are the residual functions a Wave 4B run would start from.  The
    canonical flags of the ref file are never changed here.  Each record is
    stamped with the report's own `presets`, `base_flags` and `omf_symbol_addrs`.
    `by_link` is retained for signature compatibility. Addresses come from the
    audit's scoring context, where `None` means a name was absent from the DB.
    `dependency_clean` describes the unresolved fixups of the best attempt.
    Eligibility comes from the attempts. Each retained row must reproduce the
    selected attempt and the digest binding the candidate, declared and best
    attempts, OMF summary and address stamp. A fresh audit supplies that evidence
    if it is missing or fails to reproduce.

    Returns `[]` for an incomplete/dirty report or one without valid
    `options.presets` / `options.base_flags`."""
    prov = _report_provenance(report)
    if prov is None:
        return []
    records, _ = _collect_improved_records(report, *prov)
    return records


def _collect_improved_records(report, presets, base_flags):
    """Return records and address-specific errors for eligible rows with invalid evidence."""
    results = report.get("results")
    if not isinstance(results, list):
        return [], []
    meta = report["meta"]
    tc = meta.get("toolchain") if isinstance(meta.get("toolchain"), dict) else {}
    out = []
    invalid = []
    for r in results:
        # Every row is sealed at audit time together with the report header, so
        # an edit to any row field (tier, status, attempts, first_diff, ...) or
        # to the bound header (toolchain, options, git state) is caught before
        # eligibility is decided.
        dig = r.get("row_sha256") if isinstance(r, dict) else None
        if not _is_sha256_hex(dig) or dig != _row_sha256(r, meta):
            invalid.append((r.get("addr") if isinstance(r, dict) else None,
                            "row_sha256 missing or mismatched (edited or pre-seal report); re-audit"))
            continue
        if r.get("tier") != "T4" or r.get("status") != "MISMATCH":
            continue
        attempts = r.get("attempts")
        attempts = attempts if isinstance(attempts, list) else []
        mismatches = [a for a in attempts if isinstance(a, dict) and a.get("result") == "MISMATCH"
                      and _score_tuple(a.get("score")) is not None]
        declared = next((a for a in mismatches if a.get("label") == "declared"), None)
        if declared is None:
            continue
        selected = min(mismatches, key=lambda a: tuple(a["score"]))   # first on ties
        decl_score, best_score = tuple(declared["score"]), tuple(selected["score"])
        if best_score >= decl_score:
            continue
        decl, best_flags = declared.get("cflags"), selected.get("cflags")
        if (isinstance(decl, str) and isinstance(best_flags, str)
                and _canon(best_flags) == _canon(decl)):
            continue
        addr = r.get("addr")
        row_flags = r.get("declared_cflags")
        best = r.get("best")
        syms = r.get("omf_symbol_addrs")
        omf = _normalized_omf_deps(r.get("omf_deps"))
        digest = _canonical_json_digest(omf) if omf is not None else None
        evidence_digest = r.get("omf_evidence_sha256")
        row_digest = r.get("row_evidence_sha256")
        unresolved = selected.get("unresolved")
        if (not isinstance(decl, str) or not isinstance(row_flags, str)
                or _canon(decl) != _canon(row_flags)):
            reason = "declared_cflags disagrees with the declared attempt"
        elif not isinstance(best, dict):
            reason = "missing or malformed best attempt"
        elif not isinstance(best_flags, str) or not _canon(best_flags) or best.get("cflags") != best_flags:
            reason = "best.cflags disagrees with the selected attempt"
        elif _score_tuple(best.get("score")) is None or best.get("score") != selected["score"]:
            reason = "best.score disagrees with the selected attempt"
        elif (not _valid_unresolved(unresolved) or not _valid_unresolved(best.get("unresolved"))
              or best["unresolved"] != unresolved):
            reason = "missing, malformed or mismatched best.unresolved"
        elif "omf_symbol_addrs" not in r:
            reason = "report predates audit-time symbol stamping; re-audit"
        elif digest is None:
            reason = "missing, incomplete or malformed omf_deps"
        elif not _valid_symbol_addrs(syms) or syms.keys() != _omf_names(omf):
            reason = "invalid omf_symbol_addrs for the OMF summary"
        elif (not _is_sha256_hex(evidence_digest)
              or evidence_digest != _omf_evidence_digest(omf, syms)):
            reason = "missing or mismatched omf_evidence_sha256"
        elif (not _is_sha256_hex(row_digest)
              or row_digest != _row_evidence_digest(r, declared, selected, omf, syms)):
            reason = "missing or mismatched row_evidence_sha256; re-audit"
        else:
            reason = None
        if reason is not None:
            invalid.append((addr, reason))
            continue
        rec = {
            "schema": IMPROVED_SCHEMA,
            "addr": addr, "addr_hex": r.get("addr_hex"),
            "name": r.get("name"), "link_name": r.get("link_name"),
            "module": r.get("module"), "ref": r.get("ref"), "toml": r.get("toml"),
            "declared_cc": r.get("declared_cc"), "declared_cflags": _canon(decl),
            "declared_score": list(decl_score),
            "best_flags": _canon(best_flags), "best_score": list(best_score),
            "first_diff": best.get("first_diff"),
            "unresolved": unresolved, "unresolved_count": len(unresolved),
            "dependency_clean": not unresolved,
            "omf_deps": omf, "omf_deps_sha256": digest,
            "symbols": dict(syms), "omf_evidence_sha256": evidence_digest,
            "row_evidence_sha256": row_digest,
            "compiler": tc.get("compiler"), "manifest_sha256": tc.get("manifest_sha256"),
            "tool_sig": tc.get("tool_sig"),
            "source_digest": r.get("source_digest"),
            "base_flags": base_flags, "presets": list(presets),
            "git_commit": meta.get("git_commit"),
        }
        record_digest = _record_digest(rec)
        if record_digest is None:
            invalid.append((addr, "record is not serializable as canonical JSON"))
            continue
        rec["record_sha256"] = record_digest
        out.append(rec)
    return sorted(out, key=_snapshot_record_key), invalid


def _iter_strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from _iter_strings(k)
            yield from _iter_strings(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _iter_strings(v)


def _is_host_path_token(tok):
    """A token that is an absolute host path: POSIX `/...`, UNC `\\\\...`, or
    a drive-letter `X:\\...` / `X:/...`."""
    if tok.startswith("/") or tok.startswith("\\\\"):
        return True
    return (len(tok) >= 3 and tok[0].isalpha() and tok[1] == ":"
            and tok[2] in ("\\", "/"))


def _has_host_path(s):
    """True when `s` contains an absolute host path, even embedded in flags.

    Tokens are split on whitespace, `=` and `,`; each token is also tried with
    a leading compiler-option prefix (`-i`, `-I`, `-fo`, `-fr`, `-fi`, `-fh`,
    `-d`, optionally followed by `=`) removed, so `-i/mnt/x/h` and
    `-foC:\\out.obj` are caught while relative keys (`repo:src/x.c`,
    `sys:stdio.h`), flag strings and hex digests are not."""
    if not isinstance(s, str) or not s:
        return False
    for tok in s.replace("=", " ").replace(",", " ").split():
        if _is_host_path_token(tok):
            return True
        for pre in _HOST_PATH_OPT_PREFIXES:
            if tok.startswith(pre):
                rest = tok[len(pre):]
                if rest.startswith("="):       # already split above; defensive
                    rest = rest[1:]
                if rest and _is_host_path_token(rest):
                    return True
    return False


def _assert_no_host_paths(obj):
    """Refuse to emit a snapshot carrying an absolute host checkout path."""
    for s in _iter_strings(obj):
        if _has_host_path(s):
            raise ValueError(f"improved-T4 snapshot would carry a host path: {s!r}")


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _is_git_hex(value):
    return (isinstance(value, str) and len(value) == 40
            and all(c in "0123456789abcdef" for c in value))


def _scrub_text(text):
    """Drop absolute host paths from a reason string."""
    words = []
    for w in str(text).split(" "):
        if _has_host_path(w) or _has_host_path(w.strip("'\"`()[]{}.,;:")):
            w = "<path>"
        words.append(w)
    return " ".join(words)


def _malformed(reason):
    return {"status": "malformed", "fresh": False,
            "reasons": [_scrub_text(f"malformed: {reason}")], "unchecked": [],
            "absent_symbols": []}


def _malformed_field(rec):
    """The first malformed-field reason of `rec`, or None."""
    if not isinstance(rec, dict):
        return "record is not a dict"
    if not _is_int(rec.get("schema")) or rec.get("schema") != IMPROVED_SCHEMA:
        return f"schema {rec.get('schema')!r} is not {IMPROVED_SCHEMA}"
    if not _valid_ref(rec.get("ref")):
        return f"ref {rec.get('ref')!r} is not a portable repository path"
    for key in ("source_digest", "omf_deps_sha256", "tool_sig", "manifest_sha256"):
        if not _is_sha256_hex(rec.get(key)):
            return f"{key} is not 64 lowercase hex"
    if not _is_git_hex(rec.get("git_commit")):
        return "git_commit is not 40 lowercase hex"
    if not isinstance(rec.get("compiler"), str) or not rec["compiler"]:
        return "compiler is not a non-empty str"
    presets = rec.get("presets")
    if (not isinstance(presets, list) or not presets
            or not all(isinstance(p, str) and p for p in presets)):
        return "presets is not a non-empty list of non-empty str"
    for key in ("base_flags", "declared_cflags"):
        if not isinstance(rec.get(key), str):
            return f"{key} is not a str"
    best_flags = rec.get("best_flags")
    if not isinstance(best_flags, str) or not _canon(best_flags):
        return "best_flags is not a non-empty str"
    if _canon(best_flags) == _canon(rec["declared_cflags"]):
        return "best_flags matches declared_cflags"
    for key in ("declared_score", "best_score"):
        if _score_tuple(rec.get(key)) is None:
            return f"{key} is not a non-empty sequence of non-negative integers"
    if tuple(rec["best_score"]) >= tuple(rec["declared_score"]):
        return "best_score does not improve on declared_score"
    link_name = rec.get("link_name")
    if not _valid_symbol_name(link_name):
        return "link_name is not a valid symbol name"
    addrs = rec.get("symbols")
    if not isinstance(addrs, dict) or not addrs:
        return "symbols is not a non-empty dict"
    if not _valid_symbol_addrs(addrs):
        return "symbols contains an invalid name or address"
    if not _is_int(addrs.get(link_name)):
        return f"symbols[{link_name!r}] is not an int (no real symbol addresses)"
    addr = rec.get("addr")
    if not _is_int(addr) or addr != addrs[link_name]:
        return "addr does not match the recorded address of link_name"
    if rec.get("addr_hex") != hex(addr):
        return "addr_hex does not match hex(addr)"
    deps = rec.get("omf_deps")
    if "omf_deps" in rec:
        if (not isinstance(deps, dict) or deps.keys() != set(_OMF_KEYS)
                or _omf_deps_digest(deps) != rec["omf_deps_sha256"]):
            return "omf_deps is malformed or does not reproduce the recorded digest"
        if addrs.keys() != _omf_names(deps):
            return "symbols does not cover exactly the OMF names"
    if "omf_evidence_sha256" in rec or "record_sha256" in rec:
        evidence_digest = rec.get("omf_evidence_sha256")
        if (deps is None or not _is_sha256_hex(evidence_digest)
                or evidence_digest != _omf_evidence_digest(deps, addrs)):
            return "omf_evidence_sha256 does not reproduce the OMF summary and symbol stamp"
    count = rec.get("unresolved_count")
    if not _is_int(count) or count < 0:
        return "unresolved_count is not a non-negative int"
    if not isinstance(rec.get("dependency_clean"), bool):
        return "dependency_clean is not a bool"
    if rec["dependency_clean"] != (count == 0):
        return "dependency_clean disagrees with unresolved_count"
    if "unresolved" in rec or "record_sha256" in rec or "row_evidence_sha256" in rec:
        unresolved = rec.get("unresolved")
        if not _valid_unresolved(unresolved):
            return "unresolved is missing or malformed"
        if count != len(unresolved):
            return "unresolved_count disagrees with the unresolved list"
        if deps is not None and any(not _matches_omf_fixup(f, deps, addrs) for f in unresolved):
            return "unresolved fixup disagrees with the OMF relocations or audit-time symbol stamp"
    if "row_evidence_sha256" in rec:
        declared = {"cflags": rec["declared_cflags"], "score": rec["declared_score"]}
        best = {"cflags": best_flags, "score": rec["best_score"], "unresolved": rec["unresolved"]}
        row_digest = rec["row_evidence_sha256"]
        if (deps is None or not _is_sha256_hex(row_digest)
                or row_digest != _row_evidence_digest(rec, declared, best, deps, addrs)):
            return "row_evidence_sha256 does not reproduce the bound audit fields"
    if "record_sha256" in rec:
        record_digest = rec["record_sha256"]
        if not _is_sha256_hex(record_digest) or record_digest != _record_digest(rec):
            return "record_sha256 does not reproduce the record"
    return None


_UNAVAILABLE = object()      # internal: "live identity already computed as unavailable"


def _check_improved_record(rec, *, repo_root=None, tool_sig=None, current_presets=None,
                           by_link=None, omf_deps=None):
    bad = _malformed_field(rec)
    if bad is not None:
        return _malformed(bad)
    root = repo_root or path()
    reasons = []
    presets = current_presets if current_presets is not None else _current_presets()
    if rec["presets"] != presets:
        reasons.append("presets: recorded preset list differs from the current one")
    if _canon(rec["base_flags"]) != _canon(match.BASE_CFLAGS):
        reasons.append("base_flags: recorded base flags differ from match.BASE_CFLAGS")
    dig = portable_source_digest(rec["ref"], repo_root=root)
    if dig is None:
        reasons.append(f"source_digest: {rec['ref']} is unreadable or outside the checkout")
    elif dig != rec["source_digest"]:
        reasons.append(f"source_digest: {rec['ref']} or an included header changed")
    if tool_sig is _UNAVAILABLE:
        live = None
    elif tool_sig is not None:
        live = tool_sig
    else:
        live = _tool_sig(root)
    if not live:
        reasons.append("tool_sig: live toolchain identity unavailable")
    elif live != rec["tool_sig"]:
        reasons.append("tool_sig: recorded toolchain identity differs from the live one")
    try:
        declared = short_flags(match.file_cflags(os.path.join(str(root), rec["ref"])))
    except (OSError, SystemExit, ValueError):
        reasons.append(f"declared_cflags: {rec['ref']} is unreadable")
    else:
        if _canon(declared) != _canon(rec["declared_cflags"]):
            reasons.append("declared_cflags: the ref file's declared flags changed")
    if omf_deps is not None:
        digest = _omf_deps_digest(omf_deps)
        if digest is None:
            reasons.append("omf_deps: summary is incomplete or malformed")
        elif digest != rec["omf_deps_sha256"]:
            reasons.append("omf_deps: summary does not reproduce the recorded digest")
    unchecked = [] if "omf_deps" in rec else ["symbol_coverage"]
    if "row_evidence_sha256" not in rec or "record_sha256" not in rec:
        unchecked.append("record_integrity")
    absent = sorted(s for s, a in rec["symbols"].items() if a is None)
    if isinstance(by_link, dict):
        moved = _changed_symbols(rec["symbols"], by_link)
        if moved:
            reasons.append("symbols: addresses or presence changed: " + ", ".join(moved))
    else:
        unchecked.append("symbols")
    if reasons:
        return {"status": "stale", "fresh": False,
                "reasons": [_scrub_text(r) for r in reasons], "unchecked": [],
                "absent_symbols": absent}
    if unchecked:
        return {"status": "partial", "fresh": False, "reasons": [], "unchecked": unchecked,
                "absent_symbols": absent}
    return {"status": "fresh", "fresh": True, "reasons": [], "unchecked": [],
            "absent_symbols": absent}


def check_improved_record(rec, *, repo_root=None, tool_sig=None, current_presets=None,
                          by_link=None, omf_deps=None):
    """Provenance check of an `improved_t4_records` entry (never raises).

    Returns `{"status": "fresh"|"stale"|"partial"|"malformed", "fresh": bool,
    "reasons": [...], "unchecked": [...], "absent_symbols": [...]}`.

    Checks the live sources and headers, toolchain, presets and flags, and
    symbol DB. The embedded `omf_deps` accounts for every stamped symbol and
    corroborates unresolved fixups. `row_evidence_sha256` binds the candidate,
    attempts, OMF summary and symbol stamp. `record_sha256` covers the full
    record. Malformed fields and edits or mixed evidence that fail to reproduce
    a digest are rejected. A deliberate rewrite can reproduce every digest.

    Legacy records missing either digest have `record_integrity` unchecked,
    plus `symbol_coverage` if they lack the summary. The optional `omf_deps`
    argument checks an independent summary against the summary digest.
    Staleness takes precedence over a partial check. If in doubt, re-audit.

    `by_link` must be the complete symbol DB of the checked checkout. Passing
    a partial map that makes a name appear absent is a caller error. Without
    a dict, symbol addresses are unchecked. `absent_symbols` lists the names
    absent from the DB at audit time (recorded as `None`). A name that appears
    later makes the record stale. `unresolved_count` counts unresolved external
    fixups in the best attempt, and `dependency_clean` is true when that count
    is zero. An absent local _TEXT name can coexist with `dependency_clean`."""
    try:
        return _check_improved_record(rec, repo_root=repo_root, tool_sig=tool_sig,
                                      current_presets=current_presets, by_link=by_link,
                                      omf_deps=omf_deps)
    except Exception as ex:              # never let a malformed record crash a caller
        return _malformed(f"{type(ex).__name__}: {ex}")


def _snapshot_digest(snap):
    """Digest of a whole snapshot document without its `snapshot_sha256`; the
    records enter as their sorted `record_sha256` values, so record order does
    not matter but every record, header field, summary and stat is bound."""
    doc = {k: v for k, v in snap.items() if k not in ("snapshot_sha256", "records")}
    records = snap.get("records")
    if isinstance(records, list):
        doc["records"] = sorted(str(r.get("record_sha256")) if isinstance(r, dict) else repr(r)
                                for r in records)
    else:
        doc["records"] = repr(records)
    return _canonical_json_digest(doc)


def build_improved_audit_snapshot(report, *, by_link, campaign=None, repo_root=None,
                                  tool_sig=None):
    """Reproducible `t4_improved_audit.json` document from a t3_audit report.

    Refuses an incomplete or dirty report (see `_report_provenance`), a report
    whose `toolchain.tool_sig` is not the live identity, a non-portable/stale
    record, and any absolute host path. `by_link` must be the complete, non-empty
    symbol DB of the checked checkout. Every retained audit-time symbol stamp
    must match that DB. Any otherwise-eligible improved row with missing or
    inconsistent attempt evidence or a mismatched row digest requires a re-audit.
    The snapshot also records a digest of the sorted record digests."""
    if not isinstance(by_link, dict) or not by_link:
        raise ValueError("by_link must be a non-empty dict of symbol entries")
    prov = _report_provenance(report)
    if prov is None:
        raise ValueError("cannot snapshot an incomplete/dirty audit report "
                         "without valid options.presets and options.base_flags")
    live = tool_sig if tool_sig is not None else _tool_sig(repo_root)
    if not live:
        raise ValueError("live toolchain identity unavailable")
    meta = report["meta"]
    tc = meta.get("toolchain") if isinstance(meta.get("toolchain"), dict) else {}
    if tc.get("tool_sig") != live:
        raise ValueError("report toolchain.tool_sig does not match the live toolchain identity")
    presets, base_flags = prov
    records, invalid = _collect_improved_records(report, presets, base_flags)
    if invalid:
        errors = [f"{hex(addr) if _is_int(addr) else 'unknown address'}: {reason}"
                  for addr, reason in invalid]
        raise ValueError("cannot snapshot improved-T4 rows with invalid evidence: "
                         + " | ".join(errors))
    bad = []
    for rec in records:
        if _changed_symbols(rec["symbols"], by_link):
            raise ValueError("symbol DB changed since the audit; re-audit")
        chk = check_improved_record(rec, repo_root=repo_root, tool_sig=live, by_link=by_link)
        if chk["status"] != "fresh":
            bad.append(f"{rec.get('addr_hex')}: " + "; ".join(chk["reasons"]))
    if bad:
        raise ValueError("cannot snapshot stale/non-portable improved-T4 records: "
                         + " | ".join(bad[:5]))
    snap = {
        "schema": IMPROVED_SCHEMA, "tool": "wc1.t3_audit", "kind": "t4_improved_audit",
        "campaign": campaign, "description": IMPROVED_DESCRIPTION,
        "git_commit": meta.get("git_commit"), "git_dirty": meta.get("git_dirty"),
        "presets": list(presets), "base_flags": base_flags,
        "toolchain": {"compiler": tc.get("compiler"),
                      "manifest_sha256": tc.get("manifest_sha256"), "tool_sig": live},
        "audit_stats_t4": ((report.get("stats") or {}).get("T4")),
        "summary": {"improved_total": len(records),
                    "improved_dependency_clean": sum(1 for r in records if r["dependency_clean"]),
                    "verified_fresh": len(records)},
        "records_sha256": _canonical_json_digest(sorted(r["record_sha256"] for r in records)),
        "records": records,
    }
    snap["snapshot_sha256"] = _snapshot_digest(snap)
    _assert_no_host_paths(snap)
    return snap


def _is_sha256_hex(value):
    return (isinstance(value, str) and len(value) == 64
            and all(c in "0123456789abcdef" for c in value))


def _snapshot_record_key(rec):
    if not isinstance(rec, dict):
        return (1, "")
    addr = rec.get("addr")
    return (0, addr) if _is_int(addr) else (1, str(rec.get("addr_hex") or ""))


def _check_improved_snapshot(snap, *, by_link, repo_root=None, tool_sig=None):
    root = repo_root or path()
    problems = []
    unchecked = []
    if not isinstance(snap, dict):
        problems.append("malformed: snapshot is not a dict")
        snap = {}
    if snap.get("kind") != "t4_improved_audit":
        problems.append(f"malformed: kind {snap.get('kind')!r} is not 't4_improved_audit'")
    if not _is_int(snap.get("schema")) or snap.get("schema") != IMPROVED_SCHEMA:
        problems.append(f"malformed: schema {snap.get('schema')!r} is not {IMPROVED_SCHEMA}")
    if snap.get("git_dirty") is not False:
        problems.append("malformed: git_dirty is not False")
    if not _is_git_hex(snap.get("git_commit")):
        problems.append("malformed: git_commit is not 40 lowercase hex")
    records = snap.get("records")
    if not isinstance(records, list):
        problems.append("malformed: records is not a list")
        records = []
    if not records:
        problems.append("malformed: records list is empty (nothing is verified)")
    addr_counts = Counter(r["addr"] for r in records
                          if isinstance(r, dict) and _is_int(r.get("addr")))
    duplicates = {addr for addr, count in addr_counts.items() if count > 1}
    if duplicates:
        problems.append("malformed: duplicate record addresses: "
                        + ", ".join(map(hex, sorted(duplicates))))
    summary = snap.get("summary")
    clean_count = sum(isinstance(r, dict) and r.get("dependency_clean") is True for r in records)
    # verified_fresh records the build-time count. Live records can become stale.
    for key, expected in (("improved_total", len(records)), ("improved_dependency_clean", clean_count),
                          ("verified_fresh", len(records))):
        actual = summary.get(key) if isinstance(summary, dict) else None
        if not _is_int(actual) or actual != expected:
            problems.append(f"malformed: summary.{key} disagrees with the records")
    if "snapshot_sha256" not in snap:
        unchecked.append("snapshot_integrity")
    elif (not _is_sha256_hex(snap.get("snapshot_sha256"))
          or snap["snapshot_sha256"] != _snapshot_digest(snap)):
        problems.append("malformed: snapshot_sha256 does not reproduce the snapshot document")
    if "records_sha256" not in snap:
        unchecked.append("record_set_integrity")
    else:
        digests = [r.get("record_sha256") if isinstance(r, dict) else None for r in records]
        if (not all(_is_sha256_hex(digest) for digest in digests)
                or snap["records_sha256"] != _canonical_json_digest(sorted(digests))):
            problems.append("malformed: records_sha256 does not reproduce the record set")
    live = tool_sig if tool_sig is not None else _tool_sig(root)
    tc = snap.get("toolchain") if isinstance(snap.get("toolchain"), dict) else {}
    header = {"presets": snap.get("presets"), "base_flags": snap.get("base_flags"),
              "git_commit": snap.get("git_commit"), "tool_sig": tc.get("tool_sig"),
              "compiler": tc.get("compiler"), "manifest_sha256": tc.get("manifest_sha256")}
    if header["presets"] != current_presets():
        problems.append("stale: header presets differ from the current preset list")
    if not isinstance(header["base_flags"], str) or _canon(header["base_flags"]) != _canon(match.BASE_CFLAGS):
        problems.append("stale: header base_flags differ from match.BASE_CFLAGS")
    if not live:
        problems.append("stale: live toolchain identity unavailable")
    elif header["tool_sig"] != live:
        problems.append("stale: header toolchain.tool_sig differs from the live identity")
    counts = {"total": len(records), "fresh": 0, "stale": 0, "partial": 0, "malformed": 0}
    reason_counts = {}
    out = []
    live_arg = live if live is not None else _UNAVAILABLE
    for rec in sorted(records, key=_snapshot_record_key):
        chk = check_improved_record(rec, repo_root=root, tool_sig=live_arg, by_link=by_link)
        if isinstance(rec, dict) and chk["status"] != "malformed":
            mism = [key for key in header if key != "base_flags" and rec.get(key) != header[key]]
            if (not isinstance(header["base_flags"], str)
                    or _canon(rec.get("base_flags")) != _canon(header["base_flags"])):
                mism.append("base_flags")
            if rec["addr"] in duplicates:
                chk = _malformed("duplicate record address")
            elif mism:
                chk = _malformed(f"{'/'.join(mism)} disagree with the snapshot header")
        counts[chk["status"]] += 1
        for reason in chk["reasons"]:
            cat = reason.split(":", 1)[0].strip() or "malformed"
            reason_counts[cat] = reason_counts.get(cat, 0) + 1
        addr_hex = rec.get("addr_hex") if isinstance(rec, dict) else None
        name = rec.get("name") if isinstance(rec, dict) else None
        ref = rec.get("ref") if isinstance(rec, dict) else None
        out.append({"addr_hex": _scrub_text(addr_hex) if isinstance(addr_hex, str) else addr_hex,
                    "name": _scrub_text(name) if isinstance(name, str) else name,
                    "ref": _scrub_text(ref) if isinstance(ref, str) else ref,
                    "status": chk["status"],
                    "reasons": [_scrub_text(r) for r in chk["reasons"]],
                    "unchecked": list(chk["unchecked"]),
                    "absent_symbols": chk["absent_symbols"]})
    campaign = snap.get("campaign")
    return {
        "snapshot": {"schema": snap.get("schema"),
                     "campaign": _scrub_text(campaign) if isinstance(campaign, str) else campaign,
                     "git_commit": snap.get("git_commit"), "records": len(records)},
        "live": {"tool_sig": live, "presets": current_presets(),
                 "base_flags": match.BASE_CFLAGS},
        "counts": counts,
        "fresh_with_absent_symbols": sum(1 for o in out
                                         if o["status"] == "fresh" and o["absent_symbols"]),
        "reason_counts": reason_counts,
        "snapshot_problems": [_scrub_text(p) for p in problems],
        "snapshot_unchecked": unchecked,
        "records": out,
    }


def check_improved_snapshot(snap, *, by_link, repo_root=None, tool_sig=None):
    """Snapshot-level provenance report for `improved_t4_records` (never raises).

    Checks the header, summary counts and sorted digest list for missing,
    duplicate or substituted records. Duplicate addresses and records whose
    provenance disagrees with the header are malformed. A legacy header without
    `records_sha256` leaves `record_set_integrity` unchecked. A deliberate
    rewrite can reproduce every digest. If in doubt, re-audit.

    Checks each record against the checkout's sources and headers, toolchain,
    presets and flags, and complete symbol DB (`by_link`). Returns counts,
    `fresh_with_absent_symbols`, reason categories, snapshot problems and
    unchecked dimensions, and one entry per record sorted by address."""
    try:
        return _check_improved_snapshot(snap, by_link=by_link, repo_root=repo_root,
                                        tool_sig=tool_sig)
    except Exception as ex:              # never let a malformed snapshot crash a caller
        return {
            "snapshot": {"schema": None, "campaign": None, "git_commit": None, "records": 0},
            "live": {"tool_sig": None, "presets": current_presets(),
                     "base_flags": match.BASE_CFLAGS},
            "counts": {"total": 0, "fresh": 0, "stale": 0, "partial": 0, "malformed": 0},
            "fresh_with_absent_symbols": 0,
            "reason_counts": {"malformed": 1},
            "snapshot_problems": [_scrub_text(f"malformed: {type(ex).__name__}: {ex}")],
            "snapshot_unchecked": [],
            "records": [],
        }


def is_improved_record_fresh(rec, *, repo_root=None, tool_sig=None, current_presets=None,
                             by_link=None, omf_deps=None):
    """Full freshness check for an `improved_t4_records` entry.

    Returns `check_improved_record(...)["fresh"]`. A fresh record has complete
    provenance and its symbol stamp matches the complete checkout DB in
    `by_link`."""
    return check_improved_record(rec, repo_root=repo_root, tool_sig=tool_sig,
                                 current_presets=current_presets, by_link=by_link,
                                 omf_deps=omf_deps)["fresh"]



def _brief(r):
    b = {k: r.get(k) for k in ("addr_hex", "name", "module", "ref", "toml", "status",
                               "declared_cflags", "match_flags", "flags_change", "reason")}
    if r.get("best"):
        b.update(best_flags=r["best"]["cflags"], score=r["best"]["score"],
                 counts=r["best"].get("counts"), first_diff=r["best"].get("first_diff"))
    return {k: v for k, v in b.items() if v is not None}


def _row_binding(meta):
    """The report-header fields every row digest is bound to."""
    meta = meta if isinstance(meta, dict) else {}
    tc = meta.get("toolchain") if isinstance(meta.get("toolchain"), dict) else {}
    opts = meta.get("options") if isinstance(meta.get("options"), dict) else {}
    return {"git_commit": meta.get("git_commit"), "git_dirty": meta.get("git_dirty"),
            "toolchain": {k: tc.get(k) for k in ("compiler", "manifest_sha256", "tool_sig")},
            "options": {k: opts.get(k) for k in ("cc", "presets", "base_flags",
                                                 "include_unverified")}}


def _row_sha256(row, meta):
    """Digest of a whole report row (without `row_sha256`) bound to the header."""
    if not isinstance(row, dict):
        return None
    return _canonical_json_digest({"row": {k: v for k, v in row.items() if k != "row_sha256"},
                                   "meta": _row_binding(meta)})


def _results_sha256(report):
    """Digest of the whole final report document (every top-level field, the whole
    `meta` except this seal, and every row in order); None for a malformed report."""
    meta = report.get("meta") if isinstance(report, dict) else None
    rows = report.get("results") if isinstance(report, dict) else None
    if not isinstance(meta, dict) or not isinstance(rows, list):
        return None
    doc = dict(report)                      # the whole document: schema, stats,
    doc["meta"] = {k: v for k, v in meta.items() if k != "results_sha256"}   # near misses, ...
    return _canonical_json_digest(doc)


def seal_final_report(report):
    """Stamp a *final* report with `meta.results_sha256` (in place).  Checkpoint
    reports never carry it, so an edited checkpoint cannot pass as complete."""
    if isinstance(report, dict) and isinstance(report.get("meta"), dict):
        report["meta"]["results_sha256"] = _results_sha256(report)
    return report


def seal_report_rows(report):
    """Stamp every `results` row with its `row_sha256` and the report with its
    final `results_sha256` (in place; for reports assembled outside `run()`)."""
    meta = report.get("meta")
    if isinstance(report.get("results"), list):
        report["results"] = [dict(r, row_sha256=_row_sha256(r, meta)) if isinstance(r, dict) else r
                             for r in report["results"]]
    return seal_final_report(report)


def build_report(meta, results, issues):
    results = sorted(results, key=lambda r: r["addr"])
    results = [dict(r, row_sha256=_row_sha256(r, meta)) for r in results]
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
    gd = m.get("git_dirty")
    dirty = (" (src/analysis/tools/tests dirty)" if gd is True
             else " (git state unknown)" if gd is None else "")
    L += [f"- commit: `{m['git_commit']}`" + dirty,
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
    ap.add_argument("--check-improved", default=None, metavar="FILE",
                    help="read-only provenance check of an improved-T4 snapshot: print JSON, "
                         "exit 0 only when every record is fresh and the header is clean")
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
    git_status = _git("status", "--porcelain", "--", "src", "analysis", "tools", "tests")
    meta = {"tool": "wc1.t3_audit", "started": _now(), "finished": None,
            "git_commit": _git("rev-parse", "HEAD"),
            # None means the status could not be read (unknown, never "clean")
            "git_dirty": None if git_status is None else bool(git_status),
            "toolchain": toolchain_id(),
            "invocation": ["python3", "-m", "wc1.t3_audit"] + list(argv),
            "options": {"jobs": a.jobs, "include_unverified": a.include_unverified, "cc": CC,
                        "presets": current_presets(), "base_flags": match.BASE_CFLAGS,
                        "plan": "declared flags, then wc1.permuter 10.0a presets"},
            "scope": {"tiers": ["T4", "ref"] if a.include_unverified else ["T4"],
                      "in_scope_t4": sum(1 for c in cands if c["tier"] == "T4"),
                      "filters": filters, "full_scope": not filters},
            "completion": {"status": "running", "selected": len(sel), "audited": 0, "note": None},
            "compiles": 0}
    results = {c["addr"]: _skipped(c, c["skip_reason"]) for c in sel if c["skip_reason"]}
    meta["toolchain"]["tool_sig"] = _tool_sig()
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
    report = seal_final_report(build_report(meta, list(results.values()), issues))
    write_reports(outdir, report, final=True)
    t4 = report["stats"]["T4"]
    log(f"{status}: {t4['total']} T4: " + ", ".join(f"{k} {t4[k]}" for k in STATUSES)
        + f"; reports in {os.path.relpath(outdir, path())}/")
    return code


def check_improved_file(fn, *, repo_root=None, tool_sig=None, by_link=None):
    """`--check-improved`: read-only snapshot check, JSON to stdout, exit code.

    Loads `by_link` from `symbols.load()` when not injected (tests do); fails
    closed if `by_link is None` and `repo_root` resolves to a different checkout
    than `path()`, since `symbols.load()` reads the active checkout (validating
    another checkout requires an explicit `by_link` or running with `WC1_ROOT`
    set to that checkout). Prints the `check_improved_snapshot` document and
    exits 0 only when every record is fresh and the snapshot has no problems or
    unchecked dimensions."""
    try:
        with open(fn, encoding="utf-8") as fh:
            snap = json.load(fh)
    except (OSError, ValueError) as ex:
        print(f"[CHECK IMPROVED ERROR] cannot read {fn}: {ex}", file=sys.stderr)
        return 1
    if by_link is None:
        if repo_root is not None and os.path.realpath(str(repo_root)) != os.path.realpath(path()):
            print("[CHECK IMPROVED ERROR] validating another checkout requires an explicit "
                  "by_link (or running with WC1_ROOT set to that checkout)", file=sys.stderr)
            return 1
        funcs, datas, errors = symbols.load(strict=False)
        if errors:                       # symbol addresses are evidence: no partial DB
            print(f"[CHECK IMPROVED ERROR] symbol database has {len(errors)} error(s); "
                  f"first: {errors[0]}", file=sys.stderr)
            return 1
        by_link = {e["link_name"]: e for t in (funcs, datas) for e in t.values()
                   if e.get("link_name")}
    res = check_improved_snapshot(snap, by_link=by_link, repo_root=repo_root,
                                  tool_sig=tool_sig)
    print(json.dumps(res, indent=1, sort_keys=True))
    counts = res["counts"]
    if res["snapshot_problems"] or res["snapshot_unchecked"]:
        return 1
    return 0 if counts["fresh"] == counts["total"] else 1


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    a = parse_args(argv)
    if a.check_improved is not None:
        return check_improved_file(a.check_improved)
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
