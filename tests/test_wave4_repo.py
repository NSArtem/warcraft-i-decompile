"""tests/wave4_repo.py: where the disposable repositories go, and that their removal
is bounded and waits for the private wineserver."""
import os
import shutil
import subprocess
import time

import pytest
import wave4_repo
from wc1 import oldcc

GB = 1 << 30
V1_UNLIMITED = 9223372036854771712


# ----------------------------------------------------------- memory budget ---

@pytest.fixture
def cgroups(tmp_path):
    """make(self lines, {dir: (limit, usage)}) -> cgroup_available()'s arguments."""
    def make(lines, files, v1=False):
        root = tmp_path / "cgroup"
        for d, (limit, usage) in files.items():
            (root / d).mkdir(parents=True, exist_ok=True)
            names = ("memory.limit_in_bytes", "memory.usage_in_bytes") if v1 else ("memory.max", "memory.current")
            for name, v in zip(names, (limit, usage)):
                if v is not None:
                    (root / d / name).write_text(f"{v}\n")
        (tmp_path / "self").write_text(lines)
        return str(tmp_path / "self"), str(root)
    return make


@pytest.mark.parametrize("lines, files, v1, want", [
    ("0::/a/b\n", {"a/b": ("max", 5)}, False, None),                             # no limit
    ("0::/a/b\n", {"a/b": (10 * GB, 4 * GB)}, False, 6 * GB),
    ("0::/a/b\n", {"a/b": ("max", 5), "a": (3 * GB, GB)}, False, 2 * GB),        # an ancestor's limit
    ("0::/a/b\n", {"a/b": (9 * GB, 0), "a": (8 * GB, 7 * GB)}, False, GB),       # the tightest one
    ("0::/a/b\n", {"a/b": (GB, 2 * GB)}, False, -GB),                            # over the limit
    ("0::/\n", {".": (4 * GB, GB)}, False, 3 * GB),                              # cgroup namespace
    ("0::/host/only/path\n", {".": (4 * GB, GB)}, False, 3 * GB),                # no such directory here
    ("0::/../../x\n", {".": (4 * GB, GB)}, False, 3 * GB),                       # outside the namespace
    ("0::/a\n", {"a": (4 * GB, None)}, False, 4 * GB),                           # no usage file
    ("0::/a\n", {"a": ("garbage", 1)}, False, None),
    ("5:cpu,memory:/d/c\n0::/\n", {"memory/d/c": (2 * GB, GB)}, True, GB),       # v1 (hybrid)
    ("5:memory:/d/c\n", {"memory": (2 * GB, GB)}, True, GB),                     # v1 in a container
    ("5:memory:/d\n", {"memory/d": (V1_UNLIMITED, GB)}, True, V1_UNLIMITED - GB),
    ("4:cpu:/d\n", {"memory": (2 * GB, GB)}, True, None),                        # no memory controller
    ("", {}, False, None),
])
def test_cgroup_available(cgroups, lines, files, v1, want):
    assert wave4_repo.cgroup_available(*cgroups(lines, files, v1)) == want


def test_cgroup_available_without_cgroups(tmp_path):
    assert wave4_repo.cgroup_available(str(tmp_path / "none"), str(tmp_path)) is None
    here = wave4_repo.cgroup_available()
    assert here is None or isinstance(here, int)


@pytest.mark.parametrize("allowed, host, tmpfs", [
    (None, 64 * GB, True),
    (8 * GB, 64 * GB, True),
    (8 * GB - 1, 64 * GB, False),           # the container would be killed
    (-GB, 64 * GB, False),
    (64 * GB, 7 * GB, False),               # the host is the limit
    (V1_UNLIMITED, 64 * GB, True),
])
def test_repo_base_respects_the_cgroup_limit(tmp_path, monkeypatch, allowed, host, tmpfs):
    meminfo = tmp_path / "meminfo"
    meminfo.write_text(f"MemTotal: 1 kB\nMemAvailable: {host >> 10} kB\n")
    monkeypatch.setattr(wave4_repo, "NEED", 8 * GB)
    monkeypatch.setattr(wave4_repo, "cgroup_available", lambda: allowed)
    real = os.statvfs(tmp_path)

    class Room:
        f_flag, f_bavail, f_frsize = real.f_flag & ~os.ST_NOEXEC, 1 << 30, 4096
    monkeypatch.setattr(wave4_repo.os, "statvfs", lambda d: Room)
    assert (wave4_repo.repo_base(str(tmp_path), str(meminfo)) == str(tmp_path)) == tmpfs


# ----------------------------------------------------------------- removal ---

