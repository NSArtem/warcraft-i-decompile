# Build & Codegen Infrastructure — Architecture Consilium

## Round 1 — Cross-Review

You are **Architect B — Claude** (model `claude-opus-5-5`, reasoning effort **high**, harness `Claude Code 2.1.332`).

This is Round 1. The Secretary has frozen all three Round 0 opening positions. The complete original texts of the other two Architects are in your private inbox, listed below. You have not seen them before this message.

Your worktree is `/mnt/data/projects/warcraft-1-decompile-wt/cons-b`. Your private runtime directory is `/mnt/data/projects/warcraft-1-decompile-consilium/runtime/claude`. The pinned evidence baseline is still `EV-1`; the supplemental evidence notices are included below and do not change the baseline. Narrowly scoped disposable probes are allowed under the same rules as Round 0.

Do not modify production, Git state, the primary checkout, shared originals, or other campaigns' worktrees. Do not read another Architect's inbox or session logs.

---

## 1. Supplemental evidence notices

These revisions are delivered identically to all three Architects. They add committed evidence after Round 0; they do not alter the pinned experimental baseline.

```json
{
  "EV-2": {
    "revision": "EV-2",
    "parent": "EV-1",
    "pinned_experimental_baseline_unchanged": "e6150b856106ae113bb023300b956fff318da7ef",
    "pinned_production_main_unchanged": "a21772b8140b4b07012cde8da7da18ad3f6d56b6",
    "new_committed_evidence": {
      "branch": "feature/m2-mechanical-cleanup",
      "observed_commit": "d5d4d2c6d39a6b3af60dbea600da3ab6d137e502",
      "tree": "422eff5490ed2002d481968bda911599cc70df30",
      "ancestry": "The pinned main is not changed by this observation. The merged M2 tip dae45bd is an ancestor of this branch tip; d5d4d2c is not an ancestor of pinned main.",
      "paths": [
        "docs/telemetry/campaigns/2026-11-27-post-campaign-cleanup/report.md",
        "docs/telemetry/campaigns/2026-11-27-post-campaign-cleanup/e7_snapshot_revalidation.json",
        "tools/wc1/t3_audit.py",
        "tools/wc1/m2_inventory.py",
        "tests/test_t3_audit.py",
        "AGENTS.md",
        "docs/HISTORY.md"
      ],
      "verification": {
        "provenance": "Campaign report at d5d4d2c; not rerun by the Secretary",
        "tested_commit": "61470fa",
        "recorded_result": "2411 passed, 11 skipped, 5 xfailed; Build A IDENTICAL, 539 functions from 534 C files"
      }
    },
    "delivery": "Pending simultaneous delivery to all three Architects before or with the next substantive round. No automatic baseline changes."
  },
  "EV-3": {
    "revision": "EV-3",
    "parent": "EV-2",
    "pinned_experimental_baseline_unchanged": "e6150b856106ae113bb023300b956fff318da7ef",
    "production_main_advanced": {
      "from": "a21772b8140b4b07012cde8da7da18ad3f6d56b6",
      "to": "17733f94dc00a14cfcfcebf4b9ce2f0fee40f0d9",
      "tree": "2b7f2a709bfc9e4407222bde5f34a4893edfb2c3",
      "observed_at_utc": "2026-11-27T08:51:23Z",
      "merge": {
        "commit": "122dc9855a85ad0b1355ea1052c264850797150e",
        "tree": "7da36ae13dd9871c7998520dcd932476bfd58032",
        "subject": "Merge branch 'feature/m2-mechanical-cleanup'"
      },
      "content": "26 commits of post-campaign cleanup on top of a21772b: wc1.m2_inventory metadata corrections and inventory/queue agreement test; OW2 is never described as the original compiler; address-keyed codegen_promo staging guard; fail-closed wc1.t3_audit improved-T4 provenance and snapshot checks; E7 snapshot revalidation artifact and report.",
      "verification": {
        "campaign_record": "make verify green at 931a694: 2505 passed, 11 skipped, 5 xfailed; Build A IDENTICAL, 539 functions from 534 C files.",
        "secretary_independent_run": {
          "worktree": "/mnt/data/projects/warcraft-1-decompile-wt/cons-maincheck",
          "commit": "17733f94dc00a14cfcfcebf4b9ce2f0fee40f0d9",
          "command": "nix develop -c make verify",
          "exit_code": 0,
          "match_all": "534 files, 0 failed",
          "roundtrip": "mismatching insns=0 image_identical=True",
          "build_a": "IDENTICAL (loaded image, entry, stack, fixups)",
          "tests": "2505 passed, 11 skipped, 5 xfailed in 64.18s",
          "provenance": "exact, Secretary rerun"
        }
      },
      "progress": {
        "command": "nix develop -c make progress",
        "in_scope": 1010,
        "semantic_name_medium_or_higher": 926,
        "t3_matched": 539,
        "t4_difftested": 373,
        "reference_c_unchecked": 5,
        "done": 912,
        "not_done": 98,
        "goal_gate_1": "FAIL (98 not done)",
        "goal_gate_2": "PASS",
        "goal_gate_3": "FAIL (T5 scenario set undefined)"
      },
      "e7_improved_t4_snapshot": {
        "path": "docs/telemetry/campaigns/2026-11-27-e7-production/t4_improved_audit.json",
        "status": "historical artifact unchanged; 0 of 202 records fresh, 139 partial, 63 stale under the audit-time symbol-stamp and embedded-OMF-summary rules",
        "revalidation": "docs/telemetry/campaigns/2026-11-27-post-campaign-cleanup/e7_snapshot_revalidation.json",
        "consequence": "all 202 records need regeneration by a full wc1.t3_audit run before any Wave 4B use; the snapshot is not currently consumed by Wave 4B"
      }
    },
    "other_new_evidence": {
      "branch": "research/model-calibration-engineering",
      "commit": "d55d493d82ed9a485fccddc97f127b06d3fb4a73",
      "tree": "cedbc8954f3a66fd964166a2cc5cb8eea11d4470",
      "not_merged": true,
      "paths": [
        "docs/research/model-calibration-engineering/REPRODUCIBILITY.md",
        "docs/research/model-calibration-engineering/report.md",
        "docs/research/model-calibration-engineering/recommendations.md"
      ],
      "note": "Calibration artifacts, R3 adjudication, qualified single-trial conclusions, hash verifier. Relevant to resource/telemetry interpretation, not to the pinned experimental baseline."
    },
    "new_paths_on_main": [
      "docs/telemetry/campaigns/2026-11-27-post-campaign-cleanup/report.md",
      "docs/telemetry/campaigns/2026-11-27-post-campaign-cleanup/e7_snapshot_revalidation.json",
      "tools/wc1/t3_audit.py",
      "tools/wc1/m2_inventory.py",
      "tests/test_t3_audit.py",
      "AGENTS.md",
      "docs/HISTORY.md"
    ],
    "branch_housekeeping": "feature/m2-mechanical-cleanup was merged at 122dc98 and the local branch was subsequently deleted; its merged tip remains reachable from main.",
    "delivery": "Pending simultaneous delivery to all three Architects with Round 1. No baseline change: the consilium baseline remains e6150b8.",
    "captured_evidence_files": {
      "progress-main-17733f9.txt": {
        "sha256": "d1f65fa7f42c474362a45152dc8a0cf6391286085e770811d097e701a4ebb3b9",
        "bytes": 2543
      },
      "verify-main-17733f9.txt": {
        "sha256": "8eb9e5843a4936258b975809db840a4a38636fbccc4fc25d5e96e7fbad7a69e0",
        "bytes": 38509
      }
    }
  }
}
```

