"""The analysis.run() result cache (build/cache/analysis-*.pickle) must give
exactly what a fresh discovery gives."""
import os
import pickle

from wc1 import analysis, path


def _fingerprint(p):
    return {
        "func_starts": list(p.func_starts),
        "functions": p.functions,
        "owner": dict(p.owner),
        "table_bytes": set(p.table_bytes),
        "jump_tables": dict(p.jump_tables),
        "call_targets": set(p.call_targets),
        "jump_targets": set(p.jump_targets),
        "ptr_targets": {k: set(v) for k, v in p.ptr_targets.items()},
        "conflicts": list(p.conflicts),
        "seed_kind": dict(p.seed_kind),
        "gaps": p.gaps(),
        "insns": sorted(p.insns),
    }


def test_cached_run_equals_fresh_run(tmp_path, monkeypatch):
    fresh = analysis.run(cache=False)
    cached = analysis.run(cache=True)          # load or create
    again = analysis.run(cache=True)           # certainly a load now
    assert _fingerprint(cached) == _fingerprint(fresh)
    assert _fingerprint(again) == _fingerprint(fresh)
    # the lazily decoded instructions are the same instructions
    for a in list(fresh.insns)[::97]:
        f, c = fresh.insns[a], again.insns[a]
        assert (c.address, c.size, c.bytes, c.mnemonic, c.op_str) == \
               (f.address, f.size, f.bytes, f.mnemonic, f.op_str)
        assert [o.type for o in c.operands] == [o.type for o in f.operands]
    assert 0x10000 - 1 not in again.insns and again.insns.get(-1) is None


def test_each_call_returns_a_fresh_object():
    a, b = analysis.run(), analysis.run()
    assert a is not b and a.functions is not b.functions


def test_key_follows_the_inputs(monkeypatch):
    k = analysis._cache_key(None)
    assert analysis._cache_key(None) == k
    monkeypatch.setattr(analysis, "_CACHE_FORMAT", analysis._CACHE_FORMAT + 1)
    assert analysis._cache_key(None) != k


def test_corrupt_cache_file_is_recomputed(monkeypatch):
    good = analysis.run()
    # a private key, so the shared cache file is never touched
    monkeypatch.setattr(analysis, "_CACHE_FORMAT", -os.getpid())
    f = path("build", "cache", f"analysis-{analysis._cache_key(None)}.pickle")
    os.makedirs(os.path.dirname(f), exist_ok=True)
    with open(f, "wb") as fh:
        fh.write(b"not a pickle")
    try:
        p = analysis.run()
        assert p.func_starts == good.func_starts
        with open(f, "rb") as fh:
            assert pickle.load(fh).func_starts == good.func_starts
    finally:
        os.unlink(f)
