import os
import struct

import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case, T4Stub


pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = 'src/mod_19470'
EXTRA = {
    '_game_rng_seed': 0x50D7C,
    '_custom_map_index': 0x50E50,
    '_custom_map_group': 0x50E52,
    '_scenario_music_track': 0x500CC,
    '_scenario_size_error': 0x56BF0,
    '_game_init_in_progress': 0x5A7C2,
    '_packet_tick_intervals': 0x517CE,
    '_game_tick_delays': 0x517F1,
    '_game_tick_delay_phase': 0x594F4,
    '_packet_tick_countdown': 0x594F6,
    '_game_mode_dword_low': 0x59614,
    '_pending_save_image': 0x599B0,
    'GameSetRandomSeed_': 0x19470,
    'GameResolveCustomScenario_': 0x194A8,
    'GameUpdateFrame_': 0x197B0,
}


def u16(*values):
    return struct.pack('<' + 'H' * len(values), *values)


def u32(*values):
    return struct.pack('<' + 'I' * len(values), *values)


def read16(e, addr):
    return struct.unpack('<H', e.read(addr, 2))[0]


def noargs(*addresses):
    return tuple(T4Stub(addr, log_regs=()) for addr in addresses)


def test_t3_matches():
    t4spec.assert_t3_matches(path('src/mod_19470'), ['game_run_session.c'])


def test_reference_near_misses():
    t4spec.assert_ref_mismatch(path('src/mod_19470'), ['game_handle_pending_load_reference.c', 'game_init_session_reference.c', 'game_resolve_custom_scenario_reference.c', 'game_run_active_loop_reference.c', 'game_set_random_seed_reference.c', 'game_shutdown_session_reference.c', 'game_update_frame_reference.c'])


def test_game_set_random_seed():
    def case(seed, label=''):
        return T4Case(args=(seed,), mem={0x50D7C: u32(seed ^ 0xFFFFFFFF, 0x76543210)}, label=label)

    t4spec.run_spec(
        f'{SRC}/game_set_random_seed_reference.c', 'GameSetRandomSeed_', 0x19470,
        [case(v, hex(v)) for v in (0, 1, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF)],
        watch=[(0x50D7C, 8)], out_regs=(), extra=EXTRA,
        rand_cases=12, rand_gen=lambda rng: case(rng.getrandbits(32)),
    )


def test_game_resolve_custom_scenario():
    def case(label, custom, index, group, net):
        return T4Case(label=label, mem={
            0x50D82: u16(0xCAFE), 0x50E4E: u16(custom, index, group),
            0x5160C: u32(0xABCD0000 | index),
            0x51620: u32(0x98760000 | group), 0x52586: u16(net),
        })

    def rng(e, log):
        arg = e.reg('eax')
        log(arg)
        return {0x1D: 0x101, 0x1C: -5, 0x31: -9}[arg] & 0xFFFFFFFF

    cases = [case(f'switch-{i}', 0, i, 3, i & 1) for i in range(6)]
    cases += [case('unsigned-default', 0, 0xFFFF, 3, 1),
              case('fixed-group-wrap', 0, 0xFFFF, 0xFFFF, 0)]
    custom = case('copy-then-resolve', 2, 4, 3, 2)
    custom.mem[0x50E4E] = u16(2, 0, 1)
    cases.append(custom)
    t4spec.run_spec(
        f'{SRC}/game_resolve_custom_scenario_reference.c', 'GameResolveCustomScenario_', 0x194A8,
        cases, watch=[(0x50E50, 4), (0x50D82, 2)],
        stubs=[T4Stub(0x19478, log_regs=('eax',), fn=rng)], out_regs=(), extra=EXTRA,
    )


