"""Recursive-descent code discovery and function partitioning for war.exe.

Because LE requires a fixup for every absolute address, the set of
fixups whose target lies in the code object is (modulo computed addresses) the
complete set of indirect entry points: function pointers, jump-table targets,
callbacks. Together with the program entry point and direct call/jump targets
this gives a sound code/data split of the code object.

Outputs a JSON description consumed by the asm emitter, the Ghidra importer
and the symbol database tooling.
"""
import bisect
import json
import struct
from collections import defaultdict

import capstone
from capstone import x86

from . import le as lefmt

CODE_OBJ, DATA_OBJ = 1, 2

COND_JUMPS = {
    "jo", "jno", "jb", "jae", "je", "jne", "jbe", "ja", "js", "jns", "jp", "jnp",
    "jl", "jge", "jle", "jg", "jcxz", "jecxz", "loop", "loope", "loopne",
}
TERMINATORS = {"ret", "retf", "iret", "iretd", "hlt", "jmp", "ljmp"}

# Instructions that never appear in Watcom-generated code and essentially never
# in the hand-written asm of this era; decoding one means we are in data.
IMPLAUSIBLE = {"bound", "arpl", "aaa", "aas", "daa", "das", "aam", "aad", "into",
               "salc", "insb", "insd", "insw", "icebp", "ud0", "ud1", "ud2",
               "lldt", "ltr", "lgdt", "lidt"}
# (cmc, les/lss/lgs, fwait, in/out, outs*, pusha/popa and push/pop of segment
#  registers all occur in the genuine runtime / hand-written asm; so do the
#  unprivileged sidt/sgdt/smsw used for environment detection.)


class _Reject(Exception):
    pass


