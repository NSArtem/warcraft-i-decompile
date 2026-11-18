# Save format: mod_24860, the save-file loader and writer (0x24860..0x24e50)

Area = `mod_24860` in `analysis/modules.toml`, 10 discovered functions
0x248e0..0x24e50 (the 0x24860..0x248e0 part is data, section 5).  The
neighbouring objects are `SAVE.C` 0x23ec0..0x24860 (the two-player link half of
saving/loading, `docs/subsystems/save_score.md`) and `SCORE.C` 0x24e50.
Names/prototypes/per-address evidence: `analysis/symbols/mod_24860.toml`;
reconstructed C: `src/mod_24860/`; declarations: `src/include/mod_24860.h`;
tests: `tests/test_mod_24860.py`.

This module is everything that touches the bytes of a save file:

* `SaveLoadImage` 0x24900 reads a whole save image from an open stdio stream
  into a `GdsAlloc` buffer and validates its header through SAVE.C's
  `SaveStreamValidate` 0x241a4;
* the stream helpers `SaveReadStream` 0x249a4 / `SaveSkipStream` 0x249c8 walk
  the loaded image; `SaveFreeImage` 0x249e0 releases it;
* `RefRelocate` 0x248e0 converts the pointers inside the saved records to and
  from offsets, and `SaveRelocObjectMap` 0x24a68 / `SaveRelocUnits` 0x24aa8 /
  `SaveRelocObjects` 0x24b88 apply it to the three record arrays;
* `SaveWriteImage` 0x24bf0 + `SaveWriteBytes` 0x249f8 write the image to an
  open slot file.

The code that decides *when* to save or load, opens the slot file, names the
slot and finishes (checksum/close/delete) lives just outside the range:
`fn_1aa7c` 0x1aa7c / `fn_1abc0` 0x1abc0 (save), `fn_19908` 0x19908 /
`fn_1e158` 0x1e158 (load), `fn_14ad8` 0x14ad8 (create a slot file),
`fn_1498c` 0x1498c (open a slot file for loading), `fn_146cc` 0x146cc (finish:
checksum+close, or delete on error) and `fn_14670` 0x14670 (the checksum).
They are documented here because the image alone does not explain the file.

## 1. The slot file on disk

A save slot (0..6, the seven entries of the slot name table at 0x592e8,
0x20 bytes each) is one file.  `fn_14ad8` creates it and writes the header,
`fn_146cc` finishes it:

| file offset | size | content | evidence |
|---|---|---|---|
| 0x00 | 0x20 | slot name, NUL-padded (the 32-byte slot table entry) | `FileWrite(name, 0x20, 1)` 0x14bf4; the loader reads it at 0x1488f and `fn_1498c` skips it |
| 0x20 | 4 | **checksum** of the image, written last (0 until then) | `FileSeek(fp,0x20,SEEK_SET); FileWrite(&sum,4,1)` 0x14706-0x14727; read at 0x14a58 |
| 0x24 | 4 | 0 (reserved; never validated) | written 0x14c2c from the zeroed local `[esp+0xa0]`; no reader |
| 0x28 | 4 | `'War1'` = 0x31726157 | written 0x14c48 from `[esp+0x9c]`; checked at 0x148c8 and 0x14a91 |
| 0x2c | 0x109ee | the save image (section 2) | the writer is called with the file positioned here (0x14bf4 writes 0x2c bytes first); the loader reads to EOF (0x24936) and the checksum starts at 0x2c (0x14687) |

The checksum (`fn_14670` 0x14670): seek to 0x2c, then for each 4-byte dword
`d` of the image (read in 200-byte chunks) do `sum = 2 * (sum + d)` starting
from 0; the final 2 bytes of the image (0x109ee is 2 mod 4) are not covered.
`fn_1498c` recomputes it (0x14aa0) and compares with the stored value
(0x14aa5); a mismatch, a missing `'War1'` or an unreadable dword closes the
file and returns NULL (`loc_14ac0`).

## 2. The save image

The image is a fixed sequence of blocks.  It is produced by `SaveWriteImage`
(in this order, all through `SaveWriteBytes`) and consumed by the loaders at
the same offsets:

