"""T4 differential tests of Watcom 10.x runtime functions of war.exe.

Each original routine is executed under the Unicorn harness (wc1.emu) on many
inputs and compared with a Python model of the standard C library behaviour
(strncmp, memcmp, strtol, itoa, sprintf, gmtime, ...).  Addresses are those of
analysis/symbols/clib.toml; the `verified_by = "difftest: ..."` entries point
here.
"""
import os
import random
import struct
import time

import pytest

from wc1 import path

pytestmark = pytest.mark.skipif(not os.path.exists(path("original", "install", "war.exe")),
                                reason="original files not extracted")

ADDR = dict(strncmp=0x30C6F, memcpy=0x31789, memcmp=0x31F96, strcat=0x31FEB, memmove=0x3CEFC,
            strncpy=0x3E08C, strnicmp=0x3DFDB, strrchr=0x33F76, strlwr=0x30E38, memset=0x30C50,
            atoi=0x324DD, stol=0x30C98, strtoul=0x30DD1, utoa=0x40A7F, itoa=0x40AC9,
            ultoa=0x40B1B, ltoa=0x40B64, rand=0x33B61, leapyear=0x40B8D, rotl=0x30C68,
            gmtime=0x410E9, sprintf=0x31BE2, getenv=0x3E032, makepath=0x31C24,
            fmemcmp=0x34963, fmemcpy=0x34988)
RNG = random.Random(1994)


def _seg_trace(emu, addr, size):
    """Unicorn pops segment registers with a 16-bit stack pointer here, so
    `push es/ds` and `pop es/ds` (flat model: selectors are irrelevant to the
    code under test) are executed as plain stack adjustments."""
    from unicorn.x86_const import UC_X86_REG_EIP
    if size == 2 and emu.read(addr, 1)[0] == 0x8E:      # mov sreg, r32: flat model, skip
        emu.uc.reg_write(UC_X86_REG_EIP, addr + 2)
        return
    if size == 1:
        op = emu.read(addr, 1)[0]
        if op in (0x06, 0x1E):
            esp = emu.reg("esp") - 4
            emu.reg("esp", esp)
            emu.put_u32(esp, 0)
            emu.uc.reg_write(UC_X86_REG_EIP, addr + 1)
        elif op in (0x07, 0x1F):
            emu.reg("esp", emu.reg("esp") + 4)
            emu.uc.reg_write(UC_X86_REG_EIP, addr + 1)


@pytest.fixture()
def emu():
    from wc1.emu import Emu
    e = Emu()
    e.trace = _seg_trace
    return e


def cstr(emu, s):
    a = emu.alloc(len(s) + 16)
    emu.write(a, s + b"\0")
    return a


def sgn(x):
    return (x > 0) - (x < 0)


def s32(v):
    v &= 0xFFFFFFFF
    return v - (1 << 32) if v & 0x80000000 else v


WORDS = [b"", b"a", b"abc", b"abd", b"ABC", b"abcdef", b"hello world", b"Hello World", b"x" * 20, b"\x80\xff"]


def test_strncmp(emu):
    for a in WORDS:
        for b in WORDS:
            for n in (0, 1, 2, 3, 5, 30):
                r = s32(emu.call(ADDR["strncmp"], cstr(emu, a), cstr(emu, b), n))
                x, y = a[:n], b[:n]
                assert sgn(r) == sgn((x > y) - (x < y)), (a, b, n, r)
                if x != y:
                    i = next(i for i in range(max(len(x), len(y)) + 1)
                             if (x[i:i + 1] or b"\0") != (y[i:i + 1] or b"\0"))
                    assert r == (x[i:i + 1] or b"\0")[0] - (y[i:i + 1] or b"\0")[0]


