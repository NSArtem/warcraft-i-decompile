"""T3/T4 tests for mod_2b8e0 (terrain tile tables and autotiling)."""
import os
import random
import struct

import pytest

from wc1 import path, t4spec
from wc1.emu import Emu

pytestmark = pytest.mark.skipif(
    not (os.path.exists(path('original', 'install', 'war.exe')) and os.environ.get('WATCOM')),
    reason='needs original/ and $WATCOM')

SRC = ('src', 'mod_2b8e0')

_KNOWN = {
    'map_scroll_x': 0x500d0, 'map_scroll_y': 0x500d2, 'dat_500da': 0x500da,
    'terrain_tbl_a': 0x5514c, 'terrain_tbl_b': 0x55150,
    'terrain_tbl_c': 0x55154, 'terrain_tbl_d': 0x55158,
    'terrain_hdr_a': 0x5a430, 'terrain_hdr_b': 0x5a434,
    'terrain_hdr_c': 0x5a438, 'terrain_hdr_d': 0x5a43c,
    'dat_5a440': 0x5a440, 'dat_5a442': 0x5a442, 'dat_5a444': 0x5a444,
    'dat_5a446': 0x5a446, 'dat_5a330': 0x5a330, 'dat_5a334': 0x5a334,
    'tile_map': 0x58584, 'map_flags': 0x5857c,
    'dat_55204': 0x55204, 'dat_55206': 0x55206,
    'terrain_autotile_base': 0x5a450, 'terrain_autotile_map': 0x5a454,
    'terrain_rect_cb': 0x5a458, 'terrain_autotile_stride': 0x5a45c,
    'terrain_autotile_first': 0x5a45e, 'terrain_flag_mask': 0x5a460,
}
_lenient = {}
_extra = {}


def A(name):
    if name in _KNOWN:
        return _KNOWN[name]
    if not _lenient:
        _funcs, datas = t4spec.load_lenient()
        for e in datas.values():
            _lenient.setdefault(e['name'], e['addr'])
    return _lenient[name]


def _get_extra():
    """Link-name -> entry map for symbols missing from the main database."""
    if not _extra:
        funcs, datas = t4spec.load_lenient()
        for e in funcs.values():
            _extra.setdefault(e['name'] + '_', e)
        for e in datas.values():
            _extra.setdefault('_' + e['name'], e)
        _extra.setdefault('TerrainRoadCell_', {'name': 'TerrainRoadCell', 'addr': 0x2c100})
        _extra.setdefault('TerrainApplyCellFlags_',
                          {'name': 'TerrainApplyCellFlags', 'addr': 0x2c14c})
    return _extra


def w16(emu, name, v):
    emu.write(A(name), struct.pack('<H', v & 0xffff))


def w32(emu, name, v):
    emu.write(A(name), struct.pack('<I', v & 0xffffffff))


def _build(emu):
    rng = random.Random(1234)
    env = {}
    env['tm'] = emu.alloc(0x2000, 16)
    env['mf'] = emu.alloc(0x2000, 16)
    for k in ('ta', 'tb', 'tc', 'td'):
        env[k] = emu.alloc(0x400, 16)
    env['st'] = emu.alloc(16, 16)
    env['am'] = emu.alloc(64, 16)
    env['u'] = emu.alloc(0x100, 16)
    env['pt'] = emu.alloc(16, 16)
    env['rect'] = emu.alloc(16, 16)
    tm = b''.join(struct.pack('<H', (8 + rng.randrange(40)) | (rng.randrange(32) << 11))
                  for _ in range(0x1000))
    mf = bytes(rng.randrange(256) for _ in range(0x2000))
    emu.write(env['tm'], tm)
    emu.write(env['mf'], mf)
    for k in ('ta', 'tb', 'tc', 'td'):
        emu.write(env[k], b''.join(struct.pack('<H', rng.randrange(0x4000))
                                   for _ in range(0x200)))
    emu.write(env['st'], struct.pack('<8H', 0, 1, 2, 3, 1, 2, 0, 3))
    emu.write(env['am'], b''.join(struct.pack('<H', rng.randrange(4)) for _ in range(32)))
    w32(emu, 'tile_map', env['tm'])
    w32(emu, 'map_flags', env['mf'])
    for n, k in (('a', 'ta'), ('b', 'tb'), ('c', 'tc'), ('d', 'td')):
        w32(emu, 'terrain_tbl_' + n, env[k])
        emu.write(A('terrain_hdr_' + n), struct.pack('<HH', 4, 5))
    w16(emu, 'dat_5a442', 10)
    w16(emu, 'dat_5a446', 15)
    w16(emu, 'dat_5a440', 20)
    w16(emu, 'dat_5a444', 25)
    w16(emu, 'map_scroll_x', 10)
    w16(emu, 'map_scroll_y', 10)
    w32(emu, 'terrain_scan_x', 12)
    w32(emu, 'terrain_scan_y', 14)
    w32(emu, 'terrain_scan_table', env['st'])
    w32(emu, 'terrain_autotile_map', env['am'])
    w32(emu, 'terrain_autotile_base', env['tb'])
    w16(emu, 'terrain_autotile_stride', 4)
    w16(emu, 'terrain_autotile_first', 10)
    w16(emu, 'terrain_flag_mask', 3)
    w16(emu, 'dat_55204', 0)
    w16(emu, 'dat_55206', 1)
    return env


