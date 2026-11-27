# Consilium handoff — PAUSED_AWAITING_OWNER

**Blocker:** At the Round 1 preflight, OpenCode2 2.4.1 accepted
`opencode-go/deepseek-v4.1-flash` but the provider rejected the request:
**OpenCode Go monthly usage limit reached**, with a reset estimate of **13d 11h**
at observation. No model response was produced. No fallback, extra usage,
account switch, or automatic reset/resume was used. The administrative OpenCode
session that prepared and froze Round 0 was `openai/gpt-6.2-sol`, not DeepSeek;
the role labels in the original charter and prompts are not model telemetry.
See `participants.json` for the correction and the provider event's log hashes.
No Secretary architectural position or approval was recorded.

## Durable checkpoint

- Branch: `research/build-codegen-consilium`; Secretary worktree:
  `/mnt/data/projects/warcraft-1-decompile-wt/cons-sec`.
- Experimental baseline: `e6150b856106ae113bb023300b956fff318da7ef`; production
  baseline: `a21772b8140b4b07012cde8da7da18ad3f6d56b6`. Neither has changed.
- Round 0: closed. The three exact responses, delivered prompts, hash records,
  and session metadata are in [`rounds/r00/`](rounds/r00/). The response commits
  are `2cc3aa7` (GPT), `827c7b4` (Claude), and `7816ad6` (Gemini).
- [`decisions.json`](decisions.json) and [`objections.json`](objections.json)
  index 41 structured proposals and 29 objections. Exact propositions and
  supporting evidence remain in the ledger and original responses. No decision
  is unanimous. No round of cross-review or RFC drafting has occurred.
- Next round: **r01, cross-review**. Pending delivery: each Architect receives
  the other two complete opening positions and the same
  [EV-2 notice](evidence-revisions/EV-2.json). Nothing from Round 1 has been
  delivered. No end-of-campaign assessment was solicited while the required
  Secretary configuration was unavailable; the original positions are the latest.
- Raw logs and disposable probes remain outside Git under
  `/mnt/data/projects/warcraft-1-decompile-consilium/` and the Architect
  worktrees. None of the Round 0 probes has been accepted by the consilium.

| Architect | Worktree under `/mnt/data/projects/warcraft-1-decompile-wt/` | Native session ID |
|---|---|---|
| GPT | `cons-a` | `01a21b18-3f30-7111-a0a7-0aefa369a288` |
| Claude | `cons-b` | `13aab0ab-0931-4926-815e-bfba7f5aa256` |
| Gemini | `cons-c` | `56960ce2-155d-4fff-b3f0-4444e1f86949` |

## Resource checkpoint

Latest recorded aggregate snapshots after Round 0: Codex 19% (5h), 22% (7d);
Claude 61% (5h), 14% (7d); AGY percentage unavailable. These are shared
provider measurements, not consilium-attributable percentages or current
balances. Provider-specific token and wall-time records are under
[`telemetry/`](telemetry/). Prior smoke calls and any concurrent external usage
must not be attributed to the Architect sessions.

## Resume

1. Wait for the owner's authorization to continue, and verify the required
   Secretary configuration or record the owner's explicit replacement
   authorization. Take fresh provider snapshots. Reconcile any reset with the
   prior authorized allocations; do not treat a refreshed window as newly
   authorized spend. Pause if any Architect cannot participate.
2. In the Secretary worktree, check `state.json` and
   `rounds/r00/manifest.json`; verify each `response.md` against its frozen
   SHA-256. Do **not** relaunch Round 0. Use
   `rounds/r01/prompt-template.md`, the same EV-2 notice for all three, and
   the proposition revision/hash index from `decisions.json`.
3. Deliver each pair of opening positions as two separate, byte-identical files
   in that Architect's own inbox, with hashes and byte lengths in the prompt.
   Require full reads (split reads as needed, without dropping bytes). Do not
   put complete cross-review payloads on the command line: the combined inputs
   can exceed the OS single-argument limit. The existing `launch-files` path
   should only receive the short inbox-index prompts, not embedded payloads.
   Keep current-round outputs out of peer inboxes. Check the native resume
   command and final-event checks for each harness before a substantive call.
4. Resume Codex with `codex exec resume <thread-id> -` and explicit
   `gpt-6.2-sol` / `high`; Claude with `claude -p --resume <uuid>` and explicit
   `claude-opus-5-5` / `high`; AGY with `agy --conversation <id> ... -p
   <inbox-index>` and explicit `gemini-4-neon-high`. Start all three before
   releasing any new responses. Record each invocation, verify model metadata
   and quota, preserve each original response, and only close the barrier once
   every required completed response has been validated.

The primary checkout and `main` are not targets for any resume operation.
