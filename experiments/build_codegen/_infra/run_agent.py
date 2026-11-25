"""Run a fresh Codex or OpenCode2 Developer/Reviewer session with full telemetry capture."""
import argparse
import datetime
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

DEFAULT_TIMEOUT_BY_ROLE = {
    "reviewer": 1800,
    "developer": 2700,
}
DEFAULT_RESUME_TIMEOUT_S = 300
RESUME_PROMPT = (
    "Stop investigating. Commit finished, tested work, or give your verdict from the "
    "evidence you have; list what is unchecked."
)

_EXPLICIT_VERDICT_RE = re.compile(
    r"(?im)^\s*(?:[#*>\-]+\s*|\d+\.\s*)*\*{0,2}VERDICT\s*[:=]\s*\*{0,2}"
    r"(APPROVE|REQUEST_CHANGES|REJECT|BLOCKED)\b"
)
_BARE_VERDICT_RE = re.compile(r"\b(APPROVE|REQUEST_CHANGES|REJECT|BLOCKED)\b")


def default_timeout_for_role(role):
    if role not in DEFAULT_TIMEOUT_BY_ROLE:
        raise ValueError(f"invalid role: {role}")
    return DEFAULT_TIMEOUT_BY_ROLE[role]


def _make_session_tmpdir(session_id):
    """Create a short, unique per-session TMPDIR under /tmp (<= ~32 chars for Watcom 10.0a)."""
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", str(session_id)).strip("-") or "sess"
    if len(safe) > 18:
        h = hashlib.sha256(str(session_id).encode("utf-8")).hexdigest()[:6]
        safe = f"{safe[:11]}-{h}"
    base = f"/tmp/wc1-{safe}"
    path = base
    n = 1
    while os.path.exists(path):
        path = f"{base}-{os.getpid() % 1000}-{n}"
        n += 1
    os.makedirs(path, exist_ok=True)
    return path


def _build_effective_prompt(prompt_text, *, role, timeout_s, start_epoch=None, start_utc=None):
    """Append hard deadline and operational efficiency rules to every session prompt."""
    if start_epoch is None:
        start_epoch = int(time.time())
    if start_utc is None:
        start_utc = datetime.datetime.fromtimestamp(
            start_epoch, tz=datetime.timezone.utc
        ).isoformat().replace("+00:00", "Z")
    checkpoint_s = int(timeout_s * 0.7)
    checkpoint_utc = datetime.datetime.fromtimestamp(
        start_epoch + checkpoint_s, tz=datetime.timezone.utc
    ).isoformat().replace("+00:00", "Z")
    hard_utc = datetime.datetime.fromtimestamp(
        start_epoch + int(timeout_s), tz=datetime.timezone.utc
    ).isoformat().replace("+00:00", "Z")
    role_guidance = (
        "Commit finished, tested atomic units as you go rather than waiting until the end; "
        "begin writing your final report and final commits by the 70% mark."
        if role == "developer"
        else "Begin writing your final review report and explicit `VERDICT: ...` line by the 70% mark."
    )
    footer = (
        "\n\n---\n"
        "## Session Operational Rules & Hard Deadline (Appended by Runner)\n"
        f"- **Launch time:** `{start_utc}` (Unix epoch `{start_epoch}`)\n"
        f"- **Hard wall-clock limit:** `{int(timeout_s)} s` (~`{int(timeout_s) // 60} min`, hard cutoff `{hard_utc}`)\n"
        f"- **70% wrap-up checkpoint:** `{checkpoint_s} s` (`{checkpoint_utc}`) — check elapsed time periodically with `date -u +%s`.\n"
        f"- **Pacing:** {role_guidance}\n"
        "- **Efficiency:** Do NOT use `sleep` polling loops. Do NOT run `make verify` or the full repository test suite unless explicitly required by your assignment. Batch independent shell commands into a single step where safe to reduce turn latency.\n"
    )
    return prompt_text.rstrip() + footer


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


