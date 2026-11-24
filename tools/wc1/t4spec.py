"""Declarative T4 differential test harness on top of wc1.cemu.

Replaces repetitive per-area pytest boilerplate with compact specs that declare:
  - target function (src, link_name, orig_addr)
  - explicit edge cases + optional seeded random generator
  - callee stubs with automatic call-log recording into watched scratch memory
  - watched globals / memory ranges
Also provides shared lenient symbol loading and T3/ref-guard assertion helpers.
"""
import glob
import hashlib
import json
import os
import random
import struct
import tomllib
from dataclasses import dataclass, field

from . import analysis, cemu, match, path, symbols
from .emu import Emu


def load_lenient():
    """Load symbols ignoring syntax errors in unrelated in-progress TOMLs."""
    funcs, datas = {}, {}
    for f in sorted(glob.glob(path("analysis", "symbols", "*.toml"))):
        try:
            with open(f, "rb") as fh:
                doc = tomllib.load(fh)
        except tomllib.TOMLDecodeError:
            continue
        for kind, table in (("func", funcs), ("data", datas)):
            for e in doc.get(kind, []):
                e = dict(e)
                if not isinstance(e.get("addr"), int) or "name" not in e:
                    continue
                if kind == "func" and e.get("conv", "watcall") not in (
                        "watcall", "cdecl", "asm", "pascal"):
                    continue
                try:
                    e["link_name"] = symbols.link_name(kind, e)
                except KeyError:
                    continue
                e["_kind"] = kind
                table.setdefault(e["addr"], e)
    return funcs, datas


def by_link_lenient():
    funcs, datas = load_lenient()
    return {e["link_name"]: e for t in (funcs, datas) for e in t.values()}


def assert_t3_matches(src_dir, files, by_link=None):
    """Assert every C file in `files` under `src_dir` matches under its declared compiler."""
    by_link = by_link or by_link_lenient()
    p = analysis.run()
    bad = []
    for name in files:
        src = os.path.join(src_dir, name)
        out = match.unique_obj(src, "t4spec", match.file_cc(src))
        os.makedirs(os.path.dirname(out), exist_ok=True)
        mod = match.compile_c(src, None, out, cc=match.file_cc(src))
        for fn, st, probs in match.match_module(p, mod, by_link):
            if st != "MATCH":
                bad.append((name, fn, probs[:2]))
    assert not bad, f"T3 mismatch: {bad}"


def _rel(src):
    """Normalized repository-relative path with forward slashes."""
    return os.path.relpath(os.path.abspath(src), symbols.path()).replace(os.sep, "/")


def t3_promoted(src):
    """True when some symbols entry builds from this file (`src =`).  File-level
    information only: it must never decide how an individual function is verified
    (use assert_ref_results, which classifies per function)."""
    rel = _rel(src)
    funcs, _, _ = symbols.load(strict=False)
    return any(e.get("src") == rel for e in funcs.values())


def _by_link_db():
    funcs, datas, _ = symbols.load(strict=False)
    return {e["link_name"]: e for t in (funcs, datas) for e in t.values()}