| image offset | size | global | consumer |
|---|---|---|---|
| 0x0000 | 2 | record type word `0x43 0x00` (`'C'`) | `SaveStreamValidate` 0x241a4 (word must be 0x43) |
| 0x0002 | 2 | `dat_516ae` 0x516ae (link/session flag; 0 = single player) | `SaveStreamValidate` (0 in single player, non-zero for a two-player save) |
| 0x0004 | 0x0c | `net_enemy_record` 0x5a084 (partner identity block) | `SaveStreamValidate`/`NetLoadSyncMessage` in two-player mode |
| 0x0010 | 6 | `net_send_state` 0x58d9c (3 link words) | link replay |
| 0x0016 | 0x550 | `net_send_ring` 0x58848 (10 x 0x88 message ring) | link replay |
| 0x0566 | 4 | `net_ring_state` 0x58d98 (ring index, size-1) | link replay |
| 0x056a | 0x14 | `prefs_block` 0x532b4 (5 words from PREFS.WAR) | `fn_195ac` reads it at 0x195cf and calls `SndApplyOptions` |
| 0x057e | 0xbb8 | scenario block 0x50004 (`scenario_unit_mask` is its first dword) | `fn_195ac` at 0x195e0 (fatal error if the resource is bigger, 0x19670) |
| 0x1136 | 0x200 | game-state block 0x50d7c (RNG seed, scenario number, counters, player score) | `fn_195ac` at 0x195f1, then `fn_19470(seed)` |
| 0x1336 | 0x2000 | `tile_map` 0x58584 (64x64 tile words) | `fn_1b198` at 0x1b358 |
| 0x3336 | 0x2000 | `map_flags` 0x5857c (64x64 flag words) | `fn_1b198` at 0x1b36c |
| 0x5336 | 0x4000 | `object_map` 0x58580 (64x64 dwords: tile -> unit) | `fn_1b198` at 0x1b380 + `SaveRelocObjectMap` |
| 0x9336 | 0x2000 | `fog_map` 0x58578 (64x64 fog words) | `fn_1b198` at 0x1b39b |
| 0xb336 | 0x47e0 | 200 unit records (0x5c each, `unit_array` 0x59640) | `UnitsInitGame` 0x2d4b8 at 0x2d4f6 + `SaveRelocUnits` |
| 0xfb16 | 0xed8 | 100 object records (0x26 each, `object_array` 0x59644) | `UnitsInitGame` at 0x2d511 + `SaveRelocObjects` |

Total 0x109ee bytes.  `SaveLoadImage` accepts an image up to **0x11170**
(0x24949), so a valid file can be up to 0x1119c bytes; the written size is
exactly 0x109ee.

The first 0x56a bytes are the link header: 12-byte identity block + 6 counter
bytes = the 18-byte block `SaveStreamValidate` compares in two-player mode
(0x2424f) and then the 0x550-byte ring + 4 counters.  In single player
`SaveStreamValidate` skips exactly those 0x566 bytes after the 4-byte header
(0x24205) and returns image+0x56a, which is the stream position the loaders
start from: the block at 0x56a is the first one `fn_195ac` reads.

## 3. The load flow

1. `fn_19908`/`fn_1e158` have the slot `FILE *` in `[0x59610]` (left at 0x2c
   by `fn_1498c`) and call `SaveLoadImage(fp)` (0x24940/0x24900).  It seals
   the size (file size - 0x2c), allocates the image, reads it, clears
   `save_reloc_state`'s mode word (0x2490b: load direction) and calls
   `SaveStreamValidate(image)`; the returned position goes to `[0x599b0]`.
2. `fn_195ac([0x599b0])` reads the prefs, scenario and game-state blocks
   through `SaveReadStream` (0x195cf/0x195e0/0x195f1), applies the sound
   prefs and reseeds the RNG (`fn_19470`), then `fn_1b198(position)` reads
   the tile map, map flags, object map (rebasing it) and fog map
   (0x1b358-0x1b39b) and `UnitsInitGame(position)` reads the unit and object
   records, rebases them, and stores the first two object records in
   0x5a7b8/0x5a7b4 (the damage-overlay objects).
3. `SaveFreeImage()` (0x249e0, called at 0x19733) frees the image once
   everything has been copied out.

`SaveReadStream` returns the new stream position (`pos + (count & 0xffff)`)
and decrements `save_stream_left` 0x5a0b0 by the 16-bit count; callers chain
the returned position.  Every offset in section 2 is therefore also the
"bytes left" budget of the load: `0x109ee - consumed`.

## 4. The pointer relocation scheme

Pointers inside the saved records are stored as offsets from a *base* so a
save reloads into whichever address the game allocated this run:

```
save  (mode 1): stored = (ptr == NULL) ? -1 : ptr - base
load  (mode 0): ptr    = (stored == -1) ? NULL : stored + base
```

`RefRelocate(ref, base, to_offset)` 0x248e0 implements it; the mode arrives
as its 16-bit third argument.  The mode word is `[0x5a0b4]`
(`save_reloc_state.w.mode`): `SaveLoadImage` stores 0 (0x2490b),
`SaveWriteImage` stores 1 (0x24bff) before writing the record blocks.  The
relocation call sites read it as a 32-bit value at 0x5a0b2 shifted right 16
(fixup target 0x5a0b2, e.g. 0x24a81), so the linked code has two relocation
targets for one piece of state: 0x5a0b2 for the dword read and 0x5a0b4 for the
word store (whether the original object had two symbols or one symbol with an
addend is not decidable from the linked image).  The database keeps the word
as the high half of `save_reloc_state` (0x5a0b2).

