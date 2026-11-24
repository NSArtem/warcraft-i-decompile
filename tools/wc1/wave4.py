"""Wave 4: T4 -> T3 recovery (one confirmed T4 function per task).

A T4 function has reference C whose behaviour a difftest verified (wc1.progress
"T4").  Wave 4 tries to turn it into T3 (`src =`, byte-identical under Watcom
10.0a).  Per function, breadth first, one bounded attempt:

  A  prepare evidence: the candidate, its ref file, the declared flags
  B  deterministic check: wc1.t3_audit.audit_unit (declared flags, then the 10.0a
     presets; exact match + in-place buildability), 0 LLM tokens
  C  bounded LLM repair of the ref C (minimal patches, never a rewrite) while the
     audit still reports a MISMATCH; the file is restored if it never matches
  D  the T4 difftest cited by the entry must still pass on the patched file
  E  on an exact buildable match: `ref` -> `src` in the TOML (+ the file's codegen
     flags header); wc1.overnight then runs make verify and commits or rolls back

The outcome of an attempt goes to build/wave4/outcomes/<addr>.json
(PROMOTED, NO_IMPROVEMENT, UNBUILDABLE, FAILED, TOOLCHAIN_ERROR); diagnostics and
the audit rows to build/wave4/diag/.  Nothing here edits a file unless the
function is PROMOTED (the ref file is restored on every other outcome).
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import tomllib
from bisect import bisect_right
from pathlib import Path

from . import match, oldcc, path, symbols, t3_audit

PROMOTED, NO_IMPROVEMENT, UNBUILDABLE = "PROMOTED", "NO_IMPROVEMENT", "UNBUILDABLE"
FAILED, TOOLCHAIN_ERROR = "FAILED", "TOOLCHAIN_ERROR"
OUTCOMES = (PROMOTED, NO_IMPROVEMENT, UNBUILDABLE, FAILED, TOOLCHAIN_ERROR)
REPORT = ("build", "t3_audit", "report.json")
OUT_DIR = ("build", "wave4")
CODEX_RECOVERY_STAGE = "stage4"
CLAUDE_RECOVERY = ("sonnet", "medium")
# Bump when the audit/matcher or repair algorithm (including prompt/schema) changes.
RECOVERY_VERSION = 3

REPAIR_SCHEMA = {
    "type": "object",
    "properties": {
        "diagnosis": {"type": "string",
                      "description": "One line: the first differing instruction and the C spelling that causes it"},
        "patches": {"type": "array", "items": {
            "type": "object",
            "properties": {"old": {"type": "string"}, "new": {"type": "string"}},
            "required": ["old", "new"]}},
    },
    "required": ["diagnosis", "patches"],
}

REPAIR_RULES = (
    "You repair reference C so Watcom 10.0a produces the original machine code EXACTLY.\n"
    "The C is already behaviourally verified against the original (a difftest): MODIFY it with the "
    "fewest changes, do NOT regenerate or restructure it, and keep its behaviour.\n"
    "Change only spellings that steer code generation (operand order, types, temporaries, ?: vs if, "
    "loop shape, volatile / bitfield views).  Do not touch comments, the codegen headers, tests or "
    "any other file.  Return search-and-replace patches: 'old' must occur exactly once in the file."
)


# --- A: discovery and ordering --------------------------------------------------

def report_path():
    return path(*REPORT)


def _git(*args):
    r = subprocess.run(["git", *args], cwd=path(), capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def load_report(report_file=None, head=None, dirty=None):
    """(state, report): state is fresh | stale | missing | invalid.  Fresh means
    meta.git_commit is HEAD and the audited tree was clean, and the tree now
    has no uncommitted src/analysis/tools/tests change (the audit's own
    definition of git_dirty)."""
    fn = report_file or report_path()
    if not os.path.isfile(fn):
        return "missing", None
    try:
        with open(fn) as fh:
            rep = json.load(fh)
        meta = rep["meta"]
        rep["results"]
    except (OSError, ValueError, KeyError, TypeError):
        return "invalid", None
    if not isinstance(meta, dict) or not meta.get("git_commit"):
        return "invalid", None
    head = head if head is not None else _git("rev-parse", "HEAD")
    if dirty is None:
        dirty = bool(_git("status", "--porcelain", "--", "src", "analysis", "tools", "tests"))
    complete = (meta.get("completion") or {}).get("status") == "complete"
    if meta["git_commit"] != head or meta.get("git_dirty") or dirty or not complete:
        return "stale", rep
    return "fresh", rep


def eligible(c):
    """A candidate Wave 4 may process: in-scope T4, an auditable ref file, a
    well-formed difftest citation (the audit already skipped invalid entries)."""
    if c["tier"] != "T4" or c["skip_reason"] or not c["ref"]:
        return False
    nodes, err = symbols.parse_ref_verified_by_nodes(c.get("ref_verified_by") or "")
    return not err and bool(nodes)


def order_key(c, row):
    """(group, sort key) - lower first.  Groups: 0 audited exact + buildable,
    1 near miss (by score), 2 not audited / unknown (no t3_blocker first: never
    tried), 3 exact match that does not build (handled last, separately)."""
    st = (row or {}).get("status")
    if st == "MATCH_BUILDABLE":
        return (0, (), c["ref"], c["addr"])
    if st == "MISMATCH" and (row.get("best") or {}).get("score"):
        return (1, tuple(row["best"]["score"]), c["ref"], c["addr"])
    if st == "MATCH_UNBUILDABLE":
        return (3, (), c["ref"], c["addr"])
    return (2, (1 if c.get("t3_blocker") else 0,), c["ref"], c["addr"])


def discover(inputs=None, report=None, report_state=None):
    """Eligible T4 functions in processing order.  Returns (queue, info); queue
    entries are the t3_audit candidates plus group / audit_status.  A
    missing / stale / invalid report is not an error: the ordering is then the
    deterministic fallback (group 2 for everyone)."""
    p, funcs, by_link, rows, issues = inputs or t3_audit.load_inputs()
    cands, d_issues = t3_audit.discover(funcs, rows)
    if report_state is None:
        report_state, report = load_report()
    ninsns = {f["start"]: f["ninsns"] for f in p.functions}
    by_addr = {}
    if report_state == "fresh" and report:
        by_addr = {r["addr"]: r for r in report["results"]}
    out = []
    for c in cands:
        if not eligible(c):
            continue
        row = by_addr.get(c["addr"])
        k = order_key(c, row)
        out.append(dict(c, group=k[0], audit_status=(row or {}).get("status"), ninsns=ninsns.get(c["addr"], 0),
                        _key=k))
    out.sort(key=lambda c: c["_key"])
    for c in out:
        c.pop("_key")
    return out, {"report": report_state, "eligible": len(out), "issues": list(issues) + d_issues,
                 "matcher_signature": matcher_signature(p.functions, by_link)}


def matcher_signature(functions, by_link):
    """The address/extent and link-name map audit/match actually consult,
    without confidence, prose evidence, or Git revision."""
    resolved = sorted((name, row["addr"], row.get("_kind")) for name, row in by_link.items())
    extents = sorted((row["start"], row.get("end")) for row in functions)
    return hashlib.sha256(json.dumps([resolved, extents]).encode()).hexdigest()


def next_candidate(queue, skip_addrs=()):
    skip = set(skip_addrs)
    return next((c for c in queue if c["addr"] not in skip), None)


_INCLUDE = re.compile(r"(?:#|%:)[ \t\f\v]*(include\w*|import|embed)\b[ \t\f\v]*([^\r\n]*)")
_TRIGRAPH = re.compile(rb"\?\?[=/'()!<>-]")


def _literal_includes(data):
    # C splices lines and replaces comments with spaces before preprocessing.
    # Search conservatively (also see directives with comment prefixes or
    # continuations); a false positive just disables the cache for this unit.
    if _TRIGRAPH.search(data):
        # C90 expands these before recognizing quotes and comments. Do not
        # risk interpreting a real include as part of either one.
        raise ValueError("trigraphs in preprocessor input")
    text = _C_SPLICE.sub("", data.decode("latin-1"))
    pieces, offset = [], 0
    for start, end, _ in _c_comments(text):
        pieces.extend((text[offset:start], " "))
        offset = end
    pieces.append(text[offset:])
    for keyword, directive in _INCLUDE.findall("".join(pieces)):
        m = re.fullmatch(r'(?:"([^"]+)"|<([^>]+)>)[ \t\f\v]*', directive)
        if keyword != "include" or not m:
            raise ValueError("unsupported or nonliteral include")
        yield os.fsdecode((m[1] or m[2]).encode("latin-1")).replace("\\", "/")


def _source_inputs(src, include_dirs):
    """Hash the translation unit and its literal includes. Fail open on a
    dependency we can't resolve rather than caching under an incomplete key."""
    hashes, pending = {}, [src]
    while pending:
        fn = pending.pop()
        if fn in hashes:
            continue
        data = fn.read_bytes()
        hashes[fn] = hashlib.sha256(data).hexdigest()
        for name in _literal_includes(data):
            # Hash every possible local resolution, including shadowed headers.
            deps = [d / name for d in (fn.parent, *include_dirs) if (d / name).is_file()]
            if not deps:
                raise ValueError(f"unresolved include: {name}")
            pending.extend(f.resolve() for f in deps)
    return {str(fn): digest for fn, digest in hashes.items()}


