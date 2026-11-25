import os
import struct

import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case, T4Stub


pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = 'src/mod_2b400'
DEMO = 0x5152C
STATUS_TEXT = 0x55148
CUR_BITMAP = 0x55438
CUR_FONT = 0x5ACF0
CACHE = 0x5A380
HELP_GOLD = 0x5A422
HELP_LUMBER = 0x5A424
TARGET_LUMBER = 0x50060
TARGET_GOLD = 0x50074
DISPLAY_LUMBER = 0x5A418
DISPLAY_GOLD = 0x5A41C


def _u16(value):
    return struct.pack('<H', value)


def _u32(value):
    return struct.pack('<I', value & 0xFFFFFFFF)


def _read32(e, addr):
    return struct.unpack('<I', e.read(addr, 4))[0]


def _text(e, addr):
    text = e.cstr(addr, 64)
    return text.encode('ascii') if isinstance(text, str) else bytes(text)


def _strcmp(e, log):
    lhs = _text(e, e.reg('eax'))
    rhs = _text(e, e.reg('edx'))
    return ((lhs > rhs) - (lhs < rhs)) & 0xFFFFFFFF


def _strcpy(e, log):
    dst = e.reg('eax')
    e.write(dst, _text(e, e.reg('edx')) + b'\0')
    return dst


def _draw_text(e, log):
    # Log the string contents: the two builds need not use the same stack slot.
    text = _text(e, e.reg('ebx'))
    log(e.reg('eax') & 0xFFFF, e.reg('edx') & 0xFFFF, len(text), *text)
    return 0


def _sprintf_decimal(e, log):
    sp = e.reg('esp')
    dst, fmt, value = struct.unpack('<IIi', e.read(sp + 4, 12))
    log(fmt, value)
    assert _text(e, fmt) == b'%d'
    text = str(value).encode('ascii')
    e.write(dst, text + b'\0')
    return len(text)


def _animate_counter(e, log):
    displayed = e.reg('ecx')
    target = _read32(e, e.reg('esp') + 4)
    log(e.reg('eax'), e.reg('edx') & 0xFFFF, e.reg('ebx') & 0xFFFF,
        displayed, target)
    # A stand-in for the callee's write, not a model of its animation.
    e.write(displayed, _u32(target))
    return 0


def _blit_background(e, log):
    log(e.reg('eax') & 0xFFFF, e.reg('edx') & 0xFFFF, e.reg('ebx'))
    return 0


def test_reference_codegen_guard():
    t4spec.assert_ref_mismatch(path('src/mod_2b400'), ['resource_counters_update_reference.c', 'status_bar_draw_text_reference.c'])


def test_status_bar_draw_text():
    cases = []
    watch = [(CACHE, 32), (CUR_BITMAP, 4), (CUR_FONT, 4)]

    def init_emu(emu):
        explicit = emu.alloc(64, 16)
        fallback = emu.alloc(64, 16)

        def add(label, text, default, cached, flag, demo=0, lumber=0, gold=0):
            mem = {
                DEMO: _u16(demo),
                STATUS_TEXT: _u32(fallback if default is not None else 0),
                explicit: (text or b'').ljust(64, b'\0'),
                fallback: (default or b'').ljust(64, b'\0'),
                CACHE: cached + b'\0' + b'\xA5' * (31 - len(cached)),
                CUR_BITMAP: _u32(0x5A360),
                CUR_FONT: _u32(0),
                HELP_LUMBER: _u16(lumber),
                HELP_GOLD: _u16(gold),
            }
            cases.append(T4Case(args=(explicit if text is not None else 0, flag),
                                mem=mem, label=label))

        add('nonzero demo suppresses redraw', b'New', None, b'Old', 1, demo=0x100)
        add('explicit text overrides fallback', b'Build Farm', b'Other', b'Old', 0)
        add('matching text ignores a cost flag change', b'Build Farm', None, b'Build Farm', 1)
        add('null argument uses global text and draws costs', None, b'Build Road',
            b'Old', 0x80, lumber=65535, gold=32768)
        add('cost flag uses only DL', b'Build Wall', None, b'Old', 0x100,
            lumber=2, gold=3)
        add('zero and one-digit costs', b'Build', None, b'Old', 1, lumber=0, gold=7)
        add('explicit empty string clears despite fallback and cost flag', b'',
            b'Other', b'Old', 1)
        add('both pointers null clears stale text', None, None, b'Old', 1)
        add('both pointers null with empty cache is a no-op', None, None, b'', 0)

    t4spec.run_spec(
        f'{SRC}/status_bar_draw_text_reference.c', 'StatusBarDrawText_', 0x2B67C,
        cases, init_emu=init_emu, watch=watch, out_regs=(),
        stubs=(
            T4Stub(0x329D0, log_regs=('eax', 'edx'), fn=_strcmp),
            T4Stub(0x31CEF, log_regs=('eax', 'edx'), fn=_strcpy),
            T4Stub(0x33B00, log_regs=('eax', 'edx', 'ebx'), fn=_blit_background),
            T4Stub(0x32030, log_regs=('eax',)),
            T4Stub(0x31DCC, log_regs=('eax', 'edx', 'ebx'), fn=_draw_text),
            T4Stub(0x326F0, log_regs=('eax', 'edx', 'ebx')),
            T4Stub(0x31BE2, log_regs=(), fn=_sprintf_decimal),
            T4Stub(0x349F0, log_regs=('eax',)),
        ),
    )


def test_resource_counters_update():
    def case(label, demo, displayed_lumber, displayed_gold, lumber, gold):
        return T4Case(label=label, mem={
            DEMO: _u16(demo),
            DISPLAY_LUMBER: _u32(displayed_lumber),
            DISPLAY_GOLD: _u32(displayed_gold),
            TARGET_LUMBER: _u32(lumber) + _u32(0x12345678),
            TARGET_GOLD: _u32(gold) + _u32(0x87654321),
            CUR_BITMAP: _u32(0x5A408),
            CUR_FONT: _u32(0),
        })

    cases = [
        case('demo suppresses mismatched counters', 0x100, 0, 0, 10, 20),
        case('both displayed values already match', 0, 10, 20, 10, 20),
        case('lumber only changed', 0, 9, 20, 10, 20),
        case('gold only changed', 0, 10, 21, 10, 20),
        case('both changed', 0, 40, 0, 0, 55),
        case('full dword comparison and forwarding', 0, 1, 2, 0x10001, 0x80000002),
        case('equal high-bit values do not redraw', 0, 0xFFFFFFFF, 0x80000000,
             0xFFFFFFFF, 0x80000000),
    ]
    t4spec.run_spec(
        f'{SRC}/resource_counters_update_reference.c', 'ResourceCountersUpdate_',
        0x2B824, cases, out_regs=(),
        watch=((DISPLAY_LUMBER, 4), (DISPLAY_GOLD, 4), (CUR_BITMAP, 4), (CUR_FONT, 4)),
        stubs=(
            T4Stub(0x33B00, log_regs=('eax', 'edx', 'ebx'), fn=_blit_background),
            T4Stub(0x32030, log_regs=('eax',)),
            T4Stub(0x2B7C4, log_regs=('eax', 'edx', 'ebx', 'ecx'),
                   fn=_animate_counter, stack_pop=4),
            T4Stub(0x349F0, log_regs=('eax',)),
        ),
    )
