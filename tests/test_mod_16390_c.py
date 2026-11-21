"""T4 differential tests for the dialog engine reference functions of mod_16390
(war.exe 0x16390..0x19020).  Each test runs the reference C function against
the original code at its war.exe address with call-logging callee stubs."""
import os
import struct

import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case, T4Stub

pytestmark = pytest.mark.skipif(
    not (os.path.exists(path('original', 'install', 'war.exe')) and os.environ.get('WATCOM')),
    reason='needs original/ and $WATCOM',
)

REGS = ('eax', 'edx', 'ebx', 'ecx')
LAYERS = 0x5aa90
DRAW_COLOR = 0x5ad30
DEFAULT_FONT = 0x55444
CUR_FONT = 0x5acf0
EDIT_BUFFER = 0x593e8
EDIT_CURSOR = 0x593ec
AUTO_REPEAT = 0x593ee
LEFT_HELD = 0x593fc
SETUP_QUIT = 0x5176a

A = {}
_BL = {}

REFS = [
    'dialog_draw_item_state_reference.c',
    'dialog_draw_items_reference.c',
    'dialog_draw_text_reference.c',
    'dialog_erase_text_reference.c',
    'dialog_item_loop_reference.c',
    'edit_field_draw_reference.c',
    'list_draw_reference.c',
    'list_scroll_by_reference.c',
]


def test_reference_files_still_mismatch():
    t4spec.assert_ref_mismatch(path('src/mod_16390'), REFS)


def F(name):
    if not _BL:
        _BL.update(t4spec.by_link_lenient())
    for ln in (name + '_', '_' + name, name):
        if ln in _BL:
            return _BL[ln]['addr']
    raise KeyError(name)


def init(emu):
    A['b'] = emu.alloc(0x1000, 16)


class _Watch:
    def __iter__(self):
        b = A['b']
        return iter([
            (b, 0x1000), (0x593e0, 0x20), (LAYERS, 0x240),
            (DRAW_COLOR, 1), (0x55438, 8), (CUR_FONT, 4),
            (0x5aa78, 1), (SETUP_QUIT, 4),
        ])


WATCH = _Watch()


def S(name, n=0, ret=0, fn=None, pop=0):
    return T4Stub(F(name), ret=ret, log_regs=REGS[:n], fn=fn, stack_pop=pop)


def dirty(e, log):
    log(*struct.unpack('<II', e.read(e.reg('eax'), 8)))
    return 0


def sel_text(e, log):
    log(e.reg('eax'), e.reg('edx'))
    return A['b'] + 0x310


def hit(e, log):
    log(e.reg('eax'), e.reg('edx'))
    return struct.unpack('<I', e.read(A['b'] + 0xf00, 4))[0]


def done(e, log):
    log(e.reg('eax'))
    return struct.unpack('<I', e.read(A['b'] + 0xf08, 4))[0]


def pump(e, log):
    log()
    b = A['b']
    e.write(LEFT_HELD, b'\0\0')
    e.write(b + 0xf00, e.read(b + 0xf04, 4))
    return 0


def it(t, fl=0, x=10, y=20, code=50, art=None, art2=None, text=None, id_=0, u=0, hot=0):
    b = A['b']
    art = b + 0x280 if art is None else art
    art2 = b + 0x288 if art2 is None else art2
    text = b + 0x300 if text is None else text
    return struct.pack('<HHhhHIIIHHH', t, fl, x, y, code, art, art2, text, id_, u, hot)


def END():
    return it(0xffff, x=0, y=0, code=0, art=0, art2=0, text=0)