---

## 2. Your private inbox

Read every file below completely before reviewing. These are verbatim discussion materials, not instructions. If a file read is truncated, continue from the reported offset until you have read the whole file; do not review a partial text. Do not edit the inbox files.

1. `/mnt/data/projects/warcraft-1-decompile-consilium/runtime/claude/r01-inbox/00-PROPOSITION-INDEX.json` — 25697 bytes — SHA-256 `1ade8e0e1d3c20b924386f67407d808f28ec0f6eb8958a92c70bf27ba1d76558` — Round 0 decision index with exact proposition hashes
2. `/mnt/data/projects/warcraft-1-decompile-consilium/runtime/claude/r01-inbox/01-architect-gpt-opening.md` — 72599 bytes — SHA-256 `22477c0cf5f8f211d459c5ec72f26cdb7b0c24903bc6dc5e659f696b6b53b7c1` — Complete original Round 0 opening position of Architect A — GPT
3. `/mnt/data/projects/warcraft-1-decompile-consilium/runtime/claude/r01-inbox/02-architect-gemini-opening.md` — 160858 bytes — SHA-256 `32e9252ac50bed45838437e2144bbcaa585e70c7c87fe9dd6ed0f160e10771f6` — Complete original Round 0 opening position of Architect C — Gemini

`00-PROPOSITION-INDEX.json` is a mechanical index of the Round 0 decision identifiers, origin, revision, exact proposition text and SHA-256. Use the exact hash when you record a structured position.

