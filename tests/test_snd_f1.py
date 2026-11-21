import os
import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = path('src/snd')
TABLE = {}


def _init(emu):
    # anim_table: 0x200 words; first words are byte offsets into table
    TABLE['tbl'] = emu.alloc(0x400, 16)
    TABLE['obj'] = emu.alloc(0x40, 16)


def _mk_table(emu):
    t = TABLE['tbl']
    data = bytearray()
    for i in range(0x200):
        data += ((i * 6 + 0x20) & 0xFFFF).to_bytes(2, 'little')
    # make first 0x80 entries small offsets so idx stays within table
    for i in range(0x80):
        data[i * 2:i * 2 + 2] = ((i * 2) & 0xFFFF).to_bytes(2, 'little')
    emu.write(t, bytes(data))
    emu.write(TABLE['ptr'], t.to_bytes(4, 'little'))


def _init2(emu):
    _init(emu)
    TABLE['ptr'] = None


def test_t3_files_match():
    files = ['anim_table_free.c', 'anim_table_load.c']
    t4spec.assert_t3_matches(SRC, files)


def test_ref_mismatch():
    t4spec.assert_ref_mismatch(SRC, ['bullet_start_anim_reference.c', 'fn_26360_reference.c'])


def _cases(off_field, kind):
    def setup_for(fieldval, sound):
        def setup(emu):
            t = TABLE['tbl']
            data = bytearray()
            for i in range(0x200):
                data += ((i * 4) & 0xFFFF).to_bytes(2, 'little')
            emu.write(t, bytes(data))
            o = TABLE['obj']
            emu.write(o, b'\xAA' * 0x40)
            emu.write(o + off_field, bytes([fieldval]))
        return setup
    out = []
    for fv in (0, 1, 5, 0x10):
        for s in (0, 1, 3, 7):
            out.append((fv, s, setup_for(fv, s)))
    return out


def _run(name, link, addr, off_field, base_off):
    def init(emu):
        _init(emu)
        TABLE['ptr'] = None

    cases = []
    for fv, s, setup in _cases(off_field, name):
        cases.append(T4Case(args=(0, s), setup=setup, label=f'f{fv}_s{s}'))
    return cases


def _anim_ptr_sym(emu):
    pass


def _build(addr, link, field_off, out_off):
    def init(emu):
        _init(emu)

    def mk(fv, s):
        def setup(emu):
            t = TABLE['tbl']
            o = TABLE['obj']
            data = b''.join(((i * 4) & 0xFFFF).to_bytes(2, 'little') for i in range(0x200))
            emu.write(t, data)
            emu.write(o, b'\xAA' * 0x40)
            emu.write(o + field_off, bytes([fv]))
        return setup

    return init, mk


def test_fn_26360():
    init, mk = _build(0x26360, 'fn_26360_', 0x1b, 4)

    def init_emu(emu):
        init(emu)

    cases = []
    for fv in (0, 1, 5, 0x10):
        for s in (0, 1, 3, 7):
            def setup(emu, fv=fv, s=s):
                mk(fv, s)(emu)
            cases.append(T4Case(args=(TABLE_OBJ(), s), setup=setup, label=f'{fv}_{s}'))
    if not os.path.exists(os.path.join(SRC, 'fn_26360.c')):
        pytest.skip('fn_26360.c not present')
    t4spec.run_spec(os.path.join(SRC, 'fn_26360.c'), 'fn_26360_', 0x26360, cases,
                    out_regs=(), init_emu=init_emu,
                    watch=[(0, 0)] if False else [])


def TABLE_OBJ():
    return TABLE.get('obj', 0)


def test_bullet_start_anim():
    init, mk = _build(0x26390, 'BulletStartAnim_', 0, 0xa)

    cases = []
    for fv in (0, 1, 5, 0x10):
        for s in (0, 1, 3, 7):
            def setup(emu, fv=fv, s=s):
                mk(fv, s)(emu)
            cases.append(T4Case(args=(TABLE_OBJ(), s), setup=setup, label=f'{fv}_{s}'))
    if not os.path.exists(os.path.join(SRC, 'bullet_start_anim.c')):
        pytest.skip('bullet_start_anim.c not present')
    t4spec.run_spec(os.path.join(SRC, 'bullet_start_anim.c'), 'BulletStartAnim_', 0x26390, cases,
                    out_regs=(), init_emu=init)