def test_memcmp_memcpy_memset(emu):
    for _ in range(200):
        n = RNG.randrange(0, 70)
        a = bytes(RNG.randrange(0, 3) for _ in range(n))
        b = bytes(RNG.randrange(0, 3) for _ in range(n))
        pa, pb = emu.alloc(n + 8), emu.alloc(n + 8)
        emu.write(pa, a)
        emu.write(pb, b)
        r = s32(emu.call(ADDR["memcmp"], pa, pb, n))
        assert r == (a > b) - (a < b)
        dst = emu.alloc(n + 8)
        assert emu.call(ADDR["memcpy"], dst, pa, n) == dst
        assert emu.read(dst, n) == a
        c = RNG.randrange(0, 256)
        emu.write(dst, b"\xaa" * (n + 8))
        assert emu.call(ADDR["memset"], dst, c, n) == dst
        assert emu.read(dst, n + 8) == bytes([c]) * n + b"\xaa" * 8


def test_memmove_overlap(emu):
    for _ in range(200):
        n = RNG.randrange(0, 40)
        off = RNG.randrange(-12, 13)
        buf = emu.alloc(200)
        data = bytes(RNG.randrange(256) for _ in range(120))
        emu.write(buf, data)
        src, dst = buf + 30, buf + 30 + off
        expect = bytearray(data)
        expect[30 + off:30 + off + n] = data[30:30 + n]
        assert emu.call(ADDR["memmove"], dst, src, n) == dst
        assert emu.read(buf, 120) == bytes(expect)


def test_far_mem(emu):
    for _ in range(50):
        n = RNG.randrange(0, 40)
        a = bytes(RNG.randrange(0, 2) for _ in range(n))
        b = bytes(RNG.randrange(0, 2) for _ in range(n))
        pa, pb, pd = emu.alloc(n + 8), emu.alloc(n + 8), emu.alloc(n + 8)
        emu.write(pa, a)
        emu.write(pb, b)
        # watcall: eax=a_off, edx=a_sel, ebx=b_off, ecx=b_sel, stack: n (ret 4)
        r = s32(emu.call(ADDR["fmemcmp"], pa, 0, pb, 0, stack_args=(n,)))
        assert r == (a > b) - (a < b)
        assert emu.call(ADDR["fmemcpy"], pd, 0, pa, 0, stack_args=(n,)) == pd
        assert emu.read(pd, n) == a


def test_strings(emu):
    for a in WORDS:
        for b in WORDS:
            buf = emu.alloc(80)
            emu.write(buf, a + b"\0" + b"\xee" * 60)
            assert emu.call(ADDR["strcat"], buf, cstr(emu, b)) == buf
            assert emu.cstr(buf) == a + b
            for n in (0, 1, 4, 12, 30):
                d = emu.alloc(64)
                emu.write(d, b"\xee" * 64)
                assert emu.call(ADDR["strncpy"], d, cstr(emu, b), n) == d
                assert emu.read(d, 64) == (b[:n] + b"\0" * n)[:n] + b"\xee" * (64 - n)
            for n in (0, 1, 3, 40):
                r = s32(emu.call(ADDR["strnicmp"], cstr(emu, a), cstr(emu, b), n))
                x, y = a[:n].lower(), b[:n].lower()
                assert sgn(r) == sgn((x > y) - (x < y)) or (x.startswith(b"\x80") or y.startswith(b"\x80")), (a, b, n)
        s = cstr(emu, a)
        for c in b"abc\\ZK":
            r = emu.call(ADDR["strrchr"], s, c)
            i = a.rfind(bytes([c]))
            assert r == (0 if i < 0 else s + i)
        emu.call(ADDR["strlwr"], s)
        assert emu.cstr(s) == bytes(ch + 32 if 65 <= ch <= 90 else ch for ch in a)


def test_rotl(emu):
    for _ in range(100):
        v, n = RNG.randrange(1 << 32), RNG.randrange(0, 32)
        assert emu.call(ADDR["rotl"], v, n) == (((v << n) | (v >> (32 - n))) & 0xFFFFFFFF if n else v)


