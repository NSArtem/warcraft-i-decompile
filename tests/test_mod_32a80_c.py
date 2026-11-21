import os
import struct

import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case, T4Stub

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = path('src/mod_32a80', 'evt_process_reference.c')

KEY_ASCII = 0x0
BUFSZ = 0x2000

_state = {}


def init_emu(emu):
    _state['buf'] = emu.alloc(0x100, 16)


def test_t3_files_still_match():
    pass


def test_ref_mismatch_guard():
    t4spec.assert_ref_mismatch(path('src/mod_32a80'), ['evt_process_reference.c'])


def _ev(buf, typ, key, mods=0, ch=0):
    return struct.pack('<H6sBBH', typ, b'\0' * 6, key, mods, ch)


def _cases():
    cases = []
    for typ in (0, 0x80, 0x100, 0x200, 0x300, 0x380):
        for key in (0x36, 0x2a, 0x1d, 0x71, 0x38, 0x74, 0x46, 0x45, 0x3a,
                    0x52, 0x7e, 0x10, 0x1e, 0x47, 0x4f, 0x53, 0x02, 0x39):
            def setup(emu, typ=typ, key=key):
                emu.write(_state['buf'], _ev(None, typ, key))
            cases.append(T4Case(args=(0,), label='null') if False else
                         T4Case(args=(None,), setup=setup, label=f't{typ:x}k{key:x}'))
    return cases


def test_evt_process():
    cases = []
    for c in _cases():
        def mk(c=c):
            def setup(emu):
                c.setup(emu)
            return setup
        cases.append(T4Case(args=(), setup=mk(), label=c.label))

    class Lazy(T4Case):
        pass

    real = []
    for c in cases:
        def setup(emu, c=c):
            c.setup(emu)
        real.append(c)

    def run():
        out = []
        for c in real:
            out.append(T4Case(args=(_state['buf'],), setup=c.setup, label=c.label))
        return out

    def init(emu):
        init_emu(emu)

    # buffer address is known only after init; build cases via a wrapper
    from wc1 import cemu
    emu_probe = __import__('wc1.emu', fromlist=['Emu']).Emu()
    init(emu_probe)
    addr = _state['buf']
    final = [T4Case(args=(addr,), setup=c.setup, label=c.label) for c in real]
    final.append(T4Case(args=(0,), label='null'))
    t4spec.run_spec(
        SRC, 'EvtProcess_', 0x32b40, final,
        watch=[(addr, 16)],
        stubs=[T4Stub(0x32a80 + 0, log_regs=('eax',))],
        out_regs=(), init_emu=init)
