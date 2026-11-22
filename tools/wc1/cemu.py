"""T4 harness: run compiled C under wc1.emu (docs/GOAL.md milestone M1).

A C source is compiled with its codegen flags (wc1.match.compile_c), its OMF
segments are placed in the emulator's scratch area and every relocation is
resolved against the symbol database, so the module's code and data are live
next to the original image: calls and data references go to the original
addresses, its own segments to the copy just placed.  The module's functions
are then called like the original ones (watcall by default).

    from wc1 import cemu
    from wc1.emu import Emu

    emu = Emu()
    cm = cemu.load(emu, "src/save_score/score_reference.c")
    cm.call("TotalActiveMen_")

`run_pair` is the differential driver: it runs the original and the compiled
function on identical inputs (it restores the watched memory between the two
calls) and compares the requested output registers and memory effects.

    diffs = cemu.run_pair(emu, 0x24e50, cm, "TotalActiveMen_",
                          watch=[(0x58e28, 8)], out_regs=("eax",))
    assert not diffs

Relocations: only the kinds Watcom emits for C objects are handled - 32-bit
external references (calls and absolute data addresses, `ext`) and
module-local segment references (`seg`, e.g. a call or jump to another
function of the same file).  Group/frame fixups, communal variables and
unknown external names raise `CEmuError` naming the symbol, so a test can add
the missing symbol to the database.
"""
import hashlib
import json
import os
import struct

from . import match, omf, path, symbols
from .emu import Emu

# segment classes that carry no runnable/addressable data: OW2's DWARF and
# Watcom 10.x's own -d1/-d2 format ($$SYMBOLS in DEBSYM, $$TYPES in DEBTYP,
# with ptr16:32 fixups that only the linker resolves)
_SKIP_CLASSES = {"DWARF", "DEBUG", "INFO", "DEBSYM", "DEBTYP"}

_MODS = {}          # (abs src path, cflags, compiler) -> parsed OMF module
_BY_LINK = None     # link name -> symbol-database entry


class CEmuError(Exception):
    pass


def _by_link():
    global _BY_LINK
    if _BY_LINK is None:
        funcs, datas, _ = symbols.load()
        _BY_LINK = {e["link_name"]: e for t in (funcs, datas) for e in t.values()}
    return _BY_LINK


def compile_module(src, cflags=None):
    """Compile and parse `src` (cached per process).  Returns the OMF module."""
    src = os.path.abspath(path(src))
    flags = cflags or match.file_cflags(src)
    cc = match.file_cc(src)
    key = (src, flags, cc)
    mod = _MODS.get(key)
    if mod is not None:
        return mod
    out = path("build", "cemu", cc,
               os.path.splitext(os.path.basename(src))[0] + ".obj")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    mod = match.compile_c(src, flags, out, cc=cc)
    if mod.comdefs:
        raise CEmuError(f"communal variables are not supported: "
                        f"{sorted(mod.comdefs)}")
    _MODS[key] = mod
    return mod


def _align_for(seg):
    """Segment alignment in bytes (OMF align codes: 1 byte, 2 word, 3 para,
    4 page(256), 5 dword)."""
    return {0: 1, 1: 1, 2: 2, 3: 16, 4: 256, 5: 4}.get(seg.align, 16)


class CModule:
    """One compiled C object placed in one emulator."""

    def __init__(self, emu, src, cflags=None, extra=None, mod=None):
        self.emu = emu
        self.src = src
        self.mod = mod or compile_module(src, cflags)
        self.extra = dict(extra or {})   # link name -> address, for symbols
                                         # the database does not know
        mod = self.mod
        self.base = {}                   # segment index -> emulator address
        mem = []                         # (segment index, base, size)
        for i, seg in enumerate(mod.segments, 1):
            if seg.cls in _SKIP_CLASSES:
                continue
            if not seg.length:
                # keep an address so a relocation to an object-less segment
                # (should not happen) still resolves consistently
                self.base[i] = emu.alloc(0, _align_for(seg))
                continue
            b = emu.alloc(seg.length, _align_for(seg))
            self.base[i] = b
            mem.append((i, b))
        for i, b in mem:
            seg = mod.segments[i - 1]
            emu.write(b, bytes(seg.data))
        # public *and* static (LPUBDEF) names: Watcom refers to a file-static
        # symbol through the external-name table (LEXT DEF), so a module-local
        # static must be resolved before the symbol database
        self.publics = {}
        self.local_names = {}
        for name, (si, off) in list(mod.publics.items()) + list(mod.statics.items()):
            if si in self.base:
                self.local_names[name] = self.base[si] + off
                if name in mod.publics:
                    self.publics[name] = self.base[si] + off
        # relocate: the initial field is the addend (Watcom keeps it there)
        for i, b in mem:
            seg = mod.segments[i - 1]
            for fu in seg.fixups:
                self._reloc(seg, b, fu)

    def _target(self, fu):
        if fu.target_kind == "ext":
            if fu.target in self.local_names:
                return self.local_names[fu.target]
            e = _by_link().get(fu.target) or self.extra.get(fu.target)
            if e is None:
                raise CEmuError(f"{self.src}: unknown external symbol "
                                f"{fu.target!r} (add it to the symbol "
                                f"database or pass extra=")
            return e["addr"] if isinstance(e, dict) else e
        if fu.target_kind == "seg":
            if fu.target not in self.base:
                raise CEmuError(f"{self.src}: fixup to unplaced segment "
                                f"{fu.target}")
            return self.base[fu.target]
        raise CEmuError(f"{self.src}: unsupported fixup target kind "
                        f"{fu.target_kind!r}")

    def _reloc(self, seg, base, fu):
        a = base + fu.offset
        field = seg.data[fu.offset:fu.offset + fu.size]
        if fu.loc == 9:
            addend = struct.unpack_from("<i", seg.data, fu.offset)[0] + fu.disp
            tgt = self._target(fu)
            val = tgt + addend - (a + 4 if fu.self_rel else 0)
            self.emu.write(a, struct.pack("<I", val & 0xFFFFFFFF))
            return
        raise CEmuError(f"{self.src}: unsupported fixup location {fu.loc} "
                        f"({omf.LOC_NAMES.get(fu.loc, '?')}) at {fu.offset:#x}")

    # -- calls ------------------------------------------------------------
    def fn(self, name):
        """Address of a public function of the module (by link name)."""
        a = self.publics.get(name)
        if a is None:
            raise CEmuError(f"{self.src}: no public function {name!r} "
                            f"(have {sorted(self.publics)})")
        return a

    def call(self, name, *args, **kw):
        return self.emu.call(self.fn(name), *args, **kw)


def load(emu, src, cflags=None, extra=None):
    """Compile `src` and place it in `emu`; returns the CModule."""
    return CModule(emu, src, cflags=cflags, extra=extra)


def regs(emu, names):
    return {n: emu.reg(n) for n in names}


# Exact byte addresses allowed to neutralize a debug `int3` (0xCC -> 0x90):
# 0x23cf7 is the debug `int3` inside FlicOverrun (0x23cf4).
_ALLOWED_INT3_NOP_ADDRS = frozenset({0x23CF7})


def _orig_func_span(emu, orig_addr, default_span=64):
    """Return `(obj, off, span)` covering the original function bytes starting at `orig_addr`."""
    p = getattr(emu, "p", None)
    if p is None or not hasattr(p, "le") or not hasattr(p, "image"):
        return None, 0, 0
    end_addr = None
    funcs = getattr(p, "functions", None)
    if funcs:
        for f in funcs:
            if f.get("start") == orig_addr and f.get("end", 0) > orig_addr:
                end_addr = int(f["end"])
                break
    for o in p.le.objects:
        if o.base <= orig_addr < o.base + o.vsize:
            img = p.image[o.index]
            off = orig_addr - o.base
            want = (end_addr - orig_addr) if end_addr else default_span
            span = max(0, min(want, len(img) - off))
            return o, off, span
    return None, 0, 0