def _complete_miss(result, addr, max_calls):
    if (not isinstance(result, dict) or result.get("addr") != f"{addr:#x}"
            or result.get("outcome") != NO_IMPROVEMENT or result.get("complete_search") is not True
            or type(result.get("llm_calls")) is not int or result["llm_calls"] != max_calls or max_calls < 1):
        return False
    history = result.get("history")
    return (isinstance(result.get("ts"), str) and isinstance(history, list) and len(history) == max_calls + 1
            and all(isinstance(entry, dict) and type(entry.get("call")) is int and entry["call"] == i
                    for i, entry in enumerate(history))
            and history[0].get("status") == "MISMATCH"
            and all(isinstance(entry.get("diagnosis"), str) and type(entry.get("applied")) is int
                    for entry in history[1:]))


class RetryCache:
    """Completed search misses only, independent of the live outcome/diagnostic files."""

    def __init__(self, provider, model_effort, max_calls, max_cost=None):
        self.max_calls = int(max_calls)
        cc_root = Path(oldcc.root())
        self.system_headers = cc_root / "h"
        self.settings = None
        self.skipped = 0
        # These compiler overrides can bring in dependencies outside our include search.
        if os.environ.get("INCLUDE") or os.environ.get("WCC386"):
            return
        files = [Path(path("original", "install", "war.exe")),
                 cc_root / "binnt/wcc386.exe", cc_root / "binb/wcc386.exe"]
        try:
            self.settings = {
                "version": RECOVERY_VERSION, "compiler": t3_audit.CC, "base_flags": match.BASE_CFLAGS,
                "tool_inputs": [hashlib.sha256(f.read_bytes()).hexdigest() for f in files],
                "provider": provider, "model_effort": list(model_effort), "max_calls": self.max_calls,
                "max_cost": max_cost if provider == "claude" else None,
            }
        except OSError:
            pass

    def fingerprint(self, cand, siblings, matcher):
        if self.settings is None or not matcher:
            return None
        try:
            src = Path(path(cand["ref"])).resolve()
            plan = t3_audit.attempt_plan(cand["declared_cflags"])
            if any(f.lower().startswith(("-i", "/i", "-fi", "/fi", "@"))
                   for _, flags in plan for f in flags.split()):
                return None
            files = _source_inputs(src, (src.parent, Path(path("src", "include")), self.system_headers))
            fields = ("addr", "name", "link_name", "ref", "declared_cc", "declared_cflags", "ref_verified_by")
            unit = [{k: c.get(k) for k in fields} for c in sorted(siblings, key=lambda c: c["addr"])]
            data = dict(self.settings, addr=cand["addr"], sources=files, unit=unit, plan=plan, matcher=matcher)
            return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        except (KeyError, OSError, ValueError):
            return None

    def _file(self, addr, key):
        return path(*OUT_DIR, "retry", f"{addr:x}", f"{key}.json")

    def contains(self, addr, key):
        try:
            rec = json.loads(Path(self._file(addr, key)).read_bytes()) if key else None
        except (OSError, ValueError):
            return False
        return (isinstance(rec, dict) and rec.get("fingerprint") == key and rec.get("settings") == self.settings
                and _complete_miss(rec.get("result"), addr, self.max_calls))

    def remember(self, addr, key, result):
        if key and _complete_miss(result, addr, self.max_calls):
            _write_json(self._file(addr, key), {"fingerprint": key, "settings": self.settings, "result": result})


