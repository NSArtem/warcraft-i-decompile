"""t4spec.assert_ref_state: near-miss while T4, exact match once promoted to T3 (src =)."""
import pytest

from wc1 import symbols, t4spec


def _fake_load(src):
    return lambda *a, **k: ({1: {"src": src}, 2: {"name": "x"}}, {}, [])


def test_t4_ref_must_not_match(monkeypatch):
    monkeypatch.setattr(symbols, "load", _fake_load("src/other/o.c"))
    t4spec.assert_ref_state("src/a/f_reference.c", ["MISMATCH", "MISMATCH"])
    with pytest.raises(AssertionError, match="promote it"):
        t4spec.assert_ref_state("src/a/f_reference.c", ["MATCH"])


def test_t3_ref_must_match_exactly(monkeypatch):
    monkeypatch.setattr(symbols, "load", _fake_load("src/a/f_reference.c"))
    t4spec.assert_ref_state("src/a/f_reference.c", ["MATCH", "MATCH"])
    for bad in (["MISMATCH"], ["MATCH", "MISMATCH"]):
        with pytest.raises(AssertionError, match="no longer matches"):
            t4spec.assert_ref_state("src/a/f_reference.c", bad)


def test_empty_results_fail(monkeypatch):
    monkeypatch.setattr(symbols, "load", _fake_load("src/x.c"))
    with pytest.raises(AssertionError):
        t4spec.assert_ref_state("src/a/f.c", [])
