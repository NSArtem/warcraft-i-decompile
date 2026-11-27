# Consilium Orchestrator

Deterministic delivery and telemetry for the three Architect sessions.

## Invocation

```bash
python3 docs/research/build-codegen-consilium/orchestrator/run_architect.py \
  launch --round r00 \
  --template docs/research/build-codegen-consilium/rounds/r00/prompt-template.md \
  --timeout 5400
```

`launch` renders one prompt per Architect from the template (substituting the
architect identity, worktree, runtime directory, timestamps and the pinned
evidence manifest), writes the exact delivered prompt under `rounds/<round>/`,
and launches all three sessions concurrently with a hard wall-clock bound.

`freeze` verifies that all three responses exist, hashes them, writes the round
manifest, and updates `state.json` and `telemetry/sessions.jsonl`:

```bash
python3 .../run_architect.py freeze --round r00
```

## Session semantics

- Codex: `codex exec` first, `codex exec resume <thread-id>` afterwards.
- Claude: `claude -p --session-id <uuid>` first, `claude -p --resume <uuid>` afterwards.
- AGY: `agy ... -p <prompt>` first, `agy --conversation <id> ... -p <prompt>` afterwards.

Native session IDs are stored in `/mnt/data/projects/warcraft-1-decompile-consilium/sessions/`
and in `participants.json` / `state.json`.

## Raw logs

Raw stdout/stderr and rollout references are stored under
`/mnt/data/projects/warcraft-1-decompile-consilium/logs/<round>/`. Tracked
telemetry records their SHA-256 hashes. Credentials are never read or copied.

## Failure handling

A completed final message is the response of record even if the CLI process has
not exited. On timeout the whole process group is terminated; partial output is
preserved and the response status is `TIMED_OUT`. An empty response blocks the
round barrier and is reported, never fabricated.