# --- E: TOML promotion ----------------------------------------------------------

_KEYS_DROPPED = ("ref", "ref_verified_by", "t3_blocker")


def promote_toml_text(text, addr, src, verified_by, evidence_line):
    """Rewrite the [[func]] block of addr: drop ref / ref_verified_by /
    t3_blocker, set confidence verified, add src + verified_by and one evidence
    line.  Text edit, the rest of the file is untouched.  ValueError if the
    block is not a plain T4 entry."""
    # A trailing [[data]] (or other table) is not part of the last [[func]].
    blocks = list(re.finditer(r"(?m)^\[\[(\w+)\]\][ \t]*(?:#[^\n]*)?\n", text))
    for i, m in enumerate(blocks):
        if m[1] != "func":
            continue
        end = blocks[i + 1].start() if i + 1 < len(blocks) else len(text)
        body = text[m.end():end]
        if not re.match(rf"addr = {addr:#x}\n", body):
            continue
        if re.search(r"(?m)^src = ", body):
            raise ValueError(f"{addr:#x}: already has src")
        if not re.search(r"(?m)^ref = ", body) or not re.search(r"(?m)^ref_verified_by = ", body):
            raise ValueError(f"{addr:#x}: not a ref + ref_verified_by entry")
        # a T4 entry may already carry a (behavioural) verified_by: the T3 one
        # replaces it (TOML forbids duplicate keys) and the old text moves to evidence
        # (the ref_verified_by difftest is cited by the caller's evidence line)
        old_vb = re.search(r"(?m)^verified_by = (.*)\n", body)
        kept = []
        if old_vb:
            kept.append("T4 verified_by before promotion: " + tomllib.loads("v = " + old_vb.group(1))["v"])
        for k in _KEYS_DROPPED + ("verified_by",):
            body = re.sub(rf"(?m)^{k} = .*\n", "", body)
        evidence_line = [evidence_line] + kept
        body, n = re.subn(r'(?m)^confidence = .*\n', 'confidence = "verified"\n'
                          f"src = {json.dumps(src)}\nverified_by = {json.dumps(verified_by)}\n", body, count=1)
        if n != 1:
            raise ValueError(f"{addr:#x}: no confidence line")
        evidence = re.search(r"(?m)^evidence[ \t]*=[ \t]*\[", body)
        if not evidence:
            raise ValueError(f"{addr:#x}: no evidence list")
        # Insert before the original evidence, so inline arrays and arrays
        # without a trailing comma work without rewriting any old evidence.
        at = evidence.end()
        if body[at:at + 1] == "\n":
            at += 1
            new_evidence = "".join(f"  {json.dumps(line)},\n" for line in evidence_line)
        else:
            new_evidence = "".join(f"{json.dumps(line)}, " for line in evidence_line)
        body = body[:at] + new_evidence + body[at:]
        tomllib.loads(body)
        return text[:m.end()] + body + text[end:]
    raise ValueError(f"{addr:#x}: no [[func]] block")


