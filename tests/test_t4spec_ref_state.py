"""t4spec.assert_ref_results: per-function T3/T4 verification of a C file.

Each function is classified by its own symbol (src = / ref =), never by whether
some other function in the file was promoted.  The _file_level_* functions below
re-implement the old file-level guard to show the mixed cases it got wrong."""
import os

import pytest

from wc1 import symbols, t4spec

F = "src/a/x.c"
OTHER = "src/a/y.c"


def _db(**entries):
    return {n: dict(link_name=n, **e) for n, e in entries.items()}


T3 = {"src": F}
T4 = {"ref": F}


def run(results, db, src=F):
    t4spec.assert_ref_results(src, results, by_link=db)


def R(name, st, probs=()):
    return (name, st, list(probs))


def test_all_t4_mismatch_passes():
    run([R("a_", "MISMATCH"), R("b_", "MISMATCH")], _db(a_=T4, b_=T4))


def test_all_t4_unexpected_match_fails():
    with pytest.raises(AssertionError, match="b_.*promote it"):
        run([R("a_", "MISMATCH"), R("b_", "MATCH")], _db(a_=T4, b_=T4))


def test_all_t3_match_passes():
    run([R("a_", "MATCH"), R("b_", "MATCH")], _db(a_=T3, b_=T3))


def test_all_t3_mismatch_fails():
    with pytest.raises(AssertionError, match="b_.*T3"):
        run([R("a_", "MATCH"), R("b_", "MISMATCH", ["byte +1"])], _db(a_=T3, b_=T3))


def test_mixed_match_mismatch_passes():
    run([R("foo_", "MATCH"), R("bar_", "MISMATCH")], _db(foo_=T3, bar_=T4))


def test_mixed_t3_mismatch_fails():
    with pytest.raises(AssertionError, match="foo_.*T3"):
        run([R("foo_", "MISMATCH"), R("bar_", "MISMATCH")], _db(foo_=T3, bar_=T4))


def test_mixed_t4_unexpected_match_fails_actionably():
    with pytest.raises(AssertionError) as ei:
        run([R("foo_", "MATCH"), R("bar_", "MATCH")], _db(foo_=T3, bar_=T4))
    msg = str(ei.value)
    assert "bar_" in msg and "promote it to T3" in msg
    assert "foo_" not in msg


@pytest.mark.parametrize("meta", [{"src": OTHER}, {"ref": OTHER}, {}])
def test_foreign_owned_duplicate_must_stay_a_near_miss(meta):
    run([R("a_", "MISMATCH")], _db(a_=meta))
    with pytest.raises(AssertionError, match="duplicate copy"):
        run([R("a_", "MATCH")], _db(a_=meta))


def test_unknown_link_name_fails_closed():
    with pytest.raises(AssertionError, match="ghost_.*no symbol entry"):
        run([R("a_", "MISMATCH"), R("ghost_", "MISMATCH")], _db(a_=T4))
    with pytest.raises(AssertionError, match="no symbol entry"):
        run([R("ghost_", "UNKNOWN")], {})


@pytest.mark.parametrize("meta", [
    {"src": F, "ref": F},          # both
    {"src": OTHER, "ref": F},
])
def test_inconsistent_metadata_fails_closed(meta):
    with pytest.raises(AssertionError):
        run([R("a_", "MISMATCH")], _db(a_=meta))
    with pytest.raises(AssertionError):
        run([R("a_", "MATCH")], _db(a_=meta))


def test_path_normalization_separates_files(tmp_path):
    root = symbols.path()
    unnormalized = os.path.join(root, "src", "a", "..", "a", "x.c")
    run([R("a_", "MATCH")], _db(a_=T3), src=unnormalized)       # same file, other spelling
    run([R("a_", "MISMATCH")], _db(a_={"ref": F}), src=unnormalized)
    # src/a/x.c vs src/a/xx.c / src/b/x.c are different files
    for other in ("src/a/xx.c", "src/b/x.c", "src/a/x.c.c"):
        with pytest.raises(AssertionError, match="owned by"):
            run([R("a_", "MATCH")], _db(a_=T3), src=os.path.join(root, other))
        run([R("a_", "MISMATCH")], _db(a_=T3), src=os.path.join(root, other))


