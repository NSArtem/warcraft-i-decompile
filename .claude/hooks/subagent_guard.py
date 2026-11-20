#!/usr/bin/env python3
"""PreToolUse / SubagentStart / SubagentStop hook: enforce AGENTS.md / .claude/agents.

Claude Code passes `agent_id` / `agent_type` in the hook input only for
tool calls made by a subagent.
For subagents (PreToolUse) it blocks:
  - git commit / git push        (only the session owner commits)
  - make build / make roundtrip  (they write shared build/ files)
  - edits to Makefile, flake.*, asm/**, src/include/war.h, .claude/**,
    .opencode/**               (shared files; the guard itself)
  - spawning further subagents (Agent / Task)
For the main agent it enforces max 1 concurrent subagent (tracking pending
PreToolUse Agent/Task calls + SubagentStart/SubagentStop in a per-session
state file under build/scratch/, with stale-entry expiry).
Mirrors the permission denies of .opencode/agents/*.md.  Exit 2 = block,
the stderr text goes back to the subagent/main agent.
"""
import fcntl
import json
import os
import re
import sys
import time

SHELL_RULES = [
    (re.compile(r"\bgit\b[^;&|\n]*\s(commit|push)\b"),
     "subagents never commit or push; the session owner commits"),
    (re.compile(r"(^|[;&|(\s])make(\s+(-\S+|\w+=\S*))*\s+[^;&|\n]*\b(build|roundtrip)(?![\w/.-])"),
     "subagents never run make build / make roundtrip (they write shared "
     "build/ files); use build/<area>/ for scratch"),
]

PROTECTED = re.compile(
    r"^(Makefile|flake\.[^/]*|asm/.*|src/include/war\.h|\.claude/.*|\.opencode/.*)$")

EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
MAX_CONCURRENT_SUBAGENTS = 1
STALE_SECONDS = 1800


def _state_path(root):
    override = os.environ.get("WC1_SUBAGENT_STATE")
    if override:
        return override
    return os.path.join(root, "build", "scratch", "active_subagents.json")


def _update_state(state_file, fn):
    os.makedirs(os.path.dirname(state_file), exist_ok=True)
    with open(state_file, "a+") as fh:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        fh.seek(0)
        raw = fh.read().strip()
        try:
            state = json.loads(raw) if raw else {}
        except ValueError:
            state = {}
        now = time.time()
        # Prune stale entries so a killed/crashed subagent never deadlocks future work
        state = {
            sid: {k: v for k, v in entries.items() if now - v.get("ts", 0) < STALE_SECONDS}
            for sid, entries in state.items()
            if isinstance(entries, dict)
        }
        state = {sid: entries for sid, entries in state.items() if entries}
        result = fn(state, now)
        fh.seek(0)
        fh.truncate()
        json.dump(state, fh)
        fh.flush()
        return result


def handle_lifecycle(data, root):
    """Update active subagent tracking for SubagentStart/SubagentStop/PostToolUseFailure."""
    ev = data.get("hook_event_name", "")
    sid = data.get("session_id")
    if not sid:
        return None
    sf = _state_path(root)
    if ev == "SubagentStart":
        aid = data.get("agent_id") or data.get("tool_use_id") or "sub"
        def add(state, now):
            cur = state.setdefault(sid, {})
            # Replace oldest pending slot if one was reserved at PreToolUse
            pending = [k for k, v in cur.items() if v.get("pending")]
            if pending:
                del cur[pending[0]]
            cur[aid] = {"ts": now, "type": data.get("agent_type", ""), "pending": False}
        _update_state(sf, add)
    elif ev in ("SubagentStop", "PostToolUseFailure"):
        aid = data.get("agent_id")
        tid = data.get("tool_use_id")
        def remove(state, _now):
            cur = state.get(sid)
            if not cur:
                return
            if aid and aid in cur:
                del cur[aid]
            elif tid and f"pending:{tid}" in cur:
                del cur[f"pending:{tid}"]
            elif ev == "SubagentStop" and cur:
                # Fallback if agent_id wasn't matched: drop oldest entry
                oldest = min(cur.items(), key=lambda kv: kv[1].get("ts", 0))[0]
                del cur[oldest]
        _update_state(sf, remove)
    return None


def check(data, root):
    """Return a block reason, or None to allow."""
    ev = data.get("hook_event_name", "PreToolUse")
    if ev in ("SubagentStart", "SubagentStop", "PostToolUseFailure"):
        return handle_lifecycle(data, root)
    tool = data.get("tool_name", "")
    inp = data.get("tool_input") or {}
    if not data.get("agent_id") and not data.get("agent_type"):
        # Main agent: enforce max concurrent subagents on Agent/Task spawns
        sid = data.get("session_id")
        if tool in ("Agent", "Task") and sid:
            tid = data.get("tool_use_id") or f"t{time.time_ns()}"
            def reserve(state, now):
                cur = state.setdefault(sid, {})
                if len(cur) >= MAX_CONCURRENT_SUBAGENTS:
                    active = ", ".join(sorted(cur.keys()))
                    return (f"max {MAX_CONCURRENT_SUBAGENTS} concurrent subagent allowed "
                            f"(active: {active}); wait for it to finish before spawning another")
                cur[f"pending:{tid}"] = {"ts": now, "pending": True}
                return None
            return _update_state(_state_path(root), reserve)
        return None
    if tool in ("Agent", "Task"):
        return "subagents do not spawn subagents; report the need instead"
    if tool == "Bash":
        cmd = inp.get("command", "")
        for rx, why in SHELL_RULES:
            if rx.search(cmd):
                return why
    if tool in EDIT_TOOLS:
        path = inp.get("file_path") or inp.get("notebook_path") or ""
        cwd = data.get("cwd") or root
        full = os.path.normpath(os.path.join(cwd, path))
        rel = os.path.relpath(full, root)
        if not rel.startswith("..") and PROTECTED.match(rel):
            return (f"{rel} is a shared file subagents must not edit; put the "
                    "change in your report as a patch sketch")
    return None


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return 0
    root = os.environ.get("CLAUDE_PROJECT_DIR") or os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    why = check(data, os.path.normpath(root))
    if why:
        print(f"Blocked by .claude/hooks/subagent_guard.py: {why}.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