_C_TOKEN = re.compile(r"""/\*[\s\S]*?(?:\*/|\Z)|//[^\r\n]*|"(?:\\[^\r\n]|[^"\\\r\n])*"|"""
                      r"""'(?:\\[^\r\n]|[^'\\\r\n])*'|["']""")
_C_SPLICE = re.compile(r"(?:\\|\?\?/)(?:\r?\n|\r)")
_HEADER_KEY = re.compile(r"[ \t]*(?:\*[ \t]*)?(codegen-(?:compiler|flags))\b")
_HEADER_PARSERS = {"codegen-compiler": match.CC_RE, "codegen-flags": match.FLAGS_RE}


def _c_comments(text):
    # C joins escaped lines before recognizing comments and quoted literals.
    # Keep coordinates in the original spelling for the actual edits.
    pieces, positions, widths = [], [], [0]
    start = removed = 0
    for splice in _C_SPLICE.finditer(text):
        pieces.append(text[start:splice.start()])
        positions.append(splice.start() - removed)
        removed += splice.end() - splice.start()
        widths.append(removed)
        start = splice.end()
    pieces.append(text[start:])
    for token in _C_TOKEN.finditer("".join(pieces)):
        value = token.group()
        if value in ("'", '"') or (value.startswith("/*") and value.find("*/", 2) == -1):
            raise ValueError("cannot normalize codegen metadata in an unterminated C token")
        if value.startswith(("//", "/*")):
            left = token.start() + widths[bisect_right(positions, token.start())]
            last = token.end() - 1
            right = last + widths[bisect_right(positions, last)] + 1
            yield left, right, value


