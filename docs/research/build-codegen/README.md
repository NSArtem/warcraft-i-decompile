# Build & Codegen Infrastructure — Experimental Research Campaign (E0–E8)

- **Campaign branch:** `research/build-codegen-experiments`
- **RFC baseline:** `architecture/build-codegen-rfc` (`6f319ac8ff780bb45ff028d006216016fc932a13`)
- **Production baseline (`main`):** `e14d5c0a5d37d2f85ffcfcc311008004bb5c40da`
- **Campaign status:** **COMPLETE** — **9 of 9 experiments (`E0`–`E8`) independently `APPROVE`d and integrated (`--no-ff`)**, **0 production diffs**, **401/401 experimental + infra tests passing**, and serialized global **`make verify` green** (`2257 passed, 11 skipped, 5 xfailed`, Build A `IDENTICAL`).

## Core Reports
- [**Consolidated Final Research Report (`summary.md`)**](summary.md) — full technical synthesis (§§18.1–18.10).
- [**RFC Architectural Decision Register (`decisions.md`)**](decisions.md) — decision-by-decision verdicts, refuted premises, and production-hardening prerequisites.
- [**Campaign Ledger (`ledger.json`)**](ledger.json) — machine-readable experiment state, commit provenance, and session inventory.
- [**Orchestration Telemetry Report (`../telemetry/campaigns/2026-11-25-build-codegen/report.md`)**](../telemetry/campaigns/2026-11-25-build-codegen/report.md) — exact token, wall-time, quota, and review-loop telemetry across 38 sessions.

## Experiment Index

| ID | Topic | Outcome | Merge Commit | Tests | Report | Machine Results | Contract |
|---|---|---|---|---:|---|---|---|
| **E0** | Matcher Soundness & 519-T3 Re-Audit | `CONFIRMED` | `7c23d23` | 77 pass | [E0-matcher-soundness.md](E0-matcher-soundness.md) | [results/e0/](results/e0/) | [E0](contracts/E0-contract.md) |
| **E1** | Shared Epilogue Reproduction | `CONFIRMED` | `b2965ba` | 18 pass | [E1-shared-epilogues.md](E1-shared-epilogues.md) | [results/e1/](results/e1/) | [E1](contracts/E1-contract.md) |
| **E2** | Compilation-Context Sensitivity & Alignment | `PARTIALLY_CONFIRMED` | `c30f3f5` | 27 pass | [E2-compilation-context.md](E2-compilation-context.md) | [results/e2/](results/e2/) | [E2](contracts/E2-contract.md) |
| **E3** | Partial Object Matching | `PARTIALLY_CONFIRMED` | `13963fb` | 24 pass | [E3-partial-matching.md](E3-partial-matching.md) | [results/e3/](results/e3/) | [E3](contracts/E3-contract.md) |
| **E4** | Selective OMF32 Extraction Feasibility | `CONFIRMED` | `7edf63b` | 17 pass | [E4-omf-extraction.md](E4-omf-extraction.md) | [results/e4/](results/e4/) | [E4](contracts/E4-contract.md) |
| **E5** | Data-Anchor Decoupling (Fix B3) | `CONFIRMED` | `ed21ca3` | 86 pass | [E5-data-anchors.md](E5-data-anchors.md) | [results/e5/](results/e5/) | [E5](contracts/E5-contract.md) |
| **E6** | Multi-Function T4 Verification (`wc1.cemu`) | `PARTIALLY_CONFIRMED` | `bb3387b` | 96 pass | [E6-multifunction-t4.md](E6-multifunction-t4.md) | [results/e6/](results/e6/) | [E6](contracts/E6-contract.md) |
| **E7** | Original Compiler Calibration (Watcom 10.0a) | `CONFIRMED` | `c946f38` | 20 pass | [E7-compiler-calibration.md](E7-compiler-calibration.md) | [results/e7/](results/e7/) | [E7](contracts/E7-contract.md) |
| **E8** | Original CU Boundary Evidence Validation | `PARTIALLY_CONFIRMED` | `9ae6dce` | 30 pass | [E8-cu-boundaries.md](E8-cu-boundaries.md) | [results/e8/](results/e8/) | [E8](contracts/E8-contract.md) |

## Quick Reproduction

Run from the repository root on branch `research/build-codegen-experiments` inside the Nix dev shell with a short `TMPDIR` (avoiding Watcom 10.0a's ~129-char path-length bug):

```sh
nix develop .#ci -c bash -c '
  export TMPDIR=/tmp/wc1-repro
  mkdir -p "$TMPDIR"
  for s in _infra/test_infra.py e0/test_e0.py e1/test_e1.py e2/test_e2.py e3/test_e3.py e4/test_e4.py e5/test_e5.py e6/test_e6.py e7/test_e7.py e8/test_e8.py; do
    python3 -m pytest -q "experiments/build_codegen/$s"
  done
  make verify
'
```
