import os
import random

import pytest

from wc1 import t4spec
from wc1 import path
from wc1.t4spec import T4Case

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC_DIR = 'src/mod_3cc5e'
BUF = 0x400


def test_t3_files_match():
    t4spec.assert_t3_matches(path('src/mod_3cc5e'), [])


def test_reference_files_still_mismatch():
    t4spec.assert_ref_mismatch(path('src/mod_3cc5e'),
                               ['rect_copy_reference.c', 'rect_copy_transparent_reference.c'])


def _make_env():
    bufs = {}

    def init_emu(emu):
        bufs['src'] = emu.alloc(BUF, 16)
        bufs['dst'] = emu.alloc(BUF, 16)

    return bufs, init_emu


def _case(bufs, width, height, src_skip, dst_skip, seed, zeros=False):
    rng = random.Random(seed)
    n = height * (width + max(src_skip, 0)) + 8
    if zeros:
        sdata = bytes(rng.choice((0, 0, rng.randrange(1, 256))) for _ in range(n))
    else:
        sdata = bytes(rng.randrange(256) for _ in range(n))
    ddata = bytes(rng.randrange(256) for _ in range(BUF))
    c = T4Case(label="w%d h%d ss%d ds%d" % (width, height, src_skip, dst_skip))

    def setup(emu):
        emu.write(bufs['src'], sdata)
        emu.write(bufs['dst'], ddata)
        c.args = (bufs['src'], bufs['dst'], src_skip, dst_skip, width, height)

    c.setup = setup
    return c


def _cases(bufs, even_only, zeros):
    out = []
    seed = 1
    for w in (1, 2, 3, 4, 5, 8, 9, 16):
        if even_only and w & 1 and False:
            continue
        for h in (1, 2, 5):
            for ss, ds in ((0, 0), (3, 7), (5, 1)):
                out.append(_case(bufs, w, h, ss, ds, seed, zeros))
                seed += 1
    return out


def test_rect_copy():
    bufs, init_emu = _make_env()
    t4spec.run_spec(
        'src/mod_3cc5e/rect_copy_reference.c', '_RectCopy', 0x3cc5e,
        _cases(bufs, False, False),
        watch=[], out_regs=(), cdecl=True, init_emu=init_emu,
        extra=None,
    ) if False else _run_rect_copy(bufs, init_emu)


def _run_rect_copy(bufs, init_emu):
    emu_watch = _Watch(bufs)
    t4spec.run_spec(
        'src/mod_3cc5e/rect_copy_reference.c', '_RectCopy', 0x3cc5e,
        _cases(bufs, False, False),
        watch=emu_watch, out_regs=(), cdecl=True, init_emu=init_emu,
    )


class _Watch(list):
    """Watch list resolved lazily: addresses are filled in by init_emu."""

    def __init__(self, bufs):
        super().__init__()
        self.bufs = bufs

    def __iter__(self):
        return iter([(self.bufs['dst'], BUF)])


def test_rect_copy_transparent():
    bufs, init_emu = _make_env()
    t4spec.run_spec(
        'src/mod_3cc5e/rect_copy_transparent_reference.c', '_RectCopyTransparent', 0x3ccb2,
        _cases(bufs, False, True),
        watch=_Watch(bufs), out_regs=(), cdecl=True, init_emu=init_emu,
    )