def test_leapyear(emu):
    for y in range(1580, 2420):
        assert (emu.call(ADDR["leapyear"], y) != 0) == (y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)), y


def test_number_to_string(emu):
    digs = "0123456789abcdefghijklmnopqrstuvwxyz"

    def conv(v, r):
        if v == 0:
            return "0"
        s = ""
        while v:
            s = digs[v % r] + s
            v //= r
        return s

    for _ in range(300):
        r = RNG.choice([2, 8, 10, 16, 36, 7])
        u = RNG.choice([0, 1, RNG.randrange(1 << 32), RNG.randrange(1000), 0xFFFFFFFF])
        buf = emu.alloc(48)
        assert emu.call(ADDR["utoa"], u, buf, r) == buf and emu.cstr(buf).decode() == conv(u, r)
        assert emu.call(ADDR["ultoa"], u, buf, r) == buf and emu.cstr(buf).decode() == conv(u, r)
        sv = s32(u)
        exp = ("-" + conv(-sv, 10)) if (r == 10 and sv < 0) else conv(u, r)
        assert emu.call(ADDR["itoa"], u, buf, r) == buf and emu.cstr(buf).decode() == exp
        assert emu.call(ADDR["ltoa"], u, buf, r) == buf and emu.cstr(buf).decode() == exp


def test_atoi_strtol(emu):
    cases = [b"0", b"12", b"-34", b"+56", b"  \t78x", b"99999", b"-2147483647", b"abc", b"", b"  -  3"]
    for c in cases:
        s = cstr(emu, c)
        v = s32(emu.call(ADDR["atoi"], s))
        import re
        m = re.match(rb"[ \t\n\v\f\r]*([+-]?)(\d*)", c)
        exp = int(m.group(1) + m.group(2) or b"0") if m.group(2) else 0
        assert v == s32(exp), c
    end = emu.alloc(8)
    for c, base, exp, used in [(b"123abc", 10, 123, 3), (b"  -42", 10, -42, 5), (b"0x1F", 0, 31, 4),
                               (b"0x1F", 16, 31, 4), (b"017", 0, 15, 3), (b"101", 2, 5, 3),
                               (b"zz", 36, 35 * 36 + 35, 2), (b"xyz", 10, 0, 0), (b"7fffffff", 16, 0x7FFFFFFF, 8)]:
        s = cstr(emu, c)
        r = s32(emu.call(ADDR["stol"], s, end, base, 1))
        assert r == exp, (c, base, r)
        assert emu.u32(end) - s == used, (c, base)
    # unsigned entry and overflow clamps
    assert emu.call(ADDR["strtoul"], cstr(emu, b"4294967295"), 0, 10) == 0xFFFFFFFF
    assert s32(emu.call(ADDR["stol"], cstr(emu, b"99999999999"), 0, 10, 1)) == 0x7FFFFFFF
    assert s32(emu.call(ADDR["stol"], cstr(emu, b"-99999999999"), 0, 10, 1)) == -0x80000000


def test_rand(emu):
    seed = emu.u32(0x555C0)
    for _ in range(20):
        seed = (seed * 0x41C64E6D + 0x3039) & 0xFFFFFFFF
        assert emu.call(ADDR["rand"]) == (seed >> 16) & 0x7FFF
    assert emu.u32(0x555C0) == seed


def test_gmtime(emu):
    for t in [0, 1, 86399, 86400, 951782400, 1_000_000_000, 1_234_567_890, 1_700_000_000, 2_147_483_647,
              68169600, 825_811_200] + [RNG.randrange(0, 2_000_000_000) for _ in range(150)]:
        p = emu.alloc(4)
        emu.put_u32(p, t)
        tm = emu.call(ADDR["gmtime"], p)
        f = struct.unpack("<9i", emu.read(tm, 36))
        g = time.gmtime(t)
        # C: tm_mon 0-11, tm_year-1900, tm_wday sun=0, tm_yday 0-based
        assert f[:8] == (g.tm_sec, g.tm_min, g.tm_hour, g.tm_mday, g.tm_mon - 1, g.tm_year - 1900,
                         (g.tm_wday + 1) % 7, g.tm_yday - 1), (t, f)