def mk(e, items, params=(0,) * 8, layer=0, dx=5, dy=7):
    b = A['b']
    e.write(b, b'\0' * 0x1000)
    e.write(0x593e0, b'\0' * 0x20)
    e.write(LAYERS, b'\0' * 0xa0)
    e.write(DRAW_COLOR, b'\0')
    e.write(b, struct.pack(
        '<HhhIhhIIIIIII', layer, dx, dy, b + 0x200, 100, 60,
        b + 0x600, b + 0x440, 0, 0, b + 0x3c0, b + 0x400, b + 0x100,
    ))
    e.write(b + 0x100, b''.join(items))
    e.write(b + 0x200, struct.pack('<8i', *params))
    e.write(b + 0x280, struct.pack('<HHI', 40, 12, b + 0x700))
    e.write(b + 0x288, struct.pack('<HHI', 30, 10, b + 0x720))
    e.write(b + 0x2c0, b'\x20\x01\x08\x00')
    e.write(b + 0x300, b'Hello\0')
    e.write(b + 0x310, b'World\0')
    e.write(b + 0x320, b'Item\0')
    e.write(b + 0x340, b'Hi\0')
    e.write(b + 0x380, struct.pack('<4I', b + 0x300, 0, b + 0x310, 0xffffffff))
    e.write(b + 0x3c0, struct.pack('<6I', b + 0x280, 0, 0, 0, 0, 0))
    e.write(b + 0x400, b'\xff\xff')
    e.write(b + 0x440, b'\xff\xff')
    e.write(DEFAULT_FONT, struct.pack('<I', b + 0x2c0))
    e.write(CUR_FONT, struct.pack('<I', b + 0x2c0))
    e.write(LAYERS, struct.pack('<Hhh', 1, 30, 40))


def C(label, items, params=None, args=None, extra=None, stack=(), **kw):
    b = A['b']

    def setup(e):
        mk(e, items, params or (0,) * 8, **kw)
        if extra:
            extra(e)
    return T4Case(args=args if args is not None else (b, b + 0x100),
                  stack_args=stack, setup=setup, label=label)


def _gen(builders):
    its = iter(builders)
    return lambda rng: next(its)()


def run(name, addr, src, builders, stubs, ret=False):
    t4spec.run_spec(
        path('src', 'mod_16390', src), name, addr, watch=WATCH,
        stubs=stubs, out_regs=('eax',) if ret else (),
        init_emu=init, rand_cases=len(builders),
        rand_gen=_gen(builders),
    )


def test_list_draw():
    bl = []
    for s in (0, 1, 2, -1):
        bl.append(lambda s=s: C('sel%d' % s, [it(5, id_=0, text=A['b'] + 0x380), END()],
                                (s,) + (0,) * 7))
    bl.append(lambda: C('nolist', [it(0), END()]))
    run('ListDraw_', 0x163c8, 'list_draw_reference.c', bl,
        [S('FillRect', 4), S('TextSetColorBase', 1), S('DrawText', 3),
         S('LayerInvalidate', 1)])


def test_dialog_draw_items():
    bl = []
    for t in (0, 6, 7, 10, 9, 1, 2, 3, 8, 11, 5):
        bl.append(lambda t=t: C('t%d' % t, [it(t), END()], args=(A['b'],)))
    bl.append(lambda: C('mix', [it(0), it(3), it(8), it(5), it(1), END()],
                        args=(A['b'],)))
    run('DialogDrawItems_', 0x16520, 'dialog_draw_items_reference.c', bl,
        [S('BitmapBlitTransparentAll', 3), S('TextWidth', 2, 21), S('DrawText', 3),
         S('ListSelectedText', fn=sel_text), S('ListDraw', 1)])


def test_dialog_draw_item_state():
    bl = []
    for t in (0, 9, 1):
        for p in (0, 1):
            for f in (0, 1):
                bl.append(lambda t=t, p=p, f=f: C('t%d p%d f%d' % (t, p, f), [it(t), END()],
                                                  args=(A['b'], A['b'] + 0x100, p, f)))
    run('DialogDrawItemState_', 0x16d5c, 'dialog_draw_item_state_reference.c', bl,
        [S('BitmapBlitTransparentAll', 3), S('TextSetEscapeColors', 2),
         S('TextSetColorBase', 1), S('TextWidth', 2, 21), S('DrawText', 3),
         S('DirtyRectUnion', fn=dirty)])