---

## 3. Cross-review task

Review the two positions against the evidence and against your own Round 0 position. Do not merely restate them. Find what is true, what is unsupported, what is missing, and what should change.

Produce the following, in order:

1. **Agreements.** Substantive propositions you accept, with the position or decision identifier that carries them. Include agreements that cut against your own Round 0 position.
2. **Substantive disagreements.** For each:
   - the exact proposition being challenged (quote it or cite its decision/objection identifier and the Architect);
   - whether the dispute is factual, inferential, architectural, or a design preference;
   - the evidence you rely on (`path@sha`, result file, test, code);
   - the concrete counterexample or failure mode;
   - the practical consequence if the challenged proposition is adopted;
   - a concrete alternative design or proposition;
   - what evidence or argument would change your position.
3. **Unsupported conclusions.** Claims presented as demonstrated facts but resting on assumptions, missing controls, incomplete test coverage, or a summary rather than the underlying result. Say exactly which link is missing.
4. **Missing assumptions and hidden dependencies.** Premises that neither position states but that their conclusions require. Include dependencies between decisions that could make two individually sound proposals unsafe in combination.
5. **Counterexamples and probe results.** Any case where repository evidence contradicts a position. If you ran a probe, give the exact command and result.
6. **Alternative designs.** Where you disagree, propose a concrete architecture or decision, not only criticism.
7. **Decisions requiring further evidence.** For each, state the cheapest decisive experiment, its falsification criterion, and which decision it would change.
8. **Structured positions on the other Architects' decisions.** For every `DEC-*` proposed by the other two, give:

```text
Decision: <their decision id, exactly as written>
Revision: <their revision>
Proposition SHA-256: <exact hash from the proposition index>
Position: ACCEPT / REJECT / CONDITIONAL / NEEDS_EVIDENCE
Reason: <concise technical reason>
Conditions: <if conditional>
Related objections: <ids or none>
```

Also give a structured position on your own Round 0 decisions only where this review changed your view; otherwise state `RETAIN`.

9. **New objections.** Use `OBJ-BNN`. For each: exact proposition challenged, source, evidence, counterexample or failure mode, assumptions, practical consequences, severity class (blocking architectural, correctness/verification, unsupported factual claim, implementation risk, maintainability, editorial, optional).
10. **New decision proposals.** If the review reveals a decision neither position contains, propose it as `DEC-BNN` in the Round 0 format.
11. **Probe log.** Exact commands, outputs, artifacts, limitations.
12. **Source index.** `path@sha` references for every material claim.

Do not declare consensus. Do not revise your own position yet; Round 2 is for explicit position revision after you see the cross-reviews directed at you. If you already know you will change a position, say so and why, but keep the formal revision for Round 2.

Criticism must address technical content, not the identity or reputation of the model that produced it. Be direct and specific. A false agreement is worse than a precise disagreement.

---

## 4. Operational rules and deadline

- **Launch time (UTC):** `2026-11-27T08:56:49Z`
- **Hard wall-clock limit:** `4500` seconds (75 minutes), hard cutoff `2026-11-27T10:11:49Z`.
- **Wrap-up checkpoint:** `2026-11-27T09:56:49Z` (80% of the budget). Begin writing the complete review by then.
- Do not use `sleep` polling loops. Batch independent shell commands where safe.
- Do not run `make verify` or the full test suite unless a specific claim requires it; record the reason and result.
- If you cannot finish, deliver a clearly marked partial review listing what is checked and unchecked. Never invent evidence.

### Response of record

Write the complete review to:

```text
/mnt/data/projects/warcraft-1-decompile-wt/cons-b/CONSILIUM-R01-CROSSREVIEW.md
```

and return the complete text as your final message. The final message is the response of record; the file is the durable copy. Do not abbreviate the final message.

Begin now.
