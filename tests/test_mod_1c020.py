import os
import struct

import pytest

from wc1 import path, t4spec


pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')


LINES = 0x596A0
BUFFER_PTR = 0x59850
FONT_PTR = 0x5ACF0
LINE_CAP = 100
BUFFER_SIZE = 256


def test_t3_matches():
    t4spec.assert_t3_matches(path('src/mod_1c020'), ['blit_transparent_in_text_band.c', 'free_wrap_text_buffer.c'])


def test_reference_near_miss():
    t4spec.assert_ref_mismatch(path('src/mod_1c020'), ['wrap_text_in_place_reference.c'])


def test_wrap_text_in_place():
    watch = []
    scratch = {}

    def init_emu(emu):
        scratch['buffer'] = emu.alloc(BUFFER_SIZE, 16)
        scratch['font'] = emu.alloc(16, 16)
        watch[:] = [(LINES, 4 * LINE_CAP), (scratch['buffer'], BUFFER_SIZE)]

    def text_width(emu, log):
        font = emu.reg('eax')
        text = emu.reg('edx')
        width = len(emu.cstr(text, 64))
        log(font, text, width)
        return width

    def case(text, width, label=''):
        def setup(emu):
            emu.write(BUFFER_PTR, struct.pack('<I', scratch['buffer']))
            emu.write(FONT_PTR, struct.pack('<I', scratch['font']))
            emu.write(scratch['buffer'], (text + b'\0').ljust(BUFFER_SIZE, b'\0'))
            emu.write(LINES, struct.pack('<I', 0xDEADBEEF) * LINE_CAP)

        return t4spec.T4Case(args=(width & 0xFFFFFFFF,), setup=setup, label=label)

    def random_case(rng):
        words = [b'x' * rng.randint(1, 6) for _ in range(rng.randint(1, 6))]
        text = b' ' * rng.randrange(4) + words[0]
        for word in words[1:]:
            text += b' ' * rng.randint(1, 3) + word
        return case(text, rng.randint(0, 30))

    t4spec.run_spec(
        'src/mod_1c020/wrap_text_in_place_reference.c',
        'WrapTextInPlace_',
        0x1C020,
        cases=[
            case(b'', 8, 'empty input clears first slot only'),
            case(b'one two', 7, 'exact fit retains space'),
            case(b'one two', 6, 'one pixel over splits at prior space'),
            case(b'  one   two  three', 5, 'leading and repeated spaces'),
            case(b'one   ', 2, 'trailing spaces after an overflow'),
            case(b'   ', 8, 'all spaces with zero-padded lookahead'),
            case(b'abc def', 2, 'first word wider than limit'),
            case(b'a\tb c', 3, 'tab is not a delimiter'),
            case(b'a b', 0, 'zero width'),
            case(b'a b', -1, 'signed negative width'),
            case(b' '.join([b'x'] * 99), 1, 'last slot receives sentinel'),
            case(b' '.join([b'x'] * 100), 1, 'full table has no sentinel'),
        ],
        watch=watch,
        stubs=[t4spec.T4Stub(0x32060, log_regs=('eax', 'edx'), fn=text_width)],
        out_regs=(),
        init_emu=init_emu,
        log_cap=4096,
        seed=0x1C020,
        rand_cases=32,
        rand_gen=random_case,
    )
