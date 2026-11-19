#!/usr/bin/env python3
"""PreToolUse hook: enforce the subagent rules of AGENTS.md / .claude/agents.

Claude Code passes `agent_id` / `agent_type` in the hook input only for
tool calls made by a subagent; the main agent's calls are never touched.
For subagents it blocks:
  - git commit / git push        (only the session owner commits)
  - make build / make roundtrip  (they write shared build/ files)
  - edits to Makefile, flake.*, asm/**, src/include/war.h, .claude/**,
    .opencode/**               (shared files; the guard itself)
  - spawning further subagents (Agent / Task)
Mirrors the permission denies of .opencode/agents/*.md.  Exit 2 = block,
the stderr text goes back to the subagent.
"""
import json
import os
import re
import sys

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


def check(data, root):
    """Return a block reason, or None to allow."""
    if not data.get("agent_id") and not data.get("agent_type"):
        return None                          # main agent: not ours to police
    tool = data.get("tool_name", "")
    inp = data.get("tool_input") or {}
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