def _git_dirty_state(wt):
    """Return structured dirty-worktree state, ignoring the expected `original` symlink."""
    r = subprocess.run(["git", "status", "--porcelain"], cwd=wt, capture_output=True, text=True)
    if r.returncode != 0:
        return {"is_dirty": None, "modified": [], "untracked": [], "error": r.stderr.strip()[:200]}
    modified = []
    untracked = []
    for raw in r.stdout.splitlines():
        if len(raw) < 4:
            continue
        status = raw[:2]
        rel = raw[3:].strip()
        if rel in ("original", "original/"):
            continue
        if status == "??":
            untracked.append(rel)
        else:
            modified.append(f"{status.strip()} {rel}")
    return {
        "is_dirty": bool(modified or untracked),
        "modified": modified,
        "untracked": untracked,
    }


def _detect_final_report(wt, produced_commits, dirty_state, final_message):
    """Detect whether a report artifact or final message was produced."""
    report_files = set()
    for sha in produced_commits or []:
        r = subprocess.run(
            ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", sha],
            cwd=wt, capture_output=True, text=True,
        )
        if r.returncode == 0:
            for p in r.stdout.splitlines():
                p = p.strip()
                if p.startswith("docs/research/build-codegen/") and p.endswith(".md"):
                    report_files.add(p)
    for item in (dirty_state.get("untracked") or []):
        if item.startswith("docs/research/build-codegen/") and item.endswith(".md"):
            report_files.add(item)
    for item in (dirty_state.get("modified") or []):
        parts = item.split(None, 1)
        rel = parts[1] if len(parts) == 2 else item
        if rel.startswith("docs/research/build-codegen/") and rel.endswith(".md"):
            report_files.add(rel)
    return {
        "has_final_message": bool((final_message or "").strip()),
        "report_files": sorted(report_files),
        "has_report_file": bool(report_files),
    }


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


def _extract_verdict(text, *, final_message=None, timed_out=False):
    """Extract reviewer verdict with fail-closed timeout safety.

    On a timed-out session, accept ONLY an explicit `VERDICT:` line inside
    `final_message`; never fall back to bare words or earlier turns.
    """
    final_txt = (final_message if final_message is not None else text) or ""
    if timed_out:
        matches = list(_EXPLICIT_VERDICT_RE.finditer(final_txt))
        return matches[-1].group(1).upper() if matches else None

    for candidate in (final_txt, text or ""):
        if not candidate:
            continue
        matches = list(_EXPLICIT_VERDICT_RE.finditer(candidate))
        if matches:
            return matches[-1].group(1).upper()
    if final_txt:
        m = _BARE_VERDICT_RE.search(final_txt)
        if m:
            return m.group(1).upper()
    return None


def _parse_opencode2_jsonl(jsonl_path):
    """Parse an opencode2 --format json JSONL stream."""
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

    if jsonl_path and os.path.isfile(jsonl_path):
        with open(jsonl_path, encoding="utf-8", errors="replace") as fh:
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

    return {
        "session_id": oc_session_id,
        "turns": turns,
        "tool_calls": tool_calls,
        "input_tokens": in_tok,
        "cached_input_tokens": cached_tok,
        "output_tokens": out_tok,
        "reasoning_tokens": reason_tok,
        "has_tok": has_tok,
        "peak_context_tokens": peak_ctx,
        "text_parts": text_parts,
        "final_message": text_parts[-1].strip() if text_parts else "",
        "reasoning_summaries": reasoning_summaries,
        "tool_events": tool_events,
        "errors": errors,
    }