def _check_header_value(key, value):
    if key == "codegen-compiler":
        valid = value in match.COMPILERS
    else:
        valid = (bool(re.fullmatch(r"[-/][^\s]+(?:[ \t]+[-/][^\s]+)*", value))
                 and not any(s in value for s in ("/*", "*/", "//", "codegen-", "\0")))
    if not valid:
        raise ValueError(f"malformed {key}: {value!r}")


def set_flags_header(text, cc, short_flags):
    """Put canonical metadata first and remove old declarations from C comments."""
    # Preserve a BOM at byte zero rather than moving it into the C source.
    bom = "\ufeff" if text.startswith("\ufeff") else ""
    text = text[len(bom):]
    flags = " ".join(re.split(r"[ \t]+", short_flags.strip(" \t")))
    _check_header_value("codegen-compiler", cc)
    _check_header_value("codegen-flags", flags)
    newline = re.search(r"\r\n|\n|\r", text)
    nl = newline.group() if newline else "\n"
    head = f"/* codegen-compiler: {cc} */{nl}/* codegen-flags: {flags} */{nl}"
    # match reads 2048 characters through universal-newline translation.
    parser_head = (bom + head.replace(nl, "\n"))[:2048]
    for key, expected in (("codegen-compiler", cc), ("codegen-flags", flags)):
        found = _HEADER_PARSERS[key].search(parser_head)
        if not found or found[1] != expected:
            raise ValueError(f"{key} does not fit the match header")

    edits = []
    for start, end, token in _c_comments(text):
        if not _HDR.search(token):
            continue
        if text[start:end] != token:
            raise ValueError("ambiguous codegen metadata in a continued C comment")
        block = token.startswith("/*")
        body = token[2:-2] if block else token[2:]
        offset, declarations, has_prose = start + 2, [], False
        for line in body.splitlines(keepends=True):
            content = line.rstrip("\r\n")
            key = _HEADER_KEY.match(content)
            if key:
                kind = key[1]
                tag_start = offset + key.start(1)
                physical = re.split(r"\r\n|\r|\n", text[tag_start:], maxsplit=1)[0]
                found = _HEADER_PARSERS[kind].fullmatch(physical)
                if found is None or not content[key.end():].startswith(":"):
                    raise ValueError(f"malformed {kind} declaration")
                value = content[key.end() + 1:].strip(" \t")
                _check_header_value(kind, value)
                if found[1] != value:
                    raise ValueError(f"ambiguous {kind} declaration")
                # Keep the opener's newline when its line contained a declaration.
                stop = offset + (len(content) if offset == start + 2 else len(line))
                declarations.append((offset, stop, ""))
            else:
                if any(kind + ":" in content for kind in _HEADER_PARSERS):
                    raise ValueError("ambiguous codegen metadata embedded in a comment")
                if (declarations and re.fullmatch(r"[ \t]*\*?[ \t]*[-/]\S+(?:[ \t]+[-/]\S+)*[ \t]*",
                                                  content)):
                    raise ValueError("ambiguous continuation of codegen flags")
                has_prose |= bool(content.strip(" \t*"))
            offset += len(line)
        if not declarations:
            continue
        if has_prose:
            edits.extend(declarations)
            continue
        # Do not absorb the next line into a continued preprocessor directive,
        # or join tokens separated by a block comment.
        line_start = max(text.rfind("\n", 0, start), text.rfind("\r", 0, start)) + 1
        tail = re.match(r"[ \t]*(?:\r\n|\r|\n|\Z)", text[end:])
        previous_line = text[:line_start].rstrip("\r\n")
        if (not text[line_start:start].strip(" \t") and tail
                and not previous_line.endswith(("\\", "??/"))):
            edits.append((line_start, end + tail.end(), ""))
        else:
            inner_newlines = "".join(re.findall(r"\r\n|\n|\r", token))
            replacement = "/*" + inner_newlines + "*/" if inner_newlines else ""
            if not replacement and start and not text[start - 1].isspace() and end < len(text) and not text[end].isspace():
                replacement = " "
            edits.append((start, end, replacement))
    pieces, cursor = [bom, head], 0
    for start, end, replacement in edits:
        pieces.append(text[cursor:start])
        pieces.append(replacement)
        cursor = end
    return "".join(pieces) + text[cursor:]


