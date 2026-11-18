"""Fast re-check of the clib.toml `libsig:` verifications.

For every clib.toml entry whose verified_by starts with "libsig:", the library
unit named there is re-compared with the original bytes at the entry's address
(Matcher.check_bytes or Matcher.check_insn, the level recorded in verified_by).
No full search is run (no clib_sig.run_matching).

The library is the one verified_by names: Open Watcom 2's ($WATCOM), or
Watcom 10.0a's when it says "Watcom 10.0a" (original/watcom/10.0a, the
optional library part of `make toolchain`; those entries skip with the reason
when the libraries are not installed).
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
        root = "10.0a" if "Watcom 10.0a" in vb else "ow2"
        out.append(pytest.param(e["addr"], e["name"], level, lib, module, link, root,
                                id=f"{e['addr']:#x}-{e['name']}"))
    return out


ENTRIES = _libsig_entries()


@pytest.fixture(scope="module")
def clib_env():
    from wc1 import analysis, clib_sig, oldcc
    prog = analysis.run()
    mods = {"ow2": clib_sig.load_modules()}
    bad = oldcc.check(optional=True)
    mods["10.0a"] = None if bad else clib_sig.load_modules(oldcc.root())
    return clib_sig, clib_sig.Matcher(prog), mods


def test_entries_present():
    assert len(ENTRIES) >= 15, "expected the 15 clib libsig verifications"


@pytest.mark.parametrize("addr,name,level,lib,module,link,root", ENTRIES)
def test_libsig_entry(clib_env, addr, name, level, lib, module, link, root):
    clib_sig, m, all_mods = clib_env
    mods = all_mods[root]
    if mods is None:
        pytest.skip("Watcom 10.0a runtime libraries not installed (make toolchain from a 10.0a installation)")
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