def assert_ref_results(src, results, what=None, by_link=None):
    """Per-function verification of one C file from its full named match results
    [(link_name, status, problems)] (match.match_module's return value).

    Each function symbol is classified by its own metadata:
      src == this file  -> T3: must MATCH exactly;
      ref == this file  -> T4: must NOT match (a MATCH is a promotion candidate
                           for the session owner; one matching function in a mixed
                           object does not authorize promotion by itself);
      src/ref names another file (stale duplicate copy here) -> must NOT match;
      neither src nor ref (unwired placeholder defined here) -> same: must NOT match;
      unknown link name, or both src and ref set -> fail closed.
    Object-level results (`[SEG @ addr, n bytes]`, module-local data) must MATCH
    whenever the object contains any T3 function (they are part of its exact-match
    claim); in an all-T4 object they carry no claim and are not checked.
    Not checked here: that a T3 file's T4/duplicate functions match as well - whole
    objects are linked and compared by `make match-all` (match._match_one), which
    stays the whole-object T3 buildability gate."""
    what = what or src
    rel = _rel(src)
    by_link = by_link if by_link is not None else _by_link_db()
    assert any(not n.startswith("[") for n, _, _ in results), f"{what}: no function results"
    errors, t3_fns, data = [], [], []
    for name, status, problems in results:
        if name.startswith("["):
            data.append((name, status, problems))
            continue
        e = by_link.get(name)
        if e is None:
            errors.append(f"{name}: no symbol entry (fail closed)")
            continue
        s_, r_ = e.get("src"), e.get("ref")
        if s_ and r_:
            errors.append(f"{name}: both src= and ref= set (inconsistent)")
        elif s_ == rel:
            t3_fns.append(name)
            if status != "MATCH":
                errors.append(f"{name}: T3 (src = {rel}) but {status}: {list(problems)[:2]}")
        elif r_ == rel:
            if status == "MATCH":
                errors.append(f"{name}: T4 reference {rel} now matches - promote it to T3 "
                              f"(session owner adds src =)")
        else:
            # a copy of a known symbol this file does not own (owned by another file,
            # or not wired to any C yet): no claim is made for this copy, but it must
            # stay a near miss - a matching copy is an unreviewed second implementation
            if status == "MATCH":
                errors.append(f"{name}: matches, but its symbol is {'owned by ' + repr(s_ or r_) if s_ or r_ else 'not wired to any C (no src=/ref=)'}, "
                              f"not {rel} (duplicate copy: remove it, or make this file its owner)")
    if t3_fns:
        for name, status, problems in data:
            if status != "MATCH":
                errors.append(f"{name}: object data in a file with T3 functions {t3_fns} "
                              f"is {status}: {list(problems)[:2]}")
    assert not errors, f"{what}: " + "; ".join(errors)


def sweep_results(rows, by_addr=None):
    """Adapt codegen_sweep rows (name, addr, status, ...) to named match results,
    taking the link name from the symbol at the row's address (unknown -> fail closed)."""
    if by_addr is None:
        funcs, _, _ = symbols.load(strict=False)
        by_addr = funcs
    out = []
    for r in rows:
        e = by_addr.get(r[1])
        out.append(((e["link_name"] if e else f"?{r[0]}@{r[1]:#x}"), r[2], []))
    return out


def ref_results(src, by_link=None):
    """Named match results of one C file compiled with its own codegen-compiler/-flags header."""
    out = match.unique_obj(src, "t4spec", match.file_cc(src))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    mod = match.compile_c(src, None, out, cc=match.file_cc(src))
    return match.match_module(analysis.run(), mod, by_link or by_link_lenient())


def assert_ref_mismatch(src_dir, files, by_link=None):
    """Per-function guard for every file: T4 functions must still fail to match,
    T3 (`src =`) functions must match exactly."""
    by_link = by_link or by_link_lenient()
    for name in files:
        src = os.path.join(src_dir, name)
        res = ref_results(src, by_link)
        assert_ref_results(src, res, (name, res), by_link=by_link)


@dataclass
class T4Stub:
    """Callee stub that optionally logs its call into watched scratch memory."""
    addr: int
    ret: int = 0
    log_regs: tuple = ("eax", "edx", "ebx", "ecx")
    fn: object = None          # optional custom callback(emu, log_fn) -> ret_or_None
    stack_pop: int = 0         # bytes callee pops for watcall stack args (>4 args)


@dataclass
class T4Case:
    """One test input for run_spec."""
    args: tuple = ()
    stack_args: tuple = ()
    regs_in: dict = None
    mem: dict = field(default_factory=dict)   # addr -> bytes
    setup: object = None                      # optional callback(emu)
    label: str = ""


