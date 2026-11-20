import os
import random

import pytest

from wc1 import path, t4spec
from wc1.emu import Emu
from wc1.t4spec import T4Case

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = path('src/mod_3abb0', 'grp_frame_info_reference.c')
GRP_SIZE = 4096
_B = {}


def init_emu(emu):
    _B['grp'] = emu.alloc(GRP_SIZE, 16)
    _B['out'] = emu.alloc(16, 16)
    _B['sh'] = emu.alloc(32, 16)


def _addrs():
    init_emu(Emu())
    return _B['grp'], _B['out'], _B['sh']


def _case(frame, data, label):
    grp, out, sh = _addrs()
    return T4Case(
        args=(grp, frame, out, sh),
        stack_args=(sh + 4, sh + 8, sh + 12),
        mem={grp: data, out: b"\xaa" * 16, sh: b"\x55" * 32},
        label=label,
    )


def _data(seed):
    rng = random.Random(seed)
    return bytes(rng.randrange(256) for _ in range(GRP_SIZE))


def test_t3_files_match():
    t4spec.assert_t3_matches(path('src/mod_3abb0'), [])


def test_ref_mismatch():
    t4spec.assert_ref_mismatch(path('src/mod_3abb0'), ['grp_frame_info_reference.c'])


def test_grp_frame_info():
    grp, out, sh = _addrs()
    cases = []
    for i, f in enumerate((0, 1, 2, 127, 255, 0x100, 0x1ff, 0xffffff03)):
        cases.append(_case(f, _data(i + 1), "frame=%#x" % f))
    t4spec.run_spec(
        SRC, 'GrpFrameInfo_', 0x3abb0, cases,
        watch=[(out, 16), (sh, 32)],
        out_regs=(),
        init_emu=init_emu,
    )
