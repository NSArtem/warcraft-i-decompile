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

HOST = 64 * GB                  # RAM
V1_FILES = ("memory.limit_in_bytes", "memory.usage_in_bytes")
OTHER_MOUNTS = ("22 1 0:21 / /proc rw,nosuid - proc proc rw\n"
                "23 1 0:22 / /sys/fs/cgroup ro - tmpfs tmpfs ro,mode=755\n"
                "24 23 0:23 / /sys/fs/cgroup/cpu rw shared:9 - cgroup cgroup rw,cpu,cpuacct\n")


@pytest.fixture
def cgroups(tmp_path):
    """make(self lines, {dir: (limit, usage)}, mounts) -> cgroup_available()'s arguments.
    mounts: (root, directory, fstype, super options); None = an unmounted hierarchy."""
    def make(lines, files, mounts=(("/", "cg", "cgroup2", "rw,nsdelegate"),)):
        info = OTHER_MOUNTS
        for i, (root, d, fs, options) in enumerate(mounts):
            top = tmp_path / d
            top.mkdir(parents=True, exist_ok=True)
            where = str(top).replace("\\", "\\134").replace(" ", "\\040")
            optional = "shared:5 master:1 " * (i % 2 == 0)      # any number of optional fields
            info += f"{30 + i} 23 0:{30 + i} {root} {where} rw,relatime {optional}- {fs} {fs} {options}\n"
        for d, (limit, usage) in files.items():
            (tmp_path / d).mkdir(parents=True, exist_ok=True)
            names = V1_FILES if d.startswith("v1") else ("memory.max", "memory.current")
            for name, v in zip(names, (limit, usage)):
                if v is not None:
                    (tmp_path / d / name).write_text(f"{v}\n")
        (tmp_path / "self").write_text(lines)
        (tmp_path / "mountinfo").write_text(info)
        return str(tmp_path / "self"), str(tmp_path / "mountinfo"), HOST
    return make


@pytest.mark.parametrize("lines, files, want", [
    ("0::/a/b\n", {"cg/a/b": ("max", 5)}, None),                                  # no limit
    ("0::/a/b\n", {"cg/a/b": (10 * GB, 4 * GB)}, 6 * GB),
    ("0::/a/b\n", {"cg/a/b": ("max", 5), "cg/a": (3 * GB, GB)}, 2 * GB),          # an ancestor's limit
    ("0::/a/b\n", {"cg/a/b": (9 * GB, 0), "cg/a": (8 * GB, 7 * GB)}, GB),         # the tightest one
    ("0::/a/b\n", {"cg/a/b": (GB, 2 * GB)}, -GB),                                 # over the limit
    ("0::/\n", {"cg": (4 * GB, GB)}, 3 * GB),                                     # cgroup namespace
    ("0::/\n", {}, None),                                                         # the root cgroup has no limit
    ("0::/a\n", {"cg/a": (None, 5)}, None),                                       # no memory controller there
    ("", {}, None),
    # what cannot be measured counts as nothing
    ("0::/a\n", {"cg/a": (4 * GB, None)}, 0),                                     # no usage file
    ("0::/a/b\n", {"cg/a/b": (40 * GB, GB), "cg/a": (50 * GB, None)}, 0),         # an ancestor's
    ("0::/a\n", {"cg/a": (4 * GB, "garbage")}, 0),
    ("0::/a\n", {"cg/a": ("garbage", 1)}, 0),
    ("0::/host/only/path\n", {"cg": (4 * GB, GB)}, 0),                            # mount does not show the group
    ("0::/../../x\n", {"cg": (4 * GB, GB)}, 0),                                   # outside the namespace
    # ... except a limit that is none
    ("0::/a\n", {"cg/a": (HOST, None)}, None),
    ("0::/a\n", {"cg/a": ("max", None)}, None),
])
def test_cgroup_available(cgroups, lines, files, want):
    assert wave4_repo.cgroup_available(*cgroups(lines, files)) == want


@pytest.mark.parametrize("options", ["rw,memory", "rw,cpu,memory", "rw,memory,hugetlb", "rw,seclabel,cpu,cpuacct,memory"])
@pytest.mark.parametrize("lines, root, files, want", [
    ("5:%s:/d/c\n", "/", {"v1/d/c": (2 * GB, GB)}, GB),
    ("5:%s:/d/c\n0::/\n", "/", {"v1/d/c": (V1_UNLIMITED, GB), "v1/d": (3 * GB, GB)}, 2 * GB),    # hybrid, no v2 mount
    ("5:%s:/docker/c\n", "/docker/c", {"v1": (2 * GB, GB)}, GB),                  # a container sees its own only
    ("5:%s:/d\n", "/", {"v1/d": (V1_UNLIMITED, GB)}, V1_UNLIMITED - GB),
    ("5:%s:/d\n", "/", {"v1/d": (V1_UNLIMITED, None)}, None),
    ("5:%s:/d\n", "/", {"v1/d": (2 * GB, None)}, 0),
    ("5:%s:/d\n", "/e", {"v1": (2 * GB, GB)}, 0),                                 # another group's mount
])
def test_cgroup_v1_memory_controller(cgroups, options, lines, root, files, want):
    """The controller is found by its mount, whatever it is combined with or mounted at."""
    lines %= ",".join(o for o in options.split(",") if o not in ("rw", "seclabel"))
    assert wave4_repo.cgroup_available(*cgroups(lines, files, [(root, "v1", "cgroup", options)])) == want


