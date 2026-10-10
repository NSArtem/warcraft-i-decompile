"""Mechanical checks for the audio area (analysis/symbols/audio.toml).

* the driver file-name tables and AIL strings are where the evidence says
* AIL_startup installs the documented default preferences
* every call from the game sound layer into the AIL range hits a named AIL entry
* small pure AIL functions are differential-tested in the Unicorn harness
  against Python reference models (T4)
"""
import os
import random
import struct

import pytest

from wc1 import path

pytestmark = pytest.mark.skipif(not os.path.exists(path("original", "install", "war.exe")),
                                reason="original files not extracted")

AIL_LO, AIL_HI = 0x34D83, 0x3AAC0          # documented in docs/subsystems/audio.md


@pytest.fixture(scope="module")
def prog():
    from wc1 import analysis
    return analysis.run()


def _cstr(p, addr):
    img = bytes(p.image[2])
    off = addr - p.data.base
    return img[off:img.index(b"\0", off)]


def _u32(p, addr):
    img = bytes(p.image[2])
    return struct.unpack_from("<I", img, addr - p.data.base)[0]


def test_driver_tables(prog):
    dig = [_cstr(prog, _u32(prog, 0x533B8 + 4 * i)) for i in range(7)]
    mdi = [_cstr(prog, _u32(prog, 0x533D4 + 4 * i)) for i in range(10)]
    assert dig == [b"drivers\\" + n for n in
                   (b"sblaster.dig", b"sbpro.dig", b"sb16.dig", b"proaudio.dig",
                    b"ultra.dig", b"jammer.dig", b"rap10.dig")]
    assert mdi == [b"drivers\\" + n for n in
                   (b"adlib.mdi", b"adlibg.mdi", b"sblaster.mdi", b"sbpro1.mdi", b"sbpro2.mdi",
                    b"sbawe32.mdi", b"pas.mdi", b"pasplus.mdi", b"mpu401.mdi", b"ultra.mdi")]
    assert _cstr(prog, 0x5341C) == b"drivers\\warcraft"


def test_ail_strings(prog):
    expect = {0x57F9C: b"AIL3DIG", 0x57FA4: b"AIL3MDI", 0x57FAC: b"Invalid driver type\n",
              0x57FC1: b"Out of driver handles\n", 0x5810C: b"Out of sequence handles\n"[0:],
              0x582EC: b"Out of sample handles\n", 0x5830E: b"Creative", 0x58317: b"WAVE",
              0x5831C: b"Unrecognized digital audio file type\n"}
    for a, s in expect.items():
        got = _cstr(prog, a)
        assert got == s or got.endswith(s), (hex(a), got)


def test_startup_defaults(prog):
    """AIL_startup (0x351b8) = a run of `push value; push index; call AIL_set_preference`."""
    insns = sorted(a for a in prog.insns if 0x351B8 <= a < 0x352A0)
    prefs, stack = {}, []
    for a in insns:
        i = prog.insns[a]
        if i.mnemonic == "push" and i.op_str.startswith(("0x", "-")) or (
                i.mnemonic == "push" and i.op_str.isdigit()):
            stack.append(int(i.op_str, 0))
        elif i.mnemonic == "call" and int(i.op_str, 0) == 0x34E5B:
            idx, val = stack[-1], stack[-2]
            prefs[idx] = val
            stack.clear()
    assert [prefs[k] for k in sorted(prefs)] == \
        [200, 1, 0x8000, 100, 16, 100, 655, 0, 0, 1, 120, 8, 127, 1, 0, 2, 1, 1]


def test_game_calls_hit_named_ail_entries(prog):
    from wc1 import symbols
    funcs, _, _ = symbols.load(strict=False)
    named = {a for a, e in funcs.items() if e["_file"].endswith("audio.toml")}
    bad = []
    for a, i in prog.insns.items():
        if 0x263C0 <= a < 0x27670 and i.mnemonic == "call":
            try:
                t = int(i.op_str, 0)
            except ValueError:
                continue
            if AIL_LO <= t < AIL_HI and t not in named:
                bad.append((hex(a), hex(t)))
    assert not bad, bad


def test_audio_functions_are_discovered_starts(prog):
    from wc1 import symbols
    funcs, _, _ = symbols.load(strict=False)
    starts = {f["start"] for f in prog.functions}
    missing = [hex(a) for a, e in funcs.items() if e["_file"].endswith("audio.toml") and a not in starts]
    assert not missing, missing


# ---------------------------------------------------------------- T4 difftests
@pytest.fixture()
def emu():
    from wc1.emu import Emu
    return Emu()


def _bswap(x):
    return int.from_bytes(x.to_bytes(4, "little"), "big")


def test_bswap32(emu):
    rnd = random.Random(1)
    for x in [0, 1, 0xFF, 0x12345678, 0xFFFFFFFF, 0x80000000] + [rnd.getrandbits(32) for _ in range(200)]:
        assert emu.call(0x356B0, x, cdecl=True) == _bswap(x)


def _vlq(data):
    v, n = 0, 0
    for n in range(1, 5):
        b = data[n - 1]
        v = (v << 7) | (b & 0x7F)
        if not b & 0x80:
            break
    return v, n


def test_read_vlq(emu):
    rnd = random.Random(2)
    pp = emu.alloc(4)
    buf = emu.alloc(16)
    for _ in range(300):
        k = rnd.randint(1, 4)
        data = bytes([rnd.getrandbits(7) | 0x80 for _ in range(k - 1)] + [rnd.getrandbits(7)])
        data += bytes(8)
        emu.write(buf, data)
        emu.put_u32(pp, buf)
        want, used = _vlq(data)
        assert emu.call(0x35680, pp, cdecl=True) == want
        assert emu.u32(pp) == buf + used
    # a fifth continuation byte is never consumed
    emu.write(buf, bytes([0xFF] * 8))
    emu.put_u32(pp, buf)
    assert emu.call(0x35680, pp, cdecl=True) == (0x7F << 21 | 0x7F << 14 | 0x7F << 7 | 0x7F)
    assert emu.u32(pp) == buf + 4


def test_set_preference_returns_old_and_stores(emu):
    base = 0x62AB8
    for idx, val in ((0, 5), (5, 77), (12, 0x7F), (17, 3)):
        old = emu.u32(base + 4 * idx)
        assert emu.call(0x34E5B, idx, val, cdecl=True) == old
        assert emu.u32(base + 4 * idx) == val


def test_sample_status_and_release(emu):
    hs = emu.alloc(0x40)
    emu.put_u32(hs + 4, 4)
    assert emu.call(0x3A220, hs, cdecl=True) == 4
    assert emu.call(0x3A220, 0, cdecl=True) == 0
    emu.call(0x3A170, hs, cdecl=True)            # AIL_release_sample_handle
    assert emu.u32(hs + 4) == 1
