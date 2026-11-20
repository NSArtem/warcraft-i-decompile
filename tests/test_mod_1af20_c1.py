import os
import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case, T4Stub

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original', 'install', 'war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = path('src/mod_1af20')

FOG_TABLE = 0x59000
FOG_MAP = 0x59004
SCROLL_X = 0x59008
SCROLL_Y = 0x5900a
DST_PTR = 0x5a874


def test_t3_files():
    t4spec.assert_t3_matches(path('src/mod_1af20'), [])


def test_ref_mismatch():
    t4spec.assert_ref_mismatch(path('src/mod_1af20'), ['fog_draw_cell_reference.c', 'fog_draw_viewport_reference.c', 'place_box_release_reference.c'])


def _syms():
    by = t4spec.by_link_lenient()
    return by


def _addr(name):
    return _syms()[name]["addr"]


def test_fog_draw_cell():
    tbl = {}

    def init_emu(emu):
        tbl['buf'] = emu.alloc(0x100, 16)
        tbl['dst'] = emu.alloc(0x2000, 16)
        tbl['tab'] = emu.alloc(0x400, 16)

    def mk(cell):
        def setup(emu):
            emu.write(_addr('_fog_cell_table'), tbl['tab'].to_bytes(4, 'little'))
            data = bytes((i * 7 + 3) & 0xff for i in range(0x400))
            emu.write(tbl['tab'], data)
        return T4Case(args=(cell, 0), setup=setup, label="cell%d" % cell)

    cases = []
    for c in (0, 1, 5, 10, 11, 0x1f, 0x20, 0x2a, 0xff, 0x1ff):
        cs = mk(c)

        def setup(emu, cs=cs):
            cs.setup(emu)
        cases.append(T4Case(args=(c, 0x1000), setup=cs.setup, label=cs.label))
    # dst is a dummy pointer; callees are stubbed
    t4spec.run_spec(
        os.path.join(SRC, 'fog_draw_cell_reference.c'), 'FogDrawCell_', 0x1af20,
        cases, out_regs=(),
        stubs=[T4Stub(_addr('FillBlack16_'.rstrip('_')) if False else _addr_of('FillBlack16'), log_regs=("eax",)),
               T4Stub(_addr_of('MiniTileMasked'), log_regs=("eax", "edx"))],
        init_emu=init_emu)


def _addr_of(name):
    by = _syms()
    for k in (name + '_', '_' + name, name):
        if k in by:
            return by[k]["addr"]
    raise KeyError(name)


def test_fog_draw_viewport():
    st = {}

    def init_emu(emu):
        st['map'] = emu.alloc(0x4000 * 2, 16)

    def setup_for(sx, sy):
        def setup(emu):
            by = _syms()
            emu.write(by['_fog_map']['addr'], st['map'].to_bytes(4, 'little'))
            emu.write(by['_map_scroll_x']['addr'], sx.to_bytes(2, 'little'))
            emu.write(by['_map_scroll_y']['addr'], sy.to_bytes(2, 'little'))
            emu.write(by['_dat_5a874']['addr'] if '_dat_5a874' in by else DST_PTR,
                      (0x300000).to_bytes(4, 'little'))
            emu.write(st['map'], bytes((i * 5 + 1) & 0xff for i in range(0x8000)))
        return setup

    cases = [T4Case(setup=setup_for(0, 0), label="origin"),
             T4Case(setup=setup_for(3, 2), label="scrolled"),
             T4Case(setup=setup_for(20, 30), label="far")]
    t4spec.run_spec(
        os.path.join(SRC, 'fog_draw_viewport_reference.c'), 'FogDrawViewport_', 0x1af90,
        cases, out_regs=(),
        stubs=[T4Stub(_addr_of('FogDrawCell'), log_regs=("eax", "edx"))],
        init_emu=init_emu, log_cap=8192)


def test_place_box_release():
    st = {}

    def init_emu(emu):
        st['evt'] = emu.alloc(32, 16)

    def mk(x, y, sx, sy):
        def setup(emu):
            by = _syms()
            emu.write(st['evt'] + 4, (x & 0xffff).to_bytes(2, 'little') + (y & 0xffff).to_bytes(2, 'little'))
            emu.write(by['_map_scroll_x']['addr'], sx.to_bytes(2, 'little'))
            emu.write(by['_map_scroll_y']['addr'], sy.to_bytes(2, 'little'))
        return setup

    pts = [(0x48, 0xc, 0, 0), (0x48 + 0xef, 0xc + 0xaf, 5, 7),
           (0x47, 0xc, 1, 1), (0x48, 0xb, 1, 1),
           (0x48 + 0xf0, 0xc, 1, 1), (0x48, 0xc + 0xb0, 1, 1),
           (0x100, 0x80, 10, 20), (0x60, 0x30, 0x30, 0x31)]
    cases = []
    for x, y, sx, sy in pts:
        def setup(emu, x=x, y=y, sx=sx, sy=sy):
            mk(x, y, sx, sy)(emu)
        cases.append(T4Case(args=(0,), setup=setup, label="%x,%x" % (x, y)))

    # evt pointer is allocated in init_emu; patch via regs_in-less setup: use args lazily
    def fix(c):
        orig = c.setup

        def setup(emu):
            orig(emu)
        c.setup = setup
        return c

    class Lazy(T4Case):
        pass

    real = []
    for c in cases:
        real.append(c)

    def init2(emu):
        init_emu(emu)
        for c in real:
            c.args = (st['evt'],)

    t4spec.run_spec(
        os.path.join(SRC, 'place_box_release_reference.c'), 'PlaceBoxRelease_', 0x1b4dc,
        real, out_regs=(),
        stubs=[T4Stub(_addr_of('NetSendPlaceConfirm'), log_regs=("eax",)),
               T4Stub(0x1a388, log_regs=("eax",))],
        init_emu=init2)