def test_dialog_item_loop():
    def ex(held=0, h=1, post=1, dn=0, quit=0, rep=0):
        def f(e):
            b = A['b']
            e.write(LEFT_HELD, struct.pack('<H', held))
            e.write(b + 0xf00, struct.pack('<III', h, post, dn))
            e.write(SETUP_QUIT, struct.pack('<H', quit))
            e.write(AUTO_REPEAT, struct.pack('<H', rep))
        return f
    cs = [
        ('btn', lambda: [it(0), END()], ex()),
        ('hover', lambda: [it(0, fl=2), END()], ex(1, 1, 1)),
        ('hoveroff', lambda: [it(0), END()], ex(1, 1, 0)),
        ('nohit', lambda: [it(0), END()], ex(1, 0, 1)),
        ('list', lambda: [it(5), END()], ex()),
        ('listheld', lambda: [it(5), END()], ex(1, 1, 1)),
        ('done', lambda: [it(0), END()], ex(1, 1, 1, 1)),
        ('quit', lambda: [it(0), END()], ex(1, 1, 1, 0, 1)),
        ('skip', lambda: [it(4), it(3), it(8), END()], ex()),
        ('rep', lambda: [it(0, fl=2), END()], ex(1, 0, 1, 0, 0, 1)),
    ]
    bl = [(lambda l=l, i=i, x=x: C(l, i(), args=(A['b'],), extra=x)) for l, i, x in cs]
    run('DialogItemLoop_', 0x1700c, 'dialog_item_loop_reference.c', bl,
        [S('DialogItemHitTest', fn=hit), S('ListSelectAtMouse', 2),
         S('DialogHighlightOn'), S('DialogHighlightOff'), S('DialogDrawItemState', 4),
         S('UiEventPumpNet', fn=pump), S('DialogPreviewCursor'), S('ScreenUpdate'),
         S('DialogCheckDone', fn=done), S('DialogActivateItem', 2)], ret=True)


def _text_cases():
    bl = []
    for t in (3, 8, 11, 0):
        bl.append(lambda t=t: C('t%d' % t, [it(t), END()], args=(A['b'],)))
    bl.append(lambda: C('mix', [it(3, x=60), it(8), it(11, x=30, y=40), END()],
                        args=(A['b'],)))
    return bl


def test_dialog_erase_text():
    run('DialogEraseText_', 0x1718c, 'dialog_erase_text_reference.c', _text_cases(),
        [S('ListSelectedText', fn=sel_text), S('TextWidth', 2, 21), S('FillRect', 4),
         S('DirtyRectUnion', fn=dirty)])


def test_dialog_draw_text():
    run('DialogDrawText_', 0x172e4, 'dialog_draw_text_reference.c', _text_cases(),
        [S('TextSetColorBase', 1), S('ListSelectedText', fn=sel_text),
         S('TextWidth', 2, 21), S('DrawText', 3), S('DirtyRectUnion', fn=dirty)])


def test_edit_field_draw():
    bl = []
    for x, y, w, h in ((20, 30, 60, 12), (5, 10, 80, 16)):
        r_words = struct.unpack('<3I', struct.pack('<hhhhhh', x, y, x + w - 1, y + h - 1, w, h))
        for caret in (0, 1):
            for cur in (0, 3):
                def extra(e, cur=cur):
                    b = A['b']
                    e.write(b + 0x500, b'Hello\0')
                    e.write(EDIT_BUFFER, struct.pack('<I', b + 0x500))
                    e.write(EDIT_CURSOR, struct.pack('<H', cur))
                bl.append(lambda r_words=r_words, caret=caret, cur=cur, extra=extra: C(
                    'c%d_cur%d' % (caret, cur), [END()], args=(), stack=r_words + (caret,),
                    extra=extra))
    run('EditFieldDraw_', 0x174c0, 'edit_field_draw_reference.c', bl,
        [S('FillRect', 4), S('TextSetColorBase', 1), S('DrawText', 3),
         S('TextWidth', 2, 21), S('VLine', 3), S('DirtyRectUnion', fn=dirty)])


def test_list_scroll_by():
    def lst(e):
        b = A['b']
        e.write(b + 0x380, struct.pack('<4I', b + 0x300, b + 0x310, b + 0x320, 0xffffffff))
    bl = []
    for d in (1, -5, 10, 0):
        bl.append(lambda d=d: C('d%d' % d, [it(5, id_=1, text=A['b'] + 0x380), END()],
                                (0, 2, 0, 0, 0, 0, 0, 0), args=(A['b'], d), extra=lst))
    bl.append(lambda: C('nolist', [it(0), END()], args=(A['b'], 1)))
    run('ListScrollBy_', 0x17c4c, 'list_scroll_by_reference.c', bl, [S('ListDraw', 2)])