class Program:
    def __init__(self, exe=None):
        self.le = lefmt.load(exe)
        self.image = self.le.loaded_image()
        self.code = self.le.obj(CODE_OBJ)
        self.data = self.le.obj(DATA_OBJ)
        self.cbytes = bytes(self.image[CODE_OBJ])
        self.md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
        self.md.detail = True
        # fixup lookup by absolute source address
        self.fix_at = {}
        for f in self.le.fixups_unique:
            src = self.le.obj(f.obj).base + f.src_off
            tgt = (self.le.obj(f.target_obj).base + f.target_off) & 0xFFFFFFFF
            self.fix_at[src] = (f, tgt)

    @property
    def data_init_size(self):
        """Initialised extent of the data object. The LE writer trims trailing
        zero bytes from the last page, which can cut into the final pointer;
        extend to cover every fixup field."""
        d = self.data
        end = max([d.file_size] + [s + 4 - d.base for s in self.fix_at if d.base <= s < d.end])
        return end

    def in_code(self, a):
        return self.code.base <= a < self.code.base + self.code.vsize

    def insn_at(self, a):
        off = a - self.code.base
        for i in self.md.disasm(self.cbytes[off:off + 16], a, 1):
            return i
        return None

    # ------------------------------------------------------------------
    def _operand_slots(self, i):
        """Byte offsets within insn i that may legitimately carry a 32-bit fixup."""
        slots = set()
        if i.disp_size == 4:
            slots.add(i.address + i.disp_offset)
        if i.imm_size == 4:
            slots.add(i.address + i.imm_offset)
        return slots

    def _closure(self, seed, owner, strict=True):
        """Speculatively decode the flow closure of `seed`. Returns
        (insns, calls, jumps) or raises _Reject. Already-accepted instructions
        terminate paths."""
        local, lowner = {}, {}
        calls, jumps = set(), set()
        work = [seed]
        while work:
            a = work.pop()
            while True:
                if a in self.insns or a in local:
                    break
                if not self.in_code(a):
                    raise _Reject("flow-leaves-code", a)
                if a in owner or a in lowner:
                    raise _Reject("overlap", a)
                if a in self.table_bytes:
                    raise _Reject("into-table", a)
                i = self.insn_at(a)
                if i is None:
                    raise _Reject("bad-decode", a)
                if strict and i.mnemonic in IMPLAUSIBLE:
                    raise _Reject("implausible", a, i.mnemonic)
                if strict and i.bytes[:2] == b"\x00\x00":
                    raise _Reject("zero-bytes", a)
                slots = self._operand_slots(i)
                for k in range(i.size):
                    b = a + k
                    if b in owner or b in lowner:
                        raise _Reject("overlap", b)
                    if b in self.table_bytes:
                        raise _Reject("into-table", b)
                    if b in self.fix_at and b not in slots:
                        raise _Reject("fixup-misaligned", b)
                    if b in self.fix_at and b not in slots:
                        raise _Reject("fixup-misaligned", b)
                # a fixup may also start inside the insn but straddle its end
                for b in range(a - 3, a + i.size):
                    if b in self.fix_at and b < a + i.size < b + 4 and b not in slots:
                        raise _Reject("fixup-straddles", b)
                local[a] = i
                for k in range(i.size):
                    lowner[a + k] = a
                m = i.mnemonic
                if m == "call" or m in COND_JUMPS or m == "jmp":
                    op = i.operands[0] if i.operands else None
                    if op is not None and op.type == x86.X86_OP_IMM:
                        t = op.imm & 0xFFFFFFFF
                        (calls if m == "call" else jumps).add(t)
                        work.append(t)
                if m in TERMINATORS:
                    break
                a += i.size
        return local, lowner, calls, jumps

    def _jump_tables(self, i):
        """For an accepted `jmp dword ptr [disp + reg*4]` whose disp is a fixup
        into the code object, return (table_addr, [targets])."""
        if i.mnemonic != "jmp" or not i.operands or i.operands[0].type != x86.X86_OP_MEM:
            return None
        mem = i.operands[0].mem
        if mem.scale != 4 or mem.base != 0:
            return None
        slot = i.address + i.disp_offset
        if slot not in self.fix_at:
            return None
        tbl = self.fix_at[slot][1]
        if not self.in_code(tbl):
            return None
        out, a = [], tbl
        while a in self.fix_at and self.in_code(self.fix_at[a][1]) and a not in self.owner:
            out.append(self.fix_at[a][1])
            a += 4
        return tbl, out

    FILLERS = (bytes.fromhex("8d8000000000"), bytes.fromhex("8d9200000000"),
               bytes.fromhex("8d542200"), bytes.fromhex("8d4000"),
               bytes.fromhex("8d5200"), bytes.fromhex("8bc0"), bytes.fromhex("8bd2"),
               b"\x90", b"\x00")

    def _skip_filler(self, a, b):
        """Skip Watcom alignment filler starting at a (bounded by b)."""
        while a < b:
            for f in self.FILLERS:
                n = len(f)
                if a + n <= b and self.cbytes[a - self.code.base:a - self.code.base + n] == f:
                    a += n
                    break
            else:
                break
        return a

    def discover(self):
        self.insns, self.owner = {}, {}
        self.table_bytes = set()
        self.jump_tables = {}
        self.call_targets, self.jump_targets = set(), set()
        self.rejected = []
        self.seed_kind = {}

        # classify every fixup that targets the code object
        data_ptrs, operand_ptrs, code_ptrs = set(), set(), set()
        for s, (f, t) in self.fix_at.items():
            if not self.in_code(t):
                continue
            if not self.in_code(s):
                data_ptrs.add(t)
            else:
                code_ptrs.add(t)

        def accept(seed, kind):
            if seed in self.insns:
                return True
            try:
                local, lowner, calls, jumps = self._closure(
                    seed, self.owner, strict=kind not in ("entry", "jump-table"))
            except _Reject as r:
                self.rejected.append((kind, seed) + r.args)
                return False
            self.insns.update(local)
            self.owner.update(lowner)
            self.call_targets |= calls
            self.jump_targets |= jumps
            self.seed_kind.setdefault(seed, kind)
            # newly accepted indirect jumps may reveal jump tables
            for a, i in local.items():
                jt = self._jump_tables(i)
                if jt:
                    tbl, targets = jt
                    self.jump_tables[tbl] = (a, targets)
                    self.table_bytes.update(range(tbl, tbl + 4 * len(targets)))
                    for t in targets:
                        pending.append((t, "jump-table"))
            return True

        pending = [(self.le.entry, "entry")]
        def drain():
            while pending:
                accept(*pending.pop())
        drain()
        # function pointers stored in the data object
        for t in sorted(data_ptrs):
            pending.append((t, "data-ptr"))
            drain()
        # pointers into code referenced from code (callbacks pushed/moved
        # as immediates, tables in code). Only accept those that validate.
        for t in sorted(code_ptrs):
            pending.append((t, "code-ptr"))
            drain()

        # Unreferenced (dead) code: the linker keeps every function of every
        # object file, so unused functions remain in the image. Scan gaps,
        # skipping alignment filler, and accept strictly-validated closures.
        progress = True
        while progress:
            progress = False
            for a, b in self.gaps():
                a = self._skip_filler(a, b)
                if a is None or a >= b:
                    continue
                if accept(a, "gap-scan"):
                    drain()
                    progress = True

        # any fixup in the code object that is not inside an instruction is data
        for s in self.fix_at:
            if self.in_code(s) and s not in self.owner:
                self.table_bytes.update(range(s, s + 4))

        self.ptr_targets = defaultdict(set)
        for s, (f, t) in self.fix_at.items():
            if self.in_code(t):
                if not self.in_code(s):
                    self.ptr_targets[t].add("data")
                elif s in self.owner:
                    self.ptr_targets[t].add("code-operand")
                else:
                    self.ptr_targets[t].add("code-table")
        for tbl, (j, targets) in self.jump_tables.items():
            for t in targets:
                self.ptr_targets[t].add("jump-table")
        self.code_data = self.table_bytes
        self.conflicts = [r for r in self.rejected]
        return self

    # ------------------------------------------------------------------
    def partition(self):
        """Partition decoded code into functions.

        Function starts: entry, direct call targets, and pointer targets that
        are referenced from data or as instruction operands (callbacks).
        Jump-table targets (code-table only) are internal labels.
        Each function extends to the next function start; we then check that
        no non-call control flow crosses a function boundary except to another
        function's start (tail call)."""
        starts = {self.le.entry} | self.call_targets
        for t, kinds in self.ptr_targets.items():
            if t in self.insns and kinds - {"code-table", "jump-table"}:
                starts.add(t)
        starts = sorted(s for s in starts if s in self.insns)
        self.func_starts = starts
        code_end = self.code.base + self.code.vsize

        funcs = []
        for k, s in enumerate(starts):
            limit = starts[k + 1] if k + 1 < len(starts) else code_end
            # reachable instructions from s within [s, limit)
            seen, work, cross = set(), [s], []
            while work:
                a = work.pop()
                while a not in seen:
                    i = self.insns.get(a)
                    if i is None:
                        break
                    if not (s <= a < limit):
                        if a not in starts:
                            cross.append(a)
                        break
                    seen.add(a)
                    m = i.mnemonic
                    if (m in COND_JUMPS or m == "jmp") and i.operands and \
                            i.operands[0].type == x86.X86_OP_IMM:
                        t = i.operands[0].imm & 0xFFFFFFFF
                        if s <= t < limit:
                            work.append(t)
                        elif t not in starts:
                            cross.append(t)
                    if m in TERMINATORS:
                        break
                    a += i.size
            # also include jump-table targets inside the range
            for t, kinds in self.ptr_targets.items():
                if s < t < limit and "jump-table" in kinds and t not in seen:
                    work = [t]
                    while work:
                        a = work.pop()
                        while a not in seen and s <= a < limit and a in self.insns:
                            i = self.insns[a]
                            seen.add(a)
                            m = i.mnemonic
                            if (m in COND_JUMPS or m == "jmp") and i.operands and \
                                    i.operands[0].type == x86.X86_OP_IMM:
                                tt = i.operands[0].imm & 0xFFFFFFFF
                                if s <= tt < limit:
                                    work.append(tt)
                            if m in TERMINATORS:
                                break
                            a += i.size
            end = max((a + self.insns[a].size for a in seen), default=s)
            funcs.append({"start": s, "end": end, "limit": limit,
                          "ninsns": len(seen), "cross": sorted(set(cross))})
        self.functions = funcs
        return self

    # ------------------------------------------------------------------
    def coverage(self):
        lo, hi = self.code.base, self.code.base + self.code.vsize
        insn_bytes = len(self.owner)
        table_bytes = len(self.code_data)
        return {"code_size": hi - lo, "insn_bytes": insn_bytes,
                "table_bytes": table_bytes,
                "unclassified": hi - lo - insn_bytes - table_bytes}

    def gaps(self):
        """Maximal runs of code-object bytes that are neither decoded
        instructions nor fixup tables."""
        lo, hi = self.code.base, self.code.base + self.code.vsize
        out, a = [], lo
        while a < hi:
            if a in self.owner or a in self.table_bytes:
                a += 1
                continue
            b = a
            while b < hi and b not in self.owner and b not in self.table_bytes:
                b += 1
            out.append((a, b))
            a = b
        return out

    def to_json(self):
        return {
            "entry": self.le.entry,
            "objects": [{"index": o.index, "base": o.base, "vsize": o.vsize,
                         "flags": o.flags, "file_size": o.file_size}
                        for o in self.le.objects],
            "functions": self.functions,
            "ptr_targets": {hex(k): sorted(v) for k, v in sorted(self.ptr_targets.items())},
            "gaps": self.gaps(),
            "conflicts": self.conflicts,
            "coverage": self.coverage(),
        }


def run(exe=None):
    return Program(exe).discover().partition()


if __name__ == "__main__":
    import sys
    p = run()
    print(json.dumps(p.coverage()))
    print("functions:", len(p.functions), "conflicts:", len(p.conflicts))
    for c in p.conflicts[:30]:
        print("  rejected", [hex(x) if isinstance(x, int) else x for x in c])
    gaps = p.gaps()
    print("gaps:", len(gaps), "bytes:", sum(b - a for a, b in gaps))
    for a, b in gaps[:60]:
        print(f"  {a:08x}-{b:08x} {b-a:6d} {p.cbytes[a-p.code.base:min(b,a+24)-p.code.base].hex()}")
    crossing = [f for f in p.functions if f["cross"]]
    print("functions with crossing flow:", len(crossing))
    for f in crossing[:20]:
        print(f"  {f['start']:08x} -> {[hex(c) for c in f['cross']]}")
