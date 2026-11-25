"""Shared setup of the disposable repositories of the Wave 4 end-to-end tests."""
from collections import Counter
import contextlib
import filecmp
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tempfile
import time

from wc1 import analysis, oldcc, path


NEED = 8 << 30                  # every disposable repository at once, 0.55 GB each


def _unescape(s):
    r"""A field of mountinfo: \040 \011 \012 \134 are octal escapes."""
    return re.sub(r"\\([0-7]{3})", lambda m: chr(int(m[1], 8)), s)


def _cgroup_mounts(mountinfo):
    """Memory cgroup mounts and counts of all mounts at each mount point."""
    out, mountpoints = [], Counter()
    with open(mountinfo, errors="surrogateescape") as fh:
        for line in fh:
            mount, _, fs = line.partition(" - ")
            mount, fs = mount.split(), fs.split()
            if len(mount) < 6 or len(fs) < 3:
                raise ValueError("invalid mountinfo entry")
            top = _unescape(mount[4])
            mountpoints[top] += 1
            if fs[0] == "cgroup2" or fs[0] == "cgroup" and "memory" in fs[2].split(","):
                major, minor = map(int, mount[2].split(":"))
                out.append((fs[0] == "cgroup2", _unescape(mount[3]), top, os.makedev(major, minor)))
    return out, mountpoints


def _headroom(directory, limit, usage, total):
    """Bytes the limit of one cgroup directory still allows; None without one.  A limit
    below `total` whose usage cannot be read allows nothing, as does an unreadable limit."""
    try:
        with open(os.path.join(directory, limit)) as fh:
            value = fh.read().strip()
    except (FileNotFoundError, NotADirectoryError):
        return None                     # a root cgroup, or the controller is not enabled
    except OSError:
        return 0
    if value == "max":
        return None
    try:
        value = int(value)
    except ValueError:
        return 0
    try:
        with open(os.path.join(directory, usage)) as fh:
            return value - int(fh.read())
    except (OSError, ValueError):
        return 0 if total is None or value < total else None


def _ram():
    try:
        return os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE")
    except (OSError, ValueError):
        return None


INIT_NS = "cgroup:[4026531835]"         # the initial cgroup namespace (PROC_CGROUP_INIT_INO)


def _all_ancestors(ns):
    """Whether the paths of this process start at the real root of the hierarchies: in
    a cgroup namespace they start at its root, and the groups above are invisible."""
    try:
        return os.readlink(ns) == INIT_NS
    except FileNotFoundError:
        return True                     # a kernel without cgroup namespaces
    except OSError:
        return False


def cgroup_available(proc="/proc/self/cgroup", mountinfo="/proc/self/mountinfo", total=None,
                     ns="/proc/self/ns/cgroup"):
    """Bytes the memory cgroups of this process still allow (a limit of any ancestor
    counts), or None without a finite limit.  Page cache counts as used, so this is
    on the low side; what cannot be measured counts as 0 (the caller uses the disk):
    also when the group is unknown, or an ancestor of it is not visible.
    `total`: RAM of the host (a limit at or above it is none)."""
    total = total or _ram()
    try:
        mounts, mountpoints = _cgroup_mounts(mountinfo)
    except (OSError, ValueError, OverflowError):
        return 0
    try:
        with open(proc, errors="surrogateescape") as fh:
            lines = [l.split(":", 2) for l in fh.read().splitlines() if l.count(":") > 1]
    except FileNotFoundError:
        return 0 if mounts else None    # None: a system without cgroups
    except OSError:
        return 0
    groups = [(not controllers, group) for _, controllers, group in lines
              if not controllers or "memory" in controllers.split(",")]
    if groups and not _all_ancestors(ns):
        return 0
    found, unseen = [], []
    for v2, group in groups:
        names = ("memory.max", "memory.current") if v2 else ("memory.limit_in_bytes", "memory.usage_in_bytes")
        seen = False
        for m_v2, root, top, mount_dev in mounts:
            if m_v2 != v2 or root != "/" or ".." in group.split("/"):
                continue                # this mount does not show the group and all its ancestors
            rel = group.strip("/")
            directories = []
            while True:                 # up to the mount point, the root
                directory = os.path.join(top, rel) if rel else top
                expected_mounts = 0 if rel else 1
                if mountpoints[directory] > expected_mounts:
                    return 0            # even a bind mount on the same device can cover a cgroup
                try:
                    entry = os.stat(directory)
                except OSError:
                    return 0
                if entry.st_dev != mount_dev or not stat.S_ISDIR(entry.st_mode):
                    return 0
                directories.append(directory)
                if not rel:
                    break
                rel = os.path.dirname(rel)
            seen = True
            for directory in directories:
                h = _headroom(directory, *names, total)
                if h is not None:
                    found.append(h)
        if not seen:
            unseen.append(v2)
    # The memory controller is in one hierarchy: a v2 hierarchy that is not mounted does
    # not matter beside a v1 one (hybrid).  Otherwise the limits are unknown.
    if unseen and not (unseen == [True] and len(groups) > 1):
        found.append(0)
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
    ws = oldcc.find_wineserver(env)     # the server that was killed
    if ws:
        try:
            subprocess.run([ws, "-w"], env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=timeout)
        except (OSError, subprocess.SubprocessError):
            pass                        # the removal below has its own deadline


def remove_tree(directory, timeout=20):
    """rmtree, retried while something still writes there; what cannot be removed
    in `timeout` seconds is an error.  No attempt starts at or after the deadline."""
    deadline = time.monotonic() + timeout
    while True:
        try:
            shutil.rmtree(directory)
            return
        except OSError:                 # FileNotFoundError: an entry that vanished meanwhile
            if not os.path.lexists(directory):
                return
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise
            time.sleep(min(0.1, remaining))
            if time.monotonic() >= deadline:
                raise


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
    if key is None:
        return False
    src = path("build", "cache", f"analysis-{key}.pickle")
    if not os.path.isfile(src):
        return False
    dst = repo / "build/cache" / os.path.basename(src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    return True
