#!/usr/bin/env python3
"""Generate the administrative hand-off / resume document.

It contains only measured state: rounds, hashes, session IDs, worktrees, quota,
ledger counts and the exact next action. Architectural narrative belongs in the
Architects' own responses, not here.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess

SEC = "/mnt/data/projects/warcraft-1-decompile-wt/cons-sec"
CONSILIUM = os.path.join(SEC, "docs/research/build-codegen-consilium")
STATE_ROOT = "/mnt/data/projects/warcraft-1-decompile-consilium"


def load(path, default=None):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", required=True)
    ap.add_argument("--note", default="")
    args = ap.parse_args()
    state = load(os.path.join(CONSILIUM, "state.json"), {}) or {}
    dec = load(os.path.join(CONSILIUM, "decisions.json"), {}) or {}
    obj = load(os.path.join(CONSILIUM, "objections.json"), {}) or {}
    parts = load(os.path.join(CONSILIUM, "participants.json"), {}) or {}

    lines = []
    lines.append("# Consilium Hand-off")
    lines.append("")
    lines.append(f"- **Status:** `{args.status}`")
    lines.append(f"- **Generated at (UTC):** `{__import__('datetime').datetime.utcnow().isoformat()}Z`")
    lines.append(f"- **Phase:** `{state.get('phase')}`")
    lines.append(f"- **Baseline:** `research/build-codegen-experiments` @ `{state.get('baseline', {}).get('sha')}`")
    lines.append(f"- **Consilium branch:** `research/build-codegen-consilium`")
    lines.append(f"- **Evidence revision:** `{state.get('current_evidence_revision')}`")
    lines.append(f"- **Next round:** `{state.get('next_round')}`")
    if args.note:
        lines.append(f"- **Note:** {args.note}")
    lines.append("")
    lines.append("## Worktrees")
    for k, v in (state.get("worktrees") or {}).items():
        lines.append(f"- `{k}`: `{v}`")
    lines.append("")
    lines.append("## Sessions")
    for arch in ("gpt", "claude", "gemini"):
        s = load(os.path.join(STATE_ROOT, "sessions", f"{arch}.json"), {}) or {}
        lines.append(f"- `{arch}`: native id `{s.get('native_session_id')}`, "
                     f"invocations `{s.get('invocations')}`")
    lines.append("")
    lines.append("## Rounds")
    for rid in sorted((state.get("rounds") or {})):
        r = state["rounds"][rid]
        lines.append(f"- `{rid}`: status `{r.get('status')}`, barrier `{r.get('barrier')}`")
        for arch in ("gpt", "claude", "gemini"):
            h = ((r.get("responses") or {}).get(arch) or {}).get("sha256")
            lines.append(f"  - `{arch}`: `{h}`")
    lines.append("")
    ds = dec.get("decisions", [])
    by = {}
    for d in ds:
        by[d.get("status")] = by.get(d.get("status"), 0) + 1
    lines.append(f"## Ledger")
    lines.append(f"- Decisions: `{len(ds)}` {by}")
    lines.append(f"- Objections: `{len(obj.get('objections', []))}`")
    lines.append("")
    lines.append("## Resource snapshots")
    qpath = os.path.join(CONSILIUM, "telemetry", "quota-snapshots.jsonl")
    if os.path.isfile(qpath):
        for line in open(qpath, encoding="utf-8").read().strip().splitlines()[-6:]:
            q = json.loads(line)
            lines.append(f"- `{q.get('round')}/{q.get('architect') or q.get('provider')}`: {q.get('quota')}")
    else:
        lines.append("- No quota snapshots recorded yet.")
    lines.append("")
    lines.append("## Blockers")
    for b in state.get("blockers", []):
        lines.append(f"- `{json.dumps(b)}`")
    if not state.get("blockers"):
        lines.append("- None recorded.")
    lines.append("")
    lines.append("## Pending messages")
    for m in state.get("pending_messages", []):
        lines.append(f"- `{json.dumps(m)}`")
    if not state.get("pending_messages"):
        lines.append("- None.")
    lines.append("")
    lines.append("## Recent commits")
    try:
        out = subprocess.check_output(["git", "log", "--oneline", "-12"], cwd=SEC, text=True)
        lines.append("```text")
        lines.append(out.strip())
        lines.append("```")
    except subprocess.CalledProcessError:
        lines.append("(git log unavailable)")
    lines.append("")
    lines.append("## Exact resume procedure")
    lines.append("1. Read `state.json`, the latest `rounds/<round>/manifest.json`, `decisions.json`, `objections.json`.")
    lines.append("2. Inspect raw logs under `/mnt/data/projects/warcraft-1-decompile-consilium/logs/` and session IDs above.")
    lines.append("3. If the next round is pending: compose it from the frozen previous round, then `launch-files`.")
    lines.append("4. If resuming an interrupted round: check `logs/<round>/` for partial output; a completed final message is the response of record.")
    lines.append("5. Never treat silence or a partial response as agreement.")
    path = os.path.join(CONSILIUM, "handoff.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
