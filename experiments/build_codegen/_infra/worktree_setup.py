"""Create and isolate per-experiment Git worktrees (Section 5.1 & 5.2)."""
import argparse
import json
import os
import shutil
import subprocess
import sys

from . import MAIN_REPO, WT_ROOT


def _run(cmd, cwd=None, check=True):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"Command failed ({r.returncode}): {' '.join(cmd)}\n{r.stdout}\n{r.stderr}")
    return r


def setup_worktree(name, base_ref, branch=None, detach=False):
    wt_path = os.path.join(WT_ROOT, name)
    os.makedirs(WT_ROOT, exist_ok=True)
    base_sha = _run(["git", "rev-parse", base_ref], cwd=MAIN_REPO).stdout.strip()

    if os.path.isdir(wt_path):
        # Verify existing worktree
        cur_sha = _run(["git", "rev-parse", "HEAD"], cwd=wt_path).stdout.strip()
        cur_br = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=wt_path).stdout.strip()
    else:
        if detach:
            _run(["git", "worktree", "add", "--detach", wt_path, base_sha], cwd=MAIN_REPO)
            cur_br = "HEAD"
        else:
            assert branch, "branch required when detach=False"
            # Check if branch exists
            chk = _run(["git", "show-ref", "--verify", f"refs/heads/{branch}"], cwd=MAIN_REPO, check=False)
            if chk.returncode == 0:
                _run(["git", "worktree", "add", wt_path, branch], cwd=MAIN_REPO)
            else:
                _run(["git", "worktree", "add", "-b", branch, wt_path, base_sha], cwd=MAIN_REPO)
            cur_br = branch
        cur_sha = _run(["git", "rev-parse", "HEAD"], cwd=wt_path).stdout.strip()

    # 1. Shared read-only dependency: original/ symlink
    orig_dst = os.path.join(wt_path, "original")
    orig_src = os.path.join(MAIN_REPO, "original")
    if not os.path.exists(orig_dst) and not os.path.islink(orig_dst):
        os.symlink(orig_src, orig_dst)

    # 2. Isolated mutable build directories (tmp, cache, wineprefix)
    os.makedirs(os.path.join(wt_path, "build", "tmp"), exist_ok=True)
    os.makedirs(os.path.join(wt_path, "build", "cache"), exist_ok=True)
    os.makedirs(os.path.join(wt_path, "build", "oldcc"), exist_ok=True)

    # CoW copy analysis cache if absent
    src_cache = os.path.join(MAIN_REPO, "build", "cache")
    dst_cache = os.path.join(wt_path, "build", "cache")
    if os.path.isdir(src_cache):
        for fname in os.listdir(src_cache):
            sp = os.path.join(src_cache, fname)
            dp = os.path.join(dst_cache, fname)
            if os.path.isfile(sp) and not os.path.exists(dp):
                subprocess.run(["cp", "--reflink=auto", sp, dp], check=False)

    # CoW copy wineprefix if absent (isolated per worktree so wineserver never contends)
    src_pfx = os.path.join(MAIN_REPO, "build", "oldcc", "wineprefix")
    dst_pfx = os.path.join(wt_path, "build", "oldcc", "wineprefix")
    if os.path.isdir(src_pfx) and not os.path.exists(dst_pfx):
        subprocess.run(["cp", "-a", "--reflink=auto", src_pfx, dst_pfx], check=True)

    return {
        "name": name,
        "worktree": wt_path,
        "branch": cur_br,
        "base_ref": base_ref,
        "base_commit": base_sha,
        "head_commit": cur_sha,
        "wineprefix": dst_pfx,
        "tmpdir": os.path.join(wt_path, "build", "tmp"),
    }


def remove_worktree(name):
    wt_path = os.path.join(WT_ROOT, name)
    if os.path.isdir(wt_path):
        # Kill any lingering wineserver in this worktree's isolated prefix first
        pfx = os.path.join(wt_path, "build", "oldcc", "wineprefix")
        if os.path.isdir(pfx):
            env = dict(os.environ, WINEPREFIX=pfx)
            ws = shutil.which("wineserver")
            if ws:
                subprocess.run([ws, "-k"], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
        _run(["git", "worktree", "remove", "--force", wt_path], cwd=MAIN_REPO, check=False)
        if os.path.isdir(wt_path):
            shutil.rmtree(wt_path, ignore_errors=True)
    return {"removed": name, "path": wt_path}


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    add = sub.add_parser("add")
    add.add_argument("--name", required=True)
    add.add_argument("--base", required=True)
    add.add_argument("--branch", default=None)
    add.add_argument("--detach", action="store_true")
    rm = sub.add_parser("remove")
    rm.add_argument("--name", required=True)
    args = ap.parse_args()
    if args.cmd == "add":
        res = setup_worktree(args.name, args.base, branch=args.branch, detach=args.detach)
    else:
        res = remove_worktree(args.name)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
