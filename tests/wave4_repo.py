"""Shared setup of the disposable repositories of the Wave 4 end-to-end tests."""
import contextlib
import filecmp
import os
from pathlib import Path
import shutil
import tempfile
import time

from wc1 import analysis, path


NEED = 8 << 30                  # every disposable repository at once, 0.55 GB each


def repo_base(shm="/dev/shm"):
    """Short directory for the repositories (Watcom 10.0a can crash on long paths).
    A tmpfs when it has room: each repository copies a 540 MB Wine prefix, and doing
    that on btrfs blocked the whole machine for seconds (space reservation), long
    enough to fail unrelated wall-clock tests."""
    try:
        st = os.statvfs(shm)
        with open("/proc/meminfo") as fh:
            avail = next(int(l.split()[1]) << 10 for l in fh if l.startswith("MemAvailable:"))
        if (os.access(shm, os.W_OK | os.X_OK) and not st.f_flag & os.ST_NOEXEC
                and min(st.f_bavail * st.f_frsize, avail) >= NEED):
            return shm
    except (OSError, StopIteration):
        pass
    return "/tmp/opencode" if os.path.isdir("/tmp/opencode") else "/tmp"


@contextlib.contextmanager
def disposable_repo(prefix):
    """A temporary repository directory.  A wineserver killed by the test still
    flushes its registry into the prefix while it exits, so the removal is retried
    until nothing writes there any more; what cannot be removed is an error."""
    directory = tempfile.mkdtemp(prefix=prefix, dir=repo_base())
    try:
        yield Path(directory)
    finally:
        deadline = time.monotonic() + 20
        while True:
            try:
                shutil.rmtree(directory)
                break
            except FileNotFoundError:
                if not os.path.exists(directory):
                    break
            except OSError:
                if time.monotonic() > deadline:
                    raise
            time.sleep(0.1)


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
