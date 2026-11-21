"""Shared live state, streaming worker logs, rate-limit cache, and control IPC.

All files live under git-ignored `build/live/`:
  - `state.json`:          current overnight runner state (pid, status, workers, queue, progress)
  - `rate_limits.json`:    latest 5h/7d rate-limit windows from `stream-json`
  - `control.json`:        one-shot control commands sent by `wc1.tui`
                           (`pause`, `resume`, `wake`, `graceful_stop`, `kill`)
  - `workers/<id>.jsonl`:  live NDJSON stream of thinking, output, permuter, match, verify events
  - `workers/<id>.meta.json`: live phase/stage metadata for an active worker
"""
import json
import os
import signal
import time

from . import path


def live_dir(root=None):
    return os.path.join(root, "build", "live") if root else path("build", "live")


def workers_dir(root=None):
    return os.path.join(live_dir(root), "workers")


def state_path(root=None):
    return os.path.join(live_dir(root), "state.json")


def rate_limits_path(root=None):
    return os.path.join(live_dir(root), "rate_limits.json")


def control_path(root=None):
    return os.path.join(live_dir(root), "control.json")


def worker_stream_path(worker_id, root=None):
    return os.path.join(workers_dir(root), f"{worker_id}.jsonl")


def worker_meta_path(worker_id, root=None):
    return os.path.join(workers_dir(root), f"{worker_id}.meta.json")


def write_json_atomic(fpath, obj):
    """Write JSON via sibling temp file + os.replace so readers never see partial writes."""
    os.makedirs(os.path.dirname(fpath), exist_ok=True)
    tmp = f"{fpath}.{os.getpid()}.{time.time_ns()}.tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, indent=2, ensure_ascii=False)
            fh.flush()
        os.replace(tmp, fpath)
    finally:
        if os.path.exists(tmp):
            try:
                os.unlink(tmp)
            except OSError:
                pass