@pytest.mark.parametrize("error", [FileNotFoundError(2, "gone"), OSError(39, "not empty"), PermissionError(13, "no")])
def test_removal_deadline_holds_for_every_error(tmp_path, monkeypatch, error):
    """A tree that never goes away is an error after the deadline, whatever rmtree says."""
    clock, calls = [0.0], []

    def rmtree(d):
        calls.append(d)
        assert len(calls) < 1000, "unbounded"
        raise error
    monkeypatch.setattr(wave4_repo.shutil, "rmtree", rmtree)
    monkeypatch.setattr(wave4_repo.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(wave4_repo.time, "sleep", lambda s: clock.__setitem__(0, clock[0] + s))
    with pytest.raises(type(error)):
        wave4_repo.remove_tree(str(tmp_path), timeout=5)
    assert 4.5 < clock[0] < 5.01 and len(calls) > 40


@pytest.mark.parametrize("timeout, took, starts", [
    (0.05, 0.0, [0.0]),                     # the sleep is cut to the deadline
    (0.25, 0.0, [0.0, 0.1, 0.2]),
    (0.25, 0.04, [0.0, 0.14]),              # 0.28 would be late
    (0.1, 0.0, [0.0]),                      # a retry exactly at the deadline is late too
    (5, 7.0, [0.0]),                        # the attempt itself ran past it
    (0, 0.0, [0.0]),                        # always one attempt
])
def test_no_removal_starts_after_the_deadline(tmp_path, monkeypatch, timeout, took, starts):
    clock, calls, slept = [0.0], [], []

    def rmtree(d):
        calls.append(round(clock[0], 6))
        clock[0] += took
        raise OSError(39, "not empty")

    def sleep(s):
        slept.append(s)
        clock[0] += s
    monkeypatch.setattr(wave4_repo.shutil, "rmtree", rmtree)
    monkeypatch.setattr(wave4_repo.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(wave4_repo.time, "sleep", sleep)
    with pytest.raises(OSError):
        wave4_repo.remove_tree(str(tmp_path), timeout)
    assert calls == starts and all(0 < s <= 0.1 for s in slept)
    assert clock[0] <= max(timeout, took) + 1e-9


def test_a_sleep_that_overruns_the_deadline_starts_no_removal(tmp_path, monkeypatch):
    clock, calls = [0.0], []

    def rmtree(d):
        calls.append(clock[0])
        raise OSError(39, "not empty")
    monkeypatch.setattr(wave4_repo.shutil, "rmtree", rmtree)
    monkeypatch.setattr(wave4_repo.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(wave4_repo.time, "sleep", lambda s: clock.__setitem__(0, clock[0] + 60))
    with pytest.raises(OSError):
        wave4_repo.remove_tree(str(tmp_path), timeout=5)
    assert calls == [0.0]


@pytest.mark.parametrize("error", [FileNotFoundError, PermissionError])
def test_removal_of_a_vanished_tree_is_done(tmp_path, monkeypatch, error):
    def rmtree(d):
        os.rmdir(d)                     # somebody else was faster
        raise error()
    d = tmp_path / "d"
    d.mkdir()
    monkeypatch.setattr(wave4_repo.shutil, "rmtree", rmtree)
    wave4_repo.remove_tree(str(d))


def test_removal_retries_an_entry_that_vanished(tmp_path, monkeypatch):
    real, calls = shutil.rmtree, []

    def rmtree(d):
        calls.append(d)
        if len(calls) == 1:
            raise FileNotFoundError(2, "an entry below")
        real(d)
    d = tmp_path / "d"
    (d / "x").mkdir(parents=True)
    monkeypatch.setattr(wave4_repo.shutil, "rmtree", rmtree)
    wave4_repo.remove_tree(str(d))
    assert len(calls) == 2 and not d.exists()


# -------------------------------------------------------------- wineserver ---

@pytest.fixture
def wine_calls(monkeypatch):
    calls = []
    monkeypatch.setattr(oldcc, "kill_wineserver", lambda env: calls.append(("kill", env["WINEPREFIX"])))
    monkeypatch.setattr(wave4_repo, "repo_base", lambda: None)
    return calls


def test_teardown_kills_then_waits_then_removes(monkeypatch, wine_calls, tmp_path):
    ws = tmp_path / "wineserver"
    ws.write_text("")
    ws.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))

    def run(argv, env, timeout, **kw):
        assert os.path.isdir(env["WINEPREFIX"])                 # not removed yet
        wine_calls.append((argv[1], env["WINEPREFIX"], timeout))
        raise subprocess.TimeoutExpired(argv, timeout)          # a server that will not go
    monkeypatch.setattr(wave4_repo.subprocess, "run", run)
    with wave4_repo.disposable_repo("w4t-") as repo:
        wine = repo / "build/wine"
        wine.mkdir(parents=True)
    assert wine_calls == [("kill", str(wine)), ("-w", str(wine), 10)]
    assert not repo.exists()


def test_kill_and_wait_use_the_server_beside_wine(monkeypatch, tmp_path):
    """wineserver is not on PATH: both -k and -w find the one beside wine."""
    bindir, links, log = tmp_path / "bin", tmp_path / "links", tmp_path / "log"
    bindir.mkdir()
    links.mkdir()
    (bindir / "wine").write_text("")
    (bindir / "wineserver").write_text(f'#!{shutil.which("sh")}\necho "$1 $WINEPREFIX" >> {log}\n')
    for f in bindir.iterdir():
        f.chmod(0o755)
    (links / "wine").symlink_to(bindir / "wine")
    monkeypatch.delenv("WC1_WINE", raising=False)
    monkeypatch.setenv("PATH", str(links))
    assert shutil.which("wineserver") is None
    prefix = tmp_path / "prefix"
    wave4_repo.stop_wineserver(prefix)
    assert log.read_text().splitlines() == [f"-k {prefix}", f"-w {prefix}"]


def test_teardown_never_touches_another_prefix(monkeypatch, wine_calls, tmp_path):
    shared = tmp_path / "shared"
    shared.mkdir()
    with wave4_repo.disposable_repo("w4t-") as repo:            # no prefix at all
        pass
    with wave4_repo.disposable_repo("w4t-") as repo:            # the shared one, linked
        (repo / "build").mkdir()
        (repo / "build/wine").symlink_to(shared)
    assert wine_calls == [] and shared.is_dir() and not repo.exists()


def test_the_wait_is_bounded(monkeypatch, wine_calls, tmp_path):
    ws = tmp_path / "wineserver"
    ws.write_text(f"#!{shutil.which('python3')}\nimport time\ntime.sleep(60)\n")
    ws.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))
    t = time.monotonic()
    wave4_repo.stop_wineserver(tmp_path, timeout=0.3)
    assert time.monotonic() - t < 20