def _run_subprocess_bounded(cmd, *, cwd, env, stdout_path, stderr_path, timeout_s, stdin_bytes=None):
    """Run a subprocess with a wall-clock timeout and clean SIGTERM -> SIGKILL fallback."""
    t0 = time.monotonic()
    timed_out = False
    exit_code = -1
    with open(stdout_path, "wb") as out_fh, open(stderr_path, "wb") as err_fh:
        proc = subprocess.Popen(
            cmd,
            cwd=os.path.abspath(cwd),
            env=env,
            stdin=subprocess.PIPE if stdin_bytes is not None else subprocess.DEVNULL,
            stdout=out_fh,
            stderr=err_fh,
        )
        try:
            if stdin_bytes is not None:
                proc.stdin.write(stdin_bytes)
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
    return exit_code, timed_out, round(time.monotonic() - t0, 3)


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
    timeout_s=None,
    predecessor_id=None,
    reviewed_commits=None,
    rationale="",
):
    assert role in ("developer", "reviewer"), f"invalid role: {role}"
    if timeout_s is None:
        timeout_s = default_timeout_for_role(role)

    with open(prompt_file, encoding="utf-8") as fh:
        raw_prompt_text = fh.read()

    start_epoch = int(time.time())
    start_ts = utc_now()
    prompt_text = _build_effective_prompt(
        raw_prompt_text, role=role, timeout_s=timeout_s, start_epoch=start_epoch, start_utc=start_ts
    )
    prompt_sha = hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()

    # Archive effective prompt into tracked telemetry
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
        details={
            "task_id": task_id,
            "worktree": worktree,
            "branch": branch,
            "timeout_s": timeout_s,
            "predecessor_id": predecessor_id,
        },
    )

    session_tmpdir = _make_session_tmpdir(session_id)
    env = dict(os.environ)
    env["WC1_ROOT"] = os.path.abspath(worktree)
    env["PYTHONPATH"] = os.path.join(os.path.abspath(worktree), "tools") + (
        ":" + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
    )
    env["WINEPREFIX"] = os.path.join(os.path.abspath(worktree), "build", "oldcc", "wineprefix")
    env["TMPDIR"] = session_tmpdir

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

    try:
        exit_code, timed_out, wall_s = _run_subprocess_bounded(
            cmd,
            cwd=worktree,
            env=env,
            stdout_path=raw_jsonl_path,
            stderr_path=raw_stderr_path,
            timeout_s=timeout_s,
            stdin_bytes=prompt_text.encode("utf-8"),
        )
    finally:
        shutil.rmtree(session_tmpdir, ignore_errors=True)

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
    dirty_state = _git_dirty_state(worktree)
    report_state = _detect_final_report(worktree, produced_commits, dirty_state, last_msg)
    verdict = _extract_verdict(last_msg, final_message=last_msg, timed_out=timed_out) if role == "reviewer" else None

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
        "timeout_s": timeout_s,
        "tmpdir": session_tmpdir,
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
        "timed_out": timed_out,
        "termination_reason": term_reason,
        "termination_initiator": term_init,
        "pre_head": pre_head,
        "post_head": post_head,
        "produced_commits": produced_commits,
        "dirty_worktree": dirty_state,
        "final_report": report_state,
        "reviewed_commits": list(reviewed_commits or []),
        "review_verdict": verdict,
        "has_explicit_verdict": verdict is not None,
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
        rationale=(
            f"Fresh disposable {role} session concluded ({task_status}); "
            f"commits={len(produced_commits)}, dirty={dirty_state.get('is_dirty')}, verdict={verdict}"
        ),
    )

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
        "dirty_worktree": dirty_state,
        "final_report": report_state,
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
    timeout_s=None,
    resume_timeout_s=DEFAULT_RESUME_TIMEOUT_S,
    predecessor_id=None,
    reviewed_commits=None,
    rationale="",
):
    assert role in ("developer", "reviewer"), f"invalid role: {role}"
    if timeout_s is None:
        timeout_s = default_timeout_for_role(role)

    with open(prompt_file, encoding="utf-8") as fh:
        raw_prompt_text = fh.read()

    start_epoch = int(time.time())
    start_ts = utc_now()
    prompt_text = _build_effective_prompt(
        raw_prompt_text, role=role, timeout_s=timeout_s, start_epoch=start_epoch, start_utc=start_ts
    )
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
    resume_jsonl_path = os.path.join(raw_dir, f"{session_id}.resume.jsonl")
    resume_stderr_path = os.path.join(raw_dir, f"{session_id}.resume.stderr.log")

    summary_dir = os.path.join(TELEMETRY_DIR, "summaries")
    os.makedirs(summary_dir, exist_ok=True)
    response_dst = os.path.join(summary_dir, f"{session_id}.md")

    pre_head = _git_head(worktree)
    log_decision(
        f"start_{role}",
        rationale or f"Launch fresh {role} session {session_id} via opencode2 ({model}) for {exp_id} ({task_id})",
        exp_id=exp_id,
        session_id=session_id,
        details={
            "task_id": task_id,
            "worktree": worktree,
            "branch": branch,
            "harness": "opencode2",
            "model": model,
            "timeout_s": timeout_s,
            "resume_timeout_s": resume_timeout_s,
            "predecessor_id": predecessor_id,
        },
    )

    session_tmpdir = _make_session_tmpdir(session_id)
    env = dict(os.environ)
    env["WC1_ROOT"] = os.path.abspath(worktree)
    env["PYTHONPATH"] = os.path.join(os.path.abspath(worktree), "tools") + (
        ":" + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
    )
    env["WINEPREFIX"] = os.path.join(os.path.abspath(worktree), "build", "oldcc", "wineprefix")
    env["TMPDIR"] = session_tmpdir

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

    resume_info = {
        "attempted": False,
        "succeeded": False,
        "exit_code": None,
        "timed_out": False,
        "wall_s": 0.0,
        "turns": 0,
        "tool_calls": 0,
        "input_tokens": None,
        "cached_input_tokens": None,
        "output_tokens": None,
        "reasoning_tokens": None,
        "raw_jsonl_path": None,
    }
    parsed_resume = None

    try:
        exit_code, timed_out, initial_wall_s = _run_subprocess_bounded(
            cmd,
            cwd=worktree,
            env=env,
            stdout_path=raw_jsonl_path,
            stderr_path=raw_stderr_path,
            timeout_s=timeout_s,
        )
        parsed = _parse_opencode2_jsonl(raw_jsonl_path)
        oc_session_id = parsed["session_id"]

        if timed_out and oc_session_id and resume_timeout_s and resume_timeout_s > 0:
            resume_info["attempted"] = True
            resume_info["raw_jsonl_path"] = resume_jsonl_path
            resume_cmd = [
                "opencode2", "run",
                "-s", oc_session_id,
                "--standalone",
                "--auto",
                "--archived",
                "--format", "json",
                "--thinking",
                "-m", model,
                RESUME_PROMPT,
            ]
            r_exit, r_to, r_wall = _run_subprocess_bounded(
                resume_cmd,
                cwd=worktree,
                env=env,
                stdout_path=resume_jsonl_path,
                stderr_path=resume_stderr_path,
                timeout_s=resume_timeout_s,
            )
            parsed_resume = _parse_opencode2_jsonl(resume_jsonl_path)
            resume_info.update({
                "succeeded": (r_exit == 0 and not r_to),
                "exit_code": r_exit,
                "timed_out": r_to,
                "wall_s": r_wall,
                "turns": parsed_resume["turns"],
                "tool_calls": parsed_resume["tool_calls"],
                "input_tokens": parsed_resume["input_tokens"] if parsed_resume["has_tok"] else None,
                "cached_input_tokens": parsed_resume["cached_input_tokens"] if parsed_resume["has_tok"] else None,
                "output_tokens": parsed_resume["output_tokens"] if parsed_resume["has_tok"] else None,
                "reasoning_tokens": parsed_resume["reasoning_tokens"] if parsed_resume["has_tok"] else None,
            })
    finally:
        shutil.rmtree(session_tmpdir, ignore_errors=True)

    end_ts = utc_now()
    wall_s = round(initial_wall_s + float(resume_info["wall_s"] or 0.0), 3)

    # Combine initial + resume telemetry while preserving resume breakdown
    turns = parsed["turns"] + (parsed_resume["turns"] if parsed_resume else 0)
    tool_calls = parsed["tool_calls"] + (parsed_resume["tool_calls"] if parsed_resume else 0)
    has_tok = parsed["has_tok"] or bool(parsed_resume and parsed_resume["has_tok"])
    in_tok = parsed["input_tokens"] + (parsed_resume["input_tokens"] if parsed_resume else 0)
    cached_tok = parsed["cached_input_tokens"] + (parsed_resume["cached_input_tokens"] if parsed_resume else 0)
    out_tok = parsed["output_tokens"] + (parsed_resume["output_tokens"] if parsed_resume else 0)
    reason_tok = parsed["reasoning_tokens"] + (parsed_resume["reasoning_tokens"] if parsed_resume else 0)
    peak_ctx = max(parsed["peak_context_tokens"], parsed_resume["peak_context_tokens"] if parsed_resume else 0)
    text_parts = list(parsed["text_parts"]) + (list(parsed_resume["text_parts"]) if parsed_resume else [])
    reasoning_summaries = list(parsed["reasoning_summaries"]) + (list(parsed_resume["reasoning_summaries"]) if parsed_resume else [])
    tool_events = list(parsed["tool_events"]) + (list(parsed_resume["tool_events"]) if parsed_resume else [])
    errors = list(parsed["errors"]) + (list(parsed_resume["errors"]) if parsed_resume else [])

    final_message = (
        parsed_resume["final_message"]
        if (parsed_resume and parsed_resume["final_message"])
        else parsed["final_message"]
    )
    combined_text = "\n".join(text_parts).strip()
    with open(response_dst, "w", encoding="utf-8") as fh:
        fh.write(combined_text or f"(No final message; exit_code={exit_code}, timed_out={timed_out})\n")

    post_head = _git_head(worktree)
    produced_commits = _git_commits_since(worktree, pre_head)
    dirty_state = _git_dirty_state(worktree)
    report_state = _detect_final_report(worktree, produced_commits, dirty_state, final_message)
    verdict = (
        _extract_verdict(combined_text, final_message=final_message, timed_out=timed_out)
        if role == "reviewer"
        else None
    )

    if timed_out:
        term_reason = (
            f"timeout after {timeout_s}s"
            + (
                f" (resume {'succeeded' if resume_info['succeeded'] else 'failed/timed_out'} in {resume_info['wall_s']}s)"
                if resume_info["attempted"]
                else ""
            )
        )
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
        "timeout_s": timeout_s,
        "resume_timeout_s": resume_timeout_s,
        "tmpdir": session_tmpdir,
        "start_ts_utc": start_ts,
        "end_ts_utc": end_ts,
        "initial_wall_s": initial_wall_s,
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
        "timed_out": timed_out,
        "resume": resume_info,
        "termination_reason": term_reason,
        "termination_initiator": term_init,
        "pre_head": pre_head,
        "post_head": post_head,
        "produced_commits": produced_commits,
        "dirty_worktree": dirty_state,
        "final_report": report_state,
        "reviewed_commits": list(reviewed_commits or []),
        "review_verdict": verdict,
        "has_explicit_verdict": verdict is not None,
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
            "initial_wall_s": initial_wall_s,
            "resume_wall_s": resume_info["wall_s"],
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
        rationale=(
            f"Fresh disposable {role} session via opencode2 ({model}) concluded ({task_status}); "
            f"commits={len(produced_commits)}, dirty={dirty_state.get('is_dirty')}, "
            f"report={report_state.get('has_report_file')}, verdict={verdict}, "
            f"resume_attempted={resume_info['attempted']}, resume_ok={resume_info['succeeded']}"
        ),
    )

    print(json.dumps({
        "session_id": session_id,
        "exp_id": exp_id,
        "role": role,
        "harness": "opencode2 v2.4.1",
        "model": model,
        "exit_code": exit_code,
        "task_status": task_status,
        "timed_out": timed_out,
        "initial_wall_s": initial_wall_s,
        "wall_s": wall_s,
        "turns": turns,
        "tool_calls": tool_calls,
        "input_tokens": in_tok if has_tok else None,
        "cached_input_tokens": cached_tok if has_tok else None,
        "output_tokens": out_tok if has_tok else None,
        "reasoning_tokens": reason_tok if has_tok else None,
        "produced_commits": produced_commits,
        "dirty_worktree": dirty_state,
        "final_report": report_state,
        "review_verdict": verdict,
        "resume": resume_info,
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
    ap.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="Hard wall-clock timeout in seconds (defaults: 1800 reviewer, 2700 developer).",
    )
    ap.add_argument(
        "--resume-timeout",
        type=int,
        default=DEFAULT_RESUME_TIMEOUT_S,
        help="Max seconds for one opencode2 -s continuation after timeout (0 disables).",
    )
    ap.add_argument("--predecessor", default=None)
    ap.add_argument("--reviewed-commits", nargs="*", default=[])
    ap.add_argument("--rationale", default="")
    a = ap.parse_args()
    timeout_s = a.timeout if a.timeout is not None else default_timeout_for_role(a.role)
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
            timeout_s=timeout_s,
            resume_timeout_s=a.resume_timeout,
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
        timeout_s=timeout_s,
        predecessor_id=a.predecessor,
        reviewed_commits=a.reviewed_commits,
        rationale=a.rationale,
    )


if __name__ == "__main__":
    sys.exit(main())
