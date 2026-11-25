"""Decoded instructions as plain records (the instruction part of the analysis cache).

Decoding the whole program through capstone's Python binding costs over a second
of ctypes work.  The result depends on the executable alone, so the analysis cache
(wc1.analysis.run) keeps it: pack() turns {address: CsInsn} into a compact state,
Insns is the mapping a loaded Program exposes.  Its values offer what CsInsn
offers; the attributes the tools use are stored, everything else is taken from
a real CsInsn, decoded on demand.
"""
import hashlib
import pickle
from array import array
from collections import namedtuple
from collections.abc import Mapping
from itertools import batched, islice
from operator import add

from . import loaded

OpMem = namedtuple("OpMem", "segment base index scale disp")


class Operand(namedtuple("Operand", "type size access avx_bcast avx_zero_opmask reg imm mem")):
    """capstone.x86.X86Op: reg/imm/mem are the views of its union, whatever `type` is."""
    __slots__ = ()

    @property
    def value(self):
        return self


_REG_NAMES = {}         # capstone register id -> name


class _Fields:
    """The stored fields of an Insn, writable while they are filled in."""
    __slots__ = ("_prog", "address", "size", "mnemonic", "op_str", "disp_offset", "disp_size",
                 "imm_offset", "imm_size", "operands")

    def __init__(self, prog, address, shape):
        self._prog = prog
        self.address = address
        (self.size, self.mnemonic, self.op_str, self.disp_offset, self.disp_size,
         self.imm_offset, self.imm_size, self.operands) = shape
        self.__class__ = Insn


class Insn(_Fields):
    """One instruction, with the interface of capstone.CsInsn; read-only."""
    __slots__ = ()

    def __setattr__(self, name, value):
        raise AttributeError(f"instructions are read-only: {name}")

    def __delattr__(self, name):
        raise AttributeError(f"instructions are read-only: {name}")

    def __reduce__(self):               # copy and pickle cannot set the fields one by one
        return _Fields, (self._prog, self.address, tuple([getattr(self, n) for n in _Fields.__slots__[2:]]))

    @property
    def bytes(self):
        off = self.address - self._prog.code.base
        return bytearray(self._prog.cbytes[off:off + self.size])

    def reg_name(self, reg_id, default=None):
        if type(reg_id) is not int:     # whatever else capstone (ctypes) takes
            return self._prog.md.reg_name(reg_id, default)
        name = _REG_NAMES.get(reg_id)
        if name is None:
            name = self._prog.md.reg_name(reg_id)
            if name is None:
                return default
            _REG_NAMES[reg_id] = name
        return name

    def __getattr__(self, name):        # only for what is not stored
        if name.startswith("__") or name in _Fields.__slots__:
            raise AttributeError(name)
        return getattr(self._prog.insn_at(self.address), name)

    def __repr__(self):
        return f"<Insn {self.address:#x} [{self.bytes.hex()}]: {self.mnemonic} {self.op_str}>"


def _operand(o):
    m = o.mem
    return (o.type, o.size, o.access, o.avx_bcast, o.avx_zero_opmask, o.reg, o.imm,
            m.segment, m.base, m.index, m.scale, m.disp)


SHAPE, OPERAND = 6, 12                  # numbers stored of one
MAX_SIZE = 15                           # of an x86 instruction


def pack(insns):
    """Picklable state of an address -> instruction mapping, in its order.  A shape
    is everything stored of an instruction except its address; shapes and operands
    are shared between the instructions.  Their tables are flat (numbers, text, refs,
    operands), so that validate() can check all of them without building any object:
    numbers    per shape: size, disp_offset, disp_size, imm_offset, imm_size, count of operands
    text       per shape: mnemonic, op_str; a line each
    refs       the operands of the shapes, one after the other
    operands   per operand: _operand()"""
    if isinstance(insns, Insns):
        return insns.state
    shapes, operands = {}, {}
    which = array("I")
    for i in insns.values():
        ops = tuple(operands.setdefault(_operand(o), len(operands)) for o in i.operands)
        shape = (i.size, i.disp_offset, i.disp_size, i.imm_offset, i.imm_size, len(ops)), i.mnemonic, i.op_str, ops
        which.append(shapes.setdefault(shape, len(shapes)))
    state = (array("I", insns), which, bytes([n for s in shapes for n in s[0]]),
             "\n".join([t for s in shapes for t in s[1:3]]), array("I", [k for s in shapes for k in s[3]]),
             array("q", [n for o in operands for n in o]))
    return *state, _digest(*state)


