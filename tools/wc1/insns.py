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
            (m.segment, m.base, m.index, m.scale, m.disp))


def pack(insns):
    """Picklable state of an address -> instruction mapping, in its order.  A shape
    is everything stored of an instruction except its address; shapes and operands
    are shared between the instructions."""
    if isinstance(insns, Insns):
        return insns.state
    shapes, operands = {}, {}
    which = array("I")
    for i in insns.values():
        ops = tuple(operands.setdefault(_operand(o), len(operands)) for o in i.operands)
        shape = (i.size, i.mnemonic, i.op_str, i.disp_offset, i.disp_size, i.imm_offset, i.imm_size, ops)
        which.append(shapes.setdefault(shape, len(shapes)))
    # nested pickle: a Program whose instructions are never looked at does not
    # pay for building the tables
    state = (array("I", insns), which, len(shapes),
             pickle.dumps((list(shapes), list(operands)), protocol=pickle.HIGHEST_PROTOCOL))
    return *state, _digest(*state)


def _digest(addrs, which, count, payload):
    h = hashlib.sha256(f"{len(addrs)} {len(which)} {count} {len(payload)} ".encode())
    for part in (addrs, which, payload):
        h.update(part)
    return h.digest()


def validate(state):
    """Raise UnpicklingError unless `state` is what pack() returned.  Covers everything
    a later lookup relies on, the nested pickle included, without building the tables."""
    if type(state) is not tuple or [type(x) for x in state] != [array, array, int, bytes, bytes]:
        raise pickle.UnpicklingError("instructions: not a packed state")
    addrs, which, count, payload, digest = state
    if addrs.typecode != "I" or which.typecode != "I" or not len(addrs) == len(which) > 0:
        raise pickle.UnpicklingError("instructions: address and shape arrays do not match")
    if digest != _digest(addrs, which, count, payload):
        raise pickle.UnpicklingError("instructions: checksum mismatch")
    if max(which) >= count:
        raise pickle.UnpicklingError("instructions: shape index out of range")


class Insns(Mapping):
    """Read-only address -> Insn mapping over a pack() state (which is validated here),
    built on first access."""

    def __init__(self, prog, state):
        validate(state)
        self.state = state
        addrs, which = state[:2]
        self._prog, self._addrs, self._which, self._memo = prog, addrs, which, {}
        self._index = dict(zip(addrs, range(len(addrs)), strict=True))
        if len(self._index) != len(addrs):
            raise pickle.UnpicklingError("instructions: repeated address")
        self._shapes = None

    def _load(self):
        shapes, operands = pickle.loads(self.state[3])
        operands = [Operand(*o[:-1], OpMem(*o[-1])) for o in operands]
        self._shapes = [(*s[:-1], tuple([operands[k] for k in s[-1]])) for s in shapes]

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
