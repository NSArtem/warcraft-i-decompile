# Editorial notes (EDITOR DRAFT)

The changes listed here do not alter architectural meaning or obligations. If anything in this file appears to change an obligation, the quoted ledger proposition governs and this file is in error.

## 1. Language

- **Change:** the baseline RFC (`6f319ac8`) is in Russian; this revision is in English.
- **Reason:** English is the consilium's working language, and every ledger proposition is English.
- **What stays normative:** the English ledger text, quoted verbatim.
- **Open to the owner:** the owner may ask for a Russian rendering. It would be a translation of the editorial prose, with the propositions kept in English or given with a translation clearly labelled non-normative.

## 2. Source of normative text

- **Rule:** the normative text is the canonical-ledger propositions (`decision-ledger.json`, a byte-identical copy of `00-CANONICAL-LEDGER-v2.json`, SHA-256 `dc6bda93ea7f3cf2b1506f481600b12af6a357c3fa9a84beb8208bbb39b4e97a`), together with the baseline provisions incorporated by reference in RFC §8 (see §6).
- **A's consolidated clauses are not used as decision text.** In r04 §1, Architect A published consolidated RFC clauses with their own SHA-256 values: Verifier, Planner and LE, Physical placement, Whole-TU promotion, Data and extraction, E6, Paths, Compiler and CU evidence. They were proposals for the RFC text and were never ledger decisions with three positions.
- **What this draft does instead:** it quotes the source decisions individually and groups them in the same way. The Architects may decide to adopt consolidated wording in a later revision. That would need new ledger records.
- **The full ledger is not copied.** `01-DECISION-LEDGER-FULL-v2.json` (`f5523c8c…`) and `02-OBJECTION-LEDGER-v2.json` (`aaf68de7…`) are referenced by hash, not copied.

## 3. Translation of baseline RFC §8.2 constraints 1–5

DEC-B08 r1 and DEC-C10 r3 cite these constraints. The translation below is faithful to `rfc-build-codegen-infrastructure.md@6f319ac8` §8.2 and is non-normative. The Russian original governs.

1. **Full transparency for canonical C.** No symbol of the form `wc1_anchor_*` may appear in `src/`, `analysis/` or `tests/`. Such symbols exist only in temporary artifacts under `build/obj/` and `build/pieces/`.
2. **Full data verification before anchoring.** Rewriting is permitted only after byte-for-byte verification of the data segment together with all its pointer fixups (baseline §5.2), and in compliance with the aliasing rules (baseline §6.3).
3. **Full FIXUPP32 and THREAD support.** The patcher must handle THREAD subrecords correctly, expanding them when re-encoding, and preserve correct FRAME semantics (FLAT/DGROUP) in wlink.
4. **No compensation for layout errors.** Fix B3 may not be used to hide an incorrect structure layout, incorrect types or an incorrect data-ownership model.
5. **Verification when removing existing artificial `extern` strings.** Lifting the `dseq == sorted(dseq)` restriction may allow removal of artificial `extern` declarations such as `txt_error_saving` and `path_war`. No such removal is automatically safe. Each needs recompilation, verification of the data contents and of aliasing, and Build A IDENTICAL preserved.

## 4. Titles

The canonical ledger has an empty `title` for 20 decisions. This draft supplies a short title for each, marked [editorial title] wherever it appears. Titles are navigation aids and are not decision text.

## 5. Grouping and order

The RFC groups decisions into contracts (§5.1–§5.11) and puts the general rule first in each group.

- **Grouping is editorial.** Every quoted decision binds, whatever its position.
- **"Compatible detailed form" is descriptive only.** It means the Editor found no contradiction between the decisions in a group. It does not merge them, and it does not withdraw any of them.

## 6. Baseline content incorporated by reference

- **This is not an editorial carry-over.** The baseline provisions that stay binding are **normative by incorporation**. RFC §0 names them as the second kind of normative content, and RFC §8 lists them (rows B-1 to B-7) at their pinned text in `docs/architecture/rfc-build-codegen-infrastructure.md@6f319ac8ff780bb45ff028d006216016fc932a13`. They are:
  - §13 invariants 1–10 (B-1);
  - §8.2 constraints 1–5 (B-2);
  - §6.1–§6.4 transform preconditions (B-3);
  - §16 minimum admission criteria (B-4a to B-4g);
  - §15 audit-handling rules (B-5);
  - §12.2 S(f) record (B-6);
  - §19.2 exclusions (B-7).
- **Not re-voted.** No ledger decision relaxes them.
- **Where an accepted decision changes or replaces part of a provision, the decision governs.** RFC §8 names the governing decision per row. Examples:
  - DEC-A02/DEC-C02 replace the §15/§16 "519 T3" audit population;
  - DEC-B14/DEC-C01 replace the §16 CandidateRegion type;
  - DEC-A10/DEC-C12/DEC-B14 replace §16's automated CU recovery.
- **Baseline sections not listed in RFC §8 are context only.** Examples: §3's 17 decisions; §4.2's storage of OriginalCUHypothesis, replaced by DEC-B14; §3 item 9, "Fix B3 strategically necessary", replaced by the deferral in DEC-B08.
- **Translations are explanatory.** The English renderings in this file (§3) and in RFC §8 do not replace the pinned Russian text.

## 7. Evidence citations

- **EV-3 figures:** the pinned campaign manifest is EV-1. EV-2 and EV-3 are included in the package as `03-EV-2.json` and `03-EV-3.json` (see RFC §12 item 4). The EV-3 figures in this draft agree with `03-EV-3.json` and are also quoted in the frozen r04 responses.
- **Experiment facts:** cited to `docs/research/build-codegen/*@e6150b8`.
- **Probes:** cited by the identifier the frozen responses use.
- **No new evidence was generated.** The Editor ran no probe and no test.

## 8. Glossary of shorthand used in decisions

| Term | Meaning |
|---|---|
| **B1** | A pre-function leading jump table in `_TEXT`, before the first public, e.g. ChooseCampaignDialog `0x157e8`. |
| **B2** | A cross-object relative branch or fallthrough between an ASM piece and an in-place C object. Variants: interior, entry, span. NASM `-f obj` cannot emit 8-bit external relocations. |
| **B3** | Data-anchor coupling. Fix B3 means rewriting data-segment references to ASM-provided anchors (E5). |
| **Group B** | IntroOpPlaySound `0x2315c`, IntroOpSyncSound `0x23170` and IntroOpWaitSound `0x231cc` (PLAYFLIC.C). |
| **Q-B05** | The single full run of the existing T4 suite with complete paired state enabled, before landing. |
| **Q-B08** | The question whether a named not-DONE function needs multi-anchor data. |
| **EXP-2 / Q-B06** | The optional compiler probes `-5r -d1+ -zp1` and `-5r -od`. |
| **IntegratedResult** | The receipt of actual assemble, link, provider evidence and hardened comparison (DEC-C01). |
| **"61+7"** | The name/C backlog figure quoted in DEC-C07 r3. Per A's r04 §5, 61 placeholder rows need naming and C, and 7 low-confidence items need evidence. |

## 9. Ledger integrity

The inconsistencies the Editor found are listed in RFC §12 and in `CONSILIUM-EDITOR-REPORT.md`. They are reported, not resolved.