def _digest(*state):
    state = [x.encode(errors="surrogatepass") if type(x) is str else x for x in state]
    h = hashlib.sha256(" ".join([str(len(x)) for x in state]).encode())
    for part in state:
        h.update(part)
    return h.digest()


def _check(ok, what):
    if not ok:
        raise pickle.UnpicklingError(f"instructions: {what}")


def validate(state, base, end):
    """Raise UnpicklingError unless `state` has the form of what pack() returns for code
    at base..end.  Covers everything a later lookup relies on: every table, index and
    range is checked here, against the tables themselves."""
    _check(type(state) is tuple and [type(x) for x in state] == [array, array, bytes, str, array, array, bytes]
           and [x.typecode for x in state if type(x) is array] == ["I", "I", "I", "q"], "not a packed state")
    addrs, which, numbers, text, refs, operands, digest = state
    _check(digest == _digest(*state[:-1]), "checksum mismatch")
    _check(len(addrs) == len(which) > 0, "address and shape arrays do not match")
    count, rest = divmod(len(numbers), SHAPE)
    _check(rest == 0 and text.count("\n") == 2 * count - 1, "malformed shapes")
    _check(max(which) < count, "shape index out of range")
    _check(sum(numbers[5::SHAPE]) == len(refs), "malformed operand lists")
    _check(len(operands) % OPERAND == 0 and set(operands[4::OPERAND]) <= {0, 1}, "malformed operands")
    _check(max(refs, default=-1) < len(operands) // OPERAND, "operand index out of range")
    for size, disp, disp_size, imm, imm_size in set(zip(*[numbers[k::SHAPE] for k in range(5)])):
        _check(0 < size <= MAX_SIZE and disp + disp_size <= size and imm + imm_size <= size, "malformed sizes")
    _check(base <= min(addrs), "address outside the code")
    if max(addrs) > end - MAX_SIZE:     # else no instruction can reach the end
        _check(max(map(add, addrs, map(numbers[::SHAPE].__getitem__, which))) <= end, "address outside the code")


class Insns(Mapping):
    """Read-only address -> Insn mapping over a pack() state (which is validated here),
    built on first access."""

    def __init__(self, prog, state):
        validate(state, prog.code.base, prog.code.base + len(prog.cbytes))
        self.state = state
        addrs, which = state[:2]
        self._prog, self._addrs, self._which, self._memo = prog, addrs, which, {}
        self._index = dict(zip(addrs, range(len(addrs)), strict=True))
        _check(len(self._index) == len(addrs), "repeated address")
        self._shapes = None

    def _load(self):
        numbers, text, refs, flat = self.state[2:6]
        operands = [Operand(*o[:4], bool(o[4]), *o[5:7], OpMem(*o[7:])) for o in batched(flat, OPERAND, strict=True)]
        refs, text = iter(refs), iter(text.split("\n"))
        self._shapes = [(size, next(text), next(text), *fields, tuple([operands[k] for k in islice(refs, n)]))
                        for size, *fields, n in batched(numbers, SHAPE, strict=True)]

    def __getitem__(self, a):
        i = self._memo.get(a)
        if i is None:
            k = self._index[a]
            if self._shapes is None:
                self._load()
            a = self._addrs[k]          # an int, whatever equal number was asked for
            i = self._memo[a] = _Fields(self._prog, a, self._shapes[self._which[k]])
        return i

    def __contains__(self, a):
        return a in self._index

    def __iter__(self):
        return iter(self._index)

    def __len__(self):
        return len(self._index)


loaded.seal("_REG_NAMES")
