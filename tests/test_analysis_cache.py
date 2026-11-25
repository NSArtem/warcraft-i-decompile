"""The analysis.run() result cache (build/cache/analysis-*.pickle) must give
exactly what a fresh discovery gives."""
import os
import pickle
import shutil
import subprocess
import sys

import pytest
import wave4_repo
import wc1
from wave4_repo import seed_analysis_cache
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


def _inputs(root, modules, exe):
    (root / "analysis").mkdir(parents=True)
    (root / "analysis" / "modules.toml").write_bytes(modules)
    (root / "war.exe").write_bytes(exe)
    return str(root / "war.exe")


def test_key_is_content_addressed(tmp_path, monkeypatch):
    """Same inputs at two paths: one key; any changed input: another key."""
    def key(name, modules, exe):
        root = tmp_path / name
        f = _inputs(root, modules, exe)
        with monkeypatch.context() as m:
            m.setattr(wc1, "path", lambda *p: os.path.join(str(root), *p))
            return analysis._cache_key(f)

    k = key("a", b"modules", b"exe")
    assert key("a_much_longer_name", b"modules", b"exe") == k
    assert len({k, key("c", b"modulez", b"exe"), key("d", b"modules", b"exf"),
                key("e", b"exe", b"modules"), key("f", b"", b"exe")}) == 5
    # the tool sources and the runtime versions are inputs too
    monkeypatch.setattr(analysis, "_CACHE_INPUTS", analysis._CACHE_INPUTS[:-1])
    assert key("g", b"modules", b"exe") != k


def test_real_key_does_not_depend_on_where_the_inputs_are(tmp_path, monkeypatch):
    k = analysis._cache_key(None)
    with open(path("analysis", "modules.toml"), "rb") as m, open(wc1.ORIGINAL_EXE, "rb") as e:
        f = _inputs(tmp_path / "copy", m.read(), e.read())
    monkeypatch.setattr(wc1, "path", lambda *p: os.path.join(str(tmp_path / "copy"), *p))
    assert analysis._cache_key(f) == k
    with open(f, "ab") as fh:
        fh.write(b"\0")
    assert analysis._cache_key(f) != k


def test_seeded_cache_file_is_used_only_for_identical_inputs(tmp_path):
    analysis.run()                             # makes sure the parent has the file
    repo = tmp_path / "repo"
    _inputs(repo, b"", b"")
    (repo / "original" / "install").mkdir(parents=True)
    (repo / "original" / "install" / "war.exe").symlink_to(wc1.ORIGINAL_EXE)
    modules = repo / "analysis" / "modules.toml"
    assert not seed_analysis_cache(repo) and not (repo / "build").exists()   # other modules.toml
    with open(path("analysis", "modules.toml"), "rb") as fh:
        modules.write_bytes(fh.read())
    assert seed_analysis_cache(repo)

    code = ("import sys\nfrom wc1 import analysis\n"
            "def cold(*a): raise SystemExit('cold discovery')\n"
            "analysis.Program.discover = cold\n"
            "print(len(analysis.run().functions))\n")

    def child():
        return subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                              env=dict(os.environ, WC1_ROOT=str(repo)), cwd=path("tools"))
    r = child()
    assert r.returncode == 0 and int(r.stdout) == len(analysis.run().functions), r.stderr
    with open(modules, "ab") as fh:            # the child's own inputs changed
        fh.write(b"\n# edited\n")
    r = child()
    assert r.returncode != 0 and "cold discovery" in r.stderr, r.stdout + r.stderr


def test_repo_base_is_a_writable_exec_directory_with_room(tmp_path, monkeypatch):
    old = "/tmp/opencode" if os.path.isdir("/tmp/opencode") else "/tmp"
    assert wave4_repo.repo_base(str(tmp_path / "missing")) == old
    assert os.access(wave4_repo.repo_base(), os.W_OK | os.X_OK)
    monkeypatch.setattr(wave4_repo, "NEED", 0)
    assert wave4_repo.repo_base(str(tmp_path)) == str(tmp_path)
    monkeypatch.setattr(wave4_repo, "NEED", 1 << 60)         # no room
    assert wave4_repo.repo_base(str(tmp_path)) == old


def test_disposable_repo_survives_a_late_writer(monkeypatch):
    """A process that still writes while the repository is removed (a wineserver
    flushing its registry) only delays the removal."""
    real, calls = shutil.rmtree, []

    def rmtree(d):
        calls.append(d)
        if len(calls) == 1:
            raise OSError(39, "Directory not empty")
        real(d)
    monkeypatch.setattr(wave4_repo.shutil, "rmtree", rmtree)
    with pytest.raises(ZeroDivisionError):         # also when the test failed
        with wave4_repo.disposable_repo("w4t-") as repo:
            (repo / "build/wine").mkdir(parents=True)
            1 / 0
    assert len(calls) == 2 and not repo.exists()
