"""Run a fresh Codex Developer or Reviewer session with full telemetry capture (Section 3, 4, 12)."""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time

from . import CAMPAIGN_ID, MAIN_REPO, MANAGER_SESSION_ID, STATE_ROOT, TELEMETRY_DIR
from .telemetry import capture_quota_snapshot, log_decision, log_termination, utc_now, write_event


def _git_head(wt):
    r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=wt, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def _git_commits_since(wt, old_head):
    if not old_head:
        return []
    r = subprocess.run(["git", "rev-list", "--reverse", f"{old_head}..HEAD"], cwd=wt, capture_output=True, text=True)
    if r.returncode != 0:
        return []
    return [ln.strip() for ln in r.stdout.splitlines() if ln.strip()]


def _parse_rollout_deep(rollout_path):
    """Extract cumulative tokens, peak context, reasoning tokens, and rate limits from rollout JSONL."""
    out = {
        "input_tokens": None,
        "cached_input_tokens": None,
        "output_tokens": None,
        "reasoning_tokens": None,
        "peak_context_tokens": None,
        "rate_limits": None,
        "first_event_ts": None,
        "last_event_ts": None,
    }
    if not rollout_path or not os.path.isfile(rollout_path):
        return out
    from wc1 import codex
    u, rl = codex.parse_rollout_telemetry(rollout_path)
    if u:
        out["input_tokens"] = u.get("input_tokens")
        out["cached_input_tokens"] = u.get("cached_input_tokens")
        out["output_tokens"] = u.get("output_tokens")
        out["reasoning_tokens"] = u.get("reasoning_output_tokens")
    if rl:
        out["rate_limits"] = rl
    peak_ctx = 0
    try:
        with open(rollout_path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if not line.strip().startswith("{"):
                    continue
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                ts = rec.get("timestamp")
                if ts:
                    if out["first_event_ts"] is None:
                        out["first_event_ts"] = ts
                    out["last_event_ts"] = ts
                pay = rec.get("payload")
                if isinstance(pay, dict) and pay.get("type") == "token_count":
                    info = pay.get("info")
                    if isinstance(info, dict):
                        last_u = info.get("last_token_usage") or {}
                        in_t = int(last_u.get("input_tokens") or 0)
                        if in_t > peak_ctx:
                            peak_ctx = in_t
    except OSError:
        pass
    if peak_ctx > 0:
        out["peak_context_tokens"] = peak_ctx
    return out


def _extract_verdict(text):
    if not text:
        return None
    m = re.search(r"\bVERDICT\s*[:=]\s*(APPROVE|REQUEST_CHANGES|REJECT|BLOCKED)\b", text, re.I)
    if m:
        return m.group(1).upper()
    m = re.search(r"\b(APPROVE|REQUEST_CHANGES|REJECT|BLOCKED)\b", text)
    return m.group(1).upper() if m else None


def run_codex_session(
    *,
    session_id,
    exp_id,
    role,
    task_id,
    worktree,
    branch,
    prompt_file,
    model="gpt-6.1-sol",
    effort="high",
    sandbox="danger-full-access",
    timeout_s=1800,
    predecessor_id=None,
    reviewed_commits=None,
    rationale="",
):
    assert role in ("developer", "reviewer"), f"invalid role: {role}"
    with open(prompt_file, encoding="utf-8") as fh:
        prompt_text = fh.read()
    prompt_sha = hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()

    # Archive prompt into tracked telemetry
    prompt_dst_dir = os.path.join(TELEMETRY_DIR, "prompts", role)
    os.makedirs(prompt_dst_dir, exist_ok=True)
    prompt_dst = os.path.join(prompt_dst_dir, f"{session_id}.md")
    with open(prompt_dst, "w", encoding="utf-8") as fh:
        fh.write(prompt_text)

    raw_dir = os.path.join(STATE_ROOT, "raw_logs")
    os.makedirs(raw_dir, exist_ok=True)
    raw_jsonl_path = os.path.join(raw_dir, f"{session_id}.jsonl")
    raw_stderr_path = os.path.join(raw_dir, f"{session_id}.stderr.log")
    last_msg_path = os.path.join(raw_dir, f"{session_id}.last_message.md")

    summary_dir = os.path.join(TELEMETRY_DIR, "summaries")
    os.makedirs(summary_dir, exist_ok=True)
    response_dst = os.path.join(summary_dir, f"{session_id}.md")

    # Pre-session state
    pre_head = _git_head(worktree)
    quota_before = capture_quota_snapshot(f"pre_{role}_{session_id}", exp_id=exp_id, session_id=session_id)
    log_decision(
        f"start_{role}",
        rationale or f"Launch fresh {role} session {session_id} for {exp_id} ({task_id})",
        exp_id=exp_id,
        session_id=session_id,
        details={"task_id": task_id, "worktree": worktree, "branch": branch, "predecessor_id": predecessor_id},
    )

    env = dict(os.environ)
    env["WC1_ROOT"] = os.path.abspath(worktree)
    env["PYTHONPATH"] = os.path.join(os.path.abspath(worktree), "tools") + (
        ":" + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
    )
    env["WINEPREFIX"] = os.path.join(os.path.abspath(worktree), "build", "oldcc", "wineprefix")
    env["TMPDIR"] = os.path.join(os.path.abspath(worktree), "build", "tmp")
    os.makedirs(env["TMPDIR"], exist_ok=True)

    cmd = [
        "codex", "exec",
        "--ignore-user-config",
        "--ignore-rules",
        "-m", model,
        "-c", f'model_reasoning_effort="{effort}"',
        "--json",
        "-s", sandbox,
        "-C", os.path.abspath(worktree),
        "-o", last_msg_path,
        "-",
    ]

    start_ts = utc_now()
    t0 = time.monotonic()
    timed_out = False
    exit_code = -1

    with open(raw_jsonl_path, "wb") as out_fh, open(raw_stderr_path, "wb") as err_fh:
        proc = subprocess.Popen(
            cmd,
            cwd=os.path.abspath(worktree),
            env=env,
            stdin=subprocess.PIPE,
            stdout=out_fh,
            stderr=err_fh,
        )
        try:
            proc.stdin.write(prompt_text.encode("utf-8"))
            proc.stdin.close()
            exit_code = proc.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            timed_out = True
            proc.terminate()
            try:
                proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=10)
            exit_code = 124

    wall_s = round(time.monotonic() - t0, 3)
    end_ts = utc_now()

    # Parse JSONL output
    thread_id = None
    turns = 0
    tool_calls = 0
    reasoning_summaries = []
    tool_events = []
    stream_usage = {"input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0, "reasoning_output_tokens": 0}
    has_stream_usage = False
    errors = []

    if os.path.isfile(raw_jsonl_path):
        with open(raw_jsonl_path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                s = line.strip()
                if not s.startswith("{"):
                    continue
                try:
                    ev = json.loads(s)
                except ValueError:
                    continue
                et = ev.get("type")
                if et == "thread.started":
                    thread_id = ev.get("thread_id")
                elif et == "turn.completed":
                    turns += 1
                    u = ev.get("usage")
                    if isinstance(u, dict):
                        has_stream_usage = True
                        stream_usage["input_tokens"] += int(u.get("input_tokens") or 0)
                        stream_usage["cached_input_tokens"] += int(u.get("cached_input_tokens") or 0)
                        stream_usage["output_tokens"] += int(u.get("output_tokens") or 0)
                        stream_usage["reasoning_output_tokens"] += int(u.get("reasoning_output_tokens") or 0)
                elif et == "item.completed":
                    item = ev.get("item") or {}
                    it = item.get("type")
                    if it == "reasoning":
                        txt = (item.get("text") or "").strip()
                        if txt:
                            reasoning_summaries.append(txt[:1000])
                    elif it not in ("agent_message", "reasoning"):
                        tool_calls += 1
                        te = {"type": it}
                        if it == "command_execution":
                            te["command"] = (item.get("command") or "")[:300]
                            te["exit_code"] = item.get("exit_code")
                            te["status"] = item.get("status")
                        elif it == "file_change":
                            te["changes"] = len(item.get("changes") or [])
                            te["status"] = item.get("status")
                        tool_events.append(te)
                elif et in ("turn.failed", "error"):
                    errors.append(str(ev.get("message") or ev.get("error") or ev)[:400])

    # Parse rollout for exact cumulative usage & post-session rate limits
    rollout_path = None
    rollout_info = {}
    if thread_id:
        from wc1 import codex
        rollout_path = codex.find_rollout_for_thread(thread_id)
        rollout_info = _parse_rollout_deep(rollout_path)

    quota_after = capture_quota_snapshot(f"post_{role}_{session_id}", exp_id=exp_id, session_id=session_id)

    # Prefer rollout totals if available, else stream usage
    if rollout_info.get("input_tokens") is not None:
        in_tok = rollout_info["input_tokens"]
        cached_tok = rollout_info["cached_input_tokens"]
        out_tok = rollout_info["output_tokens"]
        reason_tok = rollout_info["reasoning_tokens"]
        tok_prov = "exact"
    elif has_stream_usage:
        in_tok = stream_usage["input_tokens"]
        cached_tok = stream_usage["cached_input_tokens"]
        out_tok = stream_usage["output_tokens"]
        reason_tok = stream_usage["reasoning_output_tokens"]
        tok_prov = "exact"
    else:
        in_tok = cached_tok = out_tok = reason_tok = None
        tok_prov = "unavailable"

    last_msg = ""
    if os.path.isfile(last_msg_path):
        with open(last_msg_path, encoding="utf-8", errors="replace") as fh:
            last_msg = fh.read()
    with open(response_dst, "w", encoding="utf-8") as fh:
        fh.write(last_msg or f"(No final message; exit_code={exit_code}, timed_out={timed_out})\n")

    post_head = _git_head(worktree)
    produced_commits = _git_commits_since(worktree, pre_head)
    verdict = _extract_verdict(last_msg) if role == "reviewer" else None

    if timed_out:
        term_reason = f"timeout after {timeout_s}s"
        term_init = "manager"
        task_status = "TIMED_OUT"
    elif exit_code == 0:
        term_reason = "completed assigned atomic task"
        term_init = "voluntary"
        task_status = "COMPLETED"
    else:
        term_reason = f"exited with code {exit_code}" + (f": {errors[0]}" if errors else "")
        term_init = "failure"
        task_status = "FAILED"

    session_rec = {
        "session_id": session_id,
        "parent_session_id": MANAGER_SESSION_ID,
        "campaign_id": CAMPAIGN_ID,
        "exp_id": exp_id,
        "role": role,
        "provider": "openai",
        "harness": "codex-cli 0.172.0",
        "model": model,
        "reasoning_effort": effort,
        "sandbox": sandbox,
        "branch": branch,
        "worktree": os.path.abspath(worktree),
        "task_id": task_id,
        "start_ts_utc": start_ts,
        "end_ts_utc": end_ts,
        "wall_s": wall_s,
        "active_processing_s": None,
        "reasoning_time_s": None,
        "tool_exec_s": None,
        "input_tokens": in_tok,
        "cached_input_tokens": cached_tok,
        "output_tokens": out_tok,
        "reasoning_tokens": reason_tok,
        "turns": turns,
        "tool_calls": tool_calls,
        "peak_context_tokens": rollout_info.get("peak_context_tokens"),
        "quota_before": quota_before.get("codex"),
        "quota_after": quota_after.get("codex"),
        "exit_code": exit_code,
        "task_status": task_status,
        "termination_reason": term_reason,
        "termination_initiator": term_init,
        "pre_head": pre_head,
        "post_head": post_head,
        "produced_commits": produced_commits,
        "reviewed_commits": list(reviewed_commits or []),
        "review_verdict": verdict,
        "predecessor_session_id": predecessor_id,
        "successor_session_id": None,
        "thread_id": thread_id,
        "rollout_path": rollout_path,
        "prompt_id": session_id,
        "prompt_sha256": prompt_sha,
        "prompt_relpath": os.path.relpath(prompt_dst, MAIN_REPO),
        "response_relpath": os.path.relpath(response_dst, MAIN_REPO),
        "reasoning_summaries_count": len(reasoning_summaries),
        "reasoning_summaries_sample": reasoning_summaries[:5],
        "tool_events": tool_events[:100],
        "errors": errors[:10],
        "metric_provenance": {
            "wall_s": "exact",
            "tokens": tok_prov,
            "reasoning_tokens": tok_prov,
            "reasoning_time_s": "unavailable",
            "active_processing_s": "unavailable",
            "tool_exec_s": "unavailable",
            "quota": quota_after.get("codex", {}).get("provenance", "unavailable"),
        },
    }
    write_event("agent_session", session_rec)
    log_termination(
        session_id=session_id,
        role=role,
        model=model,
        exp_id=exp_id,
        start_ts=start_ts,
        end_ts=end_ts,
        task_status=task_status,
        resources={
            "wall_s": wall_s,
            "input_tokens": in_tok,
            "cached_input_tokens": cached_tok,
            "output_tokens": out_tok,
            "reasoning_tokens": reason_tok,
            "turns": turns,
            "tool_calls": tool_calls,
        },
        reason=term_reason,
        initiator=term_init,
        successor_created=False,
        successor_session_id=None,
        checkpoint=post_head,
        rationale=f"Fresh disposable {role} session concluded ({task_status}); commits={len(produced_commits)}, verdict={verdict}",
    )

    # Compact summary to stdout for Manager
    print(json.dumps({
        "session_id": session_id,
        "exp_id": exp_id,
        "role": role,
        "exit_code": exit_code,
        "task_status": task_status,
        "wall_s": wall_s,
        "turns": turns,
        "tool_calls": tool_calls,
        "input_tokens": in_tok,
        "cached_input_tokens": cached_tok,
        "output_tokens": out_tok,
        "reasoning_tokens": reason_tok,
        "produced_commits": produced_commits,
        "review_verdict": verdict,
        "response_relpath": session_rec["response_relpath"],
        "quota_after_5h": (quota_after.get("codex", {}).get("primary_5h") or {}).get("used_percent"),
        "quota_after_7d": (quota_after.get("codex", {}).get("secondary_7d") or {}).get("used_percent"),
    }, indent=2))
    return exit_code


def run_opencode2_session(
    *,
    session_id,
    exp_id,
    role,
    task_id,
    worktree,
    branch,
    prompt_file,
    model="opencode-go/deepseek-v4.1-flash",
    effort="default",
    timeout_s=1800,
    predecessor_id=None,
    reviewed_commits=None,
    rationale="",
):
    assert role in ("developer", "reviewer"), f"invalid role: {role}"
    with open(prompt_file, encoding="utf-8") as fh:
        prompt_text = fh.read()
    prompt_sha = hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()

    prompt_dst_dir = os.path.join(TELEMETRY_DIR, "prompts", role)
    os.makedirs(prompt_dst_dir, exist_ok=True)
    prompt_dst = os.path.join(prompt_dst_dir, f"{session_id}.md")
    with open(prompt_dst, "w", encoding="utf-8") as fh:
        fh.write(prompt_text)

    raw_dir = os.path.join(STATE_ROOT, "raw_logs")
    os.makedirs(raw_dir, exist_ok=True)
    raw_jsonl_path = os.path.join(raw_dir, f"{session_id}.jsonl")
    raw_stderr_path = os.path.join(raw_dir, f"{session_id}.stderr.log")

    summary_dir = os.path.join(TELEMETRY_DIR, "summaries")
    os.makedirs(summary_dir, exist_ok=True)
    response_dst = os.path.join(summary_dir, f"{session_id}.md")

    pre_head = _git_head(worktree)
    log_decision(
        f"start_{role}",
        rationale or f"Launch fresh {role} session {session_id} via opencode2 ({model}) for {exp_id} ({task_id})",
        exp_id=exp_id,
        session_id=session_id,
        details={"task_id": task_id, "worktree": worktree, "branch": branch, "harness": "opencode2", "model": model, "predecessor_id": predecessor_id},
    )

    env = dict(os.environ)
    env["WC1_ROOT"] = os.path.abspath(worktree)
    env["PYTHONPATH"] = os.path.join(os.path.abspath(worktree), "tools") + (
        ":" + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
    )
    env["WINEPREFIX"] = os.path.join(os.path.abspath(worktree), "build", "oldcc", "wineprefix")
    env["TMPDIR"] = os.path.join(os.path.abspath(worktree), "build", "tmp")
    os.makedirs(env["TMPDIR"], exist_ok=True)

    cmd = [
        "opencode2", "run",
        "--standalone",
        "--auto",
        "--archived",
        "--format", "json",
        "--thinking",
        "-m", model,
        "--title", f"{CAMPAIGN_ID}:{session_id}",
        prompt_text,
    ]

    start_ts = utc_now()
    t0 = time.monotonic()
    timed_out = False
    exit_code = -1

    with open(raw_jsonl_path, "wb") as out_fh, open(raw_stderr_path, "wb") as err_fh:
        proc = subprocess.Popen(
            cmd,
            cwd=os.path.abspath(worktree),
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=out_fh,
            stderr=err_fh,
        )
        try:
            exit_code = proc.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            timed_out = True
            proc.terminate()
            try:
                proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=10)
            exit_code = 124

    wall_s = round(time.monotonic() - t0, 3)
    end_ts = utc_now()

    oc_session_id = None
    turns = 0
    tool_calls = 0
    in_tok = cached_tok = out_tok = reason_tok = 0
    has_tok = False
    peak_ctx = 0
    text_parts = []
    reasoning_summaries = []
    tool_events = []
    errors = []

    if os.path.isfile(raw_jsonl_path):
        with open(raw_jsonl_path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                s = line.strip()
                if not s.startswith("{"):
                    continue
                try:
                    ev = json.loads(s)
                except ValueError:
                    continue
                if not oc_session_id and ev.get("sessionID"):
                    oc_session_id = ev.get("sessionID")
                et = ev.get("type")
                part = ev.get("part") if isinstance(ev.get("part"), dict) else {}
                if et == "step_finish":
                    turns += 1
                    tok = part.get("tokens")
                    if isinstance(tok, dict):
                        has_tok = True
                        ci = int((tok.get("cache") or {}).get("read") or 0)
                        ii = int(tok.get("input") or 0)
                        oo = int(tok.get("output") or 0)
                        rr = int(tok.get("reasoning") or 0)
                        in_tok += ii + ci
                        cached_tok += ci
                        out_tok += oo
                        reason_tok += rr
                        if ii + ci > peak_ctx:
                            peak_ctx = ii + ci
                elif et == "text":
                    t = part.get("text") or ""
                    if t:
                        text_parts.append(t)
                elif et == "reasoning":
                    t = (part.get("text") or "").strip()
                    if t:
                        reasoning_summaries.append(t[:1000])
                elif et in ("tool_use", "tool"):
                    tool_calls += 1
                    state = part.get("state") if isinstance(part.get("state"), dict) else {}
                    tool_events.append({
                        "type": part.get("tool") or et,
                        "status": state.get("status"),
                        "title": str(state.get("title") or "")[:200],
                    })
                elif et == "error":
                    errors.append(str(ev.get("error") or ev)[:400])

    last_msg = "\n".join(text_parts).strip()
    with open(response_dst, "w", encoding="utf-8") as fh:
        fh.write(last_msg or f"(No final message; exit_code={exit_code}, timed_out={timed_out})\n")

    post_head = _git_head(worktree)
    produced_commits = _git_commits_since(worktree, pre_head)
    verdict = _extract_verdict(last_msg) if role == "reviewer" else None

    if timed_out:
        term_reason = f"timeout after {timeout_s}s"
        term_init = "manager"
        task_status = "TIMED_OUT"
    elif exit_code == 0:
        term_reason = "completed assigned atomic task"
        term_init = "voluntary"
        task_status = "COMPLETED"
    else:
        term_reason = f"exited with code {exit_code}" + (f": {errors[0]}" if errors else "")
        term_init = "failure"
        task_status = "FAILED"

    tok_prov = "exact" if has_tok else "unavailable"
    provider_name = model.split("/", 1)[0] if "/" in model else "opencode2"

    session_rec = {
        "session_id": session_id,
        "parent_session_id": MANAGER_SESSION_ID,
        "campaign_id": CAMPAIGN_ID,
        "exp_id": exp_id,
        "role": role,
        "provider": provider_name,
        "harness": "opencode2 v2.4.1",
        "model": model,
        "reasoning_effort": effort,
        "sandbox": "opencode2-standalone-auto",
        "branch": branch,
        "worktree": os.path.abspath(worktree),
        "task_id": task_id,
        "start_ts_utc": start_ts,
        "end_ts_utc": end_ts,
        "wall_s": wall_s,
        "active_processing_s": None,
        "reasoning_time_s": None,
        "tool_exec_s": None,
        "input_tokens": in_tok if has_tok else None,
        "cached_input_tokens": cached_tok if has_tok else None,
        "output_tokens": out_tok if has_tok else None,
        "reasoning_tokens": reason_tok if has_tok else None,
        "turns": turns,
        "tool_calls": tool_calls,
        "peak_context_tokens": peak_ctx if peak_ctx > 0 else None,
        "quota_before": {"provenance": "unavailable", "reason": "OpenCode Go does not expose quota % locally"},
        "quota_after": {"provenance": "unavailable", "reason": "OpenCode Go does not expose quota % locally"},
        "exit_code": exit_code,
        "task_status": task_status,
        "termination_reason": term_reason,
        "termination_initiator": term_init,
        "pre_head": pre_head,
        "post_head": post_head,
        "produced_commits": produced_commits,
        "reviewed_commits": list(reviewed_commits or []),
        "review_verdict": verdict,
        "predecessor_session_id": predecessor_id,
        "successor_session_id": None,
        "thread_id": oc_session_id,
        "rollout_path": None,
        "prompt_id": session_id,
        "prompt_sha256": prompt_sha,
        "prompt_relpath": os.path.relpath(prompt_dst, MAIN_REPO),
        "response_relpath": os.path.relpath(response_dst, MAIN_REPO),
        "reasoning_summaries_count": len(reasoning_summaries),
        "reasoning_summaries_sample": reasoning_summaries[:5],
        "tool_events": tool_events[:100],
        "errors": errors[:10],
        "metric_provenance": {
            "wall_s": "exact",
            "tokens": tok_prov,
            "reasoning_tokens": tok_prov,
            "reasoning_time_s": "unavailable",
            "active_processing_s": "unavailable",
            "tool_exec_s": "unavailable",
            "quota": "unavailable",
        },
    }
    write_event("agent_session", session_rec)
    log_termination(
        session_id=session_id,
        role=role,
        model=model,
        exp_id=exp_id,
        start_ts=start_ts,
        end_ts=end_ts,
        task_status=task_status,
        resources={
            "wall_s": wall_s,
            "input_tokens": in_tok if has_tok else None,
            "cached_input_tokens": cached_tok if has_tok else None,
            "output_tokens": out_tok if has_tok else None,
            "reasoning_tokens": reason_tok if has_tok else None,
            "turns": turns,
            "tool_calls": tool_calls,
        },
        reason=term_reason,
        initiator=term_init,
        successor_created=False,
        successor_session_id=None,
        checkpoint=post_head,
        rationale=f"Fresh disposable {role} session via opencode2 ({model}) concluded ({task_status}); commits={len(produced_commits)}, verdict={verdict}",
    )

    print(json.dumps({
        "session_id": session_id,
        "exp_id": exp_id,
        "role": role,
        "harness": "opencode2 v2.4.1",
        "model": model,
        "exit_code": exit_code,
        "task_status": task_status,
        "wall_s": wall_s,
        "turns": turns,
        "tool_calls": tool_calls,
        "input_tokens": in_tok if has_tok else None,
        "cached_input_tokens": cached_tok if has_tok else None,
        "output_tokens": out_tok if has_tok else None,
        "reasoning_tokens": reason_tok if has_tok else None,
        "produced_commits": produced_commits,
        "review_verdict": verdict,
        "response_relpath": session_rec["response_relpath"],
    }, indent=2))
    return exit_code


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--harness", default="codex", choices=("codex", "opencode2"))
    ap.add_argument("--session-id", required=True)
    ap.add_argument("--exp", required=True)
    ap.add_argument("--role", required=True, choices=("developer", "reviewer"))
    ap.add_argument("--task-id", required=True)
    ap.add_argument("--worktree", required=True)
    ap.add_argument("--branch", required=True)
    ap.add_argument("--prompt-file", required=True)
    ap.add_argument("--model", default="gpt-6.1-sol")
    ap.add_argument("--effort", default="high")
    ap.add_argument("--sandbox", default="danger-full-access")
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--predecessor", default=None)
    ap.add_argument("--reviewed-commits", nargs="*", default=[])
    ap.add_argument("--rationale", default="")
    a = ap.parse_args()
    if a.harness == "opencode2":
        return run_opencode2_session(
            session_id=a.session_id,
            exp_id=a.exp,
            role=a.role,
            task_id=a.task_id,
            worktree=a.worktree,
            branch=a.branch,
            prompt_file=a.prompt_file,
            model=a.model,
            effort=a.effort,
            timeout_s=a.timeout,
            predecessor_id=a.predecessor,
            reviewed_commits=a.reviewed_commits,
            rationale=a.rationale,
        )
    return run_codex_session(
        session_id=a.session_id,
        exp_id=a.exp,
        role=a.role,
        task_id=a.task_id,
        worktree=a.worktree,
        branch=a.branch,
        prompt_file=a.prompt_file,
        model=a.model,
        effort=a.effort,
        sandbox=a.sandbox,
        timeout_s=a.timeout,
        predecessor_id=a.predecessor,
        reviewed_commits=a.reviewed_commits,
        rationale=a.rationale,
    )


if __name__ == "__main__":
    sys.exit(main())