def test_data_result_strict_when_object_has_t3_function():
    d = _db(foo_=T3, bar_=T4)
    run([R("foo_", "MATCH"), R("bar_", "MISMATCH"), R("[CONST @ 0x1, 4 bytes]", "MATCH")], d)
    with pytest.raises(AssertionError, match="CONST.*MISMATCH"):
        run([R("foo_", "MATCH"), R("bar_", "MISMATCH"), R("[CONST @ 0x1, 4 bytes]", "MISMATCH", ["x"])], d)
    with pytest.raises(AssertionError, match="_DATA.*MISMATCH"):
        run([R("foo_", "MATCH"), R("[_DATA @ 0x1, 4 bytes]", "MISMATCH")], _db(foo_=T3))


def test_data_result_alone_is_no_promotion_signal_for_t4_object():
    run([R("a_", "MISMATCH"), R("[CONST @ 0x1, 4 bytes]", "MISMATCH")], _db(a_=T4))
    run([R("a_", "MISMATCH"), R("[CONST @ 0x1, 4 bytes]", "MATCH")], _db(a_=T4))


def test_empty_and_data_only_results_fail():
    with pytest.raises(AssertionError):
        run([], _db(a_=T4))
    with pytest.raises(AssertionError, match="no function results"):
        run([R("[CONST @ 0x1, 4 bytes]", "MISMATCH")], _db(a_=T4))


def test_sweep_style_statuses_on_t3_function_fail():
    for st in ("RELOC bad", "DATA x", "EMPTY"):
        with pytest.raises(AssertionError, match="T3"):
            run([R("a_", st)], _db(a_=T3))


def test_t4_unknown_status_is_not_a_match():
    run([R("a_", "UNKNOWN")], _db(a_=T4))


def test_default_db_comes_from_symbols_load(monkeypatch):
    funcs = {1: {"link_name": "a_", "ref": F}, 2: {"link_name": "b_", "src": F}}
    monkeypatch.setattr(symbols, "load", lambda *a, **k: (funcs, {}, []))
    t4spec.assert_ref_results(F, [R("a_", "MISMATCH"), R("b_", "MATCH")])
    with pytest.raises(AssertionError):
        t4spec.assert_ref_results(F, [R("a_", "MATCH"), R("b_", "MATCH")])


def test_sweep_results_use_symbol_at_row_address():
    by_addr = {0x10: {"link_name": "a_"}}
    assert t4spec.sweep_results([("a", 0x10, "MISMATCH", b"", b""), ("zz", 0x20, "MISMATCH", b"", b"")], by_addr) \
        == [("a_", "MISMATCH", []), ("?zz@0x20", "MISMATCH", [])]
    with pytest.raises(AssertionError, match="no symbol entry"):
        run(t4spec.sweep_results([("zz", 0x20, "MISMATCH")], by_addr), _db(a_=T4))


# ---- mutation: the previous file-level guard
def _file_level_guard(rel, results, db):
    promoted = any(e.get("src") == rel for e in db.values())
    statuses = [s for _, s, _ in results]
    if promoted:
        assert all(s == "MATCH" for s in statuses)
    else:
        assert all(s != "MATCH" for s in statuses)


def test_mutation_file_level_guard_mishandles_mixed_files():
    db = _db(foo_=T3, bar_=T4)
    good = [R("foo_", "MATCH"), R("bar_", "MISMATCH")]
    with pytest.raises(AssertionError):                 # rejects a correct mixed file
        _file_level_guard(F, good, db)
    run(good, db)
    # mixed file where the T4 function starts matching while T3 is broken-free:
    # old guard (promoted -> all MATCH) accepts it silently
    bad = [R("foo_", "MATCH"), R("bar_", "MATCH")]
    _file_level_guard(F, bad, db)
    with pytest.raises(AssertionError):
        run(bad, db)
    # a symbol with both src and ref: the old guard accepts it, per-function fails closed
    both = _db(foo_={"src": F, "ref": F})
    _file_level_guard(F, [R("foo_", "MATCH")], both)
    with pytest.raises(AssertionError, match="inconsistent"):
        run([R("foo_", "MATCH")], both)
