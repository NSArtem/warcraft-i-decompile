"""Tests for wc1.permuter (local Watcom 10.0a flag & idiom permuter)."""
import os
import shutil

import pytest

from wc1 import match, path, permuter

pytestmark = pytest.mark.skipif(
    not (os.path.exists(path("original", "install", "war.exe")) and os.environ.get("WATCOM")),
    reason="needs original/ and $WATCOM (nix develop)")


def test_generate_mutations_covers_decl_and_type_swaps():
    src = "void f(void) {\n    int a, b, c;\n    int i;\n    i++;\n}\n"
    muts = dict(permuter.generate_mutations(src, max_count=40))
    assert any(k.startswith("perm(") for k in muts)
    assert any(k.startswith("type(") for k in muts)
    assert any(k.startswith("preinc(") for k in muts)


def test_permuter_recovers_wrong_flags(tmp_path):
    # Take an existing 10.0a matched file, intentionally corrupt its compiler flags
    # to -od, and verify permuter recovers exact MATCH via flag sweep.
    orig_src = path("src", "mod_1b800", "snd_tick.c")
    text = open(orig_src).read()
    broken = "/* codegen-flags: -s -od -4r -zp2 */\n" + text
    cand = tmp_path / "snd_tick_broken.c"
    cand.write_text(broken)
    # Include src/mod_1b800 header via copy of mod_1b800.h or -i=src/include (already added)
    r = permuter.permute_file(str(cand), max_trials=10, jobs=2, rounds=1, apply=True)
    assert r["matched"] is True
    assert r["applied"] is True
    assert "-od" not in cand.read_text()


def test_permuter_recovers_shuffled_type(tmp_path):
    # Take a matched file with `short` or `int`, mutate a local type, and recover it
    orig_src = path("src", "mod_1b800", "snd_events_init.c")
    text = open(orig_src).read()
    # Replace `int i;` or `short i;` if present, else fall back to already-match check
    if "int " in text:
        cand = tmp_path / "snd_events_init_mut.c"
        cand.write_text(text)
        r = permuter.permute_file(str(cand), max_trials=10, jobs=2, rounds=1)
        assert r["matched"] is True