def read_json(fpath, default=None):
    """Tolerant JSON reader: returns `default` on missing or partially-written files."""
    try:
        with open(fpath, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def append_event(worker_id, kind, text, root=None, **extra):
    """Append one NDJSON event to a worker's live stream."""
    if not worker_id:
        return
    fpath = worker_stream_path(worker_id, root=root)
    os.makedirs(os.path.dirname(fpath), exist_ok=True)
    rec = {"ts": round(time.time(), 3), "kind": kind, "text": str(text)}
    if extra:
        rec.update(extra)
    try:
        with open(fpath, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        pass


def update_worker_meta(worker_id, root=None, **fields):
    """Atomically update a worker's live phase/stage metadata (e.g. THINKING, PERMUTING)."""
    if not worker_id:
        return
    fpath = worker_meta_path(worker_id, root=root)
    cur = read_json(fpath, {}) or {}
    cur.update(fields)
    cur["updated_at"] = time.time()
    try:
        write_json_atomic(fpath, cur)
    except OSError:
        pass


def read_worker_meta(worker_id, root=None):
    if not worker_id:
        return {}
    return read_json(worker_meta_path(worker_id, root=root), {}) or {}


def tail_events(worker_id, offset=0, root=None, max_events=500):
    """Incrementally read complete NDJSON lines from a worker stream.

    Returns `(events, new_offset)`. Tolerates an incomplete trailing line without
    a terminating newline (leaves `offset` before it so it will be read next poll)
    and skips malformed lines safely.
    """
    if not worker_id:
        return [], offset
    fpath = worker_stream_path(worker_id, root=root)
    try:
        size = os.path.getsize(fpath)
    except OSError:
        return [], offset
    if size < offset:
        offset = 0  # file was truncated/recreated
    if size == offset:
        return [], offset

    events = []
    new_offset = offset
    try:
        with open(fpath, "rb") as fh:
            fh.seek(offset)
            while len(events) < max_events:
                pos = fh.tell()
                raw = fh.readline()
                if not raw:
                    break
                if not raw.endswith(b"\n"):
                    # Incomplete trailing line — retry on next poll
                    new_offset = pos
                    break
                new_offset = fh.tell()
                line = raw.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    if isinstance(rec, dict) and "text" in rec:
                        events.append(rec)
                except ValueError:
                    continue
    except OSError:
        return events, new_offset
    return events, new_offset


def parse_rate_limit_event(ev):
    """Extract normalized 5h/7d rate-limit info from a Claude `rate_limit_event`."""
    if not isinstance(ev, dict):
        return None
    info = ev.get("rate_limit_info") or {}
    if not isinstance(info, dict) or not info:
        return None
    out = {"updated_at": time.time(), "status": info.get("status", "unknown")}
    uw = info.get("unifiedWindows") or {}
    if isinstance(uw, dict):
        for key in ("five_hour", "seven_day"):
            w = uw.get(key)
            if isinstance(w, dict):
                util = w.get("utilization")
                util_f = float(util) if util is not None else None
                out[key] = {
                    "utilization": util_f,
                    "used_percentage": round(util_f * 100.0, 1) if util_f is not None else None,
                    "resets_at": w.get("resetsAt"),
                    "status": w.get("status", "unknown"),
                }
    rl_type = info.get("rateLimitType")
    if rl_type in ("five_hour", "seven_day") and rl_type not in out:
        util = info.get("utilization")
        util_f = float(util) if util is not None else None
        out[rl_type] = {
            "utilization": util_f,
            "used_percentage": round(util_f * 100.0, 1) if util_f is not None else None,
            "resets_at": info.get("resetsAt"),
            "status": info.get("status", "unknown"),
        }
    return out


def parse_stream_json_line(line):
    """Parse one NDJSON line from `claude -p --output-format stream-json`.

    Returns a normalized dict with `kind` in:
      `thinking_delta`, `text_delta`, `input_json_delta`, `tool_use`,
      `rate_limit`, `result`, `other`, or `None` for non-JSON/blank lines.
    """
    s = (line or "").strip()
    if not s:
        return None
    try:
        obj = json.loads(s)
    except ValueError:
        return None
    if not isinstance(obj, dict):
        return None
    etype = obj.get("type")
    if etype == "stream_event":
        ev = obj.get("event") or {}
        ev_type = ev.get("type")
        if ev_type == "content_block_delta":
            delta = ev.get("delta") or {}
            dtype = delta.get("type")
            if dtype == "thinking_delta":
                return {"kind": "thinking_delta", "text": delta.get("thinking") or ""}
            if dtype == "text_delta":
                return {"kind": "text_delta", "text": delta.get("text") or ""}
            if dtype == "input_json_delta":
                return {"kind": "input_json_delta", "text": delta.get("partial_json") or ""}
        elif ev_type == "content_block_start":
            cb = ev.get("content_block") or {}
            if cb.get("type") == "tool_use":
                return {"kind": "tool_use", "name": cb.get("name") or ""}
            if cb.get("type") == "thinking":
                return {"kind": "thinking_start"}
        return {"kind": "other", "raw": obj}
    if etype == "rate_limit_event":
        rl = parse_rate_limit_event(obj)
        return {"kind": "rate_limit", "rate_limit": rl} if rl else {"kind": "other", "raw": obj}
    if etype == "result":
        return {"kind": "result", "result": obj}
    return {"kind": "other", "raw": obj}


def save_rate_limits(parsed_rl, fpath=None, root=None):
    if not parsed_rl:
        return
    dst = fpath or rate_limits_path(root=root)
    cur = read_json(dst, {}) or {}
    cur["updated_at"] = parsed_rl.get("updated_at", time.time())
    cur["status"] = parsed_rl.get("status", cur.get("status", "unknown"))
    for key in ("five_hour", "seven_day"):
        if key in parsed_rl and isinstance(parsed_rl[key], dict):
            prev = cur.get(key) or {}
            merged = dict(prev)
            for k, v in parsed_rl[key].items():
                if v is not None:
                    merged[k] = v
            cur[key] = merged
    write_json_atomic(dst, cur)


def load_rate_limits(fpath=None, root=None):
    return read_json(fpath or rate_limits_path(root=root), {}) or {}


def send_control(action, fpath=None, root=None, **extra):
    rec = {"ts": time.time(), "action": action}
    rec.update(extra)
    write_json_atomic(fpath or control_path(root=root), rec)


def peek_control(fpath=None, root=None):
    return read_json(fpath or control_path(root=root), None)


def consume_control(fpath=None, root=None):
    p = fpath or control_path(root=root)
    rec = read_json(p, None)
    if rec is not None:
        try:
            os.unlink(p)
        except OSError:
            pass
    return rec


def pid_alive(pid):
    if not pid:
        return False
    try:
        p = int(pid)
    except (TypeError, ValueError):
        return False
    if p <= 0:
        return False
    try:
        os.kill(p, 0)
        return True
    except OSError:
        return False


def terminate_process_tree(proc, grace=3.0):
    """Terminate a Popen process and its entire process group safely (no orphans)."""
    if proc is None or proc.poll() is not None:
        return
    pid = proc.pid
    sent_pg = False
    try:
        pgid = os.getpgid(pid)
        if pgid == pid:
            os.killpg(pgid, signal.SIGTERM)
            sent_pg = True
    except OSError:
        pass
    if not sent_pg:
        try:
            proc.terminate()
        except OSError:
            return

    deadline = time.time() + max(0.2, grace)
    while time.time() < deadline:
        if proc.poll() is not None:
            return
        time.sleep(0.05)

    try:
        if sent_pg:
            os.killpg(pid, signal.SIGKILL)
        else:
            proc.kill()
    except OSError:
        pass
    try:
        proc.wait(timeout=3.0)
    except Exception:
        pass
