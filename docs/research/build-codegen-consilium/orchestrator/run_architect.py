#!/usr/bin/env python3
"""Deterministic delivery and telemetry for the Build & Codegen Architecture Consilium.

Subcommands:
  launch   Render one prompt per Architect, launch all three concurrently with a
           hard wall-clock bound, capture raw logs, response and metadata.
  freeze   Verify that all three responses exist, hash them, write the round
           manifest, and update the tracked state/telemetry.

The script never interprets responses and never edits them. The response of
record is the Architect's final message exactly as emitted by its harness.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import glob
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import time
import uuid

SEC = "/mnt/data/projects/warcraft-1-decompile-wt/cons-sec"
CONSILIUM = os.path.join(SEC, "docs/research/build-codegen-consilium")
STATE = "/mnt/data/projects/warcraft-1-decompile-consilium"
MANIFEST = os.path.join(CONSILIUM, "evidence-manifest.json")

ARCHITECTS = {
    "gpt": {
        "identity": "A",
        "display": "GPT",
        "model_id": "gpt-6.2-sol",
        "effort": "high",
        "harness": "codex-cli 0.172.0",
        "worktree": "/mnt/data/projects/warcraft-1-decompile-wt/cons-a",
        "runtime": os.path.join(STATE, "runtime", "gpt"),
    },
    "claude": {
        "identity": "B",
        "display": "Claude",
        "model_id": "claude-opus-5-5",
        "effort": "high",
        "harness": "Claude Code 2.1.332",
        "worktree": "/mnt/data/projects/warcraft-1-decompile-wt/cons-b",
        "runtime": os.path.join(STATE, "runtime", "claude"),
    },
    "gemini": {
        "identity": "C",
        "display": "Gemini",
        "model_id": "gemini-4-neon-high",
        "effort": "high",
        "harness": "agy 1.5.17",
        "worktree": "/mnt/data/projects/warcraft-1-decompile-wt/cons-c",
        "runtime": os.path.join(STATE, "runtime", "gemini"),
    },
}


def utc(epoch: float | None = None) -> str:
    return (
        dt.datetime.fromtimestamp(epoch if epoch is not None else time.time(), tz=dt.timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: str, default=None):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def write_json(path: str, obj) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    os.replace(tmp, path)


def render(template: str, arch: str, timeout_s: int, launch_epoch: int, extra: dict | None = None) -> str:
    cfg = ARCHITECTS[arch]
    manifest = load_json(MANIFEST, {})
    launch_utc = utc(launch_epoch)
    deadline = utc(launch_epoch + timeout_s)
    checkpoint = utc(launch_epoch + int(timeout_s * 0.8))
    values = {
        "IDENTITY": cfg["identity"],
        "IDENTITY_LOWER": arch,
        "DISPLAY_NAME": cfg["display"],
        "MODEL_ID": cfg["model_id"],
        "HARNESS": cfg["harness"],
        "WORKTREE": cfg["worktree"],
        "RUNTIME_DIR": cfg["runtime"],
        "LAUNCH_UTC": launch_utc,
        "TIMEOUT_S": str(timeout_s),
        "TIMEOUT_MIN": str(max(1, timeout_s // 60)),
        "DEADLINE_UTC": deadline,
        "CHECKPOINT_UTC": checkpoint,
        "EVIDENCE_MANIFEST_JSON": json.dumps(manifest, indent=2, ensure_ascii=False),
    }
    out = template
    for key, val in values.items():
        out = out.replace("{{" + key + "}}", val)
    for key, val in (extra or {}).items():
        out = out.replace("{{" + key + "}}", val)
    missing = re.findall(r"\{\{[A-Z0-9_]+\}\}", out)
    if missing:
        raise SystemExit(f"unrendered placeholders: {sorted(set(missing))}")
    return out


def session_path(arch: str) -> str:
    return os.path.join(STATE, "sessions", f"{arch}.json")


def load_session(arch: str) -> dict:
    cfg = ARCHITECTS[arch]
    return load_json(session_path(arch), {
        "architect": arch,
        "identity": cfg["identity"],
        "native_session_id": None,
        "invocations": 0,
        "history": [],
    })


def save_session(arch: str, rec: dict) -> None:
    write_json(session_path(arch), rec)


def short_tmpdir(arch: str, tag: str) -> str:
    path = f"/tmp/opencode/cn-{arch}-{tag}"
    os.makedirs(path, exist_ok=True)
    return path


def base_env(arch: str, tmpdir: str) -> dict:
    cfg = ARCHITECTS[arch]
    env = dict(os.environ)
    env["WC1_ROOT"] = cfg["worktree"]
    env["PYTHONPATH"] = os.path.join(cfg["worktree"], "tools") + (
        ":" + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
    )
    env["WINEPREFIX"] = os.path.join(cfg["worktree"], "build", "oldcc", "wineprefix")
    env["TMPDIR"] = tmpdir
    env["WC1_CONSILIUM"] = "1"
    env["WC1_CONSILIUM_ARCHITECT"] = arch
    return env


def run_bounded(cmd, *, cwd, env, stdout_path, stderr_path, timeout_s, stdin_bytes=None):
    """Run a command with a hard wall bound; kill the whole process group on timeout."""
    start = time.monotonic()
    timed_out = False
    with open(stdout_path, "wb") as out_fh, open(stderr_path, "wb") as err_fh:
        proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            env=env,
            stdin=subprocess.PIPE if stdin_bytes is not None else subprocess.DEVNULL,
            stdout=out_fh,
            stderr=err_fh,
            start_new_session=True,
        )
        try:
            if stdin_bytes is not None:
                try:
                    proc.stdin.write(stdin_bytes)
                    proc.stdin.close()
                except (BrokenPipeError, OSError):
                    pass
            exit_code = proc.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                exit_code = proc.wait(timeout=20)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                except ProcessLookupError:
                    pass
                exit_code = proc.wait(timeout=15)
            exit_code = 124 if exit_code == 0 else exit_code
    return exit_code, timed_out, round(time.monotonic() - start, 3)


# ---------------------------------------------------------------------------
# Harness-specific execution and parsing
# ---------------------------------------------------------------------------


def _codex_find_rollout(thread_id: str) -> str | None:
    if not thread_id:
        return None
    home = os.path.expanduser("~/.codex")
    matches = glob.glob(os.path.join(home, "sessions", "**", f"*{thread_id}*.jsonl"), recursive=True)
    return max(matches, key=os.path.getmtime) if matches else None


def _codex_parse_rollout(path: str) -> dict:
    out = {
        "input_tokens": None,
        "cached_input_tokens": None,
        "output_tokens": None,
        "reasoning_tokens": None,
        "rate_limits": None,
        "model_observed": None,
        "effort_observed": None,
        "peak_context_tokens": 0,
    }
    if not path or not os.path.isfile(path):
        return out
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if not line.strip().startswith("{"):
                    continue
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                typ = rec.get("type")
                pay = rec.get("payload") if isinstance(rec.get("payload"), dict) else {}
                if typ == "turn_context":
                    out["model_observed"] = pay.get("model") or out["model_observed"]
                    out["effort_observed"] = pay.get("effort") or pay.get("reasoning_effort") or out["effort_observed"]
                if typ == "event_msg" and pay.get("type") == "token_count":
                    info = pay.get("info") or {}
                    tot = info.get("total_token_usage") or {}
                    if tot:
                        out["input_tokens"] = int(tot.get("input_tokens") or 0)
                        out["cached_input_tokens"] = int(tot.get("cached_input_tokens") or 0)
                        out["output_tokens"] = int(tot.get("output_tokens") or 0)
                        out["reasoning_tokens"] = int(tot.get("reasoning_output_tokens") or 0)
                    last = info.get("last_token_usage") or {}
                    peak = int(last.get("input_tokens") or 0)
                    if peak > out["peak_context_tokens"]:
                        out["peak_context_tokens"] = peak
                    rl = pay.get("rate_limits")
                    if rl:
                        out["rate_limits"] = rl
    except OSError:
        pass
    return out


def run_codex(arch: str, prompt: str, timeout_s: int, sess: dict, log_dir: str) -> dict:
    cfg = ARCHITECTS[arch]
    tmpdir = short_tmpdir(arch, "run")
    env = base_env(arch, tmpdir)
    stdout_path = os.path.join(log_dir, f"{arch}.stdout.jsonl")
    stderr_path = os.path.join(log_dir, f"{arch}.stderr.log")
    lastmsg_path = os.path.join(log_dir, f"{arch}.last_message.md")
    first = not sess.get("native_session_id")
    common = [
        "codex", "exec",
        "--ignore-user-config",
        "--ignore-rules",
        "-m", cfg["model_id"],
        "-c", f'model_reasoning_effort="{cfg["effort"]}"',
        "--json",
        "-o", lastmsg_path,
    ]
    if first:
        cmd = common + ["-s", "danger-full-access", "-C", cfg["worktree"], "-"]
        session_arg = None
    else:
        session_arg = sess["native_session_id"]
        cmd = common + ["--dangerously-bypass-approvals-and-sandbox", "resume", session_arg, "-"]
    started = time.time()
    exit_code, timed_out, wall_s = run_bounded(
        cmd, cwd=cfg["worktree"], env=env, stdout_path=stdout_path,
        stderr_path=stderr_path, timeout_s=timeout_s, stdin_bytes=prompt.encode("utf-8"),
    )
    ended = time.time()

    thread_id = None
    turns = 0
    tool_calls = 0
    errors: list[str] = []
    agent_messages: list[str] = []
    stream_usage = {"input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0, "reasoning_output_tokens": 0}
    has_stream_usage = False
    try:
        with open(stdout_path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if not line.strip().startswith("{"):
                    continue
                try:
                    ev = json.loads(line)
                except ValueError:
                    continue
                typ = ev.get("type")
                if typ == "thread.started":
                    thread_id = ev.get("thread_id") or thread_id
                elif typ == "turn.completed":
                    turns += 1
                    u = ev.get("usage") or {}
                    if u:
                        has_stream_usage = True
                        for k in stream_usage:
                            stream_usage[k] += int(u.get(k) or 0)
                elif typ == "item.completed":
                    item = ev.get("item") or {}
                    it = item.get("type")
                    if it == "agent_message":
                        txt = item.get("text") or ""
                        if txt.strip():
                            agent_messages.append(txt)
                    elif it not in ("reasoning",):
                        tool_calls += 1
                elif typ in ("turn.failed", "error"):
                    errors.append(str(ev.get("message") or ev.get("error") or ev)[:500])
    except OSError:
        pass

    response = ""
    if os.path.isfile(lastmsg_path):
        response = open(lastmsg_path, encoding="utf-8", errors="replace").read()
    if not response.strip() and agent_messages:
        response = agent_messages[-1]
    if not response.strip():
        pos = os.path.join(cfg["worktree"], "CONSILIUM-R00-POSITION.md")
        if os.path.isfile(pos):
            response = open(pos, encoding="utf-8", errors="replace").read()

    rollout_path = _codex_find_rollout(thread_id)
    rollout = _codex_parse_rollout(rollout_path)
    if rollout["input_tokens"] is not None:
        usage = {
            "input_tokens": rollout["input_tokens"],
            "cached_input_tokens": rollout["cached_input_tokens"],
            "output_tokens": rollout["output_tokens"],
            "reasoning_tokens": rollout["reasoning_tokens"],
            "reasoning_included_in_output": True,
            "provenance": "exact (codex rollout cumulative)",
        }
    elif has_stream_usage:
        usage = {
            "input_tokens": stream_usage["input_tokens"],
            "cached_input_tokens": stream_usage["cached_input_tokens"],
            "output_tokens": stream_usage["output_tokens"],
            "reasoning_tokens": stream_usage["reasoning_output_tokens"],
            "reasoning_included_in_output": True,
            "provenance": "exact (codex stream events)",
        }
    else:
        usage = {"provenance": "unavailable"}

    rl = rollout.get("rate_limits") or {}
    quota = {
        "five_hour_used_percent": (rl.get("primary") or {}).get("used_percent"),
        "five_hour_resets_at_epoch": (rl.get("primary") or {}).get("resets_at"),
        "seven_day_used_percent": (rl.get("secondary") or {}).get("used_percent"),
        "seven_day_resets_at_epoch": (rl.get("secondary") or {}).get("resets_at"),
        "plan_type": rl.get("plan_type"),
        "provenance": "exact (codex rollout rate_limits)" if rl else "unavailable",
    }
    return {
        "session_id": thread_id or session_arg,
        "session_was_resumed": not first,
        "response": response,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "wall_s": wall_s,
        "started_epoch": started,
        "ended_epoch": ended,
        "turns": turns,
        "tool_calls": tool_calls,
        "usage": usage,
        "quota_after": quota,
        "model_observed": rollout.get("model_observed"),
        "effort_observed": rollout.get("effort_observed"),
        "peak_context_tokens": rollout.get("peak_context_tokens"),
        "stdout_path": stdout_path,
        "stderr_path": stderr_path,
        "errors": errors[:20],
    }


def run_claude(arch: str, prompt: str, timeout_s: int, sess: dict, log_dir: str) -> dict:
    cfg = ARCHITECTS[arch]
    tmpdir = short_tmpdir(arch, "run")
    env = base_env(arch, tmpdir)
    stdout_path = os.path.join(log_dir, f"{arch}.stdout.jsonl")
    stderr_path = os.path.join(log_dir, f"{arch}.stderr.log")
    first = not sess.get("native_session_id")
    cmd = [
        "claude", "-p",
        "--model", cfg["model_id"],
        "--effort", cfg["effort"],
        "--dangerously-skip-permissions",
        "--output-format", "stream-json",
        "--verbose",
    ]
    if first:
        new_id = str(uuid.uuid4())
        cmd += ["--session-id", new_id]
        session_arg = new_id
    else:
        session_arg = sess["native_session_id"]
        cmd += ["--resume", session_arg]
    cmd.append(prompt)
    started = time.time()
    exit_code, timed_out, wall_s = run_bounded(
        cmd, cwd=cfg["worktree"], env=env, stdout_path=stdout_path,
        stderr_path=stderr_path, timeout_s=timeout_s,
    )
    ended = time.time()

    result = None
    rate = None
    session_id = session_arg
    errors: list[str] = []
    text_parts: list[str] = []
    turns = 0
    tool_calls = 0
    try:
        with open(stdout_path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                s = line.strip()
                if not s.startswith("{"):
                    continue
                try:
                    ev = json.loads(s)
                except ValueError:
                    continue
                typ = ev.get("type")
                sid = ev.get("session_id")
                if sid:
                    session_id = sid
                if typ == "rate_limit_event":
                    rate = ev.get("rate_limit_info") or rate
                elif typ == "result":
                    result = ev
                elif typ == "assistant":
                    msg = ev.get("message") or {}
                    for block in msg.get("content") or []:
                        if isinstance(block, dict) and block.get("type") == "text":
                            text_parts.append(block.get("text") or "")
                        elif isinstance(block, dict) and block.get("type") == "tool_use":
                            tool_calls += 1
                elif typ == "user":
                    msg = ev.get("message") or {}
                    for block in msg.get("content") or []:
                        if isinstance(block, dict) and block.get("type") == "tool_result":
                            tool_calls += 1
                elif typ == "system" and ev.get("subtype") == "init":
                    turns = max(turns, 0)
                elif typ == "error":
                    errors.append(str(ev.get("error") or ev)[:500])
    except OSError:
        pass

    response = ""
    usage = {"provenance": "unavailable"}
    if result:
        response = result.get("result") or ""
        u = result.get("usage") or {}
        if u:
            inp = int(u.get("input_tokens") or 0)
            cache_read = int(u.get("cache_read_input_tokens") or 0)
            cache_create = int(u.get("cache_creation_input_tokens") or 0)
            out_tok = int(u.get("output_tokens") or 0)
            think = int((u.get("output_tokens_details") or {}).get("thinking_tokens") or 0)
            usage = {
                "input_tokens": inp + cache_read + cache_create,
                "uncached_input_tokens": inp,
                "cached_input_tokens": cache_read,
                "cache_creation_input_tokens": cache_create,
                "output_tokens": out_tok,
                "thinking_tokens": think,
                "reasoning_included_in_output": True,
                "total_cost_usd": result.get("total_cost_usd"),
                "provenance": "exact (claude result usage)",
            }
        turns = int(result.get("num_turns") or turns or 0)
    if not response.strip() and text_parts:
        response = "".join(text_parts)
    if not response.strip():
        pos = os.path.join(cfg["worktree"], "CONSILIUM-R00-POSITION.md")
        if os.path.isfile(pos):
            response = open(pos, encoding="utf-8", errors="replace").read()

    quota = {"provenance": "unavailable"}
    if rate:
        uw = rate.get("unifiedWindows") or {}
        five = uw.get("five_hour") or {}
        week = uw.get("seven_day") or {}
        quota = {
            "five_hour_used_percent": (five.get("utilization") or 0) * 100 if five else None,
            "five_hour_resets_at_epoch": five.get("resetsAt"),
            "seven_day_used_percent": (week.get("utilization") or 0) * 100 if week else None,
            "seven_day_resets_at_epoch": week.get("resetsAt"),
            "status": rate.get("status"),
            "provenance": "exact (claude rate_limit_event)",
        }
    model_observed = None
    if result:
        mu = result.get("modelUsage") or {}
        if mu:
            model_observed = sorted(mu.keys())[0]
    return {
        "session_id": session_id,
        "session_was_resumed": not first,
        "response": response,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "wall_s": wall_s,
        "started_epoch": started,
        "ended_epoch": ended,
        "turns": turns,
        "tool_calls": tool_calls,
        "usage": usage,
        "quota_after": quota,
        "model_observed": model_observed,
        "effort_observed": cfg["effort"],
        "peak_context_tokens": None,
        "stdout_path": stdout_path,
        "stderr_path": stderr_path,
        "errors": errors[:20],
    }


def run_agy(arch: str, prompt: str, timeout_s: int, sess: dict, log_dir: str) -> dict:
    cfg = ARCHITECTS[arch]
    tmpdir = short_tmpdir(arch, "run")
    env = base_env(arch, tmpdir)
    stdout_path = os.path.join(log_dir, f"{arch}.stdout.jsonl")
    stderr_path = os.path.join(log_dir, f"{arch}.stderr.log")
    first = not sess.get("native_session_id")
    cmd = [
        "agy",
        "--model", cfg["model_id"],
        "--output-format", "stream-json",
        "--dangerously-skip-permissions",
    ]
    if not first:
        cmd += ["--conversation", sess["native_session_id"]]
    cmd += ["-p", prompt]
    started = time.time()
    exit_code, timed_out, wall_s = run_bounded(
        cmd, cwd=cfg["worktree"], env=env, stdout_path=stdout_path,
        stderr_path=stderr_path, timeout_s=timeout_s,
    )
    ended = time.time()

    conversation_id = sess.get("native_session_id") if not first else None
    result = None
    init_model = None
    errors: list[str] = []
    text_parts: list[str] = []
    tool_calls = 0
    try:
        with open(stdout_path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                s = line.strip()
                if not s.startswith("{"):
                    continue
                try:
                    ev = json.loads(s)
                except ValueError:
                    continue
                if ev.get("event") == "init":
                    conversation_id = ev.get("conversation_id") or conversation_id
                    init_model = (ev.get("init") or {}).get("model") or init_model
                elif ev.get("event") == "result":
                    result = ev.get("result") or {}
                    conversation_id = result.get("conversation_id") or conversation_id
                elif ev.get("event") == "step_update":
                    su = ev.get("step_update") or {}
                    txt = su.get("text_delta")
                    if txt and su.get("step_type") == "agent_response":
                        text_parts.append(txt)
                    if su.get("step_type") == "tool_call" and su.get("state") == "DONE":
                        tool_calls += 1
                elif ev.get("event") == "error":
                    errors.append(str(ev.get("error") or ev)[:500])
    except OSError:
        pass

    response = (result or {}).get("response") or ""
    if not response.strip() and text_parts:
        response = "".join(text_parts)
    if not response.strip():
        pos = os.path.join(cfg["worktree"], "CONSILIUM-R00-POSITION.md")
        if os.path.isfile(pos):
            response = open(pos, encoding="utf-8", errors="replace").read()

    usage = {"provenance": "unavailable"}
    if result and result.get("usage"):
        u = result["usage"]
        inp = int(u.get("input_tokens") or 0)
        cache_read = int(u.get("cache_read_tokens") or 0)
        out_tok = int(u.get("output_tokens") or 0)
        think = int(u.get("thinking_tokens") or 0)
        usage = {
            "input_tokens": inp + cache_read,
            "uncached_input_tokens": inp,
            "cached_input_tokens": cache_read,
            "output_tokens": out_tok,
            "thinking_tokens": think,
            "reasoning_included_in_output": True,
            "provenance": "exact (agy result usage)",
        }
    return {
        "session_id": conversation_id,
        "session_was_resumed": not first,
        "response": response,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "wall_s": wall_s,
        "started_epoch": started,
        "ended_epoch": ended,
        "turns": int((result or {}).get("num_turns") or 0),
        "tool_calls": tool_calls,
        "usage": usage,
        "quota_after": {"provenance": "unavailable", "note": "AGY exposes no reliable local quota percentage."},
        "model_observed": (result or {}).get("model") or init_model or cfg["model_id"],
        "effort_observed": "high",
        "peak_context_tokens": None,
        "stdout_path": stdout_path,
        "stderr_path": stderr_path,
        "errors": errors[:20],
    }


RUNNERS = {"gpt": run_codex, "claude": run_claude, "gemini": run_agy}


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def _write_prompts_meta(round_id: str, prompts: dict, timeout_s: int, template_label: str) -> None:
    round_dir = os.path.join(CONSILIUM, "rounds", round_id)
    write_json(os.path.join(round_dir, "prompts.json"), {
        "round": round_id,
        "template": template_label,
        "timeout_s": timeout_s,
        "prompts": {
            arch: {
                "path": os.path.relpath(os.path.join(round_dir, f"prompt-{arch}.md"), SEC),
                "sha256": sha256_bytes(prompts[arch].encode("utf-8")),
                "bytes": len(prompts[arch].encode("utf-8")),
            }
            for arch in ARCHITECTS
        },
    })


def _launch_prompts(round_id: str, prompts: dict, timeout_s: int) -> int:
    round_dir = os.path.join(CONSILIUM, "rounds", round_id)
    os.makedirs(round_dir, exist_ok=True)
    log_dir = os.path.join(STATE, "logs", round_id)
    os.makedirs(log_dir, exist_ok=True)

    def one(arch: str) -> dict:
        cfg = ARCHITECTS[arch]
        sess = load_session(arch)
        os.makedirs(cfg["runtime"], exist_ok=True)
        os.makedirs(log_dir, exist_ok=True)
        print(f"[launch] {arch} ({cfg['model_id']}) -> {cfg['worktree']}", flush=True)
        out = RUNNERS[arch](arch, prompts[arch], timeout_s, sess, log_dir)
        rec = os.path.join(round_dir, arch, "meta.json")
        os.makedirs(os.path.dirname(rec), exist_ok=True)
        write_json(rec, {
            "round": round_id,
            "architect": arch,
            "identity": cfg["identity"],
            "model_requested": cfg["model_id"],
            "effort_requested": cfg["effort"],
            "harness": cfg["harness"],
            "worktree": cfg["worktree"],
            "prompt_sha256": sha256_bytes(prompts[arch].encode("utf-8")),
            "prompt_bytes": len(prompts[arch].encode("utf-8")),
            "start_utc": utc(out["started_epoch"]),
            "end_utc": utc(out["ended_epoch"]),
            "session_id": out["session_id"],
            "session_was_resumed": out["session_was_resumed"],
            "exit_code": out["exit_code"],
            "timed_out": out["timed_out"],
            "wall_s": out["wall_s"],
            "turns": out["turns"],
            "tool_calls": out["tool_calls"],
            "usage": out["usage"],
            "quota_after": out["quota_after"],
            "model_observed": out["model_observed"],
            "effort_observed": out["effort_observed"],
            "peak_context_tokens": out["peak_context_tokens"],
            "stdout_path": out["stdout_path"],
            "stderr_path": out["stderr_path"],
            "stderr_sha256": sha256_file(out["stderr_path"]) if os.path.isfile(out["stderr_path"]) else None,
            "stdout_sha256": sha256_file(out["stdout_path"]) if os.path.isfile(out["stdout_path"]) else None,
            "errors": out["errors"],
            "response_sha256": sha256_bytes(out["response"].encode("utf-8")),
            "response_bytes": len(out["response"].encode("utf-8")),
            "status": "COMPLETED" if out["response"].strip() and not out["timed_out"] else
                      ("TIMED_OUT" if out["timed_out"] else "EMPTY_RESPONSE"),
        })
        rpath = os.path.join(round_dir, arch, "response.md")
        with open(rpath, "w", encoding="utf-8") as fh:
            fh.write(out["response"])
        with open(os.path.join(round_dir, arch, "response.sha256"), "w", encoding="utf-8") as fh:
            fh.write(sha256_bytes(out["response"].encode("utf-8")) + "\n")

        # Update persistent session state.
        if out["session_id"]:
            sess["native_session_id"] = out["session_id"]
        sess["invocations"] = int(sess.get("invocations") or 0) + 1
        sess.setdefault("history", []).append({
            "round": round_id,
            "started_utc": utc(out["started_epoch"]),
            "ended_utc": utc(out["ended_epoch"]),
            "session_id": out["session_id"],
            "wall_s": out["wall_s"],
            "timed_out": out["timed_out"],
            "exit_code": out["exit_code"],
            "response_sha256": sha256_bytes(out["response"].encode("utf-8")),
        })
        save_session(arch, sess)
        print(f"[done] {arch}: {out['wall_s']}s exit={out['exit_code']} "
              f"response={len(out['response'])}B status={out['timed_out'] and 'TIMED_OUT' or 'ok'}", flush=True)
        return {"architect": arch, "status": "ok", "wall_s": out["wall_s"]}

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        futs = {ex.submit(one, arch): arch for arch in ARCHITECTS}
        for fut in concurrent.futures.as_completed(futs):
            arch = futs[fut]
            try:
                results.append(fut.result())
            except Exception as exc:  # noqa: BLE001 - record, never lose the round
                results.append({"architect": arch, "status": "ERROR", "error": repr(exc)})
                print(f"[error] {arch}: {exc!r}", flush=True)
    write_json(os.path.join(log_dir, "launch-summary.json"), {"round": round_id, "results": results})
    return 0 if all(r.get("status") == "ok" for r in results) else 1


def launch(round_id: str, template_path: str, timeout_s: int) -> int:
    with open(template_path, encoding="utf-8") as fh:
        template = fh.read()
    round_dir = os.path.join(CONSILIUM, "rounds", round_id)
    os.makedirs(round_dir, exist_ok=True)
    prompts = {}
    launch_epoch = int(time.time()) + 20  # one honest lead time shared by all three
    for arch in ARCHITECTS:
        prompt = render(template, arch, timeout_s, launch_epoch)
        with open(os.path.join(round_dir, f"prompt-{arch}.md"), "w", encoding="utf-8") as fh:
            fh.write(prompt)
        prompts[arch] = prompt
    _write_prompts_meta(round_id, prompts, timeout_s, os.path.relpath(template_path, SEC))
    return _launch_prompts(round_id, prompts, timeout_s)


def launch_files(round_id: str, timeout_s: int) -> int:
    """Launch pre-composed per-Architect prompts (used when each Architect receives
    different discussion material, e.g. the other two opening positions)."""
    round_dir = os.path.join(CONSILIUM, "rounds", round_id)
    prompts = {}
    for arch in ARCHITECTS:
        path = os.path.join(round_dir, f"prompt-{arch}.md")
        with open(path, encoding="utf-8") as fh:
            prompts[arch] = fh.read()
        missing = re.findall(r"\{\{[A-Z0-9_]+\}\}", prompts[arch])
        if missing:
            raise SystemExit(f"{path}: unrendered placeholders {sorted(set(missing))}")
    _write_prompts_meta(round_id, prompts, timeout_s, f"pre-composed:{round_id}")
    return _launch_prompts(round_id, prompts, timeout_s)


def freeze(round_id: str, expected_epoch: str | None = None) -> int:
    round_dir = os.path.join(CONSILIUM, "rounds", round_id)
    state_path = os.path.join(CONSILIUM, "state.json")
    prior_state = load_json(state_path, {}) or {}
    prior = ((prior_state.get("rounds") or {}).get(round_id) or {})
    metas = {}
    ok = True
    for arch in ARCHITECTS:
        meta_path = os.path.join(round_dir, arch, "meta.json")
        resp_path = os.path.join(round_dir, arch, "response.md")
        meta = load_json(meta_path)
        if not meta or not os.path.isfile(resp_path):
            print(f"[freeze] {arch}: missing meta or response", file=sys.stderr)
            ok = False
            continue
        if (meta.get("status") != "COMPLETED" or meta.get("timed_out")
                or meta.get("exit_code") != 0 or not meta.get("session_id")
                or meta.get("model_observed") != meta.get("model_requested")
                or meta.get("effort_observed") not in (None, meta.get("effort_requested"))):
            print(f"[freeze] {arch}: missing completion or model confirmation", file=sys.stderr)
            ok = False
        body = open(resp_path, "rb").read()
        digest = sha256_bytes(body)
        if not body.strip():
            print(f"[freeze] {arch}: empty response", file=sys.stderr)
            ok = False
        if meta.get("response_sha256") != digest:
            print(f"[freeze] {arch}: response hash mismatch (meta vs file)", file=sys.stderr)
            ok = False
        metas[arch] = {
            "status": meta.get("status"),
            "session_id": meta.get("session_id"),
            "model_requested": meta.get("model_requested"),
            "model_observed": meta.get("model_observed"),
            "effort_requested": meta.get("effort_requested"),
            "effort_observed": meta.get("effort_observed"),
            "prompt_sha256": meta.get("prompt_sha256"),
            "response_sha256": digest,
            "response_bytes": len(body),
            "wall_s": meta.get("wall_s"),
            "timed_out": meta.get("timed_out"),
            "usage": meta.get("usage"),
            "quota_after": meta.get("quota_after"),
        }
    if not ok:
        print("[freeze] NOT frozen: one or more responses are missing or invalid", file=sys.stderr)
        return 1
    if prior.get("status") == "frozen" and prior.get("responses") == {
        arch: {"status": metas[arch]["status"], "sha256": metas[arch]["response_sha256"]}
        for arch in metas
    }:
        print("[freeze] already frozen with identical hashes; no changes")
        return 0
    manifest = {
        "round": round_id,
        "barrier": "closed",
        "frozen_at_utc": utc(),
        "responses": metas,
        "delivery": "Round responses remain undelivered until the Secretary composes the next round.",
    }
    write_json(os.path.join(round_dir, "manifest.json"), manifest)

    # Update tracked state.
    state_path = os.path.join(CONSILIUM, "state.json")
    state = load_json(state_path, {})
    entry = state.setdefault("rounds", {}).setdefault(round_id, {})
    entry["status"] = "frozen"
    entry["barrier"] = "closed"
    entry["responses_frozen_at_utc"] = manifest["frozen_at_utc"]
    entry["responses"] = {
        arch: {"status": metas[arch]["status"], "sha256": metas[arch]["response_sha256"]}
        for arch in metas
    }
    state["next_round"] = "r01"
    state["phase"] = "ROUND_1_PENDING"
    state["sessions"] = {
        arch: {
            "native_session_id": metas[arch]["session_id"],
            "invocations": (load_session(arch).get("invocations") or 0),
        }
        for arch in metas
    }
    write_json(state_path, state)

    # Append telemetry rows (tracked, sanitized).
    tel_dir = os.path.join(CONSILIUM, "telemetry")
    os.makedirs(tel_dir, exist_ok=True)
    with open(os.path.join(tel_dir, "sessions.jsonl"), "a", encoding="utf-8") as fh:
        for arch in metas:
            m = dict(metas[arch])
            m.update({"round": round_id, "architect": arch})
            fh.write(json.dumps(m, ensure_ascii=False) + "\n")
    print("[freeze] frozen:", ", ".join(f"{a}={metas[a]['response_sha256'][:12]}" for a in metas))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    lp = sub.add_parser("launch")
    lp.add_argument("--round", required=True)
    lp.add_argument("--template", required=True)
    lp.add_argument("--timeout", type=int, required=True)
    lf = sub.add_parser("launch-files")
    lf.add_argument("--round", required=True)
    lf.add_argument("--timeout", type=int, required=True)
    fp = sub.add_parser("freeze")
    fp.add_argument("--round", required=True)
    args = ap.parse_args()
    if args.cmd == "launch":
        return launch(args.round, args.template, args.timeout)
    if args.cmd == "launch-files":
        return launch_files(args.round, args.timeout)
    if args.cmd == "freeze":
        return freeze(args.round)
    return 2


if __name__ == "__main__":
    sys.exit(main())