def _env():
    return _build(Emu())


def _run(fname, link, addr, cases, **kw):
    kw.setdefault('extra', _get_extra())
    t4spec.run_spec(path(*SRC, fname), link, addr, cases,
                    init_emu=_build, **kw)


def C(args=(), mem=None, label=''):
    return t4spec.T4Case(args=tuple(args), mem=mem or {}, label=label)


def _maps(env):
    return [(env['tm'], 0x2000), (env['mf'], 0x2000)]


CACHE = t4spec.T4Stub(0x1246c, log_regs=('eax', 'edx', 'ebx'))
REGION = t4spec.T4Stub(0x2b1b0, log_regs=())
CROSS = t4spec.T4Stub(0x2c0bc, log_regs=('eax', 'edx', 'ebx'))
CELL = t4spec.T4Stub(0x2bf64, log_regs=('eax', 'edx', 'ebx'))
LOAD = t4spec.T4Stub(0x2b8e0, log_regs=('eax', 'edx', 'ebx'))
ROAD = t4spec.T4Stub(0x2c100, log_regs=('eax', 'edx', 'ebx'))
APPLY = t4spec.T4Stub(0x2c14c, log_regs=('eax', 'edx', 'ebx'))


def _flag_test(e, log):
    a, d, b = e.reg('eax'), e.reg('edx'), e.reg('ebx')
    log(a, d, b)
    return (a + d + b) & 1


FLAGTEST = t4spec.T4Stub(0x2bf30, fn=_flag_test)


def _scan(x, y, sx=10, sy=10):
    def setup(emu):
        w32(emu, 'terrain_scan_x', x)
        w32(emu, 'terrain_scan_y', y)
        w16(emu, 'map_scroll_x', sx)
        w16(emu, 'map_scroll_y', sy)
    return setup


def _scan_cases(fn_args):
    out = []
    for i, (x, y, sx, sy, idx) in enumerate(fn_args):
        c = t4spec.T4Case(args=(idx,), setup=_scan(x, y, sx, sy), label='scan%d' % i)
        out.append(c)
    return out


SCANS = [(12, 14, 10, 10, 0x41), (10, 10, 10, 10, 0x80), (25, 21, 10, 10, 0x100),
         (26, 22, 10, 10, 0x101), (9, 14, 10, 10, 0x200), (12, 9, 10, 10, 0x300),
         (12, 14, 10, 10, 0x5), (20, 20, 8, 12, 0x77), (3, 3, 0, 0, 0x2a),
         (15, 11, 0, 0, 0x33)] + [(12, 14, 10, 10, 0x40 + i * 7) for i in range(30)]


def test_terrain_tables_init():
    env = _env()
    cases = [C(mem={A('dat_500da'): struct.pack('<H', v)}, label=hex(v))
             for v in (0xc0, 0xc3, 0x00, 0x11)]
    _run('terrain_tables_init.c', 'TerrainTablesInit_', 0x2b91c, cases,
         out_regs=(), stubs=[LOAD],
         watch=[(0x5a430, 0x1c), (0x5514c, 0x10)])


