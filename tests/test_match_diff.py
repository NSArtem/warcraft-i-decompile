"""Tests for wc1.match --diff and diff_function."""
import os
import subprocess
import sys

import pytest

from wc1 import analysis, match, path, symbols

pytestmark = pytest.mark.skipif(
    not (os.path.exists(path("original", "install", "war.exe")) and os.environ.get("WATCOM")),
    reason="needs original/ and $WATCOM (nix develop)")


def test_diff_exact_match():
    funcs, datas, _ = symbols.load()
    by_link = {e["link_name"]: e for t in (funcs, datas) for e in t.values()}
    p = analysis.run()
    src = path("src", "mod_1b800", "snd_tick.c")
    out = path("build", "match", "test_diff_snd_tick.obj")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    mod = match.compile_c(src, None, out, cc=match.file_cc(src))
    d = match.diff_function(p, mod, by_link)
    assert d["matched"] is True
    assert d["score"] == (0, 0, 0, 0, 0)
    assert d["first_diff"] is None


def test_diff_reference_mismatch_reports_first_diff():
    funcs, datas, _ = symbols.load()
    by_link = {e["link_name"]: e for t in (funcs, datas) for e in t.values()}
    p = analysis.run()
    src = path("src", "mod_1b800", "snd_event_reference.c")
    out = path("build", "match", "test_diff_snd_event_ref.obj")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    mod = match.compile_c(src, None, out, cc=match.file_cc(src))
    d = match.diff_function(p, mod, by_link)
    assert d["matched"] is False
    assert d["score"] > (0, 0, 0, 0, 0)
    assert d["first_diff"] is not None
    assert len(d["lines"]) > 0


def test_classify_pair_categories():
    mk = lambda m, op: {"mnem": m, "op": op, "text": f"{m} {op}".strip()}
    assert match._classify_pair(mk("mov", "esi, eax"), mk("mov", "esi, eax")) == "EQUAL"
    assert match._classify_pair(mk("mov", "esi, eax"), mk("mov", "edi, eax")) == "REG"
    assert match._classify_pair(mk("add", "eax, 0x4"), mk("add", "eax, 0x8")) == "IMM/REL"
    assert match._classify_pair(mk("add", "eax, ebx"), mk("sub", "eax, ebx")) == "OP/STRUCT"


def test_cli_diff_flag():
    r = subprocess.run(
        [sys.executable, "-m", "wc1.match", "src/mod_1b800/snd_event_reference.c", "--diff"],
        capture_output=True, text=True, cwd=path())
    assert r.returncode == 1
    assert "MISMATCH" in r.stdout
    assert "first_diff:" in r.stdout
