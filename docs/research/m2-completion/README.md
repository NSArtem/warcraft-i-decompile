# Warcraft I M2 Completion — Blocker Analysis & Reconstruction Strategy

Analytical campaign investigating why the automated M2 reconstruction pipeline
(`wc1.overnight` Wave 2, Wave 3, Wave 4A) exhausted its eligible queues at
**899 / 1010 DONE (89.0%)**, and designing the next-generation strategy to reach
**100% DONE**.

> **Campaign nature:** Read-only architectural & empirical investigation. No
> game source (`src/`), symbol database (`analysis/symbols/*.toml`), or
> verification gate was modified.

## Verified Baseline (`d46f891`)

All figures below are **VERIFIED** directly from `nix develop -c python3 -m wc1.progress`
and `nix develop -c python3 -m wc1.m2_inventory --summary` at commit `d46f891`
(branch `analysis/m2-completion-blockers`, identical tree to `main` at `d46f891`):

| Metric | Value | Notes |
|---|---:|---|
| Git HEAD | `d46f891` | Clean working tree before analytical artifacts |
| Discovered functions (`wc1.analysis`) | 1,710 | 700 out of scope (506 Watcom runtime, 156 Miles AIL, 38 hand-written asm) |
| **In-scope functions** | **1,010** | game 882, runtime 90 (6 unclassified), gfx 27, resource 11 |
| Semantic name (`>= medium`) | 914 (90.5%) | 96 not semantically named |
| C: T3 matched, built from C | 519 (51.4%) | Watcom 10.0a: 518; Open Watcom 2: 1 |
| C: T4 reference C, difftested | 385 (38.1%) | 0 missing `t3_blocker` |
| C: reference C, unchecked (`ref`) | 6 (0.6%) | 1 unwired passing test + 5 xfailed divergences |
| C: no C (`none`) | 100 (9.9%) | Includes 14 already-matched C files without `src =` |
| **DONE** | **899 (89.0%)** | game 777/882, runtime 84/90, gfx 27/27, resource 11/11 |
| **Remaining not-DONE backlog** | **111 (11.0%)** | 105 `game` + 6 `runtime` (`gfx` and `resource` are 100% DONE) |

### Live Queue Exhaustion Snapshot (`d46f891`)

- **Wave 2 (`c-only`) + Wave 3 (`full`)** (`wc1.overnight --dry-run --wave all`):
  - **1 eligible item (4 functions)**: `mod_3df40` (`0x3fe34`, `0x4002a`, `0x40088`, `0x400b4`) — failed 3 consecutive Wave 3 attempts (`20261122_225226_mod_3df40`, `20261125_134900_mod_3df40_f1`, `20261125_192531_mod_3df40_f2`) because these 4 functions are **third-party Miles AIL hand-written assembly** misclassified as `kind = "runtime"`.
  - **27 functions skipped** by `overnight.DEFAULT_SKIP = ("BULLET.C", "STATUS.C", "PLAYFLIC.C")`.
  - **80 functions excluded** as `needs_human` (`existing cross-TOML entry`: 59, `locked TOML`: 7, `name-only`: 5, `unbuildable T3`: 5, `data-in-code`: 2, `T4 incomplete`: 2).
  - Total accounted for: `4 + 27 + 80 = 111`.