def test_terrain_tile_advance_b():
    env = _env()
    _run('terrain_tile_advance_b_reference.c', 'TerrainTileAdvanceB_', 0x2ba50,
         _scan_cases(SCANS), out_regs=(), stubs=[CACHE],
         watch=_maps(env) + [(A('terrain_scan_x'), 4)])


def test_terrain_start_region_b():
    env = _env()
    cases = []
    for x, y in ((3, 4), (0x20, 0x31), (0, 0), (0xffff, 7)):
        cases.append(C((env['u'],),
                       mem={env['u'] + 0x4c: struct.pack('<HHH', 0x1234, x, y)},
                       label='%d,%d' % (x, y)))
    _run('terrain_start_region_b.c', 'TerrainStartRegionB_', 0x2bb38, cases,
         out_regs=(), stubs=[REGION],
         watch=[(A('terrain_scan_x'), 4), (A('terrain_scan_y'), 4),
                (0x5a330, 8), (A('terrain_scan_table'), 4), (A('terrain_scan_cb'), 4)])


def test_terrain_tile_is_clear():
    env = _env()
    cases = []
    for i, (x, y) in enumerate([(0, 0), (1, 1), (5, 9), (20, 20), (63, 63),
                                (10, 3), (33, 40), (2, 61), (7, 7), (17, 5),
                                (30, 30), (45, 12), (12, 45), (8, 8), (9, 9)]):
        cases.append(C((env['pt'],), mem={env['pt']: struct.pack('<HH', x, y)},
                       label='pt%d' % i))
    _run('terrain_tile_is_clear_reference.c', 'TerrainTileIsClear_', 0x2bb7c, cases,
         out_regs=('eax',))


def test_terrain_find_clear_tile():
    env = _env()
    cases = []
    for i, (x, y) in enumerate([(20, 20), (5, 5), (0, 0), (60, 60), (32, 8),
                                (10, 50), (63, 63), (1, 40), (40, 1), (25, 30)]):
        cases.append(C((env['pt'],), mem={env['pt']: struct.pack('<HH', x, y)},
                       label='pt%d' % i))
    _run('terrain_find_clear_tile_reference.c', 'TerrainFindClearTile_', 0x2bbe4, cases,
         out_regs=('eax',), watch=[(env['pt'], 4)])


def test_terrain_tile_advance_a():
    env = _env()
    idxs = [(12, 14, 10, 10, i) for i in range(0, 4000, 97)] + SCANS[:10]
    _run('terrain_tile_advance_a_reference.c', 'TerrainTileAdvanceA_', 0x2bd00,
         _scan_cases(idxs), out_regs=(), stubs=[CACHE],
         watch=_maps(env))


def test_terrain_start_region_a():
    env = _env()
    cases = []
    for t in range(0, 0x30, 1):
        for (x, y) in ((4, 5),):
            cases.append(C((env['u'],),
                           mem={env['u'] + 8: struct.pack('<HHH', 0, x, y),
                                env['u'] + 0x1b: bytes([t])},
                           label='t%d' % t))
    _run('terrain_start_region_a_reference.c', 'TerrainStartRegionA_', 0x2bdd4, cases,
         out_regs=(), stubs=[REGION],
         watch=[(A('terrain_scan_x'), 4), (A('terrain_scan_y'), 4),
                (0x5a330, 8), (A('terrain_scan_table'), 4), (A('terrain_scan_cb'), 4)])


def test_terrain_autotile_cell():
    env = _env()
    cases = []
    pts = [(5, 5), (0, 0), (63, 63), (12, 14), (10, 10), (25, 21), (0x40, 5),
           (5, 0x40), (31, 31), (1, 62), (62, 1), (16, 12), (9, 9)]
    for x, y in pts:
        for fl in (0xffff, 0, 1, 2, 3, 0x10, 0xc):
            cases.append(C((x, y, fl), label='%d,%d,%#x' % (x, y, fl)))
    cases.append(C((12, 14, 0xffff), mem={A('dat_55204'): struct.pack('<H', 3)},
                   label='base3'))
    _run('terrain_autotile_cell_reference.c', 'TerrainAutotileCell_', 0x2bf64, cases,
         out_regs=(), stubs=[FLAGTEST, CACHE], watch=_maps(env))


