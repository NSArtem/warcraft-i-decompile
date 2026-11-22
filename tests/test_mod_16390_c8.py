import os
import struct

import pytest

from wc1 import path, t4spec

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')


def test_reference_remains_near_miss():
    t4spec.assert_ref_mismatch(path('src/mod_16390'), ['outro_show_credits_reference.c'])


def test_outro_show_credits():
    x, y, width = 0x5AB7C, 0x5AB7E, 0x5AB80
    done, is_orc, frame, tick = 0x59430, 0x59432, 0x59434, 0x59436
    handlers, cur_bitmap, cur_font = 0x59400, 0x55438, 0x5ACF0
    palette = 0x58F20
    watch = []
    scratch = {}

    def word(e, addr):
        return struct.unpack('<H', e.read(addr, 2))[0]

    def dword(e, addr):
        return struct.unpack('<I', e.read(addr, 4))[0]

    def put_word(e, addr, value):
        e.write(addr, struct.pack('<H', value & 0xffff))

    def bitmap(e, addr, w, h):
        e.write(addr, struct.pack('<HHI', w, h, 0))

    def init_emu(e):
        scratch['credits'] = e.alloc(0x1000, 16)
        scratch['grp'] = e.alloc(16, 16)
        scratch['font'] = e.alloc(16, 16)
        scratch['pumps'] = e.alloc(4, 4)
        watch[:] = [
            (scratch['credits'], 0x1000), (palette, 768),
            (handlers, 0x28), (done, 8), (0x5AB7A, 10),
            (0x5AB9E, 10), (0x5ABAC, 6), (scratch['pumps'], 4),
        ]

    def make_case(label, orc, initial_y, bottom_extent, rows, finished, text):
        def setup(e):
            e.write(handlers, bytes(0x28))
            e.write(done, struct.pack('<4H', finished, orc, 99, 99))
            e.write(0x50088, struct.pack('<H', orc))
            e.write(0x5AB7A, struct.pack('<5H', 1, 7, initial_y, 42, bottom_extent & 0xffff))
            e.write(0x5AB9E, bytes(18) + b'\x01\x00')
            e.write(cur_bitmap, bytes(4))
            e.write(cur_font, struct.pack('<I', scratch['font']))
            e.write(scratch['font'], bytes((0, 0, rows, 0)))
            e.write(palette, bytes(768))
            e.write(scratch['credits'], b'\xa5' * 0x1000)
            put_word(e, scratch['pumps'], 0)
        case = t4spec.T4Case(setup=setup, label=label)
        return case, text

    def resource_read(e, log):
        dest = e.reg('eax')
        log(dest, e.reg('edx'))  # NULL, global palette, or fixed emulated heap buffer
        if dest == 0:
            return scratch['grp']
        if dest == palette:
            e.write(dest, bytes(range(256)) * 3)
        else:
            e.write(dest, credits_text)
        return dest

    def grp_frame(e, log):
        log(e.reg('eax'), e.reg('edx') & 0xff)
        bitmap(e, e.reg('ebx'), 24, 16)
        return 0

    def layer_add(e, log):
        dest, rect = e.reg('eax'), e.reg('edx')
        layer, res = e.reg('ebx') & 0xffff, e.reg('ecx') & 0xffff
        blit = dword(e, e.reg('esp') + 4)
        log(*struct.unpack('<6H', e.read(rect, 12)), layer, res, blit)
        bitmap(e, dest, layer, 200 if layer == 16 else 128)
        return 0

    def load_panel(e, log):
        log(4, 5)
        bitmap(e, e.reg('eax'), 4, 5)
        return e.reg('eax')

    def bitmap_arg(e, log):
        log(*struct.unpack('<2H', e.read(e.reg('eax'), 4)))
        return 0

    def text_page(e, log):
        src = e.reg('edx')
        log(word(e, e.reg('eax')), src - scratch['credits'])
        return src + (e.read(src, 1) != b'\x00')

    def event_pump(e, log):
        log(word(e, y), word(e, frame), word(e, tick), word(e, done))
        n = word(e, scratch['pumps']) + 1
        put_word(e, scratch['pumps'], n)
        if dword(e, handlers):
            put_word(e, done, 1)
        if n == 1:
            put_word(e, frame, 20)
        put_word(e, tick, 1 if n == 1 else 0x8000 if n == 2 else 2)
        return 0

    def invalidate(e, log):
        layer = e.reg('eax') & 0xff
        log(layer, word(e, y), word(e, 0x5AB7A))
        return 0

    def show_frame(e, log):
        log(e.reg('eax'), e.reg('edx'), word(e, e.reg('ebx')))
        return 0

    def bitmap_clear(e, log):
        log(e.reg('eax') & 0xff, word(e, dword(e, cur_bitmap)))
        return 0

    # Observe semantic arguments. For stack-local rectangles and bitmaps, log
    # their contents instead of comparing the two implementations' addresses.
    stubs = (
        t4spec.T4Stub(0x184CC, log_regs=(), fn=event_pump),
        t4spec.T4Stub(0x18810, log_regs=('eax', 'edx'), fn=text_page),
        t4spec.T4Stub(0x18890, log_regs=('eax', 'edx', 'ebx'), fn=show_frame),
        t4spec.T4Stub(0x1C10C, log_regs=('eax',), fn=load_panel),
        t4spec.T4Stub(0x1C2BC, log_regs=('eax',)),
        t4spec.T4Stub(0x21CF0, log_regs=('eax',), fn=bitmap_arg),
        t4spec.T4Stub(0x21D0C, log_regs=('eax', 'edx', 'ebx', 'ecx'), fn=layer_add, stack_pop=4),
        t4spec.T4Stub(0x267E0, log_regs=()),
        t4spec.T4Stub(0x267FC, log_regs=('eax',)),
        t4spec.T4Stub(0x26958, log_regs=('eax',)),
        t4spec.T4Stub(0x271F4, log_regs=()),
        t4spec.T4Stub(0x31870, log_regs=('eax', 'edx')),
        t4spec.T4Stub(0x31DCC, log_regs=('eax', 'edx', 'ebx')),
        t4spec.T4Stub(0x31F70, log_regs=('eax',), fn=invalidate),
        t4spec.T4Stub(0x31FC0, log_regs=('eax',), fn=bitmap_clear),
        t4spec.T4Stub(0x32060, ret=0x12340031, log_regs=('eax', 'edx')),
        t4spec.T4Stub(0x321E8, log_regs=()),
        t4spec.T4Stub(0x32558, log_regs=('eax',), fn=lambda e, log: (log(e.reg('eax')), scratch['credits'])[1]),
        t4spec.T4Stub(0x32740, log_regs=('eax', 'edx'), fn=resource_read),
        t4spec.T4Stub(0x32780, log_regs=('eax',)),
        t4spec.T4Stub(0x32E80, log_regs=('eax',)),
        t4spec.T4Stub(0x32FB0, log_regs=('eax',)),
        t4spec.T4Stub(0x33110, log_regs=('eax', 'edx', 'ebx'), fn=grp_frame),
        t4spec.T4Stub(0x33150, log_regs=('eax', 'edx', 'ebx')),
    )

    for case, credits_text in (
        make_case('human: immediate scroll exit, empty credits, already done', 0, 33, -2, 9, 1, b'\x00'),
        make_case('human: second page drawn without an emblem frame', 0, 31, 0, 9, 1, b'A\x00'),
        make_case('orc: tick gates, frame wrap, page scroll and final pump', 1, 63, 0, 11, 0, b'AB\x00'),
    ):
        t4spec.run_spec(
            'src/mod_16390/outro_show_credits_reference.c',
            'OutroShowCredits_', 0x18B64, (case,),
            watch=watch, stubs=stubs, out_regs=(), init_emu=init_emu,
            log_cap=8192,
        )
