"""The PreToolUse subagent guard (.claude/hooks/subagent_guard.py)."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / ".claude" / "hooks" / "subagent_guard.py"
SUB = {"agent_id": "a1", "agent_type": "wc1-analyst"}


def run(tool, tool_input, sub=True):
    data = {"hook_event_name": "PreToolUse", "cwd": str(ROOT),
            "tool_name": tool, "tool_input": tool_input}
    if sub:
        data.update(SUB)
    p = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(data),
                       capture_output=True, text=True,
                       env={"CLAUDE_PROJECT_DIR": str(ROOT)})
    return p.returncode, p.stderr


@pytest.mark.parametrize("cmd", [
    "git commit -m x",
    "cd /x && git -C . commit -am x",
    "git push",
    "make build",
    "nix develop -c make build",
    "make -j4 roundtrip",
    "nix develop -c make roundtrip 2>&1 | tail",
])
def test_blocks_subagent_commands(cmd):
    code, err = run("Bash", {"command": cmd})
    assert code == 2 and "subagent_guard" in err


@pytest.mark.parametrize("cmd", [
    "git status", "git log --oneline -5", "git diff HEAD",
    "make test", "make symbols", "python3 -m wc1.match src/x.c",
    "ls build/roundtrip", "cat build/foo.txt", "make progress",
])
def test_allows_subagent_commands(cmd):
    assert run("Bash", {"command": cmd})[0] == 0


@pytest.mark.parametrize("path", [
    "Makefile", "flake.nix", "flake.lock", "asm/wc1.inc",
    "src/include/war.h", ".claude/settings.json",
    ".claude/hooks/subagent_guard.py", ".opencode/agents/wc1-analyst.md",
])
def test_blocks_shared_file_edits(path):
    for p in (path, str(ROOT / path)):
        assert run("Edit", {"file_path": p})[0] == 2
        assert run("Write", {"file_path": p})[0] == 2


@pytest.mark.parametrize("path", [
    "analysis/symbols/foo.toml", "src/foo/bar.c", "src/include/foo.h",
    "tests/test_foo.py", "docs/subsystems/foo.md", "/tmp/scratch.txt",
])
def test_allows_area_file_edits(path):
    assert run("Write", {"file_path": path})[0] == 0


def test_blocks_nested_subagents():
    assert run("Agent", {"prompt": "x", "subagent_type": "wc1-mechanical"})[0] == 2


def test_main_agent_untouched():
    assert run("Bash", {"command": "git commit -m x"}, sub=False)[0] == 0
    assert run("Bash", {"command": "make build"}, sub=False)[0] == 0
    assert run("Edit", {"file_path": "Makefile"}, sub=False)[0] == 0
    assert run("Agent", {"prompt": "x"}, sub=False)[0] == 0


def test_settings_register_the_hook():
    s = json.loads((ROOT / ".claude" / "settings.json").read_text())
    cmds = [h["command"] for e in s["hooks"]["PreToolUse"] for h in e["hooks"]]
    assert any("subagent_guard.py" in c for c in cmds)
