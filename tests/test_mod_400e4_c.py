import os
import struct

import pytest

from wc1 import t4spec
from wc1.t4spec import T4Case
from wc1 import path

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = path('src/mod_400e4', 'rect_copy_transparent_flip_h_reference.c')

BUF = {}


def init_emu(emu):
    BUF['src'] = emu.alloc(0x400, 16)
    BUF['dst'] = emu.alloc(0x400, 16)


def _pattern(n, seed):
    out = bytearray()
    x = seed
    for _ in range(n):
        x = (x * 1103515245 + 12345) & 0x7FFFFFFF
        v = (x >> 16) & 0xFF
        out.append(0 if (v & 3) == 0 else v)
    return bytes(out)


def _case(width, height, src_skip, dst_skip, seed, label):
    def setup(emu):
        emu.write(BUF['src'], _pattern(0x400, seed))
        emu.write(BUF['dst'], bytes([0xEE]) * 0x400)
        # args are filled via stack_args at call time
    c = T4Case(setup=setup, label=label)
    return c


def _make_cases():
    cases = []
    specs = [(1, 1, 0, 0), (4, 1, 0, 0), (5, 3, 2, 3), (8, 4, 8, 4),
             (3, 5, 13, 1), (16, 2, 0, 0)]
    for i, (w, h, ss, ds) in enumerate(specs):
        cases.append((w, h, ss, ds, i + 1))
    return cases


def test_rect_copy_transparent_flip_h():
    cases = []
    for (w, h, ss, ds, seed) in _make_cases():
        def setup(emu, seed=seed):
            emu.write(BUF['src'], _pattern(0x400, seed))
            emu.write(BUF['dst'], bytes([0xEE]) * 0x400)
        # buffers are allocated in init_emu, so addresses are known at case build
        cases.append(None)
        cases.pop()
        cases_item = (w, h, ss, ds, setup, seed)
        cases.append(cases_item)

    def build(emu_unused=None):
        pass

    # Addresses are only known after init_emu, so run with a wrapper emu init
    # and build cases lazily through a deterministic allocation order.
    state = {}

    def init(emu):
        init_emu(emu)
        state['ok'] = True

    real = []
    for (w, h, ss, ds, setup, seed) in cases:
        real.append((w, h, ss, ds, setup))

    # first pass to learn addresses
    from wc1.emu import Emu
    probe = Emu()
    init_emu(probe)
    s, d = BUF['src'], BUF['dst']
    tcases = []
    for (w, h, ss, ds, setup) in real:
        tcases.append(T4Case(
            stack_args=(s + 0x200, d + 0x200, ss, ds, w, h),
            setup=setup,
            label=f"w{w}h{h}ss{ss}ds{ds}"))
    t4spec.run_spec(SRC, '_RectCopyTransparentFlipH', 0x400e4, tcases,
                    watch=[(d, 0x400)], out_regs=(), cdecl=True,
                    init_emu=init_emu)


def test_t3_matches():
    t4spec.assert_ref_mismatch(path('src/mod_400e4'), ['rect_copy_transparent_flip_h_reference.c'])