def _fmt_model(fmt, args):
    return (fmt.decode() % tuple(a.decode() if isinstance(a, bytes) else a for a in args)).encode()


def test_sprintf(emu):
    cases = [(b"%d", (0,)), (b"%d", (-17,)), (b"%5d|", (42,)), (b"%-5d|", (42,)), (b"%05d", (42,)),
             (b"%x", (0xBEEF,)), (b"%X", (0xBEEF,)), (b"%o", (64,)), (b"%u", (3000000000,)),
             (b"%s", (b"hello",)), (b"%10s|", (b"hi",)), (b"%-10s|", (b"hi",)), (b"%.3s", (b"abcdef",)),
             (b"%c%c", (65, 66)), (b"a%%b", ()), (b"%s=%d (%x)", (b"v", 5, 255)), (b"%+d %+d", (5, -5)),
             (b"%ld", (123456789,)), (b"%08x", (0x1234,)), (b"%i", (-8,)), (b"no format", ())]
    for fmt, args in cases:
        buf = emu.alloc(200)
        emu.write(buf, b"\xdd" * 200)
        stack = []
        for a in args:
            stack.append(cstr(emu, a) if isinstance(a, bytes) else a & 0xFFFFFFFF)
        n = s32(emu.call(ADDR["sprintf"], buf, cstr(emu, fmt), *stack, cdecl=True))
        exp = _fmt_model(fmt, [a if not (isinstance(a, int) and fmt.endswith(b"u")) else a for a in args])
        assert emu.cstr(buf) == exp, (fmt, args, emu.cstr(buf), exp)
        assert n == len(exp)


def test_getenv(emu):
    env = [b"PATH=C:\\DOS", b"Temp=D:\\TMP", b"EMPTY=", b"FOO=bar"]
    ptrs = [cstr(emu, e) for e in env]
    arr = emu.alloc(4 * (len(env) + 1))
    for i, p in enumerate(ptrs):
        emu.put_u32(arr + 4 * i, p)
    emu.put_u32(arr + 4 * len(env), 0)
    emu.put_u32(0x56780, arr)
    for name, exp in [(b"PATH", ptrs[0] + 5), (b"path", ptrs[0] + 5), (b"TEMP", ptrs[1] + 5), (b"EMPTY", ptrs[2] + 6),
                      (b"FOO", ptrs[3] + 4), (b"FO", 0), (b"MISSING", 0), (b"PATHX", 0)]:
        assert emu.call(ADDR["getenv"], cstr(emu, name)) == exp, name


def _makepath_model(drive, d, fname, ext):
    out = b""
    if drive:
        out += drive[:1] + b":"
    if d:
        out += d
        if d[-1:] not in (b"\\", b"/"):
            out += b"\\"
    out += fname or b""
    if ext:
        out += (b"" if ext[:1] == b"." else b".") + ext
    return out


def test_makepath(emu):
    for drive in (None, b"", b"c", b"D:"):
        for d in (None, b"", b"dir", b"dir\\", b"a/b/", b"\\"):
            for fname in (None, b"", b"name"):
                for ext in (None, b"", b"exe", b".dat"):
                    buf = emu.alloc(100)
                    emu.write(buf, b"\xdd" * 100)
                    args = [cstr(emu, x) if x is not None else 0 for x in (drive, d, fname)]
                    emu.call(ADDR["makepath"], buf, *args, stack_args=(cstr(emu, ext) if ext is not None else 0,))
                    got = emu.cstr(buf)
                    assert got == _makepath_model(drive, d, fname, ext), (drive, d, fname, ext, got)
