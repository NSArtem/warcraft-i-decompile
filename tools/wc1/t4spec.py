"""Declarative T4 differential test harness on top of wc1.cemu.

Replaces repetitive per-area pytest boilerplate with compact specs that declare:
  - target function (src, link_name, orig_addr)
  - explicit edge cases + optional seeded random generator
  - callee stubs with automatic call-log recording into watched scratch memory
  - watched globals / memory ranges
Also provides shared lenient symbol loading and T3/ref-guard assertion helpers.
"""
import glob
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


def assert_ref_mismatch(src_dir, files, by_link=None):
    """Near-miss guard: every reference C file must still fail to match."""
    by_link = by_link or by_link_lenient()
    p = analysis.run()
    for name in files:
        src = os.path.join(src_dir, name)
        out = match.unique_obj(src, "t4spec", match.file_cc(src))
        os.makedirs(os.path.dirname(out), exist_ok=True)
        mod = match.compile_c(src, None, out, cc=match.file_cc(src))
        res = match.match_module(p, mod, by_link)
        assert res and all(st != "MATCH" for _, st, _ in res), (name, res)


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
             out_regs=("eax",), cdecl=False, extra=None, cflags=None,
             seed=0xC0FFEE, rand_cases=0, rand_gen=None, init_emu=None,
             log_cap=1024):
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
        )
        assert not diffs, f"{func_name} ({orig_addr:#x}) failed on {lbl}: {diffs}"
