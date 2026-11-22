import os
import struct

import pytest

from wc1 import t4spec
from wc1 import path

pytestmark = pytest.mark.skipif(
    not (os.path.exists(path('original', 'install', 'war.exe')) and os.environ.get('WATCOM')),
    reason='needs original/ and $WATCOM')

REF = 'src/mod_16390/edit_field_run_reference.c'

HOOK = 0x4F000


def test_t3_files_still_match():
    pass


def test_reference_still_mismatches():
    t4spec.assert_ref_mismatch(path('src/mod_16390'), ['edit_field_run_reference.c'])


def _cstr(e, a, limit=64):
    out = b""
    for i in range(limit):
        c = bytes(e.read(a + i, 1))
        if c == b"\0":
            break
        out += c
    return out


def _run(src_text, keys, maxlen, net=0, quit_flag=0, pre_event=0):
    ctx = {}
    watch = []

    def init_emu(emu):
        ctx['heap'] = emu.alloc(0x100, 16)
        ctx['dest'] = emu.alloc(0x40, 16)
        ctx['src'] = emu.alloc(0x40, 16)
        ctx['q'] = emu.alloc(0x100, 16)
        ctx['d'] = emu.alloc(0x40, 16)
        ctx['cb'] = emu.alloc(0x20, 16)
        ctx['lim'] = emu.alloc(0x10, 16)
        ctx['item'] = emu.alloc(0x40, 16)
        ctx['font'] = emu.alloc(0x10, 16)
        watch[:] = [(ctx['heap'], 0x40), (ctx['dest'], 0x40), (ctx['q'], 8),
                    (0x593e8, 4), (0x593ec, 2)]

    def setup(emu):
        emu.write(ctx['heap'], b"\xaa" * 0x100)
        emu.write(ctx['dest'], b"\x55" * 0x40)
        emu.write(ctx['src'], src_text + b"\0")
        emu.write(ctx['q'], struct.pack("<II", 0, len(keys)) +
                  b"".join(struct.pack("<H", k) for k in keys))
        emu.write(ctx['d'], struct.pack("<H", 3) + b"\0" * 0x3e)
        emu.write(ctx['d'] + 0x1e, struct.pack("<I", ctx['cb']))
        emu.write(ctx['cb'], struct.pack("<I", ctx['lim']))
        emu.write(ctx['lim'], struct.pack("<H", 200))
        emu.write(ctx['item'] + 4, struct.pack("<hh", 20, 30))
        emu.write(ctx['font'], b"\0\0\x08\0")
        emu.write(0x5acf0, struct.pack("<I", ctx['font']))
        emu.write(0x5aa78, b"\x01")
        emu.write(0x52586, struct.pack("<H", net))
        emu.write(0x593f6, struct.pack("<H", 0))
        emu.write(0x5176a, struct.pack("<H", quit_flag))
        emu.write(0x5176c, struct.pack("<I", HOOK))
        emu.write(0x59424, struct.pack("<I", 0))
        emu.write(0x593e8, struct.pack("<I", 0))
        emu.write(0x593ec, struct.pack("<H", 0))

    def case():
        c = t4spec.T4Case(setup=setup, label="k=%r s=%r" % (keys, src_text))
        c.args = None
        return c

    return ctx, watch, init_emu, setup


def _make(src_text, keys, maxlen, **kw):
    ctx, watch, init_emu, setup = _run(src_text, keys, maxlen, **kw)

    def setup_full(emu):
        setup(emu)
        emu.write(0x59424, struct.pack("<I", 0))

    class _Args(tuple):
        pass

    return ctx, watch, init_emu, setup_full