def _install_stubs(emu, stubs, log_base, log_cap=1024):
    """Install T4Stubs that append (addr, *regs) dwords into [log_base, log_base+log_cap)."""
    # First dword at log_base = byte offset cursor (starts at 4)
    def log_entry(addr, vals):
        pos = struct.unpack("<I", emu.read(log_base, 4))[0]
        rec = struct.pack("<" + "I" * (1 + len(vals)), addr & 0xFFFFFFFF,
                          *(v & 0xFFFFFFFF for v in vals))
        if pos + len(rec) <= log_cap:
            emu.write(log_base + pos, rec)
            emu.write(log_base, struct.pack("<I", pos + len(rec)))

    for st in stubs:
        def _make(stub):
            def _handler(e):
                if stub.fn is not None:
                    return stub.fn(e, lambda *vals: log_entry(stub.addr, vals))
                vals = [e.reg(r) for r in stub.log_regs]
                log_entry(stub.addr, vals)
                return stub.ret
            return _handler
        emu.stubs[st.addr] = _make(st)
        if st.stack_pop:
            emu.stub_pops[st.addr] = st.stack_pop


def _auto_placeholder_extras(src, extra):
    """Auto-resolve placeholder link names (`fn_XXXXX_`, `_dat_XXXXX`) referenced
    by compiled `src` when not already in the symbol DB or `extra`."""
    import re
    out = dict(extra or {})
    try:
        mod = cemu.compile_module(src)
    except Exception:
        return out
    by_link = cemu._by_link()
    for seg in mod.segments:
        for fu in seg.fixups:
            if fu.target_kind != "ext":
                continue
            sym = fu.target
            if sym in by_link or sym in out:
                continue
            m = re.fullmatch(r"fn_([0-9a-fA-F]+)_", sym)
            if m:
                out[sym] = int(m.group(1), 16)
                continue
            m = re.fullmatch(r"_?dat_([0-9a-fA-F]+)", sym)
            if m:
                out[sym] = int(m.group(1), 16)
    return out


def run_spec(src, func_name, orig_addr, cases=(), *, watch=(), stubs=(),
             out_regs=("eax",), cdecl=False, interrupt=False, extra=None,
             cflags=None, seed=0xC0FFEE, rand_cases=0, rand_gen=None,
             init_emu=None, log_cap=1024):
    """Run compiled C function `func_name` in `src` against `orig_addr` on all cases.

    Automatically allocates and watches a stub call-log buffer whenever `stubs`
    is non-empty, comparing both output registers/memory AND stubbed callee
    invocations identically between original and compiled C.
    """
    emu = Emu()
    if init_emu is not None:
        init_emu(emu)
    resolved_extra = _auto_placeholder_extras(src, extra)
    cm = cemu.load(emu, src, cflags=cflags, extra=resolved_extra)
    watch_list = list(watch)
    log_base = None
    if stubs:
        log_base = emu.alloc(log_cap, 16)
        _install_stubs(emu, stubs, log_base, log_cap=log_cap)
        watch_list.append((log_base, log_cap))

    all_cases = list(cases)
    if rand_cases and rand_gen is not None:
        rng = random.Random(seed)
        for idx in range(rand_cases):
            c = rand_gen(rng)
            if not c.label:
                c.label = f"rand[{idx}]"
            all_cases.append(c)

    src_real = os.path.realpath(path(src))
    valid_watch = [(a, int(n)) for a, n in watch_list if int(n) > 0]
    cemu.record_t4_audit({
        "kind": "run_spec",
        "src": src_real,
        "func_name": func_name,
        "orig_addr": int(orig_addr),
        "cases_planned": len(all_cases),
        "stub_addrs": [int(st.addr) for st in stubs],
        "orig_stubbed": any(int(st.addr) == int(orig_addr) for st in stubs),
        "observed": bool(out_regs) or bool(valid_watch),
    })
    assert all_cases, f"{func_name} ({orig_addr:#x}) called run_spec with 0 test cases"

    completed = 0
    for idx, c in enumerate(all_cases):
        lbl = c.label or f"case[{idx}]"
        if log_base is not None:
            emu.write(log_base, struct.pack("<I", 4) + b"\x00" * (log_cap - 4))
        for addr, data in (c.mem or {}).items():
            emu.write(addr, data)
        if c.setup is not None:
            c.setup(emu)
        diffs = cemu.run_pair(
            emu, orig_addr, cm, func_name, *c.args,
            watch=watch_list, out_regs=out_regs,
            stack_args=c.stack_args, regs_in=c.regs_in, cdecl=cdecl,
            interrupt=interrupt,
        )
        assert not diffs, f"{func_name} ({orig_addr:#x}) failed on {lbl}: {diffs}"
        completed += 1

    cemu.record_t4_audit({
        "kind": "run_spec_done",
        "src": src_real,
        "func_name": func_name,
        "orig_addr": int(orig_addr),
        "cases_planned": len(all_cases),
        "cases_completed": completed,
    })


