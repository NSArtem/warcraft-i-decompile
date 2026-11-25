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
import hashlib
import json
import os
import pickle
import struct
import sys
import tomllib
from collections import defaultdict
from collections.abc import Mapping

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


# A mid-function block lifted out of its function ("function" candidates that
# begin with a stack pop, an epilogue, or parameters read through the caller's
# stack frame) can be spotted by its stack balance: walking the linear run
# from the candidate start, a pop/ret that takes the running depth below zero
# means the code did not push what it pops, i.e. it is not an entry point.
# Genuine functions that switch stacks explicitly (lss esp / mov esp) stop the
# check (Watcom's _hardresume does this) and AIL/hand-written asm is exempt
# (the caller filters by module kind).
def stack_underflow(start, insns, limit):
    """Address of the first instruction that pops below the candidate's own
    stack depth, or None.  `insns` maps address -> capstone instruction."""
    d = 0
    a = start
    while a < limit:
        i = insns.get(a)
        if i is None:
            return None
        m, ops = i.mnemonic, i.op_str
        if m == "push":
            d += 4
        elif m in ("pushal", "pushad"):
            d += 32
        elif m in ("pushfd", "pushf"):
            d += 4
        elif m == "pop":
            d -= 4
        elif m in ("popal", "popad"):
            d -= 32
        elif m in ("popfd", "popf"):
            d -= 4
        elif m == "sub" and ops.startswith("esp,"):
            try:
                d += int(ops.split(",")[1], 0)
            except ValueError:
                return None
        elif m == "add" and ops.startswith("esp,"):
            try:
                d -= int(ops.split(",")[1], 0)
            except ValueError:
                return None
        elif m == "leave" or (m == "mov" and ops.startswith("esp,")) or \
                (m == "lss" and ops.startswith("esp,")):
            return None                      # explicit stack switch
        if d < 0:
            return a
        if m in TERMINATORS or m.startswith("ret"):
            return None
        a += i.size
    return None


def _read_modules():
    """Content of analysis/modules.toml (empty when not available, e.g. while
    regenerating it).  Read once per run(): the cache key and the module kinds
    discovery uses must come from the same bytes."""
    from . import path
    try:
        with open(path("analysis", "modules.toml"), "rb") as fh:
            return fh.read()
    except OSError:
        return b""


def _module_kinds(modules):
    """Sorted (start, end, kind) of the content of a modules.toml ([] if it does
    not parse)."""
    try:
        doc = tomllib.loads(modules.decode())
    except tomllib.TOMLDecodeError:
        return []
    return sorted((m["start"], m["end"], m.get("kind", "game")) for m in doc.get("module", []))


class _Reject(Exception):
    pass


class _LazyInsns(Mapping):
    """Read-only address -> CsInsn mapping of a Program loaded from the
    analysis cache: the addresses are known, each instruction is decoded
    (with detail, exactly like discovery's insn_at) on first access."""

    def __init__(self, prog, addrs):
        self._prog, self._addrs, self._memo = prog, addrs, {}
        self._set = frozenset(addrs)

    def __getitem__(self, a):
        i = self._memo.get(a)
        if i is None:
            if a not in self._set:
                raise KeyError(a)
            i = self._memo[a] = self._prog.insn_at(a)
        return i

    def __contains__(self, a):
        return a in self._set

    def __iter__(self):
        return iter(self._addrs)

    def __len__(self):
        return len(self._addrs)