- **Wave 4A (`t3-reconcile`)** (`wave4a.discover(refresh_stale=False)`): 31 raw dependency groups (45 unresolved relocs across 17 T4 functions; 8 cached hits, 23 uncached including `owner_5aa90` blocked on `MainMenu`'s pre-function jump table and newly-added T4 units from the recent Wave 2/3 runs).
- **Wave 4B (`t3-recovery`)** (`wave4.discover(exclude_unresolved=True)`): 385 eligible T4 functions total; 368 dependency-clean, 17 routed to Wave 4A. Recent production probe (`2026-11-25`) ran 19 candidates / 37 LLM calls with 0 T3 promotions (1 `UNBUILDABLE`, 1 `FAILED`, 17 `NO_IMPROVEMENT`); 263 of 368 units currently bypass the schema-v2 retry cache solely due to unpopulated `omf_deps`.

## Methodology & Epistemic Standards

1. **Direct live-code extraction**: All backlog classification, wave eligibility, call/data graphs, jump tables, interior references, and codegen styles were extracted directly by running `wc1.analysis`, `wc1.symbols`, `wc1.progress`, `wc1.overnight`, `wc1.batch_driver`, `wc1.build`, `wc1.emit`, `wc1.codegen_survey`, `wc1.t3_audit`, `wc1.wave4a`, and `wc1.wave4`.
2. **Isolated empirical probes**: Hypotheses about buildability, compiler flags (`-5r`), Watcom 10.0a loop-to-`__STOSB` lowering, and NASM/OMF/wlink relocation constraints were tested in ephemeral `/tmp` directories with real `nasm`, `wlink`, and Watcom 10.0a (`wc1.oldcc`).
3. **Epistemic tagging**: Material claims throughout the reports are explicitly tagged:
   - **VERIFIED**: Directly observed in repository state or executed local probe.
   - **DERIVED**: Computed arithmetically or structurally from verified facts.
   - **HYPOTHESIS**: Plausible architectural inference not yet empirically executed end-to-end.
   - **UNKNOWN**: Insufficient evidence to conclude.

## Deliverables & Artifact Schemas

| File | Description |
|---|---|
| [README.md](README.md) | Baseline, methodology, artifact schemas, reproduction guide |
| [blocker-analysis.md](blocker-analysis.md) | Architectural analysis: blocker taxonomy, dependency graph, deterministic mechanisms, wave limits, matched-but-unbuildable deep dive, Wave 4B root-cause study, generalization |
| [roadmap.md](roadmap.md) | Next-generation reconstruction architecture, phased quantitative roadmap to 90%/95%/99%/100% DONE, verification/rollback design, risks & open questions |
| [inventory.json](inventory.json) | Complete machine-readable inventory of all **111** not-DONE functions (reconciled with `wc1.progress`) |
| [inventory.csv](inventory.csv) | Flat tabular export of all 111 not-DONE functions (46 columns) |
| [dependency-groups.json](dependency-groups.json) | 24 prioritized blocker/dependency groups partitioning all 111 functions without overlap |
| `tools/wc1/m2_inventory.py` | Reusable, zero-side-effect read-only inventory & dependency-group extractor |

### `inventory.json` Schema

Top-level keys:
- `meta`: Exact snapshot of `wc1.progress.summarize()` + `git_head` + `reconciled_with_wc1_progress: true`.
- `counts`: Reconciled aggregates by `by_primary_blocker`, `by_secondary_blocker`, `by_blocker_origin`, `by_resolution_phase`, `by_codegen_style`, deterministic vs LLM totals, and `overnight` default queue partition.
- `functions`: Ordered array of **111** objects (one per not-DONE in-scope function, sorted by `addr`), each carrying:
  - **Identity & binary metrics**: `addr`, `addr_hex`, `end_hex`, `limit_hex`, `size_bytes`, `ninsns`, `module`, `kind`, `subsystem`, `codegen_style`.
  - **Symbol & C status**: `name`, `is_placeholder`, `confidence`, `c_status`, `missing`, `conv`, `proto`, `src_file`, `ref_file`, `matched_unbuilt_file`, `verified_by`, `ref_verified_by`, `t3_blocker`, `toml_file`, `toml_ownership_class`, `in_datas_db`, `datas_db_name`.
  - **Graph & structural dependencies**: `caller_count`, `done_caller_count`, `not_done_caller_count`, `callee_count`, `not_done_callee_count`, `data_ptr_ref_count`, `code_ptr_ref_count`, `callers`, `callees`, `not_done_callers`, `not_done_callees`, `data_ref_count`, `named_data_refs`, `unnamed_data_ref_count`, `src_placeholder_ref_count`, `test_placeholder_ref_count`, `interior_ref_in_count`, `outgoing_cross_count`, `has_pre_function_jump_table`, `jump_tables`.
  - **Wave eligibility**: `wave2_eligible`, `wave3_eligible`, `wave4a_eligible`, `wave4b_eligible`, `wave2_exclusion_reason`, `wave3_exclusion_reason`, `wave4a_exclusion_reason`, `wave4b_exclusion_reason`, `overnight_default_status`, `overnight_noskip_status`.
  - **Blocker & resolution mapping**: `primary_blocker`, `secondary_blockers`, `blocker_origin`, `blocker_evidence`, `unlocked_by`, `dependency_group`, `resolution_phase`, `resolution_strategy`, `deterministic_unlock`, `requires_llm`.

### `dependency-groups.json` Schema

Top-level keys:
- `meta`: `git_head`, `not_done_total` (111), `group_count` (24), `sum_group_functions` (111).
- `groups`: Priority-ordered array of 24 group objects (`group_id`, `priority`, `title`, `function_count`, `total_insns`, `avg_insns`, `modules`, `toml_files`, `addresses`, `names`, `deterministic_unlock_count`, `requires_llm_count`, `total_src_placeholder_refs`, `shared_blocker`, `mechanism`, `estimated_t3_unlocks_beyond_m2`, `risk`).

## Reproducing the Inventory

All commands run inside the Nix dev shell (`nix develop -c ...`) and are strictly read-only:

```sh
# 1. Verify live progress counts
nix develop -c python3 -m wc1.progress --todo 200

# 2. Verify live Wave 2 / Wave 3 overnight queue & needs_human partition
nix develop -c python3 -m wc1.overnight --dry-run --wave all

# 3. Regenerate inventory.json, inventory.csv, and dependency-groups.json
nix develop -c python3 -m wc1.m2_inventory --out-dir docs/research/m2-completion --summary
```