def test_game_init_session():
    buf = {}
    watch = []

    def init_emu(e):
        buf['save'] = e.alloc(0x1000, 16)
        watch[:] = [(buf['save'], 0x1000), (0x50004, 0xBB8), (0x50D7C, 8),
                    (0x51214, 4), (0x51DE6, 10), (0x532B4, 20), (0x5A7C2, 2)]

    def case(label, *, resume=False, net=0, demo=0, custom=0):
        c = T4Case(label=label, mem={
            0x50004: u32(0xFFFF), 0x50088: u16(1, 2), 0x500CC: u16(0xBBBB),
            0x50D7C: u32(0x24681357) + u16(0x1234, 0x93), 0x50E4E: u16(custom),
            0x51214: u32(0xFFFFFFFF), 0x5152C: u16(demo),
            0x51DE6: u16(9, 8, 7, 6, 5), 0x52586: u16(net),
            0x532B4: u32(1, 2, 3, 4, 5), 0x5A7C2: u16(0xFFFF),
        })

        def setup(e):
            base = buf['save']
            c.args = (base if resume else 0,)
            e.write(base, u32(5, 4, 3, 2, 1) + u32(0x12345678) + bytes(0xBB4)
                    + u32(0x89ABCDEF) + u16(0x5678, 0x90) + bytes(0x1F8))

        c.setup = setup
        return c

    def save_read(e, log):
        dst, count, pos = (e.reg(r) for r in ('eax', 'edx', 'ebx'))
        log(dst, count, pos)
        e.write(dst, e.read(pos, count))
        return pos + count

    def resolve(e, log):
        log()
        e.write(0x50D82, u16(0xAA))

    def resource_read(e, log):
        dst, count = e.reg('eax'), e.reg('edx')
        log(dst, count)
        e.write(dst, u32(0x10203040))
        e.write(0x50088, u16(0x12, 0x34))
        return dst

    def unit_buffers(e, log):
        pos = e.reg('eax')
        log(pos)
        return pos + 4 if pos else 0

    def units(e, log):
        pos = e.reg('eax')
        log(pos)
        return 0x1357 if pos else 0

    def find_start(e, log):
        log()  # Both arguments point into the caller's stack; compare their use at MapCenterOnTile.
        e.write(e.reg('eax'), u32(17))
        e.write(e.reg('edx'), u32(29))

    stubs = [
        T4Stub(0x249A4, log_regs=('eax', 'edx', 'ebx'), fn=save_read),
        T4Stub(0x2674C, log_regs=('eax',)),
        T4Stub(0x331EB, ret=0x13579BDF, log_regs=('eax',)),
        T4Stub(0x194A8, log_regs=(), fn=resolve),
        T4Stub(0x31870, ret=0xBB8, log_regs=('eax', 'edx')),
        T4Stub(0x32740, log_regs=('eax', 'edx'), fn=resource_read),
        T4Stub(0x19478, ret=0xFFFFFFF9, log_regs=('eax',)),
        T4Stub(0x295D0, log_regs=('eax',)),
        T4Stub(0x1B198, log_regs=('eax',), fn=unit_buffers),
        T4Stub(0x13D04, log_regs=('eax',)),
        T4Stub(0x2D4B8, log_regs=('eax',), fn=units),
        T4Stub(0x1E7B0, log_regs=('eax',)),
        T4Stub(0x249E0, log_regs=('eax',)),
        T4Stub(0x1B12C, log_regs=(), fn=find_start),
        T4Stub(0x1B11C, log_regs=('eax', 'edx')),
        T4Stub(0x1B8D4, log_regs=('eax',)),
        *noargs(0x2B91C, 0x26320, 0x1CB90, 0x2F788, 0x1A714, 0x2B4B8,
                0x224E0, 0x2B2F0, 0x19DB4, 0x25718, 0x1A328, 0x29120,
                0x25BA0, 0x21968),
    ]
    t4spec.run_spec(
        f'{SRC}/game_init_session_reference.c', 'GameInitSession_', 0x195AC,
        [case('local-campaign-time'), case('local-demo-custom', demo=1, custom=1),
         case('network-custom', net=2, custom=1), case('restore-stream', resume=True)],
        init_emu=init_emu, watch=watch, stubs=stubs, out_regs=(), extra=EXTRA,
    )


def test_game_update_frame():
    cases = [T4Case(args=(sim, packet), mem={0x58DA4: u16(movie)},
                    label=f'movie={movie},sim={sim:#x},packet={packet:#x}')
             for movie in (0, 2) for sim in (0, 1, 0xFFFF8000)
             for packet in (0, 1, 0xFFFFFFFF)]
    t4spec.run_spec(
        f'{SRC}/game_update_frame_reference.c', 'GameUpdateFrame_', 0x197B0,
        cases, out_regs=(), extra=EXTRA,
        stubs=[*noargs(0x2D650, 0x184CC, 0x21844, 0x29A08, 0x2EC0C, 0x25684,
                       0x2B824, 0x1BF40, 0x29450, 0x2261C, 0x321E8, 0x33324),
               T4Stub(0x31F70, log_regs=('eax',))],
    )


