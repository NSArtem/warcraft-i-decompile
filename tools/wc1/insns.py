"""Decoded instructions as plain records (the instruction part of the analysis cache).

Decoding the whole program through capstone's Python binding costs over a second
of ctypes work.  The result depends on the executable alone, so the analysis cache
(wc1.analysis.run) keeps it: pack() turns {address: CsInsn} into a compact state,
Insns is the mapping a loaded Program exposes.  Its values offer what CsInsn
offers; the attributes the tools use are stored, everything else is taken from
a real CsInsn, decoded on demand.
"""
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


class Insn:
    """One instruction, with the interface of capstone.CsInsn."""
    __slots__ = ("_prog", "address", "size", "mnemonic", "op_str", "disp_offset", "disp_size",
                 "imm_offset", "imm_size", "operands")

    def __init__(self, prog, address, shape):
        self._prog = prog
        self.address = address
        (self.size, self.mnemonic, self.op_str, self.disp_offset, self.disp_size,
         self.imm_offset, self.imm_size, self.operands) = shape

    @property
    def bytes(self):
        off = self.address - self._prog.code.base
        return bytearray(self._prog.cbytes[off:off + self.size])

    def reg_name(self, reg_id, default=None):
        name = _REG_NAMES.get(reg_id)
        if name is None:
            name = self._prog.md.reg_name(reg_id)
            if name is None:
                return default
            _REG_NAMES[reg_id] = name
        return name

    def __getattr__(self, name):        # only for what is not stored
        if name.startswith("__") or name in Insn.__slots__:
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
    return array("I", insns), which, pickle.dumps((list(shapes), list(operands)),
                                                  protocol=pickle.HIGHEST_PROTOCOL)


class Insns(Mapping):
    """Read-only address -> Insn mapping over a pack() state, built on first access."""

    def __init__(self, prog, state):
        self.state = state
        addrs, which, _ = state
        self._prog, self._which, self._memo = prog, dict(zip(addrs, which)), {}
        self._shapes = None

    def _load(self):
        shapes, operands = pickle.loads(self.state[2])
        operands = [Operand(*o[:-1], OpMem(*o[-1])) for o in operands]
        self._shapes = [(*s[:-1], tuple([operands[k] for k in s[-1]])) for s in shapes]

    def __getitem__(self, a):
        i = self._memo.get(a)
        if i is None:
            k = self._which[a]
            if self._shapes is None:
                self._load()
            i = self._memo[a] = Insn(self._prog, a, self._shapes[k])
        return i

    def __contains__(self, a):
        return a in self._which

    def __iter__(self):
        return iter(self._which)

    def __len__(self):
        return len(self._which)