class Program:
    def __getstate__(self):
        # capstone objects do not pickle: keep the instruction addresses and
        # rebuild the disassembler (analysis cache, see run()).
        st = dict(self.__dict__)
        st.pop("md", None)
        st["insns"] = list(self.insns)
        return st

    def __setstate__(self, st):
        addrs = st.pop("insns")
        self.__dict__.update(st)
        self.md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
        self.md.detail = True
        self.insns = _LazyInsns(self, addrs)

    def __init__(self, exe=None, modules=None):
        """modules: content of modules.toml (_read_modules; None = read it now)."""
        self.module_kinds = _module_kinds(_read_modules() if modules is None else modules)
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

    def module_kind(self, addr):
        """modules.toml kind for addr ("game" outside every range)."""
        for lo, hi, kind in self.module_kinds:
            if lo <= addr < hi:
                return kind
        return "game"

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
               bytes.fromhex("8d542200"), bytes.fromhex("8d442000"), bytes.fromhex("8d4000"),
               bytes.fromhex("8d5200"), bytes.fromhex("8bc0"), bytes.fromhex("8bd2"),
               bytes.fromhex("8bc9"), bytes.fromhex("8bdb"),
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
            # Stack-plausibility veto for seeds that are not call targets:
            # a linear run that pops below its own frame is a lifted
            # mid-function block or data, not an entry point (e.g. the data
            # table 0x18798, the garbage at 0x24860).  AIL and hand-written
            # asm are exempt.
            if kind in ("data-ptr", "code-ptr", "gap-scan") and \
                    self.module_kind(seed) not in ("ail", "asm", "asm-shared"):
                bad = stack_underflow(seed, local,
                                      self.code.base + self.code.vsize)
                if bad is not None:
                    self.rejected.append((kind, seed, "stack-underflow", bad))
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

        Function starts: entry, direct call targets, pointer targets that
        are referenced from data or as instruction operands (callbacks), and
        gap-scan seeds (unreferenced functions the linker kept).
        Jump-table targets (code-table only) are internal labels.
        Each function extends to the next function start; we then check that
        no non-call control flow crosses a function boundary except to another
        function's start (tail call; conditional or unconditional, with the
        fall-through case excluded unless preceded by no-op filler)."""
        starts = {self.le.entry} | self.call_targets
        gap = {s for s, k in self.seed_kind.items() if k == "gap-scan"}
        for t, kinds in self.ptr_targets.items():
            if t in self.insns and kinds - {"code-table", "jump-table"}:
                starts.add(t)
        starts = sorted(s for s in starts | gap if s in self.insns)
        # A gap-scan seed that the preceding function's own flow jumps past
        # is unreachable code inside that function (dead jmp after a switch,
        # data such as the "WVIDEO" debugger signature), not a function.
        # A jump target (conditional or unconditional, from another function)
        # that cannot be reached by fall-through (preceded by a terminator or
        # by no-op padding) is a function entered only by tail calls -- unless,
        # as for gap seeds, the preceding function's flow jumps past it (a
        # shared exit label such as 0x10498).
        ends = {a + i.size: i for a, i in self.insns.items()}
        dropped, promoted = set(), set()
        while True:
            funcs = self._partition(starts)
            inner = {f2["start"] for f1, f2 in zip(funcs, funcs[1:])
                     if f2["start"] in gap | promoted
                     and f2["start"] not in self.call_targets
                     and any(c >= f2["start"] for c in f1["cross"])}
            if inner:
                dropped |= inner
                starts = [s for s in starts if s not in inner]
                continue
            tails = set()
            for a, i in self.insns.items():
                # conditional and unconditional jumps out of a function to an
                # address outside it: the target is entered only by tail calls
                if i.mnemonic not in (COND_JUMPS | {"jmp"}) or not i.operands or \
                        i.operands[0].type != x86.X86_OP_IMM:
                    continue
                t = i.operands[0].imm & 0xFFFFFFFF
                k = bisect.bisect_right(starts, a) - 1
                if k < 0 or t not in self.insns or t in dropped or \
                        funcs[k]["start"] <= t < funcs[k]["limit"]:
                    continue
                # reachable by fall-through?  (no instruction ends at t, or a
                # terminator ends there; no-op filler is NOT sufficient - a
                # decoded filler can be reachable in-function code, e.g. the
                # `mov eax,eax` at 0x2c226 before 0x2c228)
                if t not in ends or ends[t].mnemonic in TERMINATORS:
                    # Inside another function's *reachable* code?  Then it is
                    # that function's own label (e.g. the shared epilogue at
                    # 0x3c461 reached by far_strnlen/far_wcsnlen's je), not a
                    # function entered by a tail call.
                    h = funcs[bisect.bisect_right(starts, t) - 1]
                    if h["start"] <= t < h["limit"] and t in h["reach"]:
                        continue
                    tails.add(t)
            # A promoted tail target that is a call target, or lies in AIL /
            # hand-written asm, is left alone; any other tail target must
            # pass the stack plausibility check (0x2c1b3, 0x3c461 and 0x1e3ac
            # are lifted blocks / shared epilogues).
            kept = set()
            for t in tails:
                if t in self.call_targets or \
                        self.module_kind(t) in ("ail", "asm", "asm-shared"):
                    kept.add(t)
                    continue
                j = bisect.bisect_right(starts, t)
                limit = starts[j] if j < len(starts) else \
                    self.code.base + self.code.vsize
                bad = stack_underflow(t, self.insns, limit)
                if bad is None:
                    kept.add(t)
                else:
                    self.rejected.append(("tail", t, "stack-underflow", bad))
            tails = kept
            tails -= set(starts)
            if not tails:
                break
            promoted |= tails
            starts = sorted(set(starts) | tails)
        self.func_starts = starts
        self.functions = funcs
        return self

    def _partition(self, starts):
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
            flow = set(seen)   # ordinary flow only (no jump-table blocks)
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
                          "ninsns": len(seen), "cross": sorted(set(cross)),
                          "reach": flow})
        return funcs

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


# Inputs whose content determines the result of run(): a change to any of them
# (or to the Python/capstone version) gives a new cache key.  The inputs are
# hashed by role, not by path (nothing in a Program depends on where its inputs
# live), so a checkout elsewhere with the same inputs has the same key.
_CACHE_INPUTS = ("analysis.py", "le.py", "__init__.py")
_CACHE_FORMAT = 2


def _source_digest(f):
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f), "rb") as fh:
            return hashlib.sha256(fh.read()).digest()
    except OSError:
        return b"<missing>"


# at import: the code this process runs, whatever happens to the files later
_SOURCE_DIGESTS = {f: _source_digest(f) for f in _CACHE_INPUTS}


def _cache_key(exe, modules=None):
    """modules: the modules.toml content the result is computed from (None = read it now)."""
    from . import ORIGINAL_EXE
    h = hashlib.sha256(f"{_CACHE_FORMAT} {sys.version} {capstone.__version__}".encode())
    if modules is None:
        modules = _read_modules()
    h.update(b"modules.toml\0" + hashlib.sha256(modules).digest())
    h.update(b"exe\0")
    try:
        with open(exe or ORIGINAL_EXE, "rb") as fh:
            h.update(hashlib.sha256(fh.read()).digest())
    except OSError:
        h.update(b"<missing>")
    for f in _CACHE_INPUTS:
        h.update(b"wc1/" + f.encode() + b"\0" + _SOURCE_DIGESTS[f])
    return h.hexdigest()[:32]


def run(exe=None, cache=None):
    """Discovery + partition of war.exe.  The result is cached in
    build/cache/ keyed on every input (_cache_key); each call returns a fresh
    object either way.  cache=False or WC1_ANALYSIS_CACHE=0 disables it."""
    if cache is None:
        cache = os.environ.get("WC1_ANALYSIS_CACHE", "1") != "0"
    if not cache:
        return Program(exe).discover().partition()
    from . import path
    modules = _read_modules()
    f = path("build", "cache", f"analysis-{_cache_key(exe, modules)}.pickle")
    try:
        with open(f, "rb") as fh:
            return pickle.load(fh)
    except (OSError, EOFError, pickle.UnpicklingError, AttributeError, ImportError):
        pass
    p = Program(exe, modules).discover().partition()
    os.makedirs(os.path.dirname(f), exist_ok=True)
    tmp = f"{f}.{os.getpid()}.tmp"
    with open(tmp, "wb") as fh:
        pickle.dump(p, fh, protocol=pickle.HIGHEST_PROTOCOL)
    os.replace(tmp, f)                  # atomic: parallel runs never see half a file
    return p


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