def test_game_run_active_loop():
    def case(label, mode=3, cache=1, crit=0, phase=0, countdown=1):
        return T4Case(label=label, regs_in={'ecx': 0}, mem={
            0x50D80: u16(100), 0x532B4: u32(1), 0x594F0: u32(cache),
            0x594F4: u16(phase, countdown), 0x59614: u16(0xABCD, mode),
            0x61EA0: u16(crit), 0x52A5E: u16(2),
            0x517CE: bytes([1] * 7 + [3] + [1] * 27),
            0x517F1: bytes([7, 7, 4, 5]),
        })

    def clock(e, log):
        log()
        frame = read16(e, 0x50D80)
        return {101: 100, 102: 101, 103: 110}[frame]

    def mission_end(e, log):
        log(e.reg('eax'))
        if read16(e, 0x50D80) == 103:
            e.write(0x59616, u16(2))

    t4spec.run_spec(
        f'{SRC}/game_run_active_loop_reference.c', 'GameRunActiveLoop_', 0x19810,
        [case('idle', mode=2), case('warm', countdown=2), case('speed-change', cache=0),
         case('critical-error', crit=0xFFFF, phase=1), case('countdown-wrap', countdown=0)],
        watch=[(0x50D80, 2), (0x594F0, 8), (0x59614, 4), (0x61EA0, 2)],
        stubs=[T4Stub(0x30E98, log_regs=(), fn=clock),
               T4Stub(0x197B0, log_regs=('eax', 'edx')),
               T4Stub(0x2F7FC, log_regs=('eax',), fn=mission_end)],
        out_regs=(), extra=EXTRA,
    )


def test_game_handle_pending_load():
    buf = {}

    def init_emu(e):
        buf['file'] = e.alloc(32, 16)
        buf['image'] = e.alloc(32, 16)

    def case(label, has_file, not_cancelled, success=False):
        def setup(e):
            e.write(0x59610, u32(buf['file'] if has_file else 0))
            e.write(buf['file'], u32(int(success)))

        return T4Case(label=label, setup=setup, mem={
            0x516B0: u16(not_cancelled), 0x59614: u16(0xBEEF, 7),
            0x599B0: u32(0xABCD1234),
        })

    def load_image(e, log):
        fp = e.reg('eax')
        log(fp)
        return buf['image'] if e.read(fp, 4) == u32(1) else 0

    t4spec.run_spec(
        f'{SRC}/game_handle_pending_load_reference.c', 'GameHandlePendingLoad_', 0x19908,
        [case('no-request', False, 0), case('validate-null', False, 2),
         case('file-load-ok', True, 0, True), case('file-load-failed', True, 1)],
        init_emu=init_emu, watch=[(0x516B0, 2), (0x59610, 8), (0x599B0, 4)],
        stubs=[*noargs(0x21844), T4Stub(0x24900, log_regs=('eax',), fn=load_image),
               T4Stub(0x33887, log_regs=('eax',)),
               T4Stub(0x241A4, ret=0x12345678, log_regs=('eax',))],
        out_regs=('eax',), extra=EXTRA,
    )


def test_game_shutdown_session():
    def case(label, base):
        image = b''.join(u16((base + i) & 0xFFFF) + bytes([i + 1]) * 16 for i in range(32))
        return T4Case(label=label, mem={0x5AA90: image})

    def place_box_shutdown(e, log):
        log(*(read16(e, 0x5AA90 + 0x12 * i) for i in (0x0C, 0x0D, 0x16, 0x17)))

    t4spec.run_spec(
        f'{SRC}/game_shutdown_session_reference.c', 'GameShutdownSession_', 0x19B14,
        [case('all-state-words-set', 0x1200), case('mixed-state-words', 0xFFF0)],
        watch=[(0x5AA90, 32 * 0x12)], out_regs=(), extra=EXTRA,
        stubs=[*noargs(0x334FC, 0x19ED0, 0x2B400, 0x257DC, 0x292A4, 0x1CCDC,
                       0x26340, 0x1B074, 0x2BA08, 0x267E0),
               T4Stub(0x2254C, log_regs=(), fn=place_box_shutdown),
               T4Stub(0x1B8D4, log_regs=('eax',))],
    )
