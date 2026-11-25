VERDICT: REQUEST_CHANGES

The committed controls and full re-audit reproduce, but independent probes found false MATCH results.

1. **Severity: HIGH — Truncated function bodies pass.**  
   **Location:** `experiments/build_codegen/e0/matcher_proto.py:351`  
   **Explanation:** Verification uses the compiled extent without requiring it to cover the discovered original function end. Deleting the final `c3` (`ret`) from freshly compiled **InitPaths**, and decrementing its segment length, returns **FunctionMatch=MATCH, RegionMatch=MATCH**, with no findings. An independent synthetic `mov eax,1` missing its original trailing `ret` also passes.  
   **Required resolution:** Require complete original-body coverage before either MATCH verdict. Add negative controls for truncation at an instruction boundary and inside an instruction.

2. **Severity: HIGH — Trimmed bytes still count as internal branch targets.**  
   **Location:** `experiments/build_codegen/e0/matcher_proto.py:275`  
   **Explanation:** Branch classification uses the untrimmed segment length after extent retry shortens the verified region. With compiled bytes `e9 00000000 90`, original bytes `e9 00000000 c3`, and original function end at offset 5, both verdicts are MATCH. The retained region ends at `0x10005`, yet its jump targets that excluded address and records `requires_static_resolution=False`. Reachable, differing bytes have been discarded.  
   **Required resolution:** Evaluate branch closure against the final retained region. Reject trimming reachable bytes and require the appropriate relocation for targets outside that region. Cover both rel8 and rel32 cases.

3. **Severity: HIGH — External resolution ignores definitions in the same module.**  
   **Location:** `experiments/build_codegen/e0/matcher_proto.py:154`  
   **Explanation:** External targets resolve directly through the database without checking module PUBDEF/LPUBDEF definitions. In real InitPaths, adding a definition of its referenced `__argv` symbol inside `$$SYMBOLS`/`DEBSYM` still returns **RegionMatch=MATCH**, with no findings; the referenced segment is excluded as metadata. A separate probe also passes despite a DATA public’s database address contradicting its inferred segment base.  
   **Required resolution:** Reconcile local symbol definitions with inferred anchors and database addresses. Follow references through locally defined external symbols, and reject runtime references into excluded metadata.

4. **Severity: MEDIUM — Additional executable segments bypass branch obligations.**  
   **Location:** `experiments/build_codegen/e0/matcher_proto.py:413`  
   **Explanation:** Every anchored segment except `_TEXT` is checked with `code=False`, irrespective of its class. An anchored `EXTRA_TEXT`/`CODE` segment containing an exact external `call rel32` without its OMF fixup returns MATCH. Its original branch obligation is never examined.  
   **Required resolution:** Check executable segments as code, or explicitly return UNSUPPORTED for additional code segments. Add a missing-relocation negative control.

5. **Severity: MEDIUM — Completely out-of-bounds fixups disappear before validation.**  
   **Location:** `experiments/build_codegen/e0/matcher_proto.py:190`  
   **Explanation:** Fixups are filtered by overlap before bounds and unsupported-construct checks. A one-byte `ret` segment with `Fixup(offset=1, loc=11, target_kind="grp", target=99)` returns **MATCH with no findings**. The boundary fixup bypasses all three relevant checks.  
   **Required resolution:** Validate every runtime-segment fixup before extent filtering. Out-of-bounds fields must produce ERROR or UNSUPPORTED, including fields starting exactly at segment end.

6. **Severity: MEDIUM — Function-only audit errors permit successful command exit.**  
   **Location:** `experiments/build_codegen/e0/run_e0.py:20`; `experiments/build_codegen/e0/reaudit_t3.py:177`  
   **Explanation:** Both entry points check region errors only. The audit can record FunctionMatch ERROR for a missing expected T3 public while its remaining region matches. An isolated entry-point probe with one function ERROR, zero region errors, and matching inventory counts returns exit status **0**.  
   **Required resolution:** Return nonzero for ERROR at either verification level, including missing expected publics. Add an entry-point regression check.

Independent verification summary:

- Read the implementation, report, repository guidance, and RFC §§5, 14/E0, and 15. The referenced `contracts/E0-contract.md` is absent.
- Confirmed the requested production-path diff against `3ee53aa` is empty. No tracked files were changed.
- `pytest -q experiments/build_codegen/e0/test_e0.py`: **46 passed**.
- Ran the complete reproduction twice with `--jobs 4`, writing under `build/rev-e0-01/`: each freshly compiled **514 files**, audited **519 functions**, and reproduced **36/36 controls** and **519/519 MATCH** results.
- The two fresh runs produced byte-identical artifacts. Compared with committed artifacts, differences are confined to object hashes and 48 debug-metadata records, consistent with embedded absolute worktree paths. All remaining content agrees.
- Independently rejected forged data pointers, overlapping fixups, and wrong external addends as expected. The successful bypasses above remain uncovered by the suite.
- N8 retains its three independent finding categories, supporting the tested R3 behavior. The fresh baseline audit is reproducible, but its matcher still has the soundness gaps listed above.