"""wc1.insns: the instruction records of the analysis cache.  That they equal
capstone's instructions, and what the emitter makes of them, is checked on the
whole program by test_analysis_cache.test_cached_run_equals_fresh_run."""
from array import array
import copy
import ctypes
from fractions import Fraction
import os
import pickle
import types

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


def _state(prog, **changes):
    """prog's packed state with some parts replaced and a digest that fits them."""
    parts = dict(zip(PARTS, prog.insns.state)) | changes
    try:
        return *parts.values(), insns._digest(*parts.values())
    except TypeError:
        return *parts.values(), b""


PARTS = ("addrs", "which", "numbers", "text", "refs", "operands")


def _end(prog):
    return prog.code.base + len(prog.cbytes)


def _validate(prog, state):
    return insns.validate(state, prog.code.base, _end(prog))


def test_packed_state_round_trip(prog):
    s = _state(prog)
    assert s == prog.insns.state and _validate(prog, s) is None
    fresh = {a: prog.insn_at(a) for a in list(prog.insns)[::500]}
    q = insns.Insns(prog, insns.pack(fresh))
    assert list(q) == list(fresh)
    assert all((q[a].mnemonic, q[a].op_str) == (i.mnemonic, i.op_str) for a, i in fresh.items())


def _put(table, at, value):
    table = bytearray(table) if type(table) is bytes else array(table.typecode, table)
    table[at] = value
    return bytes(table) if type(table) is bytearray else table


S, O = insns.SHAPE, insns.OPERAND
LAST = 64                               # the address of which instruction is changed
MALFORMED = [
    ("match", lambda p: {"addrs": p.addrs[:-1]}),
    ("match", lambda p: {"which": p.which[:-1]}),
    ("match", lambda p: {"which": p.which + p.which[:1]}),
    ("match", lambda p: {"addrs": p.addrs + p.addrs[:1]}),
    ("match", lambda p: {"addrs": array("I"), "which": array("I")}),
    ("repeated address", lambda p: {"addrs": p.addrs[:-1] + p.addrs[:1]}),
    # types
    *(("not a packed", lambda p, part=part, t=t: {part: t(getattr(p, part))}) for part, t in [
        ("addrs", lambda x: array("Q", x)), ("addrs", list), ("addrs", memoryview), ("which", lambda x: array("i", x)),
        ("which", bytes), ("numbers", bytearray), ("numbers", list), ("text", str.encode), ("text", str.split),
        ("refs", lambda x: array("Q", x)), ("refs", list), ("operands", lambda x: array("d", x)), ("operands", list)]),
    *(("not a packed", lambda p, part=part: {part: None}) for part in PARTS),
    # shapes: the tables themselves are counted
    ("shape index", lambda p: {"which": _put(p.which, -1, len(p.numbers) // S)}),
    ("shape index", lambda p: {"which": _put(p.which, 0, 0xFFFFFFFF)}),
    ("shape index", lambda p: {"numbers": p.numbers[:-S], "text": p.text.rsplit("\n", 2)[0]}),
    ("malformed shapes", lambda p: {"numbers": b"", "text": ""}),
    ("malformed shapes", lambda p: {"numbers": p.numbers[:-S]}),
    ("malformed shapes", lambda p: {"numbers": p.numbers[:-1]}),
    ("malformed shapes", lambda p: {"text": ""}),
    ("malformed shapes", lambda p: {"text": p.text[:p.text.rindex("\n")]}),
    ("malformed shapes", lambda p: {"text": p.text + "\n"}),
    ("malformed sizes", lambda p: {"numbers": _put(p.numbers, 0, 0)}),              # size
    ("malformed sizes", lambda p: {"numbers": _put(p.numbers, 0, 16)}),
    ("malformed sizes", lambda p: {"numbers": _put(p.numbers, 1, 250)}),            # disp_offset
    ("malformed sizes", lambda p: {"numbers": _put(p.numbers, 2, 250)}),
    ("malformed sizes", lambda p: {"numbers": _put(p.numbers, 3, 250)}),            # imm_offset
    ("malformed sizes", lambda p: {"numbers": _put(p.numbers, 4, 250)}),
    # operands
    ("operand lists", lambda p: {"numbers": _put(p.numbers, 5, p.numbers[5] + 1)}),
    ("operand lists", lambda p: {"refs": p.refs[:-1]}),
    ("operand lists", lambda p: {"refs": p.refs + p.refs[:1]}),
    ("operand index", lambda p: {"refs": _put(p.refs, -1, len(p.operands) // O)}),
    ("operand index", lambda p: {"refs": _put(p.refs, 0, 0xFFFFFFFF)}),
    ("operand index", lambda p: {"operands": p.operands[:-O]}),
    ("operand index", lambda p: {"operands": p.operands[:0]}),
    ("malformed operands", lambda p: {"operands": p.operands[:-1]}),
    ("malformed operands", lambda p: {"operands": _put(p.operands, 4, 2)}),         # a bool
    # addresses
    ("outside the code", lambda p: {"addrs": _put(p.addrs, LAST, p.base - 1)}),
    ("outside the code", lambda p: {"addrs": _put(p.addrs, LAST, p.end)}),
    ("outside the code", lambda p: {"addrs": _put(p.addrs, LAST, 0xFFFFFFFF)}),
    ("outside the code", lambda p: {"addrs": _put(p.addrs, LAST, p.end - p.numbers[p.which[LAST] * S] + 1)}),
]


@pytest.mark.parametrize("what, damage", MALFORMED)
def test_malformed_states_are_rejected(prog, what, damage):
    """Also when their digest fits."""
    parts = types.SimpleNamespace(**dict(zip(PARTS, prog.insns.state)), base=prog.code.base, end=_end(prog))
    s = _state(prog, **damage(parts))
    with pytest.raises(pickle.UnpicklingError, match=what):
        insns.Insns(prog, s)


def test_an_instruction_may_end_where_the_code_ends(prog):
    addrs, which, numbers = prog.insns.state[:3]
    a = _end(prog) - numbers[which[LAST] * S]
    assert a not in prog.insns
    q = insns.Insns(prog, _state(prog, addrs=_put(addrs, LAST, a)))
    assert q[a].address + q[a].size == _end(prog) and len(q[a].bytes) == q[a].size


@pytest.mark.parametrize("part", range(7))
def test_any_damaged_part_is_rejected(prog, part):
    s = list(prog.insns.state)
    if type(s[part]) is str:
        s[part] = s[part].replace("mov", "nov", 1)
    else:
        raw = bytearray(bytes(s[part]))
        raw[len(raw) // 2] ^= 1
        s[part] = array(s[part].typecode, bytes(raw)) if type(s[part]) is array else bytes(raw)
    with pytest.raises(pickle.UnpicklingError, match="checksum"):
        _validate(prog, tuple(s))
    for bad in (None, (), prog.insns.state[:4], prog.insns.state + (1,), list(prog.insns.state)):
        with pytest.raises(pickle.UnpicklingError):
            _validate(prog, bad)


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
