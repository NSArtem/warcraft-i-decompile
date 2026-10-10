"""wc1.ghidra_decomp input preparation (Ghidra itself is not run here)."""
import os

import pytest

from wc1 import analysis, ghidra_decomp, path, symbols

pytestmark = pytest.mark.skipif(not os.path.exists(path("original", "install", "war.exe")),
                                reason="needs original/ (make extract)")


def test_prepare_meta(tmp_path, monkeypatch):
    monkeypatch.setattr(ghidra_decomp, "INPUT", str(tmp_path))
    meta = ghidra_decomp.prepare(verbose=False)
    p = analysis.run()
    funcs, _, _ = symbols.load()

    assert [f["start"] for f in meta["functions"]] == sorted(f["start"] for f in p.functions)
    assert os.path.getsize(tmp_path / "code.bin") == meta["code"]["size"]
    assert os.path.getsize(tmp_path / "data.bin") == meta["data"]["size"]
    names = {f["start"]: f["name"] for f in meta["functions"]}
    assert names[0x1d7cc] == "InitPaths"
    assert all(names[a] == e["name"] for a, e in funcs.items())

    lines = (tmp_path / "meta.txt").read_text().splitlines()
    kinds = {}
    for ln in lines:
        if ln.startswith("#"):
            continue
        k = ln.split(" ")[0]
        assert k in ("CODE", "DATA", "F", "D", "P"), ln
        assert len(ln.split(" ")) == {"CODE": 4, "DATA": 4, "F": 4, "D": 3, "P": 4}[k], ln
        kinds[k] = kinds.get(k, 0) + 1
    assert kinds["F"] == len(meta["functions"])
    assert kinds["P"] == meta["fixups_in_data"]
