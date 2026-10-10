"""Emit war.exe as fully-symbolic NASM source.

Every absolute address (LE fixup) and every relative branch target is written
as a symbol, so the program can be relinked at other addresses and functions
can be replaced by compiled C one at a time.

Two output flavours share the same source body (selected by the
WC1_FORMAT_BIN define):
  * bin: sections at the original virtual addresses; the assembled output must
    be byte-identical to the loaded image (the round-trip proof);
  * obj: OMF segments for linking with wlink into a DOS/4GW LE executable.

Instructions whose NASM encoding differs from the original are emitted as raw
bytes with their symbolic fields (fixups, branch displacements) preserved.
That set is computed by `verify_roundtrip` and persisted, so emission is
deterministic.
"""
import bisect
import os
import re
import struct
import subprocess
from collections import defaultdict

from capstone import x86

from . import analysis

STRING_OPS = re.compile(r"^(rep |repe |repne )?(movs|stos|lods|scas|cmps|ins|outs)[bwd]$")
NO_SIZE = {"lea", "les", "lds", "lss", "lfs", "lgs", "sgdt", "sidt", "lgdt", "lidt",
           "fnstenv", "fldenv", "fnsave", "frstor", "fxsave", "fxrstor", "invlpg"}
SIZE_KW = {1: "byte", 2: "word", 4: "dword", 8: "qword", 10: "tword"}
REL_BRANCH = analysis.COND_JUMPS | {"jmp", "call"}
# capstone spelling -> NASM spelling
MNEMONIC_MAP = {"pushal": "pushad", "popal": "popad", "pushfd": "pushfd", "popfd": "popfd"}


