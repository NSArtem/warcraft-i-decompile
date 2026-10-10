# Build: linking C in place

`python3 -m wc1.build` (`make build`) produces `build/war.exe` from the generated
asm and every C file named by a `src = ...` entry of the symbol database.  Since
2026-10-10 (third session) the C objects are linked **at their original
addresses**, so a build whose C files all match (T3) is **IDENTICAL** to the
original (loaded image, entry, stack and all 8770 fixups; `wc1.compare`), not
merely load-equivalent.  `make verify` requires that.

## How

1. Every C file is compiled with the flags of its `codegen-flags:` header.
2. **Placement** (`build.place`): the functions a file provides must sit in its
   `_TEXT` at the same relative offsets as in the original (same order, same
   inter-function filler).  The object then covers `[first function, first +
   len(_TEXT))` of the code object.  No other discovered function may start in
   that range.
3. **Data anchors**: for each non-empty data segment (`CONST`, `_DATA`, `_BSS`)
   the original address is derived from the code relocations (original fixup
   target minus the addend in the C object; all relocations must agree).  The
   contents are compared with the original bytes (pointer fields excepted:
   `wc1.match` checks those).  The segment is then made **zero-length** and
   renamed to the asm segment of its region (`_DATA` below the end of the
   initialised data, else `_BSS`): it becomes an anchor linked exactly at that
   address, its relocations resolve to the asm's identical bytes, and asm code
   that shares the data keeps working.  This matters: the original compiler
   merged identical literals per module, e.g. `"path.war"` (0x52538) is used
   by `InitPaths` (C) and `OpenDataArchive` 0x1d9d4 (asm).
4. `tools/wc1/omfpatch.py` sets **every segment of the C object to BYTE
   alignment** (wcc386 emits `_TEXT` PARA, data DWORD), applies the renames and
   empties the anchored segments (drops their LEDATA and following FIXUPPs).
5. `Emitter.emit_pieces` writes the asm as pieces `build/pieces/piece_NNN.asm`
   that cover everything between the C objects (code) and between the anchors
   (data); the link order is `piece0, C1, piece1, C2, ..., pieceN`.  Piece 0
   declares all segments and `DGROUP` first (`DECLARE_SECTIONS` in
   `asm/wc1.inc`), so the segment order is the original's whatever the C
   objects declare.  Labels defined in another piece are declared
   `extern name:wrt FLAT` (without `wrt FLAT`, NASM's default frame made wlink
   resolve cross-piece `call`s 0x40000 off).  Labels strictly inside a C range
   are dropped (only the functions the C object defines can be referenced;
   `Emitter._check_replaced` enforces it) and a label is added at each C range
   end, so asm expressions never span a C object.
6. Anything that cannot be placed (functions in another order, data at several
   addresses, communal variables, ...) falls back to the **legacy layout**: the
   functions are omitted from the asm up to their limit, the object is linked
   after everything else and the image is `DIFFERENT` (the build prints why).
   `--legacy` forces this for every file.

## Consequences

* Function-level C files (`src/codegen/*.c`, `src/init.c`) and whole modules
  use the same mechanism; a module-level file is just a file whose functions
  cover the module.  Per-module asm files are therefore not needed for code.
* Data stays defined by the asm.  A C module that defines initialised globals
  with *different* contents than the original fails at placement (contents
  compared), so the build can never silently change data.
* Moving data ownership to C (C objects really providing `_DATA`/`CONST`
  bytes) needs the per-module data layout of the data object
  (docs/subsystems/data_layout.md, in progress).  Not needed for identity.

## Checks

* `make build` fails if the result is not IDENTICAL and no file used the
  legacy layout.
* `tests/test_pipeline.py::test_identical_relink` compares `build/war.exe`
  with the original; `test_omfpatch` checks the object patcher.
