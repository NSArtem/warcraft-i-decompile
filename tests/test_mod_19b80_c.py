import os
import struct

import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case, T4Stub

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = path('src/mod_19b80', 'game_screen_input_init_reference.c')


def test_t3_files_match():
    t4spec.assert_t3_matches(path('src/mod_19b80'), ['net_pump_events.c'])


def test_reference_still_mismatches():
    t4spec.assert_ref_mismatch(path('src/mod_19b80'), ['game_screen_input_init_reference.c'])


def test_game_screen_input_init():
    by = t4spec.by_link_lenient()
    watch = []
    state = {}

    def init_emu(emu):
        state['buf'] = emu.alloc(64, 16)

    def mk(flag):
        def setup(emu):
            pass
        return setup

    cases = [T4Case(label="default")]
    t4spec.run_spec(
        SRC, 'GameScreenInputInit_', 0x1a328, cases,
        watch=watch,
        stubs=[T4Stub(by['UiInputInit_']['addr'], log_regs=())] if 'UiInputInit_' in by else [],
        out_regs=(),
        init_emu=init_emu,
    )
