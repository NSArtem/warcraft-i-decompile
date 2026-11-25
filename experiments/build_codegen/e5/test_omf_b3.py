"""OMF THREAD expansion unit controls; no compiler or original data needed."""
import struct
import pytest
from . import omf_b3 as b3

@pytest.mark.parametrize('slot', range(4))
@pytest.mark.parametrize('frame', [(0,1),(1,2),(2,3),(4,None),(5,None)])
@pytest.mark.parametrize('target', range(3))
def test_all_thread_slots_and_methods(slot, frame, target):
    fm, fi = frame
    reader = b3.Threads()
    definitions = bytes([0x40 | fm << 2 | slot]) + (b3.index(fi) if fi else b'')
    definitions += bytes([target << 2 | slot]) + b3.index(130)
    assert reader.parse(definitions) == []
    for self_rel in (False,True):
        for disp in (None, 0, 0x12345678):
            expected = b3.Fix(1020,9,self_rel,fm,fi,target,130,disp)
            locat = expected.encode()[:2]
            fd = 0x80 | slot << 4 | 8 | slot | (4 if disp is None else 0)
            raw = locat+bytes([fd])+(struct.pack('<I',disp) if disp is not None else b'')
            # State survives arbitrary record boundaries and explicit expansion.
            assert reader.parse(raw) == [expected]
            assert b3.Threads().parse(expected.encode()) == [expected]


def test_undefined_and_truncated_threads_fail_closed():
    for body in (bytes.fromhex('e4008c'), bytes([0x00]), bytes([0x60]), bytes.fromhex('e4005201')):
        with pytest.raises(b3.Rejected):
            b3.Threads().parse(body)


