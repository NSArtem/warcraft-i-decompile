"""Fast re-check of the clib.toml `libsig:` verifications.

For every clib.toml entry whose verified_by starts with "libsig:", the library
unit named there is re-compared with the original bytes at the entry's address
(Matcher.check_bytes or Matcher.check_insn, the level recorded in verified_by).
No full search is run (no clib_sig.run_matching).
"""
import os
import re

import pytest

from wc1 import path, symbols

HAVE_ORIGINAL = os.path.exists(path("original", "install", "war.exe"))
HAVE_WATCOM = bool(os.environ.get("WATCOM"))
pytestmark = pytest.mark.skipif(not (HAVE_ORIGINAL and HAVE_WATCOM),
                                reason="needs original/ (make extract) and $WATCOM (nix develop)")

VB = re.compile(r"^libsig: (bytes|insn) match to (\w+)\.lib\((.+?)\) (\S+) \((\d+) bytes")


def _libsig_entries():
    funcs, datas, _ = symbols.load(strict=False)
    out = []
    for e in list(funcs.values()) + list(datas.values()):
        if not e["_file"].endswith("clib.toml"):
            continue
        vb = e.get("verified_by", "")
        if not vb.startswith("libsig:"):
            continue
        m = VB.match(vb)
        assert m, f"{e['_file']}: unparsable libsig verified_by: {vb!r}"
        level, lib, module, link, _size = m.groups()
        assert link == e["link_name"], f"{e['name']}: verified_by link {link} != {e['link_name']}"
        out.append(pytest.param(e["addr"], e["name"], level, lib, module, link,
                                id=f"{e['addr']:#x}-{e['name']}"))
    return out


ENTRIES = _libsig_entries()


@pytest.fixture(scope="module")
def clib_env():
    from wc1 import analysis, clib_sig
    prog = analysis.run()
    mods = clib_sig.load_modules()
    return clib_sig, clib_sig.Matcher(prog), mods


def test_entries_present():
    assert len(ENTRIES) >= 15, "expected the 15 clib libsig verifications"


@pytest.mark.parametrize("addr,name,level,lib,module,link", ENTRIES)
def test_libsig_entry(clib_env, addr, name, level, lib, module, link):
    clib_sig, m, mods = clib_env
    hits = [mod for lname, mod in mods if lname == lib and mod.name == module]
    assert hits, f"{lib}.lib({module}) not found"
    units = [u for mod in hits for u in clib_sig.code_units(lib, mod)
             if link in u.names]
    assert units, f"{lib}({module}) has no unit named {link}"
    u = units[0]
    if level == "bytes":
        ok, why, _ = m.check_bytes(u, addr)
    else:
        ok, why, _ = m.check_insn(u, addr)
    assert ok, f"{name} at {addr:#x} vs {lib}({module}) {link}: {why}"
