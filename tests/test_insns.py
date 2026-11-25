"""wc1.insns: the instruction records of the analysis cache.  That they equal
capstone's instructions, and what the emitter makes of them, is checked on the
whole program by test_analysis_cache.test_cached_run_equals_fresh_run."""
import copy
import ctypes
from fractions import Fraction
import os
import pickle

import pytest
from capstone import CsInsn, x86

from wc1 import analysis, insns, path

pytestmark = pytest.mark.skipif(not os.path.exists(path("original", "install", "war.exe")),
                                reason="needs original/")


class _Equal(int):
    pass


class _Index:
    def __init__(self, n):
        self.n = n

    def __index__(self):
        return self.n


@pytest.fixture(scope="module")
def prog():
    p = pickle.loads(pickle.dumps(analysis.run()))
    assert isinstance(p.insns, insns.Insns)
    return p


def test_mapping_interface(prog):
    m, entry = prog.insns, prog.le.entry
    assert entry in m and m[entry] is m[entry] and m.get(entry) is m[entry]
    inside = next(a for a, o in prog.owner.items() if a != o)
    for a in (inside, 0, -1, None):
        assert a not in m and m.get(a) is None and m.get(a, 5) == 5
        with pytest.raises(KeyError):
            m[a]
    assert len(m) == len(list(m)) == len(set(m)) and list(m.keys()) == list(m)
    assert all(i.address == a for a, i in list(m.items())[::997])
    with pytest.raises(TypeError):
        m[0] = None


def test_tables_are_built_on_first_use():
    p = analysis.run()
    p = pickle.loads(pickle.dumps(p))
    assert p.le.entry in p.insns and len(p.insns) == len(list(p.insns)) > 60000
    assert p.insns._shapes is None and not p.insns._memo
    p.insns[p.le.entry]
    assert p.insns._shapes is not None and len(p.insns._memo) == 1


def test_a_loaded_program_can_be_stored_and_copied_again(prog):
    entry = prog.le.entry
    for p in (pickle.loads(pickle.dumps(prog)), copy.deepcopy(prog)):
        assert p.insns is not prog.insns and list(p.insns) == list(prog.insns)
        assert p.insns[entry]._prog is p and p.insns[entry] is not prog.insns[entry]
        assert repr(p.insns[entry]) == repr(prog.insns[entry])
    i = copy.copy(prog.insns[entry])
    assert (i.address, i.mnemonic, i.bytes) == (entry, prog.insns[entry].mnemonic, prog.insns[entry].bytes)


def test_everything_else_comes_from_a_real_instruction(prog):
    sample = list(prog.insns)[::1500]
    for a in sample:
        real, i = prog.insn_at(a), prog.insns[a]
        assert isinstance(real, CsInsn) and not isinstance(i, CsInsn)
        for name in ("id", "prefix", "opcode", "rex", "addr_size", "modrm", "sib", "disp", "sib_index",
                     "sib_scale", "sib_base", "eflags", "modrm_offset", "regs_read", "regs_write",
                     "groups"):
            assert getattr(i, name) == getattr(real, name), (hex(a), name)
        assert i.regs_access() == real.regs_access() and i.insn_name() == real.insn_name()
        assert [i.op_count(t) for t in (1, 2, 3)] == [real.op_count(t) for t in (1, 2, 3)]
        assert [i.group(g) for g in range(1, 8)] == [real.group(g) for g in range(1, 8)]


def test_unknown_attributes_are_errors(prog):
    i = prog.insns[prog.le.entry]
    with pytest.raises(Exception) as ours:
        i.no_such_attribute
    with pytest.raises(Exception) as real:
        prog.insn_at(prog.le.entry).no_such_attribute
    assert type(ours.value) is type(real.value)
    with pytest.raises(AttributeError):
        i.__no_such_protocol__
    with pytest.raises(AttributeError):
        i.no_such_attribute = 1


def test_bytes_are_the_image_and_never_shared(prog):
    i = prog.insns[prog.le.entry]
    off = i.address - prog.code.base
    b = i.bytes
    assert isinstance(b, bytearray) and b == prog.cbytes[off:off + i.size]
    b[:] = b"\xcc" * len(b)
    assert i.bytes == prog.cbytes[off:off + i.size]


@pytest.mark.parametrize("key", [float, Fraction, _Equal], ids=["float", "Fraction", "int subclass"])
def test_any_equal_key_gives_the_instruction_of_the_stored_address(prog, key):
    """As with the dict of a fresh discovery: the key of the first lookup is not kept."""
    p = pickle.loads(pickle.dumps(prog))
    entry = p.le.entry
    i = p.insns[key(entry)]
    assert type(i.address) is int and i.address == entry
    assert p.insns[entry] is i and p.insns.get(key(entry)) is i and key(entry) in p.insns
    assert i.bytes == prog.insns[entry].bytes and repr(i) == repr(prog.insns[entry])
    assert [type(a) for a in p.insns._memo] == [int]
    assert all(type(a) is int for a in p.insns)
    with pytest.raises(TypeError):
        p.insns[[entry]]


def test_fields_are_read_only(prog):
    i = prog.insns[prog.le.entry]
    fields = [n for n in insns._Fields.__slots__]
    before = [getattr(i, n) for n in fields]
    for n in fields + ["bytes", "reg_name", "id", "__class__"]:
        with pytest.raises(AttributeError):
            setattr(i, n, 1)
        with pytest.raises(AttributeError):
            delattr(i, n)
    assert [getattr(i, n) for n in fields] == before and type(i) is insns.Insn
    for c in (copy.copy(i), pickle.loads(pickle.dumps(i)), copy.deepcopy(i)):
        assert type(c) is insns.Insn and [getattr(c, n) for n in fields[1:]] == before[1:]
        assert c.bytes == i.bytes
        with pytest.raises(AttributeError):
            c.mnemonic = "nop"


def test_reg_name_takes_what_capstone_takes(prog):
    i, real = prog.insns[prog.le.entry], prog.insn_at(prog.le.entry)

    def outcome(insn, *a):
        try:
            return insn.reg_name(*a)
        except Exception as ex:
            return type(ex)
    for r in (x86.X86_REG_EAX, x86.X86_REG_ST0, 0, 9999, -1, (1 << 32) + x86.X86_REG_EAX):
        for a in (r, ctypes.c_uint(r), ctypes.c_int(r), ctypes.c_ushort(r), ctypes.c_ulonglong(r),
                  _Equal(r), _Index(r), float(r), Fraction(r), str(r), None, True):
            for rest in ((), ("default",)):
                assert outcome(i, a, *rest) == outcome(real, a, *rest), (a, rest)
    assert i.reg_name(ctypes.c_uint(x86.X86_REG_EAX)) == "eax"
    assert all(type(r) is int for r in insns._REG_NAMES)


def test_shared_records_cannot_be_changed(prog):
    i = next(i for i in prog.insns.values() if any(o.type == 3 for o in i.operands))
    o = next(o for o in i.operands if o.type == 3)
    for target, name in ((o, "imm"), (o, "value"), (o.mem, "disp")):
        with pytest.raises(AttributeError):
            setattr(target, name, 1)
    with pytest.raises(TypeError):
        i.operands[0] = None
