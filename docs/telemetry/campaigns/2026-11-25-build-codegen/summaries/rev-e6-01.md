VERDICT: REQUEST_CHANGES

Two independent adversarial probes produced false passes despite the supplied tests passing.

1. **HIGH — Callback context restoration hides ABI violations.**  
   **Location:** [experiments/build_codegen/e6/mf_cemu.py:444](/mnt/data/projects/warcraft-1-decompile-wt/rev-e6-01/experiments/build_codegen/e6/mf_cemu.py:444)  
   After executing a callback, the driver restores the saved CPU context without checking preserved registers or stack cleanup.

   **Reproduction:** Freshly compiled a temporary Options fixture containing an inline `xor ebx,ebx` in Refresh, using Watcom’s `pragma aux` facility. Group verification returned `diffs=[]` with matching callback events. Independent direct calls demonstrated the violation: original Refresh preserved EBX=`0x12345678`; compiled Refresh returned EBX=`0`. No code-image patching or forged audit state was needed.

   **Required resolution:** Validate callback return, stack cleanup, and required preserved registers before restoring context. Add negative controls for register clobbering and incorrect `ret N`.

2. **HIGH — Reachable-range truncation permits substituted-callee entry bypass.**  
   **Location:** [experiments/build_codegen/e6/mf_cemu.py:148](/mnt/data/projects/warcraft-1-decompile-wt/rev-e6-01/experiments/build_codegen/e6/mf_cemu.py:148), also lines 253–255 and 403–406.  
   Function ranges exclude instructions unreachable from the function’s entry. Both isolation checks use these shortened ranges, leaving executable trailing bytes unprotected.

   **Reproduction:** A temporary NASM fixture placed `ret; mov word [_line_timer],7; ret` at the loader symbol. Frame called the substituted loader entry, then jumped to `IntroLoadCreditLines_+1`. The computed loader range covered only its initial `ret`; the jump destination had no owner. Static construction and dynamic execution both accepted it, and Isolated verification returned `diffs=[]` with matching loader logs.

   **Required resolution:** Track ownership separately from entry reachability. Reject transfers into substituted-function non-entry bytes and unclassified executable gaps. Add this trailing-code variant alongside N6.

Independent verification summary:

- `pytest -q experiments/build_codegen/e6/test_e6.py`: **73 passed**.
- `python3 -m experiments.build_codegen.e6.run_e6 --check`: **passed**, reproducing the committed JSON byte-for-byte.
- `git diff 3ee53aa -- tools/ src/ analysis/ tests/ Makefile`: **empty**. No tracked files changed.
- Independent parsed-OMF inspection confirmed the real PLAYFLIC call at `0x12e` has **one self-relative EXTDEF fixup**, at `0x12f`, targeting `IntroLoadCreditLines_`.
- Independently confirmed `no_fixup_call.asm` has **zero call fixups**, invokes the compiled-entry hook symmetrically, and retains unchanged machine-code bytes.
- Additional pointer probes rejected swapped callbacks, interior pointers, original addresses on the C side, and non-pointer byte changes; valid correspondence passed.
- Group/Integrated execute the real compiled callbacks. The requested changes concern execution fidelity and fail-closed isolation.