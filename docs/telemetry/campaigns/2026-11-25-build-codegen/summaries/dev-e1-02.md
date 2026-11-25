Committed the E1 replay repair as `720b335`. The regenerated artifacts retain raw SHA-256 hashes and add checkout-independent parsed OMF digests. Same-root replay checks both artifacts byte-for-byte. Cross-root replay checks all scientific results and disassembly after masking checkout provenance and raw object hashes.

All 18 tests passed in the assigned worktree and a second checkout. All 97 raw object hashes differed across roots, while all 97 parsed digests matched. Both primary Build A links remained `IDENTICAL`, and the protected-path diff against `7c23d23` was empty.

Cross-checkout replay still requires a path that Watcom 10.0a accepts. A path containing a space and a longer path both failed during compilation.