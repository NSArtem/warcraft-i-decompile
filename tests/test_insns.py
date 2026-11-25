"""wc1.insns: the instruction records of the analysis cache.  That they equal
capstone's instructions, and what the emitter makes of them, is checked on the
whole program by test_analysis_cache.test_cached_run_equals_fresh_run."""
import copy
import os
import pickle

import pytest
from capstone import CsInsn

from wc1 import analysis, insns, path

pytestmark = pytest.mark.skipif(not os.path.exists(path("original", "install", "war.exe")),
                                reason="needs original/")


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


def test_shared_records_cannot_be_changed(prog):
    i = next(i for i in prog.insns.values() if any(o.type == 3 for o in i.operands))
    o = next(o for o in i.operands if o.type == 3)
    for target, name in ((o, "imm"), (o, "value"), (o.mem, "disp")):
        with pytest.raises(AttributeError):
            setattr(target, name, 1)
    with pytest.raises(TypeError):
        i.operands[0] = None