@pytest.mark.parametrize("group, mounts, files, want", [
    # a subtree mount: paths below its root, the limit of the root itself too
    ("/sys/me/run", [("/sys/me", "cg", "cgroup2", "rw")], {"cg/run": ("max", 0), "cg": (5 * GB, GB)}, 4 * GB),
    ("/sys/me", [("/sys/me", "cg", "cgroup2", "rw")], {"cg": (5 * GB, GB)}, 4 * GB),
    ("/sys/me2", [("/sys/me", "cg", "cgroup2", "rw")], {"cg": (5 * GB, GB)}, 0),  # no prefix of a name
    # of several mounts those that show the group count
    ("/a", [("/b", "other", "cgroup2", "rw"), ("/", "cg", "cgroup2", "rw")],
     {"other": (GB, GB), "cg/a": (5 * GB, GB)}, 4 * GB),
    ("/a", [("/", "cg", "cgroup2", "rw"), ("/a", "own", "cgroup2", "rw")],
     {"own": (5 * GB, GB), "cg/a": (5 * GB, GB), "cg": (3 * GB, GB)}, 2 * GB),
    ("/a", [("/", "cg", "cgroup2", "rw"), ("/a", "covered/x", "tmpfs", "rw,memory")], {"cg/a": (5 * GB, GB)}, 4 * GB),
    # the mount point needs unescaping
    ("/a", [("/", "with space\\x", "cgroup2", "rw")], {"with space\\x/a": (5 * GB, GB)}, 4 * GB),
    # mounted from another cgroup namespace
    ("/", [("/../..", "cg", "cgroup2", "rw")], {"cg": (5 * GB, GB)}, 0),
    ("/a", [], {}, 0),
])
def test_cgroup_v2_mounts(cgroups, group, mounts, files, want):
    assert wave4_repo.cgroup_available(*cgroups(f"0::{group}\n", files, mounts)) == want


def test_hybrid_hierarchies_both_count(cgroups):
    mounts = [("/", "cg", "cgroup2", "rw"), ("/", "v1", "cgroup", "rw,memory")]
    lines = "0::/a\n7:memory:/a\n3:cpu:/a\n"
    files = {"cg/a": (None, None), "v1/a": (5 * GB, GB)}
    assert wave4_repo.cgroup_available(*cgroups(lines, files, mounts)) == 4 * GB
    assert wave4_repo.cgroup_available(*cgroups(lines, files, mounts[:1])) == 0      # the v1 one is hidden
    assert wave4_repo.cgroup_available(*cgroups("3:cpu:/a\n", {}, mounts)) is None


@pytest.mark.parametrize("denied", ["memory.current", "memory.max"])
@pytest.mark.parametrize("error", [PermissionError(13, "denied"), OSError(19, "no such device")])
def test_unreadable_budget_falls_back_to_the_disk(cgroups, tmp_path, monkeypatch, denied, error):
    """A finite limit that cannot be measured never becomes headroom."""
    args = cgroups("0::/a\n", {"cg/a": (32 * GB, GB)})
    real, refuse = open, []

    def opener(f, *a, **kw):
        if refuse and str(f).endswith(denied):
            raise error
        return real(f, *a, **kw)
    monkeypatch.setattr("builtins.open", opener)
    (tmp_path / "meminfo").write_text(f"MemAvailable: {60 * GB >> 10} kB\n")
    available = wave4_repo.cgroup_available
    monkeypatch.setattr(wave4_repo, "cgroup_available", lambda: available(*args))
    st = os.statvfs(tmp_path)

    class Room:
        f_flag, f_bavail, f_frsize = st.f_flag & ~os.ST_NOEXEC, 1 << 30, 4096
    monkeypatch.setattr(wave4_repo.os, "statvfs", lambda d: Room)

    def base():
        return wave4_repo.repo_base(str(tmp_path), str(tmp_path / "meminfo"))
    assert available(*args) == 31 * GB and base() == str(tmp_path)
    refuse.append(True)
    assert available(*args) == 0
    assert base() == ("/tmp/opencode" if os.path.isdir("/tmp/opencode") else "/tmp")


def test_cgroup_available_without_cgroups(tmp_path, cgroups):
    proc, mountinfo, _ = cgroups("0::/a\n", {"cg/a": (2 * GB, GB)})
    none = str(tmp_path / "none")
    assert wave4_repo.cgroup_available(none, mountinfo) is None
    assert wave4_repo.cgroup_available(proc, none) == 0              # limits, but nowhere to read them
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
