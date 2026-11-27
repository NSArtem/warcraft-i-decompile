import os
import struct

import pytest

from wc1 import t4spec
from wc1 import path

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC_DIR = path('src/mod_13e60')
DEMO_MODE = 0x5152c
IDLE_TIMER = 0x51530
STEP_INDEX = 0x51532
STEPS = 0x51534

STUB_A = 0x13e60
STUB_B = 0x13ea0
STUB_C = 0x13ef8


def _addr(name):
    by = t4spec.by_link_lenient()
    for k in ('_' + name, name):
        if k in by:
            return by[k]['addr']
    raise KeyError(name)


def _table(entries):
    return b''.join(struct.pack('<IH', fn, sc) for fn, sc in entries)


def test_t3_files_match():
    t4spec.assert_t3_matches(SRC_DIR, ['demo_idle_tick.c', 'demo_step_main_menu.c', 'demo_idle_timer_reset.c'])


def test_ref_files_still_mismatch():
    t4spec.assert_ref_mismatch(SRC_DIR, ['demo_run_reference.c', 'demo_step_start_scenario_reference.c'])


def test_demo_step_start_scenario():
    names = ['game_mode', 'scenario_number', 'custom_game', 'own_campaign',
             'net_play_flag', 'screen_mode']
    addrs = [_addr(n) for n in names]
    watch = [(a, 2) for a in addrs]
    tbl = _table([(STUB_A, 0x0101), (STUB_B, 0x0202), (0, 0)])
    junk = struct.pack('<H', 0x5a5a)
    cases = []
    for i in range(3):
        mem = {STEPS: tbl, STEP_INDEX: struct.pack('<H', i)}
        for a in addrs:
            mem[a] = junk
        cases.append(t4spec.T4Case(mem=mem, label='idx%d' % i))
    t4spec.run_spec(os.path.join(SRC_DIR, 'demo_step_start_scenario_reference.c'),
                    'DemoStepStartScenario_', 0x13ea0, cases,
                    watch=watch)


def test_demo_run():
    watch = [(DEMO_MODE, 2), (IDLE_TIMER, 2), (STEP_INDEX, 2)]
    tbl = _table([(STUB_A, 0), (STUB_B, 0), (STUB_C, 0), (0, 0)])
    for ret_a, ret_b, ret_c in ((0, 1, 1), (0, 0, 5), (0x10000, 0, 1), (1, 1, 1)):
        stubs = [t4spec.T4Stub(STUB_A, ret=ret_a, log_regs=()),
                 t4spec.T4Stub(STUB_B, ret=ret_b, log_regs=()),
                 t4spec.T4Stub(STUB_C, ret=ret_c, log_regs=())]
        cases = []
        for i in range(4):
            mem = {STEPS: tbl, STEP_INDEX: struct.pack('<H', i),
                   DEMO_MODE: b'\x00\x00', IDLE_TIMER: b'\x77\x77'}
            cases.append(t4spec.T4Case(mem=mem, label='idx%d_%d%d%d' % (i, ret_a != 0, ret_b != 0, ret_c != 0)))
        t4spec.run_spec(os.path.join(SRC_DIR, 'demo_run_reference.c'),
                        'DemoRun_', 0x13f0c, cases,
                        watch=watch, stubs=stubs, out_regs=(),
                        extra={'_demo_idle_timer': {'addr': IDLE_TIMER}})
