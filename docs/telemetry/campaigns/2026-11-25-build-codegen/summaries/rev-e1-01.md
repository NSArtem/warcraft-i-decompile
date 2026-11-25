VERDICT: REQUEST_CHANGES

One finding:

- **Medium — checkout-dependent replay test.** [test_e1.py:217](/mnt/data/projects/warcraft-1-decompile-wt/rev-e1-01/experiments/build_codegen/e1/test_e1.py:217) unconditionally compares fresh artifacts with committed bytes. In this review worktree, pytest reports **16 passed, 1 failed**. All 107 JSON differences concern path-dependent object hashes or diagnostic paths; scientific results agree. The documented path limitation explains the failure but leaves the required review command failing. **Required resolution:** make artifact verification portable while retaining raw hashes and strict checks of code, relocations, branch targets, and verdicts.

Independent verification summary:

- Freshly compiled **97 variants / 196 function observations**; confirmed R1 separation and E0 matcher use.
- Verified Group A **`74 f5` versus original `74 f3`**, and Group B **`74 93` / `75 89`** crossing `IntroOpSyncSound`. Preserved disassembly agrees.
- Both independent `wc1.compare` commands report **IDENTICAL**, with **8,770 fixups** and zero differences.
- Linker maps attribute all six functions to compiled C objects. Omitting those objects causes undefined-symbol failures; linked object segments differ from compiler output only in alignment.
- Fixtures contain no assembly insertions. The requested production-path diff is empty; tracked files remain unchanged.
- A second fresh replay at the review path reproduces both artifacts byte-for-byte.

The shared-epilogue conclusion is independently supported; the requested change concerns artifact-test portability.