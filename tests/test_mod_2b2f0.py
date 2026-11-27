import os
import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Stub

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = path('src', 'mod_2b2f0')
FLAGS_ADDR = 0x5A350
NEP = None  # net_event_pending resolved via symbols at runtime


def _nep_addr():
    from wc1 import t4spec as t
    by = t.by_link_lenient()
    for k in ('_net_event_pending', 'net_event_pending'):
        if k in by:
            return by[k]['addr']
    raise KeyError('net_event_pending')


def _init(emu):
    emu.alloc(0x100, 16)


def _case(idx, flag, label):
    a = _nep_addr()
    mem = {a: bytes([idx, 0]),
           FLAGS_ADDR: b''.join((flag if i == idx else 0).to_bytes(2, 'little') for i in range(4))}
    return t4spec.T4Case(mem=mem, label=label)


def test_t3_files():
    files = [f for f in ['target_mode_is_active.c'] if os.path.exists(os.path.join(SRC, f))]
    if files:
        t4spec.assert_t3_matches(SRC, files)


def test_ref_mismatch():
    files = [f for f in ['target_mode_enter_reference.c', 'target_mode_exit_reference.c', 'target_mode_clear_reference.c']
             if os.path.exists(os.path.join(SRC, f))]
    if files:
        t4spec.assert_ref_mismatch(SRC, files)


def test_target_mode_clear():
    cases = [t4spec.T4Case(mem={FLAGS_ADDR: bytes([1, 0, 2, 0, 3, 0, 4, 0])}, label='filled'),
             t4spec.T4Case(mem={FLAGS_ADDR: bytes(8)}, label='zero')]
    t4spec.run_spec(os.path.join(SRC, 'target_mode_clear_reference.c'), 'TargetModeClear_', 0x2B2F0,
                    cases, watch=[(FLAGS_ADDR, 8)], out_regs=(), init_emu=_init)


def _stubs31():
    return [T4Stub(a, log_regs=r) for a, r in (
        (0x19F70, ('eax', 'edx')), (0x20C30, ('eax',)), (0x20CC0, ()), (0x25B6C, ('eax',)))]


def test_target_mode_enter():
    cases = [_case(i, f, f'idx{i}_flag{f}') for i in (0, 1, 3) for f in (0, 1)]
    t4spec.run_spec(os.path.join(SRC, 'target_mode_enter_reference.c'), 'TargetModeEnter_', 0x2B31C, cases,
                    watch=[(FLAGS_ADDR, 8), (0x59510, 12), (_nep_addr(), 2)],
                    stubs=_stubs31(), out_regs=(), init_emu=_init)


def test_target_mode_exit():
    stubs = [T4Stub(a, log_regs=r) for a, r in (
        (0x19F70, ('eax', 'edx')), (0x20C4C, ('eax',)), (0x20C6C, ()), (0x25B6C, ('eax',)))]
    cases = [_case(i, f, f'idx{i}_flag{f}') for i in (0, 1, 3) for f in (0, 1)]
    t4spec.run_spec(os.path.join(SRC, 'target_mode_exit_reference.c'), 'TargetModeExit_', 0x2B390, cases,
                    watch=[(FLAGS_ADDR, 8), (0x59510, 12), (_nep_addr(), 2)],
                    stubs=stubs, out_regs=(), init_emu=_init)