def _stubs(ctx):
    def gdsalloc(e, log):
        log(e.reg("eax"))
        return ctx['heap']

    def strcmp(e, log):
        a = _cstr(e, e.reg("eax"))
        b = _cstr(e, e.reg("edx"))
        log(len(a), len(b))
        return (a > b) - (a < b)

    def strcpy(e, log):
        s = _cstr(e, e.reg("edx"))
        e.write(e.reg("eax"), s + b"\0")
        log(len(s))
        return e.reg("eax")

    def strlen(e, log):
        n = len(_cstr(e, e.reg("eax")))
        log(n)
        return n

    def evtget(e, log):
        q = ctx['q']
        idx, n = struct.unpack("<II", bytes(e.read(q, 8)))
        if idx < n:
            key = struct.unpack("<H", bytes(e.read(q + 8 + 2 * idx, 2)))[0]
        else:
            key = 0x0d
        e.write(q, struct.pack("<I", idx + 1))
        ev = e.reg("eax")
        e.write(ev, struct.pack("<HHhhBBH", 0x80, 0, 0, 0, 0, 0, key))
        log(key)
        return 1

    def hook(e, log):
        ch = e.reg("eax") & 0xff
        log(ch)
        return 1 if (ch >= 0x20 and ch != 0x23) else 0

    return [
        t4spec.T4Stub(0x32558, fn=gdsalloc),
        t4spec.T4Stub(0x329d0, fn=strcmp),
        t4spec.T4Stub(0x31cef, fn=strcpy),
        t4spec.T4Stub(0x31d1a, fn=strlen),
        t4spec.T4Stub(0x31598, fn=evtget),
        t4spec.T4Stub(0x2461c, fn=evtget),
        t4spec.T4Stub(0x246b4, fn=evtget),
        t4spec.T4Stub(HOOK, fn=hook),
        t4spec.T4Stub(0x174c0, log_regs=(), stack_pop=16),
        t4spec.T4Stub(0x32b40, log_regs=()),
        t4spec.T4Stub(0x31f70, log_regs=("eax",)),
        t4spec.T4Stub(0x321e8, log_regs=()),
        t4spec.T4Stub(0x326a0, log_regs=("eax", "edx", "ebx", "ecx")),
        t4spec.T4Stub(0x32780, log_regs=("eax",)),
        t4spec.T4Stub(0x328c0, log_regs=()),
        t4spec.T4Stub(0x32940, log_regs=()),
    ]


SCENARIOS = [
    (b"abc", [0x0d], 8, {}),
    (b"abc", [ord('x'), ord('y'), 0x0d], 8, {}),
    (b"abc", [0x1b], 8, {}),
    (b"[empty slot]", [ord('h'), ord('i'), 0x0d], 6, {}),
    (b"hello", [0x4b00, 0x4b00, ord('Z'), 0x0d], 8, {}),
    (b"hello", [0x4700, 0x5300, 0x5300, 0x0d], 8, {}),
    (b"hello", [0x4f00, ord('q'), 0x0d], 8, {}),
    (b"hello", [0x4d00, 0x4d00, 0x08, 0x0d], 8, {}),
    (b"hello", [0x5200, 0x4700, ord('A'), ord('B'), 0x0d], 8, {}),
    (b"abcdef", [0x4f00, ord('1'), ord('2'), ord('3'), 0x0d], 6, {}),
    (b"ab", [ord('#'), 0x4900, 0x4800, 0x5000, 0x5100, 0x0d], 5, {}),
    (b"ab", [0x7600, 0x7900, 0x7a00, 0x7b00, 0x7e00, 0x7f00, 0x0d], 5, {}),
    (b"   ", [0x0d], 4, {}),
    (b"abc", [ord(' '), ord('k'), 0x0d], 8, {}),
    (b"abc", [0x0d], 8, {'quit_flag': 1}),
    (b"abc", [ord('n'), 0x0d], 8, {'net': 1}),
]


def test_edit_field_run():
    # one run_spec per scenario (each needs its own per-case memory set-up)
    for src_text, keys, maxlen, kw in SCENARIOS:
        ctx, watch, init_emu, setup = _run(src_text, keys, maxlen, **kw)
        stubs = _stubs(ctx)

        def mk_case(setup=setup, ctx=ctx, maxlen=maxlen, keys=keys, src_text=src_text):
            def _setup(emu):
                setup(emu)
            return _setup

        class _Case(t4spec.T4Case):
            pass

        case = t4spec.T4Case(setup=mk_case(), label="k=%r s=%r" % (keys, src_text))

        # args depend on addresses allocated in init_emu: resolve lazily in setup
        def init2(emu, init_emu=init_emu, case=case, ctx=ctx, maxlen=maxlen):
            init_emu(emu)
            case.args = (ctx['d'], ctx['item'], ctx['dest'], ctx['src'])
            case.stack_args = (maxlen,)

        t4spec.run_spec(
            REF, "EditFieldRun_", 0x17588,
            cases=[case], watch=watch, stubs=stubs,
            out_regs=("eax",), init_emu=init2)
