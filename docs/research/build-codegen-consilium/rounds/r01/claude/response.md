# Consilium R1 — Cross-Review by Architect B (Claude, `claude-opus-5-5`)

- **Round:** 1 (cross-review of the frozen R0 positions of Architect A, GPT, and Architect C, Gemini)
- **Inputs read in full:**
  - `r01-inbox/00-PROPOSITION-INDEX.json` (sha `1ade8e0e…`)
  - `01-architect-gpt-opening.md` (sha `22477c0c…`, 431 lines)
  - `02-architect-gemini-opening.md` (sha `32e9252a…`, 1063 lines)
- **Evidence:** EV-1 baseline unchanged; EV-2/EV-3 notices taken into account. Production `main` advanced to `17733f9`, and the build/match/emit/cemu/compare/oldcc tools are byte-unchanged from `a21772b`: `git diff --stat a21772b 17733f9 -- tools/wc1/{compare,oldcc,match,build,emit,cemu}.py` is empty.
- **Probes:** new probes this round are R1-P1…R1-P7 (§11). They ran in the same disposable export `/tmp/opencode/cn-claude/m`, which is `a21772b` plus my R0 probe edits, with my private Wine prefix.

---

## 1. Agreements

The three positions converge on more than they diverge. These agreements are substantive, not just similar wording.

1. **M2 is dominated by reconstruction, not infrastructure.** B3, extraction, the full E6 machinery and CU recovery move 0 of the 98 not-done functions. This is carried by A §1/DEC-A01, C §1/DEC-C07 and OBJ-C04, and B DEC-B01. All three independently derived 912/98 on `a21772b`, and EV-3 confirms the same counts on `17733f9`.
2. **IntroOpSyncSound is a cross-retained-piece rel8 failure that the current preflight misses.**
   - A OBJ-A01 and Q2, and C OBJ-C02 with its Probe 1, reach the same mechanism I found in R0 (P2): `0x231d7`/`0x231e1 → 0x2316c`.
   - C additionally found the *entry*-targeting class on MissionDefeat (`0x2f718`/`0x2f722`/`0x2f72e`), which I also found independently in R0 (P5, "B2-c").
   - Three independent derivations of the same three-class B2 taxonomy is strong evidence the taxonomy is right.
3. **One planner for buildability and emission** (C DEC-C05 §4.2 item 6, A DEC-A03, B DEC-B03).
4. **Group B joint TU is the preferred remedy** (A DEC-A05 and roadmap stage 3, C DEC-C06, B DEC-B06).
5. **B1 via a leading-bytes base derived from the public's object offset** (A DEC-A04, C DEC-C05, B DEC-B05). A's requirement to distinguish MainMenu's table at `0x15578` from its entry at `0x15588`, with `owner_5aa90` verified separately, is a correct refinement that I lacked.
6. **E4 out of M2** (A DEC-A07, C DEC-C08, B DEC-B09/B17).
   - C's E4 defect list is real. I confirmed in code that `Threads()` is re-instantiated per FIXUPP record (`experiments/build_codegen/e4/omf_extract.py:258,823@e6150b8`). I also confirmed that the PUBDEF/LPUBDEF filter rebases every segment's publics by the `_TEXT` slice `[lo,hi)` without checking `pseg` (`:798-807`).
   - The E4 report's "THREAD expansion" claim therefore covers intra-record threads only. That point cuts against the campaign's D6.