def _orig_code_patched(emu, orig_addr):
    """True if original image bytes in `[orig_addr, orig_end)` were overwritten in `emu`.

    Allows ONLY the explicitly whitelisted debug `int3` (0xCC) -> `nop` (0x90)
    address(es) in `_ALLOWED_INT3_NOP_ADDRS`.
    """
    o, off, span = _orig_func_span(emu, orig_addr)
    if o is None or span <= 0:
        return False
    orig_bytes = bytes(emu.p.image[o.index][off:off + span])
    try:
        cur_bytes = bytes(emu.read(orig_addr, span))
    except Exception:
        return False
    if hashlib.sha256(cur_bytes).digest() == hashlib.sha256(orig_bytes).digest():
        return False
    for idx, (ob, cb) in enumerate(zip(orig_bytes, cur_bytes)):
        if ob != cb:
            byte_addr = orig_addr + idx
            if not (byte_addr in _ALLOWED_INT3_NOP_ADDRS and ob == 0xCC and cb == 0x90):
                return True
    return False


def _orig_range_stubbed(emu, orig_addr):
    """True if any stub in `emu.stubs` falls within `[orig_addr, orig_end)`."""
    stubs = getattr(emu, "stubs", {}) or {}
    if int(orig_addr) in stubs:
        return True
    _, _, span = _orig_func_span(emu, orig_addr, default_span=1)
    end_addr = orig_addr + max(1, span)
    return any(orig_addr <= int(a) < end_addr for a in stubs)


def record_t4_audit(entry):
    """Append one JSONL runtime oracle record when `WC1_T4_AUDIT_LOG` is set."""
    log_path = os.environ.get("WC1_T4_AUDIT_LOG")
    if not log_path:
        return
    rec = dict(entry)
    rec.setdefault("node_id", os.environ.get("PYTEST_CURRENT_TEST", ""))
    nonce = os.environ.get("WC1_T4_AUDIT_NONCE", "")
    if nonce:
        rec["nonce"] = nonce
    try:
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, sort_keys=True) + "\n")
    except OSError:
        pass


def run_pair(emu, orig_addr, cmod, name, *args, watch=(), out_regs=("eax",),
             stack_args=(), regs_in=None, cdecl=False, interrupt=False):
    """Run the original at `orig_addr` and the compiled C function `name` on
    identical inputs; returns a list of differences (empty = equal).

    Memory at the `watch` ranges is snapshotted before the original call and
    restored before the C call, so both see the same globals.  The outputs
    compared are `out_regs` and the final contents of the watched ranges.
    """
    if "call" in vars(emu) or type(emu).call is not Emu.call:
        raise CEmuError("emu.call was overridden (refusing tampered emulator)")
    orig_addr_i = int(orig_addr)
    orig_stubbed = _orig_range_stubbed(emu, orig_addr_i)
    orig_patched_before = _orig_code_patched(emu, orig_addr_i)
    saved = [(a, emu.read(a, n)) for a, n in watch]
    kw = dict(stack_args=stack_args, regs=regs_in, cdecl=cdecl, interrupt=interrupt)
    emu.call(orig_addr_i, *args, **kw)
    orig_insns = int(getattr(emu, "_count", 0))
    orig_patched_after = _orig_code_patched(emu, orig_addr_i)
    ro = regs(emu, out_regs)
    mo = [(a, emu.read(a, n)) for a, n in watch]
    for a, data in saved:
        emu.write(a, data)
    cmod.call(name, *args, **kw)
    rc = regs(emu, out_regs)
    mc = [(a, emu.read(a, n)) for a, n in watch]

    diffs = []
    for r in out_regs:
        if ro[r] != rc[r]:
            diffs.append(f"{r}: original {ro[r]:#x} != C {rc[r]:#x}")
    for (a, _), (_, x), (_, y) in zip(watch, mo, mc):
        if x != y:
            for k in range(len(x)):
                if x[k] != y[k]:
                    diffs.append(f"memory {a + k:#x}: original {x[k]:02x} "
                                 f"!= C {y[k]:02x}")
                    break
    src_attr = getattr(cmod, "src", None)
    valid_watch = [(a, int(n)) for a, n in watch if int(n) > 0]
    record_t4_audit({
        "kind": "run_pair",
        "src": os.path.realpath(path(src_attr)) if src_attr else "",
        "func_name": name,
        "orig_addr": orig_addr_i,
        "orig_insns": orig_insns,
        "diffs_count": len(diffs),
        "out_regs": list(out_regs),
        "watch_count": len(valid_watch),
        "observed": bool(out_regs) or bool(valid_watch),
        "orig_stubbed": bool(orig_stubbed),
        "orig_patched": bool(orig_patched_before or orig_patched_after),
    })
    return diffs
