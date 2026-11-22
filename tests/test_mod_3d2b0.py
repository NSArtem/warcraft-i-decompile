import os
import struct

import pytest

from wc1 import path, t4spec


pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')


DEFAULT_FONT = 0x55444
CUR_FONT = 0x5ACF0
BUTTON = struct.Struct('<II4shhhh')


def test_reference_still_mismatches():
    t4spec.assert_ref_mismatch(path('src/mod_3d2b0'), ['crit_err_draw_buttons_reference.c'])


def test_crit_err_draw_buttons():
    cases = []
    watch = []
    widths_by_label = {}

    def init_emu(emu):
        buttons = emu.alloc(5 * BUTTON.size, 4)
        font = emu.alloc(16, 4)
        old_font = emu.alloc(16, 4)
        labels = []
        bitmaps = []
        for text, width in [(b'OK\0', 6), (b'Retry\0', 10), (b'Wide\0', 9)]:
            label = emu.alloc(len(text), 4)
            emu.write(label, text)
            labels.append(label)
            # Only AX contributes to the layout calculation.
            widths_by_label[label] = 0x12340000 | width
        for width in (15, 32, 5, -4):
            bitmap = emu.alloc(16, 4)
            emu.write(bitmap, struct.pack('<h', width) + bytes(14))
            bitmaps.append(bitmap)

        def row(label, bitmap, x, y):
            return BUTTON.pack(label, bitmap, b'\x11\x22\x33\x44', x, y, 1234, -2345)

        end = row(labels[0], 0, 7, 8)
        after_end = row(labels[0], bitmaps[0], 19, 20)
        first = row(labels[0], bitmaps[0], -12, -8)
        icon = row(0, bitmaps[1], -32768, 32767)
        last = row(labels[1], bitmaps[2], 32767, 32766)
        signed_width = row(labels[2], bitmaps[3], -32768, 0)
        watch[:] = [(CUR_FONT, 4), (buttons, 5 * BUTTON.size)]

        def add_case(label, selected, entries):
            image = b''.join([*entries, end, after_end]).ljust(5 * BUTTON.size, b'\xa5')
            cases.append(t4spec.T4Case(
                label=label,
                args=(selected & 0xFFFFFFFF, buttons, 0xE1, 0x93),
                mem={DEFAULT_FONT: struct.pack('<I', font),
                     CUR_FONT: struct.pack('<I', old_font), buttons: image},
            ))

        add_case('empty array resets font and ignores sentinel label', 0, [])
        add_case('first row selected, positive odd width difference', 0, [first])
        add_case('selected icon blits without text', 0, [icon])
        add_case('selection counts unlabeled rows; negative odd difference and y wrap',
                 2, [first, icon, last])
        add_case('negative selection; signed bitmap width and x wrap', -1, [signed_width])

    def text_width(emu, log):
        font, label = emu.reg('eax'), emu.reg('edx')
        log(font, label)
        return widths_by_label[label]

    t4spec.run_spec(
        'src/mod_3d2b0/crit_err_draw_buttons_reference.c',
        'CritErrDrawButtons_', 0x3D2B0, cases,
        watch=watch, out_regs=(), init_emu=init_emu,
        stubs=(
            t4spec.T4Stub(0x33B00, log_regs=('eax', 'edx', 'ebx')),
            t4spec.T4Stub(0x32060, log_regs=('eax', 'edx'), fn=text_width),
            t4spec.T4Stub(0x32030, log_regs=('eax',)),
            t4spec.T4Stub(0x31DCC, log_regs=('eax', 'edx', 'ebx')),
        ),
    )