Bases and fields (`SaveRelocUnits` 0x24aa8 for the 0x5c unit records,
`SaveRelocObjects` 0x24b88 for the 0x26 object records,
`SaveRelocObjectMap` 0x24a68 for the 64x64 dword map):

| record | field | base | note |
|---|---|---|---|
| unit, every live record | +0x3a | `unit_array` 0x59640 | related-unit pointer (read as a unit at 0x220b6: flags +0x10, +0x36) |
| unit, type <= 0x1f | +0x42 | `unit_array` | second unit link; the same dword is a tile Point for special object types (0x33..0x35, e.g. 0x22ad9), which are not rebased |
| unit, type <= 0x1f | +0x52 | `unit_array` | target unit (`UnitOrderTarget` 0x2e123, `UnitRemove` 0x2e368) |
| unit, type 0x20..0x32 | +0x46 | 0x50008 | scenario-data link (`and byte [p],0x7f` at 0x2e2de); base is the scenario block's record area, 4 bytes into the block |
| unit, type 0x20..0x32 | +0x58 | `object_array` 0x59644 | damage-overlay object (`UnitUpdateAll` 0x2d267 from 0x5a7b4; drawn by `UnitsDraw` 0x2db68) |
| object | +0x1e, +0x22 | `unit_array` | unit pointers; fn_119c0 hands out free objects (byte +1 bit 0) |
| object map | each dword | `unit_array` | 0 => -1; 64x64 cells indexed y*64+x |

A record whose free flag is set (unit `flags` +0x10 bit 0, object byte +1 bit
0) is skipped completely, so free slots keep their zeros.  For live units the
loader also clears flag bits 0x18 of +0x11 (0x24ad2) and copies the type byte
+0x1b to the type copy +0x1c (0x24ad6), the two fields the death code
maintains (`docs/subsystems/game_2c4e0.md`).

Two asymmetries are in the original and are reproduced: +0x58 is rebased only
for building types (a normal unit's overlay pointer is stale after a load, but
`UnitUpdateAll` recomputes it every tick), and the writer reuses one scratch
buffer per record array, freeing it after each block.

## 5. 0x24860 is not a function

Discovery used to report a function at 0x24860 (128 bytes).  It is an
unreferenced data block, and the 2026-11-18 discovery change
(`tools/wc1/analysis.py`, the stack-balance veto) removed the start:

* bytes 0x24860..0x2487a (26) are data, 0x2487a..0x248e0 (102) are the byte
  0x44 repeated - the only run of eight or more 0x44 bytes in the code
  object, so not compiler alignment filler;
* no call, branch or 32-bit pointer fixup anywhere in the image targets the
  block (`wc1.xref` and `analysis.Program.fix_at` are both empty for it);
* the 26 data bytes XOR 0x64 decode to
  `"warcraft\0cd\0version\0"` followed by `0x11 0x0e 0x12 0x12 0x48 0x00`;
  the 102 filler bytes 0x44 decode to spaces (`' ' ^ 0x64`), so the region
  reads as a space-padded, XOR-obfuscated text buffer;
* the executable never decodes it: no `xor` instruction in the image uses
  the constant 0x64 (the only 0x64 immediates are four `add` stores and one
  `sub`), and no code loads the block's address.

So it is dead data left in the original code object (most likely a leftover
CD/version check buffer from an earlier revision), kept as a `NOTE` in
`analysis/symbols/mod_24860.toml` and pinned by
`tests/test_mod_24860.py::test_unreferenced_block_at_0x24860`.

## 6. Per-function notes and verification status

