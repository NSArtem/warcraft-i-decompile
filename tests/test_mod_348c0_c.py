import os

import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case, T4Stub

pytestmark = pytest.mark.skipif(
    not (os.path.exists(path('original', 'install', 'war.exe')) and os.environ.get('WATCOM')),
    reason='needs original/ and $WATCOM',
)

SRC = path('src/mod_348c0', 'rect_outline_reference.c')
HLINE_ADDR = 0x3ac10
VLINE_ADDR = 0x32970


def test_ref_files_still_mismatch():
    t4spec.assert_ref_mismatch(path('src/mod_348c0'), ['rect_outline_reference.c'])


def test_rect_outline():
    cases = []
    vals = [
        (0, 0, 1, 1), (10, 20, 30, 40), (-5, -7, 8, 9),
        (319, 199, 0, 0), (100, 50, 200, 100), (-1, 3, 65535, 2),
    ]
    for x, y, w, h in vals:
        cases.append(T4Case(args=(x & 0xFFFF, y & 0xFFFF, w, h), label=f"{x},{y},{w},{h}"))

    def rand_gen(rng):
        return T4Case(args=(
            rng.randrange(0x10000), rng.randrange(0x10000),
            rng.randrange(0x10000), rng.randrange(0x10000),
        ))

    t4spec.run_spec(
        SRC, 'RectOutline_', 0x348c0, cases,
        stubs=[
            T4Stub(HLINE_ADDR, log_regs=("eax", "edx", "ebx")),
            T4Stub(VLINE_ADDR, log_regs=("eax", "edx", "ebx")),
        ],
        out_regs=(), rand_cases=24, rand_gen=rand_gen,
    )
