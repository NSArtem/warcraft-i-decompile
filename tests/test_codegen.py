"""Codegen area checks (docs/subsystems/codegen.md).

1. The prologue/epilogue classifier of tools/wc1/codegen_survey.py gives the
   documented style for known functions of each family.
2. Every function in src/codegen/*.c still reproduces the original bytes, relocation
   structure and module-local data with the flags named in its `codegen-flags:` line
   (mechanical re-check; the T3 tool wc1.match is used for the symbol-database-named ones,
   see test_codegen_match).
3. The OW2 limits documented in the doc stay true (so a toolchain change that fixes them is noticed).
"""
import glob
import os
import re

import pytest

from wc1 import codegen_survey, codegen_sweep, match, path

HAVE_ORIGINAL = os.path.exists(path("original", "install", "war.exe"))
HAVE_WATCOM = bool(os.environ.get("WATCOM"))
pytestmark = pytest.mark.skipif(not (HAVE_ORIGINAL and HAVE_WATCOM),
                                reason="needs original/ (make extract) and $WATCOM (nix develop)")


@pytest.fixture(scope="module")
def prog():
    return codegen_sweep.program()


def _feat(prog, addr):
    f = next(f for f in prog.functions if f["start"] == addr)
    return codegen_survey.feat(prog, f)


@pytest.mark.parametrize("addr,style,sub", [
    (0x26b18, "OD", (0, "imm32")),      # SndShutdownAil: -od frame, sub esp,0
    (0x27320, "OD", (4, "imm32")),      # SndActiveCount
    (0x34380, "DBG", None),             # SetUiColorBase: empty ebp frame around an optimised body
    (0x3ac10, "DBG", (4, "imm8")),      # HLine
    (0x1d798, "OPT", None),             # TrimAtWhitespace: no frame
    (0x38594, "LEAVE", None),           # Miles AIL timer helper
])
def test_style_classifier(prog, addr, style, sub):
    r = _feat(prog, addr)
    assert r["style"] == style
    assert r["sub"] == sub


def test_no_stack_checks_anywhere(prog):
    """-s everywhere: no function starts with the `cmp esp,[limit]` stack check."""
    bad = [hex(f["start"]) for f in prog.functions if codegen_survey.feat(prog, f)["stk"]]
    assert not bad, bad


def test_prologue_save_order_of_frames(prog):
    """In every OD/DBG function ebp is the last register pushed before `mov ebp,esp` (the layout of
    OW2 -od and -d1+), never `push ebp` first (OW2 -of/-of+)."""
    for f in prog.functions:
        r = codegen_survey.feat(prog, f)
        if r["style"] in ("OD", "DBG"):
            assert r["frame"] and r["pushes"][-1] == "ebp", hex(f["start"])


def _codegen_files():
    out = []
    for src in sorted(glob.glob(path("src", "codegen", "*.c"))):
        m = re.search(r"codegen-flags:\s*(.*)", open(src).read())
        if m:
            out.append(pytest.param(src, m.group(1).strip(), id=os.path.basename(src)))
    return out


@pytest.mark.parametrize("src,flags", _codegen_files())
def test_sample_matches(src, flags):
    table = codegen_sweep.sweep(src, [flags], quiet=True)
    _, rows, err = table[0]
    assert rows is not None, err
    assert rows, "no annotated function found"
    for name, a, st, g, w in rows:
        assert st == "MATCH", f"{name}: {st}"


def test_near_misses_still_miss():
    """src/codegen/near_misses.c: believed-correct C that OW2 cannot reproduce (register allocation);
    if one starts to match, move it into its module file."""
    src = path("src", "codegen", "near_misses.c")
    flags = re.search(r"codegen-near:\s*(.*)", open(src).read()).group(1).strip()
    _, rows, err = codegen_sweep.sweep(src, [flags], quiet=True)[0]
    assert rows is not None, err
    for name, a, st, g, w in rows:
        assert st != "MATCH", f"{name} now matches: promote it to its module file"
        assert st.startswith("len "), st        # compiled fine, only bytes differ


# files whose every function is in the symbol database with named externals: full T3
T3_FILES = ["init.c", "snd.c", "mod_34380.c", "mod_33a30.c", "res_init.c", "mod_409a0.c"]


@pytest.mark.parametrize("name", T3_FILES)
def test_codegen_match(name):
    src = path("src", "codegen", name)
    flags = re.search(r"codegen-flags:\s*(.*)", open(src).read()).group(1).strip()
    cflags = "-q -zl -bt=dos " + flags
    from wc1 import analysis, symbols
    mod = match.compile_c(src, cflags, path("build", "codegen", "t3_" + name + ".obj"))
    funcs, datas, _ = symbols.load()
    by_link = {e["link_name"]: e for t in (funcs, datas) for e in t.values()}
    res = match.match_module(codegen_sweep.program(), mod, by_link)
    bad = [(n, s, p) for n, s, p in res if s != "MATCH"]
    assert not bad, bad


def test_ow2_od_limits():
    """-od cannot produce the original's `sub esp,0` frame: OW2 always reserves >= 4 bytes and
    keeps `mov esp,ebp`.  If this starts failing the audio -od module (0x269f0) can be matched."""
    src = path("build", "codegen", "od_limit.c")
    os.makedirs(os.path.dirname(src), exist_ok=True)
    open(src, "w").write("extern void a(void);\n/* @0x26b18 */\nvoid f(void){ a(); a(); a(); }\n")
    table = codegen_sweep.sweep(src, ["-s -od"], quiet=True)
    _, rows, _ = table[0]
    assert rows[0][2] != "MATCH"
    assert bytes.fromhex("81ec04000000") in rows[0][3]      # sub esp,4 (the original has sub esp,0)