def promote(rows):
    """Apply an exact buildable match to the working tree: every audited row of
    the file (all MATCH_BUILDABLE, one object).  Returns [(addr, toml)]."""
    done = []
    text_by_fn = {}
    if rows:
        ref = path(rows[0]["ref"])
        with open(ref, newline="") as fh:
            normalized = set_flags_header(fh.read(), "10.0a", rows[0]["match_flags"])
    for r in rows:          # compute every rewrite first: a bad row leaves all files untouched
        ev = (f"T3 C: {r['ref']} (Watcom 10.0a {r['match_flags']}), recovered from the T4 reference C "
              f"by wc1.wave4; the T4 difftest {r['ref_verified_by'].split(':', 1)[1].strip()} still runs on it")
        vb = (f"match: python3 -m wc1.match {r['ref']} (code bytes, relocation targets, module data; "
              "flags from the codegen-flags header)")
        fn = path(r["toml"])
        if fn not in text_by_fn:
            with open(fn) as fh:
                text_by_fn[fn] = fh.read()
        text_by_fn[fn] = promote_toml_text(text_by_fn[fn], r["addr"], r["ref"], vb, ev)
        done.append((r["addr"], r["toml"]))
    for fn, new in text_by_fn.items():
        with open(fn, "w") as fh:
            fh.write(new)
    if rows:
        with open(ref, "w", newline="") as fh:
            fh.write(normalized)
    return done


# --- B/C/D: one function --------------------------------------------------------

def outcome_file(addr):
    return path(*OUT_DIR, "outcomes", f"{addr:x}.json")


def write_outcome(addr, outcome, **data):
    rec = dict(data, outcome=outcome, addr=f"{addr:#x}", ts=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    _write_json(outcome_file(addr), rec)
    return rec


def _write_json(fn, rec):
    os.makedirs(os.path.dirname(fn), exist_ok=True)
    tmp = fn + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(rec, fh, indent=1, default=str)
    os.replace(tmp, fn)


def clear_outcome(addr):
    """Archive a stale receipt before starting, so neither history nor verdicts mix between attempts."""
    fn = outcome_file(addr)
    if not os.path.exists(fn):
        return
    archive = path(*OUT_DIR, "history", f"{addr:x}")
    os.makedirs(archive, exist_ok=True)
    try:
        os.replace(fn, os.path.join(archive, f"{time.time_ns()}.json"))
    except FileNotFoundError:
        pass


def read_outcome(addr):
    try:
        with open(outcome_file(addr)) as fh:
            rec = json.load(fh)
        return rec if isinstance(rec, dict) else None
    except (OSError, ValueError):
        return None


def _write_diag(addr, name, obj):
    d = path(*OUT_DIR, "diag")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, f"{addr:x}_{name}.json"), "w") as fh:
        json.dump(obj, fh, indent=1, default=str)


