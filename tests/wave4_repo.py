"""Shared setup of the disposable repositories of the Wave 4 end-to-end tests."""
import filecmp
import os
from pathlib import Path
import shutil

from wc1 import analysis, path


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
