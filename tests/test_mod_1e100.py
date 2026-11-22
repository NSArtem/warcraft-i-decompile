import os
import struct

import pytest

from wc1 import path, t4spec


pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')


SRC = 'src/mod_1e100'
MODE = 0x59616
SLOT = 0x59610
PENDING = 0x599B0
CUSTOM = 0x50E4E
PREF_FAILED = 0x52588
COOKIE = 0x78AB9CDE


def test_t3_matches():
    t4spec.assert_t3_matches(path('src/mod_1e100'), ['init_new_campaign.c'])


def test_ref_mismatch():
    t4spec.assert_ref_mismatch(path('src/mod_1e100'), ['run_game_mode_loop_reference.c'])


def _word(value):
    return struct.pack('<H', value & 0xFFFF)


def _dword(value):
    return struct.pack('<I', value)


def _read_dword(emu, addr):
    return struct.unpack('<I', emu.read(addr, 4))[0]


def test_run_game_mode_loop():
    # A setup-menu stub injects each route once, then selects an exit mode
    # when the route returns to setup. Counters live in emulated memory so
    # each side of the differential comparison sees the same initial state.
    routes = [
        ('default-in-range', 2, {}),
        ('intro-after-preference-failure', -1, {'pref': 1}),
        ('new-campaign', 1, {}),
        ('pending-image-before-slot', 3, {'pending': True, 'slot': True}),
        ('slot-load-success', 3, {'slot': True, 'load_ok': True}),
        ('slot-load-failure', 3, {'slot': True}),
        ('packet-start', 3, {'custom': 1}),
        ('packet-first-tick-abort', 3, {'custom': 1, 'abort': 1}),
        ('packet-second-tick-abort', 3, {'custom': 1, 'abort': 2}),
        ('end-network', 6, {'net': 1}),
        ('end-setup-quit', 6, {'quit': 1}),
        ('end-mode-seven-keeps-scenario', 7, {}),
        ('end-next-scenario', 6, {'next': 13}),
        ('end-campaign-outro', 6, {'next': 0xFFFF}),
        ('end-custom-back-to-setup', 6, {'next': 0xFFFF, 'custom': 1}),
        ('demo', 9, {}),
    ]
    scratch = {}
    watch = []

    def init_emu(emu):
        scratch['state'] = emu.alloc(12, 4)
        scratch['slot'] = emu.alloc(16, 4)
        scratch['image'] = emu.alloc(16, 4)
        watch[:] = [
            (0x55824, 4), (0x62890, 4), (SLOT, 4),
            (0x59614, 4), (PENDING, 4), (0x50D82, 2),
            (0x5152C, 2), (0x516B0, 4), (scratch['state'], 12),
        ]

    def case_setup(idx):
        def setup(emu):
            emu.write(scratch['state'], struct.pack('<III', idx, 0, 0))
            # Poison the fields that startup must initialize.
            emu.write(SLOT, _dword(scratch['slot']))
            emu.write(PENDING, _dword(scratch['image']))
        return setup

    cases = [
        t4spec.T4Case(
            label=label,
            stack_args=(COOKIE, COOKIE),
            setup=case_setup(idx),
            mem={
                MODE: _word(-7), 0x59614: _word(0xBEEF),
                0x55824: _dword(0xDEADBEEF), 0x62890: _dword(0),
                PREF_FAILED: _word(cfg.get('pref', 0)),
                CUSTOM: _word(cfg.get('custom', 0)),
                0x52586: _word(cfg.get('net', 0)),
                0x5176A: _word(cfg.get('quit', 0)),
                0x500CE: _word(cfg.get('next', 23)),
                0x50D82: _word(0x1234), 0x5152C: _word(7),
                0x516B0: _word(1), 0x516B2: _word(2),
            },
        )
        for idx, (label, _, cfg) in enumerate(routes)
    ]

    def route(emu):
        return routes[_read_dword(emu, scratch['state'])]

    def setup_menu(emu, log):
        log()
        count_addr = scratch['state'] + 4
        count = _read_dword(emu, count_addr)
        emu.write(count_addr, _dword(count + 1))
        _, mode, cfg = route(emu)
        if count:
            emu.write(MODE, _word(-1))
        else:
            emu.write(PENDING, _dword(scratch['image'] if cfg.get('pending') else 0))
            emu.write(SLOT, _dword(scratch['slot'] if cfg.get('slot') else 0))
            emu.write(MODE, _word(mode))
        return 0

    def load_image(emu, log):
        log(emu.reg('eax'))
        return scratch['image'] if route(emu)[2].get('load_ok') else 0

    def packet_tick(emu, log):
        log()
        count_addr = scratch['state'] + 8
        count = _read_dword(emu, count_addr) + 1
        emu.write(count_addr, _dword(count))
        if count == route(emu)[2].get('abort'):
            emu.write(MODE, _word(4))
        return 0

    def back_to_setup(emu, log):
        log()
        emu.write(MODE, _word(4))
        return 0

    def exit_to_harness(emu, log):
        log(emu.reg('eax'))
        # exit is non-returning: returning to its immediate caller would
        # restart the infinite loop. The two harness-only stack arguments
        # tag the outer return address without assuming a common prologue
        # or stack-frame size for the reference and original functions.
        esp = emu.reg('esp')
        tag = _dword(COOKIE) * 2
        for offset in range(4, 256, 4):
            addr = esp + offset
            if emu.read(addr, 8) == tag:
                emu.write(esp, emu.read(addr - 4, 4))
                return 0
        raise AssertionError('outer emulation return address not found at exit')

    stub = t4spec.T4Stub
    stubs = [
        stub(0x1DA34, log_regs=()),
        stub(0x18488, log_regs=()),
        stub(0x13DD0, log_regs=('eax',)),
        stub(0x31F70, log_regs=('eax',)),
        stub(0x321E8, log_regs=()),
        stub(0x1E020, log_regs=()),
        stub(0x23AE0, log_regs=()),
        stub(0x13E94, log_regs=()),
        stub(0x2C3F0, log_regs=(), fn=setup_menu),
        stub(0x1E100, log_regs=()),
        stub(0x24900, log_regs=('eax',), fn=load_image),
        stub(0x33887, log_regs=('eax',)),
        stub(0x1C300, log_regs=()),
        stub(0x21C20, log_regs=('eax',)),
        stub(0x21844, log_regs=(), fn=packet_tick),
        stub(0x195AC, log_regs=('eax',)),
        stub(0x19998, log_regs=()),
        stub(0x19B14, log_regs=(), fn=back_to_setup),
        stub(0x2FCFC, log_regs=()),
        stub(0x18FB0, log_regs=()),
        stub(0x13F0C, log_regs=(), fn=back_to_setup),
        stub(0x33F5C, log_regs=('eax',), fn=exit_to_harness),
    ]
    t4spec.run_spec(
        SRC + '/run_game_mode_loop_reference.c', 'RunGameModeLoop_',
        0x1E158, cases, watch=watch, stubs=stubs, out_regs=(),
        init_emu=init_emu,
    )