| function | addr | C file | status |
|---|---|---|---|
| `RefRelocate` | 0x248e0 | `src/mod_24860/ref_relocate.c` | **T3** (`wc1.match` MATCH) |
| `SaveReadStream` | 0x249a4 | `src/mod_24860/save_read_stream.c` | **T3** |
| `SaveLoadImage` | 0x24900 | `save_io_reference.c` | T4, blocker `regalloc` (V2 zero-store registers: original `xor edx,edx` at 0x24908 and `ecx` at 0x24995, OW2 `eax`) |
| `SaveSkipStream` | 0x249c8 | `save_skip_stream.c` | T3 under Watcom 10.0a (2026-11-18); under OW2 T4, blocker `regalloc` (V3: the zero-extended count is ebx in the original, ecx in OW2) |
| `SaveFreeImage` | 0x249e0 | `save_free_image.c` | T3 under Watcom 10.0a (2026-11-18); under OW2 T4, blocker `regalloc` (V2: the null store lives in edx and is pushed/popped, OW2 uses eax) |
| `SaveWriteBytes` | 0x249f8 | `save_io_reference.c` | T4, blocker `codegen` (OW2 keeps the source pointer in edi and needs an ebp frame, reloads `fp->ptr`, one shared error exit missing) |
| `SaveRelocObjectMap` | 0x24a68 | `save_reloc_reference.c` | T4, blocker `codegen` (loop layout: the original pre-tests and duplicates `dec esi; cmp si,-1; jne` at 0x24a73/0x24a9a, OW2 keeps one test and jumps back) |
| `SaveRelocUnits` | 0x24aa8 | `save_reloc_reference.c` | T4, same loop layout + OW2 hoists the mode load; every record operation matches |
| `SaveRelocObjects` | 0x24b88 | `save_reloc_reference.c` | T4, same loop layout; the record body is byte-identical |
| `SaveWriteImage` | 0x24bf0 | `save_image_reference.c` | T4, blocker `regalloc` (scratch-copy pointers and block-address materialisation) |

The T4 evidence is `wc1.cemu.run_pair` with stubbed library functions and the
same globals: the writer test rebuilds the complete 0x109ee-byte image from
the `SaveWriteBytes` calls and compares it byte for byte between the original
and the compiled C (including a failure case that must abort, report
`fn_21c20(0xe)` and finish the slot with error=1).

Source idioms worth keeping if the functions are ever retried:

* `RefRelocate`'s third parameter must be `short` (the original tests `bx`);
  the body stays `int` arithmetic, and the save branch must come first.
* the mode argument is written `save_reloc_state.raw >> 16` with a *signed*
  shift (the original uses `sar`), and the state is declared as a union so the
  same symbol serves the dword read (0x5a0b2) and the word store (0x5a0b4).
* `SaveRelocateUnits` reads the type into a plain `int` local after the first
  `RefRelocate` call: that reproduces the original's promoted compare
  (`xor eax,eax; mov al,[+0x1b]; cmp eax,0x1f; jg`, codegen.md V4).
* `SaveReadStream` needs the `(unsigned short)` casts on every use of
  `count`, which keeps the 32-bit value in esi for the return while the
  memcpy and the subtraction use bx.

## 7. Error paths

* **Header/size**: a file larger than 0x11170 or a short read makes
  `SaveLoadImage` return 0 (freeing the image); `SaveStreamValidate` shows
  *"Saved game uses old version number!"* (0x51e4e via fn_1a914) for a wrong
  record word, and its other checks call fn_1a95c (SAVE.C).
* **Write failure**: any `SaveWriteBytes` returning 1 (fputc reported an
  error) or a failed slot write aborts `SaveWriteImage`; it frees the scratch
  copy, sends `fn_21c20(0xe)` (the packet-layer link error) and calls
  `fn_146cc(fp, 1)`, which closes and *deletes* the partial slot file
  (`remove` at 0x146f3).
* **Checksum**: a mismatch or a missing `'War1'` makes `fn_1498c` close the
  file and treat the slot as unloadable (also `fn_147a8`, the slot-list
  reader, requires `'War1'`).
* **Two-player**: the 18-byte link block at image+4 is compared with the
  live one (`fn_21cb8`) before anything is loaded, and the state machine
  `net_load_state` 0x5a0a2 coordinates the two machines
  (`docs/subsystems/save_score.md` 2.2/2.3).

## 8. Open questions

* The dword at file offset 0x24 is written as 0 and never read.  It may be a
  version or a nonce that the v1.22h code stopped checking (the loader seeks
  over it with `SEEK_CUR`).
* The scenario link field +0x46 uses 0x50008 as its base although the block
  starts at 0x50004; the first dword (`scenario_unit_mask`, status.toml) is
  the scenario's unit mask, so the record area begins at +4.  Whether the
  original source expressed this as two variables or as a struct with a
  header dword is not decidable from the compiled code.
* `SaveWriteBytes` is not the clib `fwrite` (0x3be4c): it avoids the per-byte
  call and reads `fp->cnt` as the number of characters *in* the buffer, the
  1994 watcom convention.  The original source is not recoverable (the
  near miss differs only in scheduling/registers).
* `object_map` 0x58580 and `object_array` 0x59644 are named here because this
  module relocates them; the game areas may want to re-state them.
* Module bookkeeping: the range `mod_24860` in `analysis/modules.toml` still
  starts at 0x24860, which is no longer a discovered function start after the
  2026-11-18 discovery change; the range has to be regenerated (start
  0x248e0, and `SAVE.C` extended to 0x248e0) -- a shared-file change reported
  to the owner, not edited here.
