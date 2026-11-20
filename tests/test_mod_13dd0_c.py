import os

import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case, T4Stub

pytestmark = pytest.mark.skipif(
    not (os.path.exists(path('original', 'install', 'war.exe')) and os.environ.get('WATCOM')),
    reason='needs original/ and $WATCOM')

SRC = path('src/mod_13dd0', 'set_cursor_shape_reference.c')
CUR_ADDR = 0x58F10
DESC_BASE = 0x58E50


def test_ref_mismatch_guard():
    t4spec.assert_ref_mismatch(path('src/mod_13dd0'), ['set_cursor_shape_reference.c'])


def test_set_cursor_shape():
    by_link = t4spec.by_link_lenient()
    img_addr = by_link['CursorSetImage_']['addr']
    cases = []
    for cur, new in ((0, 0), (0, 1), (1, 1), (3, 7), (0xFF, 0), (5, 5), (2, 0x20)):
        cases.append(T4Case(args=(new,), mem={CUR_ADDR: bytes([cur])},
                            label=f"cur={cur} new={new}"))
    t4spec.run_spec(
        SRC, 'SetCursorShape_', 0x13DD0, cases,
        watch=[(CUR_ADDR, 1)],
        stubs=[T4Stub(img_addr, log_regs=("eax",))],
        out_regs=())