def test_terrain_road_cell():
    cases = [C((x, y, m), label='%d,%d,%#x' % (x, y, m))
             for x, y, m in ((1, 2, 3), (63, 0, 0), (10, 20, 0xffff), (0, 0, 7))]
    _run('terrain_road_cell.c', 'TerrainRoadCell_', 0x2c100, cases,
         out_regs=(), stubs=[CROSS], watch=[(0x5a450, 0x14)])


def test_terrain_apply_cell_flags():
    env = _env()
    cases = [C((x, y, m), label='%d,%d,%#x' % (x, y, m))
             for x, y, m in ((1, 2, 3), (63, 63, 0), (10, 20, 0xffff), (0, 0, 7),
                             (33, 17, 0xc))]
    _run('terrain_apply_cell_flags_reference.c', 'TerrainApplyCellFlags_', 0x2c14c,
         cases, out_regs=(), stubs=[CROSS],
         watch=[(0x5a450, 0x14)] + _maps(env))


def _rect_cases(env):
    cases = []
    for i, (x0, y0, x1, y1) in enumerate([(4, 4, 4, 16), (4, 4, 20, 4), (0, 0, 0, 0),
                                          (6, 8, 6, 8), (10, 2, 10, 30),
                                          (30, 30, 10, 10), (2, 2, 9, 9)]):
        for k in (0, 1, 5, 15):
            cases.append(C((env['rect'], k),
                           mem={env['rect']: bytes([x0, y0, x1, y1])},
                           label='r%d/%d' % (i, k)))
    return cases


def test_terrain_fill_rect_owner_mask():
    env = _env()
    _run('terrain_fill_rect_owner_mask_reference.c', 'TerrainFillRectOwnerMask_', 0x2c1e8,
         _rect_cases(env), out_regs=(), stubs=[ROAD],
         watch=[(A('terrain_rect_cb'), 4)])


def test_terrain_fill_rect_mask():
    env = _env()
    _run('terrain_fill_rect_mask_reference.c', 'TerrainFillRectMask_', 0x2c208,
         _rect_cases(env), out_regs=(), stubs=[APPLY],
         watch=[(A('terrain_rect_cb'), 4)])


def test_terrain_wall_cell():
    cases = [C((x, y), label='%d,%d' % (x, y)) for x, y in ((1, 2), (63, 63), (0, 0), (20, 30))]
    _run('terrain_wall_cell.c', 'TerrainWallCell_', 0x2c268, cases,
         out_regs=(), stubs=[CELL], watch=[(0x5a450, 0x14), (0x55204, 2)])


def test_terrain_wall_advance():
    env = _env()
    cases = []
    for x in range(2, 40, 5):
        for y in range(2, 60, 7):
            cases.append(C((x, y), label='%d,%d' % (x, y)))
    for x, y in ((12, 14), (10, 10), (25, 21), (26, 22), (9, 14)):
        cases.append(C((x, y), label='vis%d,%d' % (x, y)))
    cases.append(C((12, 14), mem={A('dat_55206'): struct.pack('<H', 0)}, label='no_rec'))
    _run('terrain_wall_advance_reference.c', 'TerrainWallAdvance_', 0x2c2c4, cases,
         out_regs=(), stubs=[CACHE],
         watch=_maps(env) + [(0x55206, 2)])


def test_t3_files_match():
    t4spec.assert_t3_matches(path(*SRC), [
        'terrain_autotile_cross.c', 'terrain_flag_test.c',
        'terrain_road_cell.c', 'terrain_start_region_b.c',
        'terrain_table_load.c', 'terrain_tables_free.c',
        'terrain_tables_init.c', 'terrain_wall_cell.c'])


def test_reference_files_still_mismatch():
    t4spec.assert_ref_mismatch(path(*SRC), [
        'terrain_find_clear_tile_reference.c', 'terrain_apply_cell_flags_reference.c',
        'terrain_autotile_cell_reference.c', 'terrain_fill_rect_mask_reference.c',
        'terrain_fill_rect_owner_mask_reference.c', 'terrain_start_region_a_reference.c',
        'terrain_tile_advance_a_reference.c', 'terrain_tile_advance_b_reference.c',
        'terrain_tile_is_clear_reference.c', 'terrain_wall_advance_reference.c'])
