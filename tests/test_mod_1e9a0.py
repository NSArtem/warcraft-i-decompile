import os
import struct

import pytest

from wc1 import t4spec, path

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = path('src/mod_1e9a0', 'fog_update_tile_reference.c')

FOG_OWNER_MASK = 0x51dde
FOG_OWNER_SHIFT = 0x51de2
FOG_TRANS = 0x52598
FOG_CUR_OWNER = 0x599d0

MAP_WORDS = 64
_buf = {}


def _init(emu):
    _buf['map'] = emu.alloc(MAP_WORDS * 2, 16)
    _buf['scan'] = emu.alloc(16, 16)


def _addr(name):
    e = t4spec.by_link_lenient()[name]
    return e['addr']


def _case(tile, owner, mapval, scan, label):
    def setup(emu):
        fm = _addr('_fog_map')
        ts = _addr('_terrain_scan_table')
        emu.write(fm, struct.pack('<I', _buf['map']))
        emu.write(ts, struct.pack('<I', _buf['scan']))
        emu.write(_buf['scan'], struct.pack('<H', scan))
        emu.write(_buf['map'], b''.join(
            struct.pack('<H', (mapval * (i + 1) * 0x1111) & 0xFFFF)
            for i in range(MAP_WORDS)))
        emu.write(_buf['map'] + 2 * tile, struct.pack('<H', mapval))
        emu.write(FOG_OWNER_MASK, struct.pack('<HH', 0x3, 0xC))
        emu.write(FOG_OWNER_SHIFT, struct.pack('<HH', 0, 2))
        emu.write(FOG_TRANS, b''.join(
            struct.pack('<H', (i * 5 + 1) & 3) for i in range(4 * 11 + 8)))
        emu.write(FOG_CUR_OWNER, struct.pack('<H', owner))
    from wc1.t4spec import T4Case
    return T4Case(args=(tile,), setup=setup, label=label)


def test_t3_files():
    t4spec.assert_t3_matches(path('src/mod_1e9a0'), ['fog_update_area11.c', 'fog_update_area5.c', 'fog_update_area6.c', 'fog_update_area7.c', 'fog_update_area8.c', 'fog_update_area9.c'])


def test_ref_mismatch():
    t4spec.assert_ref_mismatch(path('src/mod_1e9a0'), ['fog_update_tile_reference.c'])


def test_fog_update_tile():
    watch = []

    def init(emu):
        _init(emu)
        watch[:] = [(_buf['map'], MAP_WORDS * 2)]

    cases = []
    for tile in (0, 1, 17, 63):
        for owner in (0, 1):
            for mv in (0, 1, 2, 3, 4, 8, 0xC, 0xF, 0xFFFF):
                for scan in (0, 3, 10):
                    cases.append(_case(tile, owner, mv, scan,
                                       f't{tile}o{owner}v{mv:x}s{scan}'))
    t4spec.run_spec(SRC, 'FogUpdateTile_', 0x1e9a0, cases,
                    out_regs=(), init_emu=init,
                    watch=watch)
