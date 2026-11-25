"""Shared setup of the disposable repositories of the Wave 4 end-to-end tests."""
import contextlib
import filecmp
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

from wc1 import analysis, oldcc, path


NEED = 8 << 30                  # every disposable repository at once, 0.55 GB each


def _int(filename):
    """Integer content of a cgroup file; None for "max" or an unreadable file."""
    try:
        with open(filename) as fh:
            return int(fh.read())
    except (OSError, ValueError):
        return None


def cgroup_available(proc="/proc/self/cgroup", root="/sys/fs/cgroup"):
    """Bytes the memory cgroups of this process still allow (a limit of any ancestor
    counts), or None without a finite limit.  Page cache counts as used, so this is
    on the low side.  In a container the path of /proc/self/cgroup may not exist
    below `root`, which then is the cgroup itself: the walk ends there."""
    try:
        with open(proc) as fh:
            lines = fh.read().splitlines()
    except OSError:
        return None
    found = []
    for line in lines:
        _, controllers, group = line.split(":", 2)
        if not controllers:                                     # v2
            top, limit, usage = root, "memory.max", "memory.current"
        elif "memory" in controllers.split(","):                # v1
            top, limit, usage = os.path.join(root, "memory"), "memory.limit_in_bytes", "memory.usage_in_bytes"
        else:
            continue
        group = os.path.normpath("/" + group.lstrip("/"))       # never above `top`
        while True:
            d = top + group.rstrip("/")
            lim, use = _int(os.path.join(d, limit)), _int(os.path.join(d, usage))
            if lim is not None:
                found.append(lim - (use or 0))
            if group == "/":
                break
            group = os.path.dirname(group)
    return min(found, default=None)


def repo_base(shm="/dev/shm", meminfo="/proc/meminfo"):
    """Short directory for the repositories (Watcom 10.0a can crash on long paths).
    A tmpfs when it has room: each repository copies a 540 MB Wine prefix, and doing
    that on btrfs blocked the whole machine for seconds (space reservation), long
    enough to fail unrelated wall-clock tests."""
    try:
        st = os.statvfs(shm)
        with open(meminfo) as fh:
            avail = next(int(l.split()[1]) << 10 for l in fh if l.startswith("MemAvailable:"))
        allowed = cgroup_available()
        if allowed is not None:
            avail = min(avail, allowed)
        if (os.access(shm, os.W_OK | os.X_OK) and not st.f_flag & os.ST_NOEXEC
                and min(st.f_bavail * st.f_frsize, avail) >= NEED):
            return shm
    except (OSError, StopIteration):
        pass
    return "/tmp/opencode" if os.path.isdir("/tmp/opencode") else "/tmp"


def stop_wineserver(prefix, timeout=10):
    """End the wineserver of a private Wine prefix and wait, at most `timeout` seconds,
    until it is gone (it flushes its registry into the prefix while it exits)."""
    env = dict(os.environ, WINEPREFIX=str(prefix))
    oldcc.kill_wineserver(env)
    ws = shutil.which("wineserver")
    if ws:
        try:
            subprocess.run([ws, "-w"], env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=timeout)
        except (OSError, subprocess.SubprocessError):
            pass                        # the removal below has its own deadline


def remove_tree(directory, timeout=20):
    """rmtree, retried while something still writes there; what cannot be removed
    in `timeout` seconds is an error."""
    deadline = time.monotonic() + timeout
    while True:
        try:
            shutil.rmtree(directory)
            return
        except OSError:                 # FileNotFoundError: an entry that vanished meanwhile
            if not os.path.lexists(directory):
                return
            if time.monotonic() > deadline:
                raise
        time.sleep(0.1)


@contextlib.contextmanager
def disposable_repo(prefix):
    """A temporary repository directory; its private wineserver (build/wine) is
    stopped before the directory is removed."""
    directory = tempfile.mkdtemp(prefix=prefix, dir=repo_base())
    try:
        yield Path(directory)
    finally:
        wine = os.path.join(directory, "build", "wine")
        if os.path.isdir(wine) and os.path.realpath(wine).startswith(os.path.realpath(directory) + os.sep):
            stop_wineserver(wine)       # never the shared prefix
        remove_tree(directory)


def seed_analysis_cache(repo):
    """Copy the parent's analysis.run() cache file into `repo`'s build/cache/, as an
    earlier run in that repository would have left it, so every subprocess there
    skips the cold discovery (6 s).  Nothing is trusted: the file is found by the
    content key of the same inputs, and the child recomputes the key from its own
    files before it looks at it.  Returns whether a file was copied."""
    repo = Path(repo)
    if not filecmp.cmp(path("analysis", "modules.toml"), repo / "analysis/modules.toml", shallow=False):
        return False
    key = analysis._cache_key(str(repo / "original/install/war.exe"))
    src = path("build", "cache", f"analysis-{key}.pickle")
    if not os.path.isfile(src):
        return False
    dst = repo / "build/cache" / os.path.basename(src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    return True
