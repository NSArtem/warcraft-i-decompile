@AGENTS.md

## Claude Code

Project guidance lives in `AGENTS.md` (imported above); keep Claude-specific
notes here, below the import.

The `wc1-mechanical` / `wc1-analyst` subagent definitions for Claude Code are
in `.claude/agents/` (pass `subagent_type` explicitly).

### Claude Pro budget rules

- **No repo-wide `/goal`.** Gate 3 is undefined and requires user approval, so
  a repo-wide `/goal` never terminates. Scope any `/goal` to a single atomic
  module (e.g. finish one area, verify, commit, stop).
- **Max 1 concurrent subagent** (enforced by `.claude/hooks/subagent_guard.py`).
  For single-module work, prefer running directly in a fresh `/clear` Sonnet
  session or through `wc1.batch_driver` rather than paying an Opus coordinator.
- **2-retry T3 cutoff.** After initial C + local `wc1.permuter` + at most 2
  diff-guided edits (`wc1.match --diff`), stop chasing T3, record the exact
  first-difference instruction in `t3_blocker`, and move to T4.
- **Use shared tools.** Use `wc1.dossier`, `wc1.match --diff`, `wc1.permuter`,
  and `wc1.t4spec` instead of writing per-area `*_dis.py` / `*_match.py` copies.
