"""Tests for wc1.dossier (one-shot module/function dossier generator)."""
import os

import pytest

from wc1 import dossier, path

pytestmark = pytest.mark.skipif(
    not os.path.exists(path("original", "install", "war.exe")),
    reason="needs original/install/war.exe")


def test_dossier_module_structure():
    d = dossier.build_dossier(["mod_2b8e0"], only_undone=True, max_funcs=3)
    assert d["module"] == "mod_2b8e0"
    assert d["function_count"] == 3
    assert d["compiler"] == "10.0a"
    assert d["dominant_style"] in ("OPT", "DBG", "OD")
    assert len(d["exemplars"]) >= 1
    for fn in d["functions"]:
        assert fn["asm"]
        assert fn["ninsns"] > 0


def test_dossier_markdown_tags_ghidra_as_hint_only():
    d = dossier.build_dossier(["0x119c0"], include_ghidra=True, include_exemplars=False)
    md = dossier.render_markdown(d)
    assert "# Dossier:" in md
    assert "0x119c0" in md
    if d["functions"][0]["ghidra_hint"]:
        assert "GHIDRA HINT ONLY" in md
