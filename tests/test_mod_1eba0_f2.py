import os
import struct

import pytest

from wc1 import path, t4spec


pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')


def words(*values):
    return struct.pack('<' + 'H' * len(values), *(v & 0xffff for v in values))


def dword(value):
    return struct.pack('<I', value)


def test_t3_matches():
    t4spec.assert_t3_matches(path('src/mod_1eba0'), ['minimap_begin_scroll_input.c', 'minimap_end_scroll_input.c', 'minimap_issue_order.c', 'minimap_panel_free.c', 'minimap_panel_init.c', 'minimap_scroll_from_mouse.c'])


def test_reference_mismatch():
    t4spec.assert_ref_mismatch(path('src/mod_1eba0'), ['minimap_draw_terrain_reference.c', 'minimap_redraw_reference.c', 'minimap_screen_to_tile_reference.c'])


def test_minimap_draw_terrain():
    buf = {}
    watch = []
    dest_size = 0xa000

    def init_emu(e):
        for name, size in [('dest', dest_size), ('fog', 8192), ('tiles', 8192),
                           ('cells', 2048 * 8), ('pixels', 0x20000)]:
            buf[name] = e.alloc(size, 16)
        watch[:] = [(buf['dest'], dest_size)]

    def case(label, cheat, pitch, offset, fog_values):
        def setup(e):
            e.write(0x51214, dword(cheat))
            e.write(0x5297a, words(0xa555, pitch, 0x6bbb) + dword(buf['dest']))
            e.write(0x599f8, words(offset))
            for addr, name in [(0x58570, 'pixels'), (0x58578, 'fog'),
                               (0x58584, 'tiles'), (0x5858c, 'cells')]:
                e.write(addr, dword(buf[name]))
            e.write(buf['dest'], b'\xa5' * dest_size)
            e.write(buf['fog'], words(*(fog_values[(i + i // 64) % len(fog_values)]
                                        for i in range(4096))))
            indices = (0, 1, 17, 0x7ff, 0x1f0, 0x400, 0x253)
            e.write(buf['tiles'], words(*(indices[i % len(indices)] | ((i % 8) << 11)
                                          for i in range(4096))))
            cells = bytearray()
            for i in range(2048):
                cells.extend(words((i << 5) | (i & 0x1f), 0x2468, 0xa9cc, 0x4321))
            e.write(buf['cells'], bytes(cells))
            e.write(buf['pixels'], bytes((i * 29 + i // 64 * 17 + i // 4096 * 11) & 0xff
                                         for i in range(0x20000)))
        return t4spec.T4Case(setup=setup, label=label)

    t4spec.run_spec(
        'src/mod_1eba0/minimap_draw_terrain_reference.c', 'MinimapDrawTerrain_', 0x1ec6c,
        [case('mixed fog; padded rows', 0x80000002, 79, 13, (0, 1, 0x1f, 0xffe0, 0x8000, 0x8020)),
         case('reveal bypasses fog; packed rows', 1, 64, 0x8100, (0x1f,)),
         case('signed negative pitch', 0, -80, 5100, (0, 3, 0x20)),
         case('all cells obscured', 0, 64, 1, (0x8001,))],
        watch=watch, out_regs=(), init_emu=init_emu,
    )


def test_minimap_redraw():
    buf = {}
    watch = [(0x599fa, 6), (0x55438, 4), (0x5ad30, 1)]
    stride = 0x5c

    def init_emu(e):
        buf['units'] = e.alloc(200 * stride, 16)
        buf['colors'] = e.alloc(201, 16)
        watch.extend([(buf['colors'], 201)])

    def record_rect(e, log):
        log(*(e.reg(r) for r in ('eax', 'edx', 'ebx', 'ecx')))
        pos = e.read(buf['colors'], 1)[0]
        e.write(buf['colors'] + 1 + pos, e.read(0x5ad30, 1))
        e.write(buf['colors'], bytes([pos + 1]))

    def case(label, force=0, count=2, state=4, scroll=(6, 9), last=(6, 9), markers=False):
        def setup(e):
            units = bytearray(200 * stride)
            for i in range(200):
                struct.pack_into('<H', units, i * stride + 0x10, 0x200)

            def unit(i, x, y, typ, owner, f10=0, fe=0, status=0):
                off = i * stride
                units[off + 0xa:off + 0x12] = words(x, y, fe, f10)
                units[off + 0x1b] = typ
                units[off + 0x1e] = owner
                units[off + 0x36:off + 0x38] = words(status)

            if markers:
                unit(0, 1, 2, 1, 0, status=1)
                unit(1, 4, 5, 0, 1)
                unit(2, 6, 7, 0, 2, f10=1)
                unit(3, 8, 9, 0, 3, f10=8)
                unit(4, 10, 11, 0, 4, fe=0x100)
                unit(5, 12, 13, 0, 2, status=1)
                unit(199, -32768, 32767, 1, 4, f10=0x8000, fe=0x200)
            e.write(buf['units'], bytes(units))
            e.write(buf['colors'], bytes(201))
            e.write(0x59640, dword(buf['units']))
            e.write(0x58db0, dword(buf['units']))
            e.write(0x50d80, words(state))
            e.write(0x500d0, words(*scroll))
            e.write(0x599fa, words(count, last[1], last[0]))
            e.write(0x599e0, words(-7, 20))
            e.write(0x55438, dword(0))
            e.write(0x5ad30, b'\x77')
            e.write(0x51808, bytes([0xa0, 0xa1, 0xa2, 0xa3, 0xa4]))
            e.write(0x51abc, words(1, 2, 0xffff, 0x8000))
        # The unchanged-scroll exit guarantees zero only in AX; arrange
        # equal upper halves for the full-EAX differential comparison.
        return t4spec.T4Case(args=(force,), regs_in={'esi': 0}, setup=setup, label=label)

    t4spec.run_spec(
        'src/mod_1eba0/minimap_redraw_reference.c', 'MinimapRedraw_', 0x1ed2c,
        [case('unchanged scroll throttles refresh'),
         case('zero countdown wraps and still throttles', count=0),
         case('expired countdown but redraw state too low', count=1, state=3),
         case('expired countdown redraws without eligible units', count=1),
         case('x scroll changed', scroll=(7, 9)),
         case('y scroll changed', scroll=(6, 10)),
         case('forced but redraw state too low', force=1, state=3),
         case('forced redraw with unsigned state and mixed unit filters', force=0xffff,
              state=0x8000, scroll=(0, 32767), last=(0, 32767), markers=True)],
        watch=watch, out_regs=('eax',), init_emu=init_emu,
        stubs=(t4spec.T4Stub(0x1ec6c, log_regs=()),
               t4spec.T4Stub(0x326a0, log_regs=('eax', 'edx', 'ebx', 'ecx'), fn=record_rect),
               t4spec.T4Stub(0x348c0, log_regs=('eax', 'edx', 'ebx', 'ecx'), fn=record_rect)),
    )


def test_minimap_screen_to_tile():
    buf = {}
    watch = []

    def init_emu(e):
        buf['xy'] = e.alloc(4, 16)
        watch[:] = [(buf['xy'], 4)]

    def case(label, origin, size, coords):
        def setup(e):
            e.write(0x599ec, words(*origin, 0x7abc, 0x8003, *size))
            e.write(buf['xy'], words(*coords))
        return t4spec.T4Case(setup=setup, label=label)

    def init_args(e):
        init_emu(e)
        for c in cases:
            c.args = (buf['xy'], buf['xy'] + 2)

    cases = [case('one pixel before each origin', (137, 21), (64, 47), (136, 20)),
             case('exact origin', (137, 21), (64, 47), (137, 21)),
             case('independent interior maxima', (137, 21), (64, 47), (200, 67)),
             case('exact upper bounds', (137, 21), (64, 47), (201, 68)),
             case('negative x, y above bound', (137, 21), (64, 47), (100, 90)),
             case('x above bound, negative y', (137, 21), (64, 47), (250, 5)),
             case('subtraction wraps in both directions', (1, -1), (64, 47), (-32768, 32767)),
             case('zero width and negative height', (-9, -5), (0, -2), (-9, 3))]
    t4spec.run_spec(
        'src/mod_1eba0/minimap_screen_to_tile_reference.c', 'MinimapScreenToTile_', 0x1eec8,
        cases, watch=watch, out_regs=(), init_emu=init_args,
    )