7. **B3 is a bounded proven subset, deferred, whole-segment first** (A DEC-A06, C DEC-C10's timing, B DEC-B08).
8. **CU recovery is analyst-facing with premise-carrying constraints; no automatic consolidation or splitting** (A DEC-A10, C DEC-C12, B DEC-B13).
9. **The alignment correction** (C DEC-C13's matrix, A §2 E2, B DEC-B10), *excluding* C's "-5r primary default" clause (see §2).
10. **No multi-backend framework** (C DEC-C14, A §9, B §9).
11. **A's comparator gap, against my own R0 position.** In R0 (I-3c, I-6) I treated `wc1.compare` IDENTICAL as a complete check for Build A. That is wrong. `tools/wc1/compare.py@a21772b` (unchanged at `17733f9`):
    - prints object flags (`desc`) but never compares them (`same_layout` is `(base, vsize)` only);
    - compares fixups as `(obj, src_off, target_obj, target_off)` with no fixup type or source kind.

    A's Q3 mutant (OBJ_EXEC cleared, `IDENTICAL` printed) is therefore consistent with the code. I accept OBJ-A02 and will revise DEC-B04's reliance on "IDENTICAL is a complete check" in Round 2.
12. **A's strict-input concern** (OBJ-A03: checksums not attested, FRAME distinctions collapsed in the parsed module). This is relevant before any OMF *transform* (B3/E4). It is less relevant to matching freshly compiled objects, but cheap to add at the matcher boundary.

---

## 2. Substantive disagreements

### D-1. "5 real reference-C bugs" (Architect C §1, §8.0 item 5, DEC-C07; also A §8 "five unchecked reference divergences … repair")

- **Type:** factual.
- **Evidence:** probe R1-P4 (below), extending my R0 P4. I ran the five xfailed divergence tests with **full paired-state restoration**: every mapped Unicorn region is snapshotted before the original call and restored before the C call. Production `run_pair` (`cemu.py:344-391@a21772b`) restores only the `watch` ranges.
- **Result:**

  | Test | Current harness | Full state restore |
  |---|---|---|
  | `test_intro_op_wait_sound` | FAIL `0x801130 30≠0c` | **PASS** |
  | `test_intro_run_script` | FAIL `0x801130 68≠50` | **PASS** |
  | `test_intro_play` | FAIL `0x801130 74≠68` | **PASS** |
  | `test_intro_op_start_credits` | FAIL `0x59eb9 01≠00` | FAIL (same) |
  | `test_end_screen` | FAIL `0x80054c 70≠50` | FAIL (same) |

  These tests ran against the unchanged `src/playflic/player_reference.c` and `src/mod_2efd0/*_reference.c` from `a21772b`.
- **Counterexample.** Three of the "real bugs" are asymmetric-input artefacts of the harness. The reference C for those three is behaviourally correct on the specified cases.
- **Consequence if adopted.** Stage 2 work in C and A rewrites correct C to chase a harness defect, and the defect remains latent for all future T4 tests. It is a soundness issue as well: the C side runs on different inputs than the original.
- **Alternative.** DEC-B07 (paired-state symmetry), strengthened per DEC-B18 below.
- **What would change my view.** A demonstration that full-region restoration masks a real difference, i.e. a mutation to the C that passes with restore and fails without. I see no mechanism for that, because the restore makes inputs identical and leaves outputs unconstrained.

### D-2. Invariant V4 as a Stage 0 prerequisite of the matcher (C DEC-C02 → DEC-C03 → EXP-1; OBJ-C01 "falsely reject almost every multi-string `-ot` CU … flaky")

- **Type:** inferential and architectural, with one factual sub-point.
- **Facts I confirmed:**
  - The original has non-zero pad residue (`war.exe` at `0x56b1c`: `2e6e6574 00 8d75e0 2e736176 00 0800e8 73617665256400 a5`; R1-P3).
  - Watcom 10.0a `-ot` emits non-zero pad bytes between pooled literals (R1-P2).
- **Fact I did not reproduce: consecutive-run non-determinism.** Four consecutive compiles of the same file gave byte-identical CONST, `2e6e6574 00 610074 2e736176 00 570049 …`. Changing only the **source directory name** changed the pad bytes (`200068`, `700029`). The bytes are *environment-dependent* (path or heap state), not a function of the C source. This is weaker than "non-deterministic" but has the same consequence for proof: the pad can never be required to equal the original.
- **Why V4 is not a soundness prerequisite.**
  - Without V4, E0 rejects such objects. That is fail-closed (MISMATCH), not a false MATCH.
  - Production already uses an idiom that avoids local multi-literal CONST entirely: literals as DB-named externs. `src/mod_13f60/save_slot_path.c@a21772b` uses `str_ext_net`, `str_ext_sav` and `fmt_save_d`, and is T3.
  - C itself lists SaveSlotPath as "T3 via extern symbols" (C §5.3 item 2). So "breaks E0 … on real CUs" is a *completeness* limit, relevant only once natural literals or B3 consolidation are pursued.
- **Hidden dependency C omits.** V4 in the matcher is not sufficient. Production `build.place()` (`build.py:94-104@a21772b`) separately compares DATA-class segment contents, including CONST, and raises `Unplaceable` on a difference. A V4-exempt object would still be refused placement unless `place()` uses the same rule.
- **Consequence if adopted as written.** The E0 matcher, which closes real soundness gaps (#3 is uncaught even by Build A), would wait on EXP-1 for no soundness gain.
- **Alternative.**
  - Land E0 now, failing closed on CONST pad.
  - Specify V4 as a later completeness extension applied identically in matcher and placement, with ASM as provider.
  - Separately, require object/CONST digests used for caching to normalize these bytes (consistent with A §3 provenance and E8 `rev-e8-02`).
- **What would change my view.** A remaining not-done M2 function whose T3 *requires* local multi-literal CONST, i.e. where the extern idiom is unavailable or rejected by the owner.

### D-3. "Blocked by atomic cross-module symbol migration" for 61 functions; projected "1002/1010" (C §1, §8.0 item 1, Stage 2, DEC-C07, OBJ-C04)

- **Type:** factual and inferential.
- **Evidence.** `wc1.m2_inventory` on `a21772b` (my R0 P7 output, `inv-main/inventory.json`): all 61 rows have `c_status = "none"`, `missing = ["name","C"]` and `requires_llm = True`, with strategy "reconstruct name+C+T4 in module, atomically migrate TOML entry, and deterministically rename callers".
- **Counterexample.** The binding constraint is reconstruction (name plus C plus a T4 or T3 proof). Renaming is a mechanical sub-step. No dedicated rename tool exists (`git ls-tree 17733f9 tools/wc1` has none), so the tool is a real but secondary need.
- **Consequence.** Framing M2 as unlocked by a migration tool, and projecting 1002/1010 from Stage 2, overstates the deterministic yield. The projection assumes 100% reconstruction success on 78 LLM-dependent functions, which no evidence supports.
- **Alternative.** Keep C's sequencing (which I agree with), but report Stage 2 yield as an upper bound and track measured per-batch outcomes (A's roadmap stage 1 receipts).
- **What would change my view.** Evidence that the 61 already have semantically justified names and C drafts waiting only on renaming. The inventory says otherwise.

### D-4. "-5r as the primary Watcom 10.0a default family" (C DEC-C13) and the "[FACT] war.exe was predominantly compiled with -5r" (C §2.8 fact 1)

- **Type:** factual.
- **Evidence.**
  - E7 itself says the results "justify additive original-compiler search presets, not a claim that every original CU used Pentium options" (`E7-compiler-calibration.md@e6150b8`, "R6 preservation").
  - E7 records `only_4r = 51` T3 functions in the tested grid and `-3r` also spaces at 4 bytes (E2).
  - C's "0/417 … proving `-5r` is strictly safe over `-4r` on every tested `-4r` T3" overgeneralizes. The 417 are the fixed-default `c01` matches, not all `-4r` T3s.
- **Consequence.** A "default" phrasing invites a global flag change or a historical inference that is unsupported.
- **Alternative.** Accept the matrix. Phrase `-5r` as "first-tried preset family for multi-function TUs that must reproduce 4-byte intra-object spacing; no historical-flag claim" (consistent with DEC-B11 and DEC-A09).
- **What would change my view.** Q-B06: an extended grid (5r OD/debug variants) in which all 51 `only_4r` functions also match under 5r.

### D-5. Cross-piece rel32 into a cut interior via synthesized `_loc_<addr>` PUBDEF in the C object (C DEC-C05, §4.2 item 3)

- **Type:** design preference with implementation risk.
- **Evidence.** R0 P5: the rel32 interior branch `0x2f6df` (EndCheckSurvive → MissionDefeat interior) built IDENTICAL using the original displacement with no object transform. Under in-place layout, rel32 has the same fixed-displacement property as rel8.
- **Failure mode of C's design.** It adds an OMF transform (a new public inside compiled output) to the M2 critical path. That expands the post-codegen transform surface, which RFC §6 asks to minimize, and requires the strict parser A demands (OBJ-A03) on the critical path.
- **Alternative.** Treat all cross-object ASM relative branches uniformly with a piece-local expression (A's Q2 form) or literal displacement (my P5), under the same in-place invariants. Keep symbolic EXTDEF only for rel32 to exported entries.
- **What would change my view.** A case where fixed displacement is unavailable but a public at an interior offset is legitimate, for example a non-in-place (Build B) use. That is outside Build A.

### D-6. Multi-function T4 gate wording (C DEC-C11: "hard prerequisite before consolidating any T4 function into a multi-function `.c` file"; "Multi-function T4 without E6 leaks intra-TU sibling calls")

- **Type:** factual and architectural.
- **Evidence.**
  - Production already has large multi-function reference files tested by single-function `cemu`. `src/playflic/player_reference.c@a21772b` holds 20 functions.
  - In those tests, sibling calls run the compiled sibling on the C side and the original sibling on the original side. That is a de-facto Group comparison, not a silent trust leak.
  - The real hazard E6 found is narrower: a declared stub for a sibling is bypassed because of `local_names` precedence.
- **Consequence.** As written, the gate is already violated by the status quo, and it misplaces the risk.
- **Alternative.** Trigger E6 machinery when a test needs to *substitute* an intra-TU sibling, or needs callbacks or pointer identity. Make paired-state symmetry (DEC-B07/B18) a prerequisite for all T4, single- or multi-function.

### D-7. A's Group B pilot gating (A roadmap stage 3: "Run the exact Group B pilot under stage 2's proof path")

- **Type:** sequencing preference.
- **Evidence.** R0 P3: Group B is MATCH under the *current* production matcher and builds IDENTICAL with the *current* planner (542/535), and passes the two-compiler compile check. It needs neither B1 nor the new verifier.
- **Consequence.** Gating it behind stage 2 delays 3 DONE (2 B2 rows plus the IntroOpWaitSound divergence) for no added assurance on these bytes. E0 already MATCHes them (E1 used E0 for the region).
- **Alternative.** Promote Group B as an independent unit now (B roadmap S1). Re-run it under the new verifier at the S2 cutover like every other T3.

---

## 3. Unsupported conclusions

| # | Claim (source) | Missing link |
|---|---|---|
| U-1 | "live Watcom 10.0a … emits **non-deterministic** heap bytes … across consecutive runs" (C OBJ-C01, Probe 7d) | Not reproduced across 4 consecutive runs with fixed inputs (R1-P2); the bytes vary with source path. C's runs may have used different paths. The claim needs fixed-input control runs. |
| U-2 | "157/293 fixup-bounded CONST strings non-zero pad" (C Probe 3) | The method for bounding strings by fixups is not shown; I confirmed one instance (`0x56b1c`), not the count. Not decision-critical. |
| U-3 | "`non_16_aligned_start` — 100% precision as a one-directional merge constraint" (C §2.9, §7.1 Class 2) | E8 measured 0.800 (A), 0.836 (B1) and 0.618 (B1 without `intxa386`). "100% under premise" is a logical argument; the corpora measure premise failures as false positives. It is not a measured fact. |
| U-4 | "E0 `FunctionMatch` has a confirmed bug (Cause B, 9/13)" (C §2.3 fact 3, OBJ-C05) | E2 states that the runner "retains E0's UNSUPPORTED verdict" and that the result is conservative (`E2-compilation-context.md:242-249@e6150b8`). This is a completeness limit with no false MATCH. V2 is a useful refinement but not a soundness fix. |
| U-5 | "[FACT] war.exe predominantly compiled with `-5r`" (C §2.8) | See D-4. |
| U-6 | Stage 2 exit "1,002/1,010 DONE" (C §8 Stage 2) | It assumes every LLM-dependent reconstruction succeeds. It is a target, not a projection. |
| U-7 | "5 real reference-C bugs" (C, A) | Falsified for 3/5 (R1-P4). |
| U-8 | `t3_audit` R3 bugs "on `main`" (C Probe 6, OBJ-C08, DEC-C04) | Valid at `a21772b` per C's probe, but superseded on `17733f9` (EV-3): `_default_system_headers` uses `compiler_root(repo_root)` (`t3_audit.py:160-162@17733f9`); `tool_sig` is checked live (`:1197-1206`); `_git` None is recorded as unknown, "never clean" (`:1786-1790`). Only the `oldcc` part of DEC-C04 remains open. |
| U-9 | "E1 matched `war.exe` bytes identically, which subsumes behavioural parity for `0x231cc`" (C §2.2) | True in substance, but C's own Stage 2 then schedules "fixing" `0x231cc` and treats the PLAYFLIC tests as real failures. The inconsistency stays unresolved within C's text. R1-P4 resolves it. |
| U-10 | Campaign "THREAD expansion" for E4 (summary §18.4; challenged by C) | Confirmed by C and me: per-record `Threads()` (`omf_extract.py:258,823`). The E4 claim holds only for intra-record THREAD. |
| U-11 | A: "a separate probe showed that `wc1.compare` prints IDENTICAL for a change to the code object's execute flag" | Consistent with the code (`compare.py@a21772b`; see §1.11). I did not re-run the mutant. The code-level finding suffices. |

---

## 4. Missing assumptions and hidden dependencies

1. **V4 needs placement too** (D-2). Matcher-only V4 is ineffective because `place()` independently compares CONST bytes.
2. **B2 fixed displacement versus automatic legacy fallback.** `build.main()` silently routes an `Unplaceable` object to legacy layout (`build.py:310-314@a21772b`: `print(f"legacy layout for {src}: {ex}")`). The three positions forbid B2 under `--legacy`, but none notes that legacy can be entered *per object, automatically*. The planner must reject a fixed-displacement branch whose span includes any legacy-placed object, not only the global `--legacy` flag.
3. **B1 combined with B2.** A leading-table region shifts the cut start below the first public. The cross-object branch analysis must use the region's physical start (`table_start`), not the function start. Otherwise a branch into the table area, or spanning it, is misclassified. No position states this combination test.
4. **Comparator strength combined with B2.** All three positions lean on IDENTICAL as the backstop for fixed-displacement emission. Given §1.11, the backstop covers bytes and fixup targets, which is enough for displacement correctness. It does not cover object flags or fixup types. B2 does not change either, so the combination is safe, but the R0 claim of "complete check" must be narrowed.
5. **Paired-state symmetry combined with Group B promotion.** After S1, `test_intro_op_wait_sound` still targets `player_reference.c` (xfail, `strict=False`). With DEC-B07 it becomes XPASS. Changing the test's SRC or removing the reference definition alters "what an existing test checks", which is an owner checkpoint. None of the three roadmaps lists this approval explicitly.
6. **CONST pad environment-dependence combined with provenance caches.** Path-dependent CONST bytes make raw object digests checkout-dependent. Any proof cache keyed on raw object bytes is non-portable across worktrees, the same class of bug as the `t3_audit` R3 fix. A §3 mentions normalization; C's V5 does not.
7. **C's DEC-C02 → DEC-C03 → EXP-1 chain.** It makes the soundness fix depend on a completeness experiment (D-2).
8. **A's DEC-A03 "explicit loader-relevant identity".** It needs a measured attribute policy, which A acknowledges. Until that exists, enforcing it may reject the *current* IDENTICAL build if wlink emits attribute or page-map differences that the original lacks. A's assumption field names this. The sequencing must therefore be measure first, then enforce.

---

## 5. Counterexamples and probe results (summary)

- **R1-P4:** 3/5 "divergences" pass under full paired-state restoration (D-1).
- **R1-P2:** CONST pad bytes are path-dependent and stable for fixed inputs (U-1).
- **R1-P3:** original residue at `0x56b1c` confirmed (supports C's premise).
- **R1-P5:** `t3_audit` R3 fixes present at `17733f9`; `oldcc` has no path-length guard at `17733f9` (supports the remaining part of C's DEC-C04).
- **R1-P6:** E4 per-record THREAD reset and PUBDEF segment-agnostic rebase confirmed in code.
- **R0 P3/P5/P6, still valid on `17733f9`'s unchanged tools:** Group B IDENTICAL; fixed-displacement B2 IDENTICAL (546/539); B1 IDENTICAL (547/540). Together these answer **C's EXP-3** for the literal-displacement encoding end to end. A's Q2 shows assembly of the piece-local-label encoding; a full link with that encoding is not yet shown.

---

## 6. Alternative designs

1. **Unified cross-object branch rule.** Use one rule for interior, entry and span cases, rel8 or rel32, with three encodings ranked:
   1. a symbolic EXTDEF, only for rel32 to an exported entry;
   2. a piece-local label plus constant (A's form, preferred because NASM checks range and the source stays readable);
   3. a literal displacement (fallback).

   Preconditions: every object in the span is placed in place (per-object legacy disallowed, §4.2); the target in C lies in a VerifiedRegion; the assembled field equals the original bytes (local check, as A requires); then IDENTICAL. No OMF transform of C objects (rejects C's `_loc_` PUBDEF for M2).
2. **T4 paired-state symmetry** (DEC-B18). Snapshot all mapped emulator memory before the original run and restore it before the C run. Audit-log the restored set. The harness change is about six lines (R1-P4 wrapper). Owner approval is needed because outcomes of existing tests change (XPASS).
3. **V4 as a deferred, two-sided rule.** Apply it in both the matcher and `place()`; restrict it to the CONST class; require ASM as provider; normalize digests. Trigger it on the first owner-accepted need for natural literals or for B3.
4. **Comparator hardening, measured first.** Extend `compare` to check object flags and fixup type *after* measuring the current Build A against the original (A's Q-row 2). If the current build differs in an attribute, that becomes an owner checkpoint rather than a silent gate change.

---

## 7. Decisions requiring further evidence

| Decision | Cheapest decisive probe | Falsification | Changes |
|---|---|---|---|
| DEC-B18 / DEC-B07 rollout | Run the *entire* T4 suite once with full-state restore (R1-P4 wrapper as a pytest plugin) | Any currently passing test fails, which would mean tests rely on asymmetry and must be inspected | Whether DEC-B18 can land as pure strengthening |
| DEC-A03 attribute enforcement | `le` dump of object flags, page maps and fixup types: original vs current Build A | Any attribute differs in the current IDENTICAL build | Enforce-now vs owner checkpoint |
| DEC-C03 (V4) need | List remaining not-done functions whose current reference C uses local string literals and whose T3 would need local CONST | Zero such functions → V4 stays post-M2 | Stage placement of V4 |
| B2 encoding choice | Full Build A link with A's piece-local-label encoding on the 4 B2 functions + standalone IntroOpSyncSound | Not IDENTICAL, or NASM range error | Preferred encoding in DEC-B04 rev 2 |
| DEC-C13 wording | Q-B06 (5r OD/debug variants for the 51 `only_4r`) | Any `only_4r` stays 4r-only | "Default" wording |
| IntroOpStartCredits / EndScreen | With full restore they still fail: first-diff analysis on `0x59eb9` and `0x80054c` | — | Confirms these two as genuine reference-C defects |

---

## 8. Structured positions on the other Architects' decisions

```text
Decision: DEC-A01
Revision: 1
Proposition SHA-256: cca3a6138a5467434a850794ca1632d592272c79ef8fefc172443aeb4d3acb31
Position: ACCEPT
Reason: Matches the measured backlog; T4→T3 conversions counted separately; T5 with the owner.
Conditions: none
Related objections: none
```

```text
Decision: DEC-A02
Revision: 1
Proposition SHA-256: 20349fbc30ce2eba38b56f88990e4f40f3777cb92c9af489e809a95abe525417
Position: CONDITIONAL
Reason: Two scopes of one verifier and a cutover audit of every live T3 are right (my P1 already shows 539/539 under E0). Strict raw-record admission is cheap at the matcher boundary and mandatory before any OMF transform.
Conditions: (1) Strictness failures on freshly compiled objects surface as UNSUPPORTED, not silent acceptance. (2) The matcher cutover is not blocked on the full strict-parser rewrite: checksum, record-type allow-list and FRAME preservation suffice for admission; the full codec (DEC-C09) is a B3/E4 prerequisite.
Related objections: OBJ-B20
```

```text
Decision: DEC-A03
Revision: 1
Proposition SHA-256: f48dd625f3fd34b6cee6a01ae6f9616fce969d705868f8df9fa2f7ba5881c32b
Position: CONDITIONAL
Reason: A complete one-provider partition and actual assemble+link are required (I-2). The comparator gap is real (compare.py does not compare flags or fixup types).
Conditions: (1) Measure the attribute/fixup-type policy on the current Build A vs the original before enforcing. (2) Provider "receipts" are derived build output, not a persistent store. (3) Per-object legacy fallback is treated as a plan error for any object in a fixed-displacement span.
Related objections: OBJ-B19
```

```text
Decision: DEC-A04
Revision: 1
Proposition SHA-256: 5cee3197ac45be6a908180d33ecbaf69b7d9a8d0fc63b90aa8e1ec4d5a2b05c0
Position: ACCEPT
Reason: Same as DEC-B05; P6 shows IDENTICAL on ChooseCampaignDialog with the base derived from the public offset.
Conditions: none (cross-object branch analysis uses the region's physical start; see §4.3)
Related objections: none
```

```text
Decision: DEC-A05
Revision: 1
Proposition SHA-256: aa4d747deed87bb671bbf98cacd3a06dee04c312e3dd749c5b69905937ee1e43
Position: ACCEPT
Reason: Whole-TU preference, plus a piece-local bridge with proved fixed cover and byte agreement; matches DEC-B04/B06 and is confirmed end to end by P3/P5.
Conditions: Group B is not gated on stage 2 (D-7); per-object legacy fallback excluded (§4.2).
Related objections: none
```

```text
Decision: DEC-A06
Revision: 1
Proposition SHA-256: 4900412ecbb7c67e9cc2863355109fe0079721a11249e03301438bef82173aac
Position: ACCEPT
Reason: Whole segments first, deployment only on justified need; consistent with DEC-B08.
Conditions: none
Related objections: none
```

```text
Decision: DEC-A07
Revision: 1
Proposition SHA-256: 9c28c5b2f073471389239eb6fb44da4e48a6da55224cd95ea91d05e994d2d846
Position: ACCEPT
Reason: Consistent with DEC-B09; the confirmed E4 THREAD/PUBDEF defects strengthen the deferral.
Conditions: Pilot admission additionally requires the owner decision on gate-2 semantics for src files with mismatching publics (match --all).
Related objections: none
```

```text
Decision: DEC-A08
Revision: 1
Proposition SHA-256: 652a1d04c4a5bc9febc03fae9a6637469f55698981699a3f995554e59c70a883
Position: CONDITIONAL
Reason: The boundary rules are correct, but the proposition omits the defect that matters now: paired runs must start from identical complete state. That applies to existing single-function T4, not only to multi-function T4.
Conditions: Add the full paired-state restoration rule (DEC-B18) as part of this decision, applicable to all T4.
Related objections: OBJ-B21
```

```text
Decision: DEC-A09
Revision: 1
Proposition SHA-256: 2cdd42c65d7906d4de19a4bf102f91b13f05dd02422a41c0cbefc24b20e1c95e
Position: ACCEPT
Reason: Matches DEC-B11; EV-3's 0/202 fresh snapshot records confirm "scheduling inputs only".
Conditions: none
Related objections: none
```

```text
Decision: DEC-A10
Revision: 1
Proposition SHA-256: 8dbab62c19ae9b44695421aa9fa6e1e1d79ea54a32d25ad68e6970be6505875e
Position: ACCEPT
Reason: Matches DEC-B13.
Conditions: none
Related objections: none
```

```text
Decision: DEC-C01
Revision: 1
Proposition SHA-256: 89590ee50b1609f5e5ad7e4ef98a560dd7cf5d5471e6e6850d8aa5fa0a7c6c3a
Position: ACCEPT
Reason: The three-level distinction is the central lesson of IntroOpSyncSound.
Conditions: none
Related objections: none
```

```text
Decision: DEC-C02
Revision: 1
Proposition SHA-256: 32bdbb10f84f604d9b33aa2388b5dd07c842fea749a9408695e6c52c4d9c967b
Position: CONDITIONAL
Reason: Landing E0 bidirectional obligations is right. V2 (function-scoped closure) is a useful diagnostic refinement for non-contiguous TUs, but Cause B is conservative UNSUPPORTED, not a soundness bug. Making the decision depend on DEC-C03/EXP-1 delays a soundness fix for a completeness feature.
Conditions: Remove the dependency on DEC-C03; land E0 failing closed on CONST pad. V2 is optional and must never turn a region-level UNSUPPORTED into placement permission.
Related objections: OBJ-B22
```

```text
Decision: DEC-C03
Revision: 1
Proposition SHA-256: 2e96264a171ef72dea16c558f344f5e6d44e38ea367f1645f4ff4f3b7a572896
Position: CONDITIONAL
Reason: The pad premise is real (0x56b1c residue confirmed; compiled pad is environment-dependent). The 5-condition rule is reasonable. It is not M2-critical, because the extern-literal idiom exists in production (save_slot_path.c).
Conditions: (1) Re-describe as environment-dependent, not consecutive-run non-deterministic, unless fixed-input runs differ. (2) Apply the same rule in build.place() as in the matcher. (3) Digest normalization for caches. (4) Schedule on the first need (natural literals or B3), not Stage 0.
Related objections: OBJ-B22
```

```text
Decision: DEC-C04
Revision: 1
Proposition SHA-256: 6110ad1cd89c84ed999125906beec1c44830a88c230244bb8a10dada43eb2c2b
Position: CONDITIONAL
Reason: The oldcc fail-fast path-length guard is still absent at 17733f9 and is cheap. The t3_audit R3 part is already fixed on 17733f9 (EV-3; t3_audit.py:160-162, 1197-1206, 1786-1790).
Conditions: Drop the t3_audit clause, or re-scope it to "verify fixed at 17733f9". Guard by Windows path length of every compiler-facing argument (src, -fo, -i=), fail with a toolchain error, not a silent skip.
Related objections: none
```

```text
Decision: DEC-C05
Revision: 1
Proposition SHA-256: 16a616ad8b0e5a2e1f6fffa070f8ca251cc5cf83ccc187092c1b2b6cebf78cd9
Position: CONDITIONAL
Reason: The unified planner, B1 and the three-class B2 are right and are demonstrated end to end (P5/P6 IDENTICAL). The rel32-interior `_loc_` PUBDEF injection is an unnecessary OMF transform on the M2 path; fixed displacement suffices in place (0x2f6df in P5). EXP-3 is already answered for the literal encoding.
Conditions: (1) Replace `_loc_` PUBDEF synthesis with the unified fixed-displacement rule. (2) Treat per-object automatic legacy fallback as a plan error in any fixed-displacement span. (3) No dependency on V4. (4) Accept a matcher-minted VerifiedRegion without additional type hierarchy.
Related objections: OBJ-B23
```

```text
Decision: DEC-C06
Revision: 1
Proposition SHA-256: 3bd8b1d5e90aa8cadc8158702ddbd8c16b0f3e5d72fb04fcde4dece5ab40c12a
Position: ACCEPT
Reason: Same as DEC-B06; P3 shows production MATCH and IDENTICAL with no infrastructure change.
Conditions: Its assumption "passes all existing PLAYFLIC tests" is false for test_intro_op_wait_sound under the current harness (it fails for byte-exact C too, R0 P4). The test is xfail(strict=False), so verify stays green; any change to the test needs owner approval.
Related objections: none
```

```text
Decision: DEC-C07
Revision: 1
Proposition SHA-256: 9be785e085ddec89659f364826c1f2c63175dd42918f8cc48f4936926f067b6f
Position: CONDITIONAL
Reason: The sequencing (M2 work ahead of B3/E6/E8/E4) is right. The causal framing ("68 blocked by symbol migration") and the "real ref-C bugs" premise are not.
Conditions: (1) The binding constraint for the 61+7 is reconstruction (name+C+proof); the migration tool is a supporting step. (2) Insert the T4 paired-state fix (DEC-B18) before any "ref-C bug fixing"; only IntroOpStartCredits and EndScreen remain as candidate genuine divergences (R1-P4). (3) Report Stage 2 yield as an upper bound.
Related objections: OBJ-B18, OBJ-B24
```

```text
Decision: DEC-C08
Revision: 1
Proposition SHA-256: ee55d25043dd8f9fe0658e47dda212dd5ab018901fd44d367154bb19d23031f3
Position: ACCEPT
Reason: Rejecting near-term E4 matches DEC-B17; the defects are confirmed in code (R1-P6).
Conditions: Add the owner gate-2 semantics decision as a precondition for any later E4 pilot.
Related objections: none
```

```text
Decision: DEC-C09
Revision: 1
Proposition SHA-256: dfab7c569dd76b8c399ab8dc5b66f513f079201a7e15f82b60a85f34f4bb801b
Position: CONDITIONAL
Reason: Duplicated OMF code demonstrably caused the E4 THREAD defect; one codec is right before B3/E4.
Conditions: Scope it as a precondition of B3/E4 only, not an M2 task. Do not refactor the working omfpatch/build path during M2 beyond what B1/B2 need (which is nothing in my design).
Related objections: none
```

```text
Decision: DEC-C10
Revision: 1
Proposition SHA-256: 0755146f59113b38bcc854a65ec97728b37cc79daacb0c966fac0f725422b10a
Position: CONDITIONAL
Reason: Timing (post-M2) and the V4 dependency are right.
Conditions: Scheduling is need-driven (Q-B08 count of consolidations needing B3); V4 must be applied in placement as well (§4.1); whole-segment first (DEC-A06).
Related objections: OBJ-B22
```

```text
Decision: DEC-C11
Revision: 1
Proposition SHA-256: 7a204425544c260b6b818b7daa21215e2318042fecc764b89da96c9aab06ad9b
Position: CONDITIONAL
Reason: E6 adoption on demand is right, but the trigger is misplaced: multi-function reference files already exist and are tested (player_reference.c, 20 functions). The real trigger is substituting an intra-TU sibling, callbacks or pointer identity. LogicalConstDataPtr and the switch-table allowance are speculative extensions.
Conditions: Re-state the trigger as in DEC-B12. Make paired-state symmetry (DEC-B18) a prerequisite. Treat the EXP-4 extensions as optional.
Related objections: OBJ-B25
```

```text
Decision: DEC-C12
Revision: 1
Proposition SHA-256: 9f75f979df9121edb96c8730e7c1f05854f8c57fdbcdfc0dea7933f8854c6139
Position: CONDITIONAL
Reason: The rejections are right and match DEC-B13/DEC-A10.
Conditions: Class 2 (`non_16_aligned_start`) is described with its measured precision (0.80/0.836/0.618) and premise, not "100%"; `shared_const_string_literal` stays conditional (one positive).
Related objections: OBJ-B26
```

```text
Decision: DEC-C13
Revision: 1
Proposition SHA-256: 29bf51dbcb0ca81f41d2b70321882bd2bd68fdf37eb643eb6cd87acd28ecd969
Position: CONDITIONAL
Reason: The matrix is right (DEC-B10). "Codify -5r as the primary default family" is unsupported as a historical claim and risky as a global default.
Conditions: Re-word as "first-tried search family for multi-function TUs needing 4-byte spacing; no claim about original flags"; EXP-2 additive.
Related objections: OBJ-B26
```

```text
Decision: DEC-C14
Revision: 1
Proposition SHA-256: 66419eaf72495cb7686afc137a391f7c8c6360ab605c5bd10d6d1ff5894f04cf
Position: ACCEPT
Reason: Matches B §9 and A §9.
Conditions: none
Related objections: none
```

**Own decisions.** All are RETAIN except these, which I expect to revise formally in Round 2:

- **DEC-B04:** add A's preferred piece-local encoding and the assembled-byte check; exclude per-object legacy; drop "IDENTICAL is complete".
- **DEC-B07:** superseded by the stronger DEC-B18 below.
- **DEC-B16:** extend the reclassification to IntroRunScript and IntroPlay.
- **DEC-B02:** add A's minimal strict-admission conditions.

---

## 9. New objections

**OBJ-B18**
- **Proposition challenged:** "5 real ref-C behavioural divergences" (C §1, §8.0 item 5, DEC-C07; inventory DG-04; A §8 "repair the five").
- **Evidence:** R1-P4.
- **Failure mode:** correct C is rewritten, and the harness asymmetry persists.
- **Assumptions:** the full-memory restore introduces no new asymmetry (it equalizes inputs).
- **Practical consequences:** −3 unnecessary C repairs; +3 potential DONE once the harness rule lands (owner approval).
- **Severity:** correctness/verification.

**OBJ-B19**
- **Proposition challenged:** my own R0 I-3(c)/I-6 and the RFC §13.1 framing that Build A IDENTICAL is a complete Build A check.
- **Evidence:** `compare.py@a21772b`, `17733f9` (flags printed, not compared; fixup tuple lacks type); A Q3.
- **Failure mode:** a loader-relevant object attribute or fixup-type change passes as IDENTICAL.
- **Severity:** correctness/verification. I accept this against myself.

**OBJ-B20**
- **Proposition challenged:** C DEC-C02's dependency structure (matcher landing depends on DEC-C03/EXP-1).
- **Evidence:** D-2; `save_slot_path.c@a21772b`; `build.py:94-104`.
- **Failure mode:** a soundness fix is delayed by a completeness feature.
- **Severity:** implementation risk.

**OBJ-B21**
- **Proposition challenged:** A DEC-A08 and C DEC-C11 placing paired-state reset only within multi-function T4 adoption.
- **Evidence:** R1-P4. The defect is in single-function `run_pair` today.
- **Failure mode:** current T4 proofs run on asymmetric inputs, with a false-pass possibility.
- **Severity:** correctness/verification.

**OBJ-B22**
- **Proposition challenged:** C OBJ-C01 and DEC-C03 "non-deterministic … flaky across runs" and V4 as Stage 0.
- **Evidence:** R1-P2 (stable for fixed inputs; path-dependent); D-2.
- **Failure mode:** a mis-specified root cause leads to the wrong mitigation. The practical risk is checkout-dependent digests, not run-to-run flakiness.
- **Severity:** unsupported factual claim.

**OBJ-B23**
- **Proposition challenged:** C DEC-C05's `omfpatch` `_loc_<addr>` PUBDEF synthesis for cross-piece rel32 into cut interiors.
- **Evidence:** R0 P5 (`0x2f6df` built IDENTICAL with no object transform).
- **Failure mode:** an unnecessary post-codegen object transform on the M2 path, requiring strict-codec work earlier.
- **Severity:** implementation risk.

**OBJ-B24**
- **Proposition challenged:** C "68 blocked by atomic cross-module symbol migration" and "1002/1010" (DEC-C07, OBJ-C04, Stage 2).
- **Evidence:** inventory rows (`missing=[name,C]`, `requires_llm=True` for all 61).
- **Failure mode:** over-projected deterministic yield; tooling is prioritised over reconstruction capacity.
- **Severity:** unsupported factual claim.

**OBJ-B25**
- **Proposition challenged:** C DEC-C11 "hard prerequisite before consolidating any T4 function into a multi-function `.c`"; "Multi-function T4 without E6 leaks intra-TU sibling calls".
- **Evidence:** `src/playflic/player_reference.c@a21772b` (20 functions) tested today. The E6-identified hazard is stub bypass under declared substitution, not multi-function files per se.
- **Severity:** unsupported factual claim / maintainability.

**OBJ-B26**
- **Proposition challenged:** C §2.8 "[FACT] predominantly `-5r`", §2.9/§7.1 "`non_16_aligned_start` 100% precision", DEC-C13 "-5r primary default".
- **Evidence:** E7 "R6 preservation" disclaimer and `only_4r = 51`; E8 epistemic table (0.800/0.836/0.618).
- **Severity:** unsupported factual claim.

**OBJ-B27**
- **Proposition challenged:** all three roadmaps forbidding B2 only under the global `--legacy` flag.
- **Evidence:** `build.py:310-314@a21772b` (automatic per-object legacy fallback on `Unplaceable`).
- **Failure mode:** a fixed-displacement branch spans an object that silently fell back to legacy layout. IDENTICAL would catch it, but the planner must reject it first (I-2).
- **Severity:** correctness/verification (defence in depth).

---

## 10. New decision proposals

```text
Decision: DEC-B18
Title: Full paired-state symmetry for all T4 runs
Proposition: wc1.cemu.run_pair snapshots every mapped emulator memory region before the original execution and restores it before the C execution, so both executions start from identical complete state. The audit log records the restored set. The rule applies to all T4 tests (single- and multi-function). After adoption, each xfailed divergence test is re-run and reclassified by evidence. Changes to existing tests' expected status (XPASS → pass, removal of xfail) require owner approval.
Revision: 1
Position: PROPOSE
Reason: Watch-only restoration made 3 of 5 recorded "reference-C divergences" artefacts (IntroOpWaitSound, IntroRunScript, IntroPlay pass under full restore; IntroOpStartCredits and EndScreen still fail).
Evidence: cemu.py:344-391@a21772b (unchanged @17733f9); R1-P4 (probe_q1.py); R0 P4
Assumptions: Python-side stub closures are stateless across the pair, or are reset by the test (true for the five probed tests).
Dependencies: none (supersedes DEC-B07 rev 1)
```

```text
Decision: DEC-B19
Title: Plan-level exclusion of legacy-placed objects from fixed-displacement spans
Proposition: The placement planner rejects any fixed-displacement cross-object branch whose source-to-target span includes an object placed in legacy layout. That covers both the global --legacy flag and the automatic per-object Unplaceable fallback.
Revision: 1
Position: PROPOSE
Reason: build.main() falls back to legacy per object automatically; fixed displacements are only valid for in-place layout.
Evidence: build.py:300-316@a21772b; R0 P5
Assumptions: none
Dependencies: DEC-B03, DEC-B04
```

```text
Decision: DEC-B20
Title: Comparator coverage measured, then strengthened
Proposition: Before any new placement path is admitted, measure the object flags, page/fixup records and fixup types of the current Build A against the original. If they agree, extend wc1.compare to compare them (strengthen-only). If they differ, present the difference to the owner before changing the Build A oracle.
Revision: 1
Position: PROPOSE
Reason: compare.py prints flags without comparing them and omits the fixup type; A's mutant passes IDENTICAL.
Evidence: tools/wc1/compare.py@a21772b; A Q3
Assumptions: the measurement can be done with the existing wc1.le parser
Dependencies: none
```

```text
Decision: DEC-B21
Title: CONST pad bytes are environment-dependent proof-irrelevant bytes
Proposition: Watcom 10.0a CONST inter-literal pad bytes are treated as environment-dependent. They are excluded from proof-cache digests (normalized), never required to equal the original in any future V4 rule, and V4 (when adopted) is applied identically by the matcher and build.place(), with ASM as physical provider in Build A. Until V4 is adopted, objects with such pads fail closed.
Revision: 1
Position: PROPOSE
Reason: The R1-P2 pad bytes vary with the source path and are stable for fixed inputs; the original pads contain residue (R1-P3).
Evidence: R1-P2, R1-P3; build.py:94-104@a21772b; E8 rev-e8-02 (CONST pad digest normalization)
Assumptions: none
Dependencies: DEC-B02
```

---

## 11. Probe log (Round 1)

**Common environment:** `/tmp/opencode/cn-claude/m` (export of `a21772b` plus my R0 probe edits; the tools relevant here are byte-identical to `17733f9`); `WINEPREFIX=/mnt/data/projects/warcraft-1-decompile-wt/cons-b/build/oldcc/wineprefix`; `TMPDIR=/tmp/opencode/cn-claude/t`; `nix develop -c`. Scripts are copied to `/mnt/data/projects/warcraft-1-decompile-consilium/runtime/claude/probes/scripts/`. No full `make verify` or full test suite was run; each claim needed only targeted execution.

**R1-P1 — EV-3 tool deltas.**
- Command: `git diff --stat a21772b 17733f9 -- tools/wc1/{compare,oldcc,match,build,emit,cemu}.py`.
- Output: empty.

**R1-P2 — CONST pad determinism.**
- Command: `nix develop -c python3 /tmp/opencode/cn-claude/t/cp/run.py` and `run2.py`.
- Source `c2.c`: `extern void use(const char*,const char*); void f(int x){use(x?".net":".sav","save%d");}`, compiled via `wc1.oldcc.compile_c(src, "-q -zl -zld -bt=dos -s -ot -ol -5r -zp2", out)`.
- Four consecutive runs, same path: CONST `2e6e657400 610074 2e73617600 570049 73617665256400` (×4, identical).
- Same file in a different directory: `2e6e657400 200068 2e73617600 700029 …`.
- Same path without `-zld`, or with `-4r`: identical to the first.
- **Limitation:** one source, two paths; heap-state dependence beyond the path is not isolated.

**R1-P3 — original residue.**
- Command: `orig.py` (`analysis.run()`, DATA_OBJ image).
- Output: `0x56b1c 2e6e6574008d75e02e736176000800e873617665256400a5`.

**R1-P4 — divergence tests under full paired-state restore.**
- Command: `nix develop -c python3 /tmp/opencode/cn-claude/t/probe_q1.py {base|full}`.
- The script wraps `wc1.cemu.run_pair`, also as seen by `t4spec`. Inside each pair, a class-level `Emu.call` wrapper snapshots every `uc.mem_regions()` region at the first call (original) and restores them at the second call (C).
- base: all 5 FAIL (messages in D-1).
- full: wait_sound PASS, run_script PASS, intro_play PASS; start_credits FAIL `0x59eb9 01≠00`; end_screen FAIL `0x80054c 70≠50`.
- **Limitations:**
  - I ran the five test functions directly, not via pytest collection, so the xfail markers are not exercised.
  - The audit-log path (`WC1_T4_AUDIT_LOG`) was not enabled.
  - The full T4 suite was not run with the wrapper (§7).

**R1-P5 — `t3_audit` / `oldcc` on `17733f9`.**
- Command: `git show 17733f9:tools/wc1/t3_audit.py` (lines 160-162, 626-631, 1197-1206, 1786-1790) and `git show 17733f9:tools/wc1/oldcc.py | grep` for path-length handling.
- Output: the R3 fixes are present. oldcc passes absolute `Z:` paths (`win_path`, lines 123-125, 201-203) with no length guard.

**R1-P6 — E4 code defects.**
- `experiments/build_codegen/e4/omf_extract.py@e6150b8`: `Threads()` constructed per FIXUPP record at lines 258 and 823; the PUBDEF/LPUBDEF filter at lines 798-807 applies `lo <= off < hi` regardless of `pseg`.

**R1-P7 — rename tooling.**
- Command: `git ls-tree --name-only 17733f9 tools/wc1/ | grep -i -E "renam|migrat|symbol"`.
- Output: only `symbols.py`. There is no migration tool.

---

## 12. Source index

**Architect inputs (inbox)**
- `r01-inbox/01-architect-gpt-opening.md` (sha `22477c0c…`): §§1–15, DEC-A01..A10, OBJ-A01..A08, Q1–Q4
- `r01-inbox/02-architect-gemini-opening.md` (sha `32e9252a…`): §§1–15, DEC-C01..C14, OBJ-C01..C08, Probes 1–7
- `r01-inbox/00-PROPOSITION-INDEX.json` (sha `1ade8e0e…`)

**Production code**
- `tools/wc1/compare.py@a21772b` (= `@17733f9`): flags in `desc` only; fixup tuple `(obj, src_off, target_obj, target_off)`
- `tools/wc1/cemu.py:344-391@a21772b`: `run_pair` watch-only restore
- `tools/wc1/build.py@a21772b`: 55–112 (`place`, CONST content check at 94–104), 113–146, 300–316 (per-object legacy fallback)
- `tools/wc1/t3_audit.py@17733f9`: 160–162, 626–631, 1197–1206, 1786–1790
- `tools/wc1/oldcc.py@17733f9`: 123–125, 188–203

**Production sources and tests**
- `src/mod_13f60/save_slot_path.c@a21772b` (extern-literal idiom)
- `src/playflic/player_reference.c@a21772b` (20-function reference TU)
- `tests/test_playflic_t4.py@a21772b`: 22–24, 177, 403, 481, 518
- `tests/test_mod_2efd0_t4.py@a21772b`: 180

**Experiments**
- `experiments/build_codegen/e4/omf_extract.py@e6150b8`: 250–262, 795–810, 823
- `docs/research/build-codegen/E2-compilation-context.md@e6150b8`: 220–272 (Cause B retained as UNSUPPORTED)
- `docs/research/build-codegen/E7-compiler-calibration.md@e6150b8` ("R6 preservation", "Existing T3 compatibility")
- `docs/research/build-codegen/E8-cu-boundaries.md@e6150b8` ("Epistemic classification")

**Inventory**
- `wc1.m2_inventory` output on `a21772b`: `runtime/claude/probes/inv-main/inventory.json`

**Evidence notices**
- EV-3 (`main@17733f9`, verify 2505 passed / 11 skipped / 5 xfailed; progress unchanged 912/98)

**Probe artifacts**
- `runtime/claude/probes/scripts/{probe_q1.py, run.py, run2.py, orig.py, c2.c}`
- R0 artifacts: `probe-b1-b2-groupb.patch`, `zgb.c`, `e0-main/`