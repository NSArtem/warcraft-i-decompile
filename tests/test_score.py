import functools
import os
import struct

import pytest

from wc1 import path, t4spec

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original', 'install', 'war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

_BUF = {}
PAGE_FNS = [0x25428, 0x2553c, 0x25600, 0x253cc]


@functools.cache
def A(*names):
    bl = t4spec.by_link_lenient()
    for n in names:
        for k in (n, '_' + n, n + '_'):
            if k in bl:
                return bl[k]['addr']
    raise KeyError(names)


def init_emu(emu):
    _BUF['flag'] = emu.alloc(16, 16)


def _w(v):
    return struct.pack('<H', v & 0xFFFF)


def test_t3_files_match():
    t4spec.assert_t3_matches(path('src/score'), ['score_page_harvest.c', 'score_page_men.c', 'score_page_score.c',
                                              'score_init_reference.c', 'score_update_reference.c'])


def _upd_case(page, shown, ret):
    def setup(emu):
        emu.write(A('score_page'), _w(page))
        emu.write(A('score_page_shown'), _w(shown))
        emu.write(A('score_page_fns'), b''.join(struct.pack('<I', a) for a in PAGE_FNS))
        emu.write(A('score_panel_rect'), struct.pack('<III', 11, 22, 33))
        emu.write(A('dirty_x1'), struct.pack('<III', 1, 2, 3))
        emu.write(0x5abb0, _w(0x7777))
        emu.write(0x5abc2, _w(0x6666))
        emu.write(_BUF['flag'], bytes([ret]))
    return setup


def test_score_update():
    def page_fn(e, log):
        log(e.reg('eax'))
        return e.read(_BUF['flag'], 1)[0]

    cases = []
    for page in range(4):
        for shown in (page, (page + 1) & 3):
            for ret in (0, 1):
                cases.append(t4spec.T4Case(setup=_upd_case(page, shown, ret),
                                           label='p%d s%d r%d' % (page, shown, ret)))
    stubs = [t4spec.T4Stub(a, fn=page_fn) for a in sorted(set(PAGE_FNS))]
    stubs.append(t4spec.T4Stub(A('ScreenUpdate'), log_regs=()))
    t4spec.run_spec(
        path('src', 'score', 'score_update_reference.c'), 'ScoreUpdate_', 0x25684,
        cases, out_regs=(), init_emu=init_emu, stubs=stubs,
        watch=[(A('score_page_shown'), 2), (A('dirty_x1'), 12),
               (A('score_panel_rect'), 12), (0x5abb0, 2), (0x5abc2, 2)])


def _init_case(num, race):
    def setup(emu):
        emu.write(A('scenario_number'), _w(num))
        emu.write(A('scenario_race'), _w(race))
        emu.write(A('score_cap_tbl'), b''.join(_w(0x100 + i * 3) for i in range(12)))
        emu.write(A('score_rate_tbl'), b''.join(_w(0x200 + i * 5) for i in range(12)))
        emu.write(A('score_page'), _w(5))
        emu.write(A('score_page_shown'), _w(6))
        emu.write(0x5abb0, _w(0x7777))
    return setup


def test_score_init():
    cases = []
    for num in (0, 0x70, 0x76, 0x77, 0x78, 0x79, 0x80, 0x8c, 0x8d, 0x8e, 0x90, 0xff, 0x1000):
        for race in (0, 1):
            cases.append(t4spec.T4Case(setup=_init_case(num, race), label='n%x r%d' % (num, race)))
    stubs = [
        t4spec.T4Stub(0x1eba0, log_regs=()),
        t4spec.T4Stub(A('LayerAdd'), log_regs=('eax', 'edx', 'ebx', 'ecx'), stack_pop=4),
        t4spec.T4Stub(A('BitmapCloneAlloc'), log_regs=('eax', 'edx')),
    ]
    t4spec.run_spec(
        path('src', 'score', 'score_init_reference.c'), 'ScoreInit_', 0x25718,
        cases, out_regs=(), init_emu=init_emu, stubs=stubs,
        watch=[(A('score_page'), 2), (A('score_page_shown'), 2),
               (A('score_pool'), 2), (A('score_cap'), 2), (A('score_rate'), 2),
               (0x5abb0, 2)])
