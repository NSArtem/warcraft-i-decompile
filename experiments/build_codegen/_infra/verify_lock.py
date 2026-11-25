"""Global cross-worktree serialized verification lock (Section 6.2)."""
import argparse
import datetime
import fcntl
import json
import os
import subprocess
import sys
import time
import uuid

from . import STATE_ROOT


def _utc_now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def _git_head(wt):
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=wt, capture_output=True, text=True, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None


def run_serialized_verify(worktree, exp_id, cmd="make verify", session_id=None, env_extra=None):
    lock_dir = os.path.join(STATE_ROOT, "locks")
    stream_dir = os.path.join(STATE_ROOT, "streams")
    os.makedirs(lock_dir, exist_ok=True)
    os.makedirs(stream_dir, exist_ok=True)
    lock_path = os.path.join(lock_dir, "make_verify.lock")

    req_ts = _utc_now()
    t_req = time.monotonic()
    commit_sha = _git_head(worktree)

    with open(lock_path, "a+") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        acq_ts = _utc_now()
        t_acq = time.monotonic()
        wait_s = round(t_acq - t_req, 3)

        env = dict(os.environ)
        env["WC1_ROOT"] = os.path.abspath(worktree)
        env["PYTHONPATH"] = os.path.join(os.path.abspath(worktree), "tools") + (
            ":" + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
        )
        env["WINEPREFIX"] = os.path.join(os.path.abspath(worktree), "build", "oldcc", "wineprefix")
        if env_extra:
            env.update(env_extra)

        start_ts = _utc_now()
        t_start = time.monotonic()
        proc = subprocess.run(["bash", "-lc", cmd], cwd=worktree, env=env)
        t_end = time.monotonic()
        end_ts = _utc_now()
        dur_s = round(t_end - t_start, 3)

    rec = {
        "event_type": "serialized_verify",
        "event_id": f"verify-{uuid.uuid4().hex[:12]}",
        "exp_id": exp_id,
        "session_id": session_id,
        "worktree": os.path.abspath(worktree),
        "commit_sha": commit_sha,
        "cmd": cmd,
        "request_ts_utc": req_ts,
        "lock_acquired_ts_utc": acq_ts,
        "start_ts_utc": start_ts,
        "end_ts_utc": end_ts,
        "wait_s": wait_s,
        "duration_s": dur_s,
        "exit_code": proc.returncode,
    }
    out_file = os.path.join(stream_dir, f"verify_{int(time.time()*1000)}_{os.getpid()}.json")
    with open(out_file, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, indent=2)
    return rec


def main():
    ap = argparse.ArgumentParser(description="Run serialized make verify across worktrees")
    ap.add_argument("--worktree", required=True)
    ap.add_argument("--exp", required=True)
    ap.add_argument("--cmd", default="make verify")
    ap.add_argument("--session-id", default=None)
    args = ap.parse_args()
    rec = run_serialized_verify(args.worktree, args.exp, cmd=args.cmd, session_id=args.session_id)
    print(json.dumps(rec))
    return rec["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
