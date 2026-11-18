"""wc1.clib_sig --root: the runtime libraries of another Watcom tree, here
the original's Watcom 10.0a (docs/subsystems/compiler.md).

The OMF and library-layout tests use synthetic data.  The 10.0a check needs
original/ and the optional 10.0a libraries (make toolchain from a 10.0a
installation) and skips with that reason otherwise.
"""
import os
import struct

import pytest

from wc1 import clib_sig, oldcc, omf, path

HAVE_ORIGINAL = os.path.exists(path("original", "install", "war.exe"))


def _rec(rtype, body):
    return bytes([rtype]) + struct.pack("<H", len(body) + 1) + body + b"\0"


def _module(pubdef_type, pub_body):
    lnames = b"".join(bytes([len(n)]) + n for n in (b"", b"_TEXT", b"CODE"))
    seg = bytes([0x29]) + struct.pack("<I", 16) + bytes([2, 3, 1])   # SEGDEF 0x99
    return (_rec(0x80, b"\x01m") + _rec(0x96, lnames) + _rec(0x99, seg)
            + _rec(pubdef_type, pub_body) + _rec(0x8A, b"\x00"))


def test_pubdef16_with_32bit_offsets():
    # 10.x clib3r (the emulator hook module): type 0x90 with a 4-byte offset
    body = b"\x00\x01" + bytes([3]) + b"foo" + struct.pack("<I", 5) + b"\x00"
    m, _ = omf.parse_module(_module(0x90, body))
    assert m.publics == {"foo": (1, 5)}


def test_pubdef16_regular():
    body = b"\x00\x01" + bytes([3]) + b"foo" + struct.pack("<H", 7) + b"\x00" \
        + bytes([3]) + b"bar" + struct.pack("<H", 9) + b"\x00"
    m, _ = omf.parse_module(_module(0x90, body))
    assert m.publics == {"foo": (1, 7), "bar": (1, 9)}


def test_pubdef32_regular():
    body = b"\x00\x01" + bytes([3]) + b"foo" + struct.pack("<I", 0x12345) + b"\x00"
    m, _ = omf.parse_module(_module(0x91, body))
    assert m.publics == {"foo": (1, 0x12345)}


def test_library_files_10x_layout(tmp_path):
    lib = tmp_path / "lib386"
    (lib / "dos").mkdir(parents=True)
    for rel in ("dos/clib3r.lib", "dos/emu387.lib", "dos/cstrtx3r.obj", "math3r.lib"):
        (lib / rel).write_bytes(b"")
    found, missing = clib_sig.library_files(str(tmp_path))
    got = {name: os.path.relpath(p, lib) for name, kind, p in found}
    assert got == {"clib3r": "dos/clib3r.lib", "emu387": "dos/emu387.lib",
                   "math3r": "math3r.lib", "cstrtx3r": "dos/cstrtx3r.obj"}
    assert missing == ["math387r", "noemu387"]


@pytest.fixture(scope="module")
def matcher():
    if not HAVE_ORIGINAL:
        pytest.skip("needs original/ (make extract)")
    from wc1 import analysis
    return clib_sig.Matcher(analysis.run())


def _10a_libs():
    root = oldcc.root()
    bad = oldcc.check(root, optional=True)
    if bad:
        pytest.skip(f"Watcom 10.0a runtime libraries not installed in {root}: {bad[0]}")
    return root


def _unit(root, lib, module, name):
    for lname, mod in clib_sig.load_modules(root):
        if lname == lib and mod.name == module:
            for u in clib_sig.code_units(lname, mod):
                if name in u.names:
                    return u
    raise AssertionError(f"{lib}({module}) {name} not in {root}")


def test_cstart_is_the_10_0a_startup_object(matcher):
    """_cstart_ (0x34584) is byte-identical to 10.0a's patched cstrt386 (patch A
    moved __saved_DS behind __GETDS); 10.0 GA, 10.5 and 10.6 differ."""
    u = _unit(_10a_libs(), "clib3r", "cstrt386", "_cstart_")
    ok, why, _ = matcher.check_bytes(u, 0x34584)
    assert ok, why


def test_getds_reads_save_word_behind_its_ret(matcher):
    # war.exe: 66 2e 8e 1d <0x34859> c3 at 0x34850 - the level-A placement
    code = matcher.code
    o = 0x34850 - matcher.cbase
    assert code[o:o + 4] == bytes.fromhex("662e8e1d")
    assert struct.unpack_from("<I", code, o + 4)[0] == 0x34859
    assert code[o + 8] == 0xC3