class Emitter:
    def __init__(self, prog=None, names=None, force_raw=(), replaced=(), cuts=None, entries=()):
        """replaced: function starts provided by C objects (each omitted up to its
        limit, legacy layout).  cuts: {start: end} code ranges provided by C
        objects placed in sequence (emit_pieces); entries: the function starts
        those objects define (the only addresses inside a cut that the rest of
        the program may refer to)."""
        self.p = prog or analysis.run()
        self.le = self.p.le
        self.names = names or {}          # addr -> symbol
        self.force_raw = set(force_raw)   # insn addrs to emit as raw bytes
        self.replaced = set(replaced)     # function starts provided by C objects
        self.cuts = dict(cuts or {})
        self.entries = set(entries) | set(self.cuts)
        self._build_labels()
        self._check_replaced()

    def func_range(self, a):
        """[start, limit) of the function starting at a, including trailing
        alignment filler / data up to the next function."""
        for f in self.p.functions:
            if f["start"] == a:
                return a, f["limit"]
        raise KeyError(f"{a:#x} is not a function start")

    def _check_replaced(self):
        p = self.p
        self.replaced_ranges = sorted(self.cuts.items())
        for a in sorted(self.replaced):
            s, e = self.func_range(a)
            self.replaced_ranges.append((s, e))
        self.replaced_ranges.sort()
        in_cut = lambda a: any(s <= a < e for s, e in self.replaced_ranges)
        errs = []
        for s, e in self.replaced_ranges:
            inside = lambda t: s < t < e and t not in self.entries
            for ia, i in p.insns.items():
                if s <= ia < e:
                    continue
                if i.mnemonic in REL_BRANCH and i.operands and i.operands[0].type == x86.X86_OP_IMM:
                    if inside(i.operands[0].imm & 0xFFFFFFFF):
                        errs.append(f"{ia:#x} branches into the interior of replaced {s:#x}")
            for src, (f, t) in p.fix_at.items():
                if not in_cut(src) and inside(t):
                    errs.append(f"{src:#x} references the interior of replaced {s:#x} ({t:#x})")
        if errs:
            raise ValueError("cannot replace:\n" + "\n".join(errs[:20]))

    # ------------------------------------------------------------------
    def _build_labels(self):
        p = self.p
        fstarts = set(f["start"] for f in p.functions)
        labels = {}
        for a in fstarts:
            labels[a] = f"fn_{a:05x}"
        for a in p.jump_targets | set(t for t, k in p.ptr_targets.items()):
            if a in p.insns and a not in labels:
                labels[a] = f"loc_{a:05x}"
        for a in p.call_targets:
            if a in p.insns and a not in labels:
                labels[a] = f"fn_{a:05x}"
        # every fixup target becomes a label (or label+offset)
        self.targets = set()
        for s, (f, t) in p.fix_at.items():
            self.targets.add(t)
        # bytes covered by a fixup field outside instructions (pointer data):
        # no label may be placed strictly inside such a field.
        inside_slot = set()
        for s in p.fix_at:
            if s not in p.owner:
                inside_slot.update((s + 1, s + 2, s + 3))
        data = self.le.obj(analysis.DATA_OBJ)
        code = self.le.obj(analysis.CODE_OBJ)
        for t in self.targets:
            if t in labels:
                continue
            if code.base <= t < code.end:
                if t in p.insns:
                    labels[t] = f"loc_{t:05x}"
                elif t in p.owner:
                    continue  # inside an instruction: expressed as insn label + k
                elif t not in inside_slot:
                    labels[t] = f"cd_{t:05x}"
            elif data.base <= t < data.end:
                if t not in inside_slot:
                    labels[t] = f"dat_{t:05x}"
        # instructions that own an interior target need a label themselves
        for t in self.targets:
            if t in p.owner and p.owner[t] != t and p.owner[t] not in labels:
                labels[p.owner[t]] = f"loc_{p.owner[t]:05x}"
        # names from the symbol database (also create labels for symbols that
        # no fixup references, e.g. variables only used via base+offset)
        for a, n in self.names.items():
            if a in labels:
                labels[a] = n
            elif code.base <= a < code.end and (a in p.insns or a not in p.owner):
                labels[a] = n
            elif data.base <= a < data.end and a not in inside_slot:
                labels[a] = n
        # C-provided code ranges: only the function names the C object defines
        # survive; a label at each cut end keeps symbolic expressions for
        # addresses after a cut independent of its contents.
        for s, e in self.cuts.items():
            for a in [a for a in labels if s <= a < e and a not in self.entries]:
                del labels[a]
            if e not in labels and code.base <= e < code.end:
                labels[e] = f"loc_{e:05x}"
        self.labels = labels
        self.sorted_labels = sorted(labels)
        self.code_end_label = "code_end"
        self.data_end_label = "data_end"

    def sym(self, t):
        """Symbolic expression for absolute address t."""
        if t in self.labels:
            return self.labels[t]
        p, le = self.p, self.le
        code, data = le.obj(analysis.CODE_OBJ), le.obj(analysis.DATA_OBJ)
        if t in p.owner and p.owner[t] in self.labels:
            o = p.owner[t]
            return f"{self.labels[o]}+{t - o}"
        if t == code.end:
            return self.code_end_label
        if t == data.end:
            return self.data_end_label
        # nearest label at or below within the same object, else above
        for obj, endlab in ((code, self.code_end_label), (data, self.data_end_label)):
            if obj.base <= t <= obj.end:
                i = bisect.bisect_right(self.sorted_labels, t) - 1
                if i >= 0 and self.sorted_labels[i] >= obj.base:
                    b = self.sorted_labels[i]
                    return f"{self.labels[b]}+{t - b}"
        # outside every object (biased array base): relative to the next object
        for obj in (code, data):
            if t < obj.base:
                first = min(a for a in self.sorted_labels if a >= obj.base)
                return f"{self.labels[first]}-{first - t}"
        raise ValueError(f"cannot express {t:#x}")

    # ------------------------------------------------------------------
    def _mem(self, i, op, fix_disp):
        m = op.mem
        parts = []
        if m.segment:
            seg = i.reg_name(m.segment) + ":"
        else:
            seg = ""
        if m.base:
            parts.append(i.reg_name(m.base))
        if m.index:
            parts.append(f"{i.reg_name(m.index)}*{m.scale}")
        if fix_disp is not None:
            parts.append(fix_disp)
        elif m.disp or not parts:
            d = m.disp
            if parts:
                parts.append(f"-{-d:#x}" if d < 0 else f"{d:#x}")
            else:
                parts.append(f"{d & 0xFFFFFFFF:#x}")
        expr = "+".join(parts).replace("+-", "-")
        size = "" if i.mnemonic in NO_SIZE else SIZE_KW.get(op.size, "")
        # Under -O0 every displacement width must be explicit to reproduce
        # the original disp8/disp32 choice.
        disp_kw = ""
        if m.base and fix_disp is None:
            if i.disp_size == 4:
                disp_kw = "dword "
            elif i.disp_size == 1:
                disp_kw = "byte "
        elif not m.base and m.index and m.scale > 1:
            disp_kw = "nosplit "
        return f"{size + ' ' if size else ''}[{seg}{disp_kw}{expr}]"

    def insn_text(self, i):
        """NASM text for capstone insn i, or None if it must be raw."""
        p = self.p
        if i.address in self.force_raw:
            return None
        m = i.mnemonic
        if STRING_OPS.match(m):
            # only the plain forms (no segment override on the source)
            if any(b in (0x26, 0x2E, 0x36, 0x3E, 0x64, 0x65) for b in i.bytes[:-1]):
                return None
            return m
        fix_slots = {}
        for s in range(i.address, i.address + i.size):
            if s in p.fix_at:
                fix_slots[s] = self.sym(p.fix_at[s][1])
        disp_fix = fix_slots.get(i.address + i.disp_offset) if i.disp_size == 4 else None
        imm_fix = fix_slots.get(i.address + i.imm_offset) if i.imm_size == 4 else None
        if len(fix_slots) != (disp_fix is not None) + (imm_fix is not None):
            return None
        ops = []
        if m in REL_BRANCH and i.operands and i.operands[0].type == x86.X86_OP_IMM:
            t = i.operands[0].imm & 0xFFFFFFFF
            if t not in self.labels:
                return None
            if m == "call":
                return f"call {self.labels[t]}"
            if m in ("loop", "loope", "loopne", "jecxz", "jcxz"):
                return f"{m} {self.labels[t]}"
            short = i.size == 2
            return f"{m} {'short' if short else 'near'} {self.labels[t]}"
        for op in i.operands:
            if op.type == x86.X86_OP_REG:
                r = i.reg_name(op.reg)
                r = re.sub(r"st\((\d)\)", r"st\1", r)
                ops.append(r)
            elif op.type == x86.X86_OP_IMM:
                if imm_fix is not None:
                    ops.append(imm_fix)
                else:
                    v = op.imm
                    ops.append(f"{v:#x}" if v >= 0 else f"-{-v:#x}")
            elif op.type == x86.X86_OP_MEM:
                ops.append(self._mem(i, op, disp_fix))
            else:
                return None
        mn = MNEMONIC_MAP.get(m, m)
        if mn in ("call", "jmp") and i.operands and i.operands[0].type == x86.X86_OP_MEM \
                and i.operands[0].size == 6:
            return None
        txt = mn + (" " + ", ".join(ops) if ops else "")
        # immediates: keep the original width
        if imm_fix is None and i.imm_size in (1, 4) and ops and i.operands:
            last = i.operands[-1]
            if last.type == x86.X86_OP_IMM and last.size > i.imm_size:
                ops[-1] = "byte " + ops[-1]
            elif last.type == x86.X86_OP_IMM and i.imm_size == 4:
                ops[-1] = "dword " + ops[-1]
            txt = mn + " " + ", ".join(ops)
        if imm_fix is not None and m == "push":
            txt = f"push dword {imm_fix}"
        return txt

    def raw_text(self, i):
        """Raw-byte form keeping symbolic fixup and branch fields."""
        p = self.p
        b = i.bytes
        fields = {}  # offset -> (size, expr)
        for k in range(i.size):
            s = i.address + k
            if s in p.fix_at:
                fields[k] = (4, self.sym(p.fix_at[s][1]))
        m = i.mnemonic
        if m in REL_BRANCH and i.operands and i.operands[0].type == x86.X86_OP_IMM:
            t = i.operands[0].imm & 0xFFFFFFFF
            if t in self.labels:
                n = 1 if i.size == 2 or m in ("loop", "loope", "loopne", "jecxz", "jcxz") else 4
                fields[i.size - n] = (n, f"{self.labels[t]}-($+{n})")
        out, k = [], 0
        while k < i.size:
            if k in fields:
                n, e = fields[k]
                out.append(("dd " if n == 4 else "db ") + e)
                k += n
            else:
                j = k
                while j < i.size and j not in fields:
                    j += 1
                out.append("db " + ",".join(f"0x{x:02x}" for x in b[k:j]))
                k = j
        return out

    # ------------------------------------------------------------------
    def emit(self, path):
        """Single source file: the whole program (round-trip and legacy build)."""
        code, data = self.le.obj(analysis.CODE_OBJ), self.le.obj(analysis.DATA_OBJ)
        L = []
        w = L.append
        self.line_addr = {}
        w("; war.exe (Warcraft: Orcs & Humans CD v1.22h) -- generated by tools/wc1/emit.py")
        w("; DO NOT EDIT: regenerate with `make asm`.")
        w('%include "wc1.inc"')
        w("")
        w("CODE_SECTION")
        self._emit_code(L, code.base, code.end)
        w(f"GLABEL {self.code_end_label}")
        w("")
        self._emit_data(L, data.base, data.end, legacy=True)
        w(f"GLABEL {self.data_end_label}")
        w("END_SECTIONS")
        with open(path, "w") as f:
            f.write("\n".join(L) + "\n")

    def _emit_code(self, L, start, end):
        p, le = self.p, self.le
        code = le.obj(analysis.CODE_OBJ)
        w = L.append
        fstart = {f["start"]: f for f in p.functions}
        a = start
        cimg = p.cbytes
        rr = dict(self.replaced_ranges)
        while a < end:
            if a in rr:
                w("")
                w(f"; ---- {a:#x}..{rr[a]:#x} is provided by reconstructed C: {self.labels[a]}")
                if a in self.replaced:
                    w(f"EXTERN_FN {self.labels[a]}")
                a = rr[a]
                continue
            if a in self.labels:
                if a in fstart:
                    w("")
                    w(f"; ---- function {a:#x}")
                w(f"GLABEL {self.labels[a]}")
            if a == le.entry:
                w("ENTRY_POINT")
            if a in p.insns:
                i = p.insns[a]
                t = self.insn_text(i)
                if t is None:
                    for line in self.raw_text(i):
                        self.line_addr[len(L) + 1] = a
                        w(f"    {line}")
                    w(f"    ; ^ {i.mnemonic} {i.op_str}")
                else:
                    self.line_addr[len(L) + 1] = a
                    w(f"    {t}")
                a += i.size
                continue
            # data in code (also the tail of an instruction cut by a C range)
            b = a + 1
            while b < end and b not in p.insns and b not in self.labels \
                    and (b not in p.fix_at) and (a not in p.fix_at) and b not in rr:
                b += 1
            if a in p.fix_at:
                w(f"    dd {self.sym(p.fix_at[a][1])}")
                a += 4
            else:
                self._emit_bytes(w, cimg[a - code.base:b - code.base])
                a = b
        assert a == end, (hex(a), hex(end))

    def data_regions(self):
        """[(start, end, macro)] of the data object: initialised data, BSS, stack."""
        data = self.le.obj(analysis.DATA_OBJ)
        init_end = data.base + self.p.data_init_size
        sb = self.stack_base()
        return [(data.base, init_end, "DATA_SECTION"), (init_end, sb, "BSS_SECTION"),
                (sb, data.end, "STACK_SECTION")]

    def _emit_data(self, L, start, end, legacy=False):
        p = self.p
        data = self.le.obj(analysis.DATA_OBJ)
        w = L.append
        dimg = bytes(p.image[analysis.DATA_OBJ])
        a = start
        for rs, re_, macro in self.data_regions():
            if a >= end or a >= re_:
                continue
            if legacy and macro == "STACK_SECTION":
                w("")
                w("; Main program stack: initial ESP is the end of the data object.")
            w("")
            w(macro)
            stop = min(end, re_)
            bss = macro != "DATA_SECTION"
            while a < stop:
                if a in self.labels:
                    w(f"GLABEL {self.labels[a]}")
                if not bss and a in p.fix_at:
                    w(f"    dd {self.sym(p.fix_at[a][1])}")
                    a += 4
                    continue
                b = a + 1
                while b < stop and b not in self.labels and (bss or b not in p.fix_at):
                    b += 1
                if bss:
                    w(f"    resb {b - a}")
                else:
                    self._emit_bytes(w, dimg[a - data.base:b - data.base])
                a = b
        assert a == end, (hex(a), hex(end))

    # ------------------------------------------------------------------
    def emit_pieces(self, outdir, code_pieces, data_pieces):
        """Write one OMF asm source per piece, for linking in sequence with the
        C objects in between.  code_pieces / data_pieces: lists of [start, end)
        (or None for an empty piece), equally long; piece k holds code_pieces[k]
        and data_pieces[k].  The first piece declares every segment and the
        group, so the segment order is the original's whatever the C objects
        declare.  Returns the file names."""
        code, data = self.le.obj(analysis.CODE_OBJ), self.le.obj(analysis.DATA_OBJ)
        all_names = set(self.labels.values()) | {self.code_end_label, self.data_end_label}
        ident = re.compile(r"[A-Za-z_.$?@][\w.$?@]*")
        out = []
        self.line_addr = {}
        for k, (cp, dp) in enumerate(zip(code_pieces, data_pieces)):
            L = []
            if cp:
                L.append("CODE_SECTION")
                self._emit_code(L, *cp)
                if cp[1] == code.end:
                    L.append(f"GLABEL {self.code_end_label}")
            if dp:
                self._emit_data(L, *dp)
                if dp[1] == data.end:
                    L.append(f"GLABEL {self.data_end_label}")
            defined = {l.split()[1] for l in L if l.startswith("GLABEL ")}
            used = set()
            for l in L:
                if l.startswith(("GLABEL ", ";")) or not l.startswith("    "):
                    continue
                t = l.split(";", 1)[0]
                if "'" in t:
                    continue
                used.update(n for n in ident.findall(t) if n in all_names)
            head = [f"; war.exe piece {k} -- generated by tools/wc1/emit.py (wc1.build)",
                    '%include "wc1.inc"']
            if k == 0:
                head.append("DECLARE_SECTIONS")
            head += [f"extern {n}:wrt FLAT" for n in sorted(used - defined)]
            fn = os.path.join(outdir, f"piece_{k:03d}.asm")
            with open(fn, "w") as f:
                f.write("\n".join(head + L) + "\n")
            out.append(fn)
        return out

    def stack_base(self):
        """Start of the main stack: the region from the highest labelled BSS
        address to the initial ESP. (In war.exe that label, 0x64180, is the
        top of an interrupt handler's private stack -- see fn_3d938.)"""
        data = self.le.obj(analysis.DATA_OBJ)
        assert self.le.initial_esp == data.end
        return max(a for a in self.labels if data.base <= a < data.end)

    @staticmethod
    def _emit_bytes(w, bs):
        k = 0
        while k < len(bs):
            # printable string run terminated by NUL
            j = k
            while j < len(bs) and 0x20 <= bs[j] < 0x7F and bs[j] not in (0x27, 0x5C):
                j += 1
            if j - k >= 4:
                w(f"    db '{bs[k:j].decode()}'")
                k = j
                continue
            chunk = bs[k:k + 16]
            # stop the chunk before a string run
            for m in range(1, len(chunk)):
                q = k + m
                r = q
                while r < len(bs) and 0x20 <= bs[r] < 0x7F and bs[r] not in (0x27, 0x5C):
                    r += 1
                if r - q >= 4:
                    chunk = bs[k:q]
                    break
            w("    db " + ",".join(f"0x{x:02x}" for x in chunk))
            k += len(chunk)
