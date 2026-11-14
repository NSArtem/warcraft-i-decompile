@AGENTS.md

## Claude Code

Project guidance lives in `AGENTS.md` (imported above); keep Claude-specific
notes here, below the import.

Subagents (definitions in `.claude/agents/`):

- `wc1-mechanical` (Haiku 5.5): well-specified mechanical work with
  explicit steps and acceptance criteria (signature sweeps, export tooling,
  bulk checks, tests).
- `wc1-analyst` (Sonnet 5.5): reverse-engineering judgment (subsystems, formats,
  module boundaries, semantic naming, matching C).
- Pass `subagent_type` explicitly. One owner per file/area (see
  ANALYST_GUIDE concurrency rules). Split mixed tasks so the mechanical part
  goes to Haiku.