def audit_t4_log(log_path, ref_rel=None, orig_addr=None, func_name=None,
                 repo_root=None, min_cases=1, expected_nonce=None):
    """Audit a `WC1_T4_AUDIT_LOG` JSONL file emitted during a pytest T4 run.

    Proves at runtime that:
      - `cemu.run_pair` actually executed for the exact realpath of `ref_rel`,
        `orig_addr`, and (when provided) `func_name`;
      - every matched record carries `expected_nonce` (when provided);
      - original executed >0 instructions (`orig_insns > 0`);
      - every matched `run_spec` reached `run_spec_done` with `cases_completed == cases_planned >= 1`
        (catches swallowed `UcError`/`CEmuError`/mid-loop exceptions);
      - at least `min_cases` comparisons ran;
      - ZERO comparisons produced non-empty diffs (catches swallowed AssertionErrors);
      - `orig_addr` range was never stubbed or patched;
      - at least one real output (`out_regs`, non-zero `watch` range, or stub call log) was observed.

    Returns `(ok, reason_or_stats)`.
    """
    if not log_path or not os.path.isfile(log_path):
        return False, "no runtime T4 audit log recorded (run_spec/run_pair never executed)"
    records = []
    with open(log_path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    if not records:
        return False, "empty runtime T4 audit log (run_spec/run_pair never executed)"

    root = repo_root or path()
    exp_src = os.path.realpath(os.path.join(root, ref_rel)) if ref_rel else None
    exp_addr = int(orig_addr) if orig_addr is not None else None

    def _matches_target(rec):
        if expected_nonce is not None and rec.get("nonce") != expected_nonce:
            return False
        if exp_addr is not None and rec.get("orig_addr") != exp_addr:
            return False
        if func_name is not None and rec.get("func_name") != func_name:
            return False
        if exp_src is not None:
            rsrc = rec.get("src") or ""
            if not rsrc or os.path.realpath(rsrc) != exp_src:
                return False
        return True

    pair_recs = [r for r in records if r.get("kind") == "run_pair"]
    spec_recs = [r for r in records if r.get("kind") == "run_spec"]
    done_recs = [r for r in records if r.get("kind") == "run_spec_done"]

    matched_specs = [r for r in spec_recs if _matches_target(r)]
    matched_dones = [r for r in done_recs if _matches_target(r)]
    for sr in matched_specs:
        if int(sr.get("cases_planned", 0)) < 1:
            return False, f"run_spec executed with 0 cases for {ref_rel or hex(exp_addr or 0)}"
        if sr.get("orig_stubbed"):
            return False, f"orig_addr {sr.get('orig_addr', 0):#x} was stubbed in run_spec"

    matched_pairs = [r for r in pair_recs if _matches_target(r)]
    if not matched_pairs:
        seen = sorted({
            (r.get("src") or "", hex(r.get("orig_addr", 0)), r.get("func_name") or "")
            for r in pair_recs
        })[:5]
        tgt = f"src={exp_src or '*'} addr={hex(exp_addr) if exp_addr is not None else '*'}"
        if func_name:
            tgt += f" fn={func_name}"
        return False, f"no cemu.run_pair record matched {tgt} (saw {seen})"

    bad_diffs = [r for r in matched_pairs if int(r.get("diffs_count", 0)) > 0]
    if bad_diffs:
        return False, (
            f"recorded {len(bad_diffs)}/{len(matched_pairs)} failing cemu.run_pair diff(s) "
            f"(assertion was suppressed or inverted)"
        )
    if any(r.get("orig_stubbed") for r in matched_pairs):
        return False, f"orig_addr {matched_pairs[0].get('orig_addr', 0):#x} was stubbed during run_pair"
    if any(r.get("c_stubbed") for r in matched_pairs):
        return False, "compiled C segment range was stubbed during run_pair"
    if any(r.get("trace_active") for r in matched_pairs):
        return False, "emu.trace hook was active during run_pair"
    if any(r.get("orig_patched") for r in matched_pairs):
        return False, f"orig_addr {matched_pairs[0].get('orig_addr', 0):#x} code bytes were overwritten"
    if any(r.get("c_patched") for r in matched_pairs):
        return False, "compiled C code bytes were overwritten"
    if any(r.get("prebuilt") for r in matched_pairs):
        return False, "cmod was constructed with a prebuilt OMF module instead of compiling ref_rel"
    if exp_src:
        if not os.path.isfile(exp_src):
            return False, f"ref_rel not found on disk: {exp_src}"
        with open(exp_src, "rb") as fh:
            exp_sha = hashlib.sha256(fh.read()).hexdigest()
        if any(r.get("src_sha256") != exp_sha for r in matched_pairs):
            return False, f"compiled C source sha256 did not match {exp_src} on disk"
        if not os.environ.get("WATCOM"):
            return False, "cannot verify OMF digest: $WATCOM not set"
        try:
            exp_mod = cemu.compile_module(exp_src, fresh=True)
        except Exception as ex:
            return False, f"fresh compile of {exp_src} failed: {ex}"
        exp_digest = cemu.omf_module_digest(exp_mod)
        if any(r.get("mod_digest") != exp_digest for r in matched_pairs):
            return False, f"compiled OMF digest did not match fresh compile of {exp_src}"
    if any(int(r.get("orig_insns", 0)) <= 0 for r in matched_pairs):
        return False, f"orig_addr {matched_pairs[0].get('orig_addr', 0):#x} executed 0 instructions"
    if any(int(r.get("c_insns", 0)) <= 0 for r in matched_pairs):
        return False, f"compiled C for {matched_pairs[0].get('func_name', '?')} executed 0 instructions"
    if not any(r.get("observed") for r in matched_pairs):
        return False, "cemu.run_pair observed no out_regs, watch ranges, or stub call logs"
    if matched_specs:
        if len(matched_dones) < len(matched_specs):
            return False, (
                f"run_spec aborted mid-loop ({len(matched_dones)}/{len(matched_specs)} completed — "
                f"exception was swallowed)"
            )
        for sr, dr in zip(matched_specs, matched_dones):
            if int(dr.get("cases_completed", 0)) != int(sr.get("cases_planned", 0)):
                return False, (
                    f"run_spec completed {dr.get('cases_completed')}/{sr.get('cases_planned')} cases"
                )
    if len(matched_pairs) < min_cases:
        return False, f"only {len(matched_pairs)} run_pair case(s) executed (minimum {min_cases})"
    return True, {
        "cases_run": len(matched_pairs),
        "orig_addr": matched_pairs[0].get("orig_addr"),
        "src": matched_pairs[0].get("src"),
        "func_name": matched_pairs[0].get("func_name"),
    }