def audit_function(ctx, cand, siblings):
    """Audit the candidate's ref file once (all T4 entries sharing it).
    Returns (row of cand, all rows).  Raises t3_audit.ToolchainAbort."""
    unit = {"ref": cand["ref"], "cands": [cand] + [s for s in siblings if s["addr"] != cand["addr"]]}
    rows = t3_audit.audit_unit(ctx, unit)
    return next(r for r in rows if r["addr"] == cand["addr"]), rows


def run_difftests(rows, runner=None):
    """D: the difftest nodes of every promoted entry still pass.  Returns
    (ok, detail)."""
    nodes = []
    for r in rows:
        ns, _ = symbols.parse_ref_verified_by_nodes(r.get("ref_verified_by") or "")
        nodes += [f"{f}::{n}" for f, n in ns if f"{f}::{n}" not in nodes]
    if not nodes:
        return False, "no difftest node"
    if runner:
        return runner(nodes)
    try:
        p = subprocess.run([sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", *nodes],
                           cwd=path(), capture_output=True, text=True, timeout=900)
    except subprocess.TimeoutExpired:
        return False, "difftest timeout (900 s)"
    out = p.stdout + p.stderr
    return p.returncode == 0 and _all_passed(out, len(nodes)), out[-3000:]


def _all_passed(out, n_nodes):
    """pytest exits 0 on skipped/xfailed nodes: require passes and nothing else."""
    import re
    summ = out.strip().splitlines()[-1] if out.strip() else ""
    c = {k: int(v) for v, k in re.findall(r"(\d+) (passed|skipped|xfailed|xpassed|failed|error|errors)", summ)}
    bad = sum(c.get(k, 0) for k in ("skipped", "xfailed", "xpassed", "failed", "error", "errors"))
    return c.get("passed", 0) >= n_nodes and bad == 0


def _repair_prompt(cand, text, row):
    best = row.get("best") or {}
    return (f"Function {cand['name']} ({cand['addr_hex']}), file {cand['ref']}, compiled with "
            f"Watcom 10.0a flags [{best.get('cflags') or cand['declared_cflags']}].\n"
            f"Score {best.get('score')} counts {best.get('counts')}; first difference: {best.get('first_diff')}\n"
            "Diff (original vs compiled):\n" + "\n".join(best.get("diff") or []) + "\n\n"
            f"Current file:\n```c\n{text}\n```\n\n" + REPAIR_RULES)


def run_recovery(cand, siblings, ctx, *, llm=None, max_calls=2, difftests=None, log=print,
                 apply_patches=None):
    """Process one T4 function; returns the outcome record (also on disk).
    llm(prompt, schema, label) -> dict is the repair call (None: no LLM);
    rate-limit / quota errors propagate (the ref file is restored first)."""
    addr = cand["addr"]
    ref_fn = path(cand["ref"])
    with open(ref_fn, "rb") as fh:
        original = fh.read()
    calls, history, best_score, best_row = 0, [], None, None
    work = original
    complete_search = True

    def restore():
        if open(ref_fn, "rb").read() != original:
            with open(ref_fn, "wb") as fh:
                fh.write(original)

    try:
        try:
            row, rows = audit_function(ctx, cand, siblings)
        except t3_audit.ToolchainAbort as ex:
            return write_outcome(addr, TOOLCHAIN_ERROR, reason=str(ex), llm_calls=0)
        history.append({"call": 0, "status": row["status"], "reason": row.get("reason")})
        while True:
            # A successful compile for one flag set can mask failure under another.
            complete_search &= not any(a["result"] == "COMPILE_ERROR" for r in rows for a in r.get("attempts", ()))
            st = row["status"]
            if st == "MATCH_BUILDABLE":
                promoted = [r for r in rows if r["status"] == "MATCH_BUILDABLE"]
                with open(ref_fn, "rb") as fh:
                    recovered = fh.read()
                patched = recovered != original
                # Let cited tests that read the header run the exact compiler
                # and flags being promoted, not the old reference settings.
                normalized = set_flags_header(recovered.decode("utf-8"), t3_audit.CC, row["match_flags"]).encode()
                if normalized != recovered:
                    with open(ref_fn, "wb") as fh:
                        fh.write(normalized)
                ok, detail = run_difftests(promoted, difftests)
                if not ok:
                    restore()
                    return write_outcome(addr, FAILED, reason="difftest failed on the recovered C",
                                         detail=detail, llm_calls=calls, history=history)
                done = promote(promoted)
                return write_outcome(addr, PROMOTED, llm_calls=calls, history=history,
                                     flags=row["match_flags"], flags_change=row.get("flags_change"),
                                     promoted=[f"{a:#x}" for a, _t in done], tomls=sorted({t for _a, t in done}),
                                     ref=cand["ref"], patched=patched)
            if st == "MATCH_UNBUILDABLE":
                restore()
                return write_outcome(addr, UNBUILDABLE, reason=row.get("reason"), llm_calls=calls,
                                     history=history, flags=row.get("match_flags"))
            if st != "MISMATCH" or llm is None or calls >= max_calls:
                restore()
                _write_diag(addr, "rows", [r for r in rows if r["addr"] == addr])
                out = NO_IMPROVEMENT if st == "MISMATCH" else FAILED
                return write_outcome(addr, out, reason=row.get("reason") or f"audit status {st}",
                                      llm_calls=calls, history=history,
                                      complete_search=(out == NO_IMPROVEMENT and complete_search
                                                       and calls == max_calls and calls > 0),
                                      best=(row.get("best") or {}).get("score"),
                                     first_diff=(row.get("best") or {}).get("first_diff"))
            score = tuple((row.get("best") or {}).get("score") or ())
            if best_score is None or score <= best_score:
                best_score, best_row, work = score, row, open(ref_fn, "rb").read()
            elif open(ref_fn, "rb").read() != work:   # the last patch made it worse: back to the best text
                with open(ref_fn, "wb") as fh:
                    fh.write(work)
            calls += 1
            text = work.decode("utf-8", "replace")
            res = llm(_repair_prompt(cand, text, best_row), REPAIR_SCHEMA, f"wave4:{addr:x}:repair{calls}")
            complete_search &= (isinstance(res, dict) and isinstance(res.get("diagnosis"), str)
                                and isinstance(res.get("patches"), list)
                                and all(isinstance(p, dict) and isinstance(p.get("old"), str)
                                        and isinstance(p.get("new"), str) for p in res["patches"]))
            new_text, applied = (apply_patches or _apply)(text, (res or {}).get("patches"))
            history.append({"call": calls, "diagnosis": (res or {}).get("diagnosis"), "applied": applied})
            if not applied or not _guard_ok(text, new_text):
                history[-1]["rejected"] = "no patch applied" if not applied else "patch touched the codegen headers"
                continue            # the row is unchanged; the call budget ends the loop
            with open(ref_fn, "w") as fh:
                fh.write(new_text)
            try:
                row, rows = audit_function(ctx, cand, siblings)
            except t3_audit.ToolchainAbort as ex:
                restore()
                return write_outcome(addr, TOOLCHAIN_ERROR, reason=str(ex), llm_calls=calls, history=history)
            history[-1]["status"] = row["status"]
    except BaseException:
        restore()
        raise


def _apply(text, patches):
    n = 0
    for p in patches or []:
        old, new = p.get("old", ""), p.get("new", "")
        if old and text.count(old) == 1:
            text = text.replace(old, new, 1)
            n += 1
    return text, n


_HDR = re.compile(r"codegen-(?:compiler|flags)")


def _guard_ok(old, new):
    """A repair must not move the codegen headers (the flags are the audit's)."""
    g = lambda t: [l for l in t.splitlines() if _HDR.search(l)]
    return g(old) == g(new)
