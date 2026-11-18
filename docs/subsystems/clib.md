# Watcom C runtime in war.exe (area: clib)

war.exe was linked with Watcom C/C++32 10.x (1994) `clib3r`; only a small part is
byte-identical to Open Watcom 2 (`libsig:` entries in `analysis/symbols/clib.toml`).
The rest was identified from behaviour plus mnemonic-similarity hints
(`python3 -m wc1.clib_near`, output `build/clib/near.txt`; never evidence alone).
Scratch tools: `build/clib/{dumpall,show,libdis,listmods}.py`.

## Extent and layout

The runtime is **not one block**: the linker pulled library modules in reference
order, so they are interleaved with game modules and with other libraries
(resources area, Miles AIL `[0x34d83, 0x3aac0)`, LZSS decoder `0x41530-0x41819`).
Code object `0x10000..0x4212b`:

| Range | Content |
|---|---|
| `0x10003` | `___begtext` (cstart label) |
| `0x30c50-0x30ea0` | memset, _rotl, strncmp, strtol core, strlwr, segread, int386x (clib bits among game code) |
| `0x31789-0x32030` | memcpy, mem_putc, sprintf, _makepath, strcpy, errno accessors, strlen, memcmp, strcat |
| `0x324dd`, `0x331eb-0x34390` | atoi, time(), stdio (fopen, fclose, fputs, fputc, printf, setvbuf, rand, signal/raise/abort, atexit, memset core) |
| `0x34584-0x34860` | `_cstart` (entry), exit-with-message, `__GETDS` |
| `0x3492e-0x349c9` | _dos_getdate/_dos_gettime, _fmemcmp/_fmemcpy, inp/outp, _disable/_enable |
| `0x3ac5c-0x3b58e` | malloc/free, lseek, read, open/sopen, write, filelength, puts, exit/_exit, errno setters, int386x core |
| `0x3b9b1-0x3d6ea` | ftell, fgetc, fseek, fread, fwrite, `__prtf` family, FILE alloc/flush/close, __harderr, mktime, gmtime pieces |
| `0x3d770-0x3e08c` | argv parsing, int 23h/1bh handling, `__CMain`, init/fini routine tables, getenv, strnicmp, strncpy |
| `0x3e0b4-0x3fe34`, `0x3fe34-0x40088` | **not clib**: Miles AIL digital sample conversion tables/mixers (audio) |
| `0x4011a-0x41b77` | heap (`__MemAllocator`, `__MemFree`, DOS/DPMI growth, sbrk/__brk), ioctl/qread/qwrite, itoa family, time/TZ code, stack check, FPE setup |
| `0x41b77-0x42104` | `__FPEHandler` (libsig), `__FPE2Handler`, FPU hooks per DOS extender, x87 detection |

Game wrappers of library calls (retry loops with the abort/retry dialog `0x33520`,
`file seek error (%d)` reporting) are **game code**, not clib: `0x31940` (fclose),
`0x31964` (fopen), `0x31a18` (getc), `0x31a80` (fseek), `0x31adc` (fread),
`0x32558` (GDS malloc with `CHECKSIG` guard bytes), `0x32780` (GDS free, reports
`GDS heap corrupt`), `0x30bf0` (fatal `ERROR:` printf + exit(1)).

## Conventions seen in the library

* FILE is 0x1a bytes: `ptr, cnt, base, flag(dword), handle, bufsize` (flags in
  `$WATCOM/h/stdio.h` values: 0x100/0x200/0x400 buffering, 0x01 read, 0x02 write,
  0x10 eof, 0x20 error, 0x40 binary); `_iob` at `0x555c4` (20 entries).
* errno values are the OW2 ones (EBADF 4, ENOMEM 5, EACCES 6, ENOSPC 12, EDOM 13, ERANGE 14).
* Init/fini routine tables `0x5850c..0x58536` / `0x58536..0x5853c` (6-byte entries).
* Vectors/hooks pointers: `0x56518/0x5651c/0x56520` (exit hooks), `0x56641` (FPE handler).

## Verification

`tests/test_clib_libsig.py` re-checks the `libsig:` entries; `tests/test_clib_difftest.py`
runs ~28 original routines under `wc1.emu` against Python models (strings, memory,
number conversion, strtol, rand, gmtime, sprintf, getenv, _makepath). The emulator
needs `push/pop/mov` of segment registers skipped (flat model), done in the test's trace hook.

## Watcom 10.0a library comparison (2026-11-18)

war.exe's runtime is Watcom 10.0a's (docs/subsystems/compiler.md), so its
patched libraries are the reference: `python3 -m wc1.clib_sig --root
original/watcom/10.0a` (the libraries are an optional part of `make
toolchain`; about 2 minutes).  Result: 191 library units matched, 190
byte-identical (OW2's libraries: 8).  tests/test_clib_libsig.py re-checks
every `libsig:` entry against the library its verified_by names.

Applied to analysis/symbols/clib.toml:

* 175 existing entries got the 10.0a evidence line; those without a
  `verified_by` became `verified` (`libsig: bytes match to clib3r.lib(...)
  ... (N bytes, Watcom 10.0a, clib_sig --root original/watcom/10.0a)`).
* 26 entries were renamed to the library's own names; each keeps a NOTE
  with the old name.  Examples: 0x4091b `__CHK` -> `__STK` (the real `__CHK`
  is 0x40908), 0x3b947 `__delay_impl` -> `__delay`, 0x3b915
  `__delay_calibrate` -> `__delay_init`, 0x3b88e `__clock_ticks` ->
  `clock_value`, 0x3c442/0x3c466 `far_strnlen`/`far_wcsnlen` -> `far_strlen`/
  `far_other_strlen`, 0x42104 `__x87id` -> `__init_80x87`, 0x34815
  `__do_exit_with_msg` -> `__do_exit_with_msg_`.  Older notes and docs
  (discovery.md, the AGENTS.md history) use the old names.
* 12 functions that were in scope as unclassified runtime are now
  clib.toml entries (out of scope, libsig-verified): 0x31c12 `pickup`,
  0x329d0 `strcmp`, 0x33b85 `srand`, 0x33d36 `close_file`, 0x33d9e
  `freopen`, 0x3b0da `__set_binary`, 0x40908 `__CHK`, 0x40ae4
  `_no_support_loaded`, 0x41338 `__parse_tz`, 0x4183c `_chain_intr`,
  0x418b4 `__GrabFP87`, 0x42087 `__init_8087`.  In scope 1034 -> 1022.

Open questions (left as they were, with a NOTE or the evidence line only):

* 0x3d926 is the library's `__terminate_` and 0x3d920 (6 bytes, `call
  [___abort]`, too short to match on its own) the `abort_` of the same
  module `abort`.  The database calls them `__terminate_abnormal` and
  `__terminate`, and already has an `abort` at 0x340a7 (the signal.c
  variant).  Which `abort` war.exe's code actually links needs a look at
  the callers.
* 0x3b439 is the library's `exit_` (byte-identical), but the database's
  `exit` is 0x33f5c, a wrapper with an ebp frame (`push ebp; mov ebp,esp`)
  that runs 0x33ef0 and then calls 0x3b439.  That frame is the DBG style of
  Blizzard's code, so 0x33f5c may be game code, not runtime: moving it back
  into scope needs evidence and the user's approval.
* `__MemAllocator` 0x4011a, `__MemFree` 0x401c2, `__CMain` 0x3def0,
  `__InitRtns` 0x3df40 and `__FiniRtns` 0x3df8b match byte-identically,
  but the library's symbols are undecorated (no trailing `_`) while the
  database gives them the watcall link name.  They keep their previous
  confidence until their `conv` is settled.
* Three matched units are not discovered function starts: 0x10003
  `___begtext`, 0x34838 `__exit_` (the tail `__do_exit_with_msg_` falls
  into) and 0x4036a `__ReAllocDPMIBlock_` (inside a discovered function, so
  discovery missed a start there).  No entries were added for them.

## Unclassified runtime triage (2026-11-19)

`python3 -m wc1.progress` listed 28 runtime-kind function starts that had no
semantic name (the "runtime not yet classified" counter).  Each address was
checked three ways: every 10.0a library unit was compared at the address with
`wc1.clib_sig.Matcher` (`--root original/watcom/10.0a`, not only the automatic
sweep), the callers/branches were listed (`wc1.xref`), and the data/strings it
touches were read.  Result: **12 Watcom 10.0a library functions** (now
`clib.toml`, out of scope), **12 Blizzard functions** and **4 Miles AIL
helpers** (left in scope; two of the 12 Blizzard ones, 0x318f0/0x323e0, were
promoted to T3 by the resources area while this triage ran).  `tests/test_clib_unclassified.py` re-checks the
libsig claims and pins the evidence below.

The library units added here are all shorter than the automatic sweep's
`MIN_UNMASKED`/`MIN_INSNS` thresholds - that is why the sweep had left them
unclassified.  11 get a `libsig:` claim: it rests on the direct byte
comparison (relocation fields resolved) plus the relocation targets named in
each evidence list; `tests/test_clib_unclassified.py` re-checks both, and for
the 6-byte `initrandnext_`/`getpid_` units the test also pins the data symbol
the relocation must name (`_next` / `_psp`), which is what distinguishes them
from the other `mov eax,imm32; ret` units in the libraries.  The 12th
`0x40900` is high, not verified: its unit is anonymous in the 10.0a OMF, so
there is no library link name to put in a `libsig:` line; the test still
re-checks the anonymous `< _TEXT+0>` unit's bytes.

| Address | Disposition | Evidence |
|---|---|---|
| `0x30ddb` | Watcom `strtol` (added, libsig) | byte-identical `clib3r(strtol) strtol_` (8 bytes); signed wrapper (`ecx=1`) of the shared `_stol` 0x30c98 core, the counterpart of `strtoul` 0x30dd1 (`ecx=0`) |
| `0x318f0` | Blizzard `ResourceReadHeaderBodyAt4` (in scope) | resource wrapper over `ResourceRead`; callers 0x13e32, 0x1db2b; the resources area promoted it to T3 concurrently (`resources.toml`, `src/resources/res_header_body_at4.c`) |
| `0x323e0` | Blizzard `ResourceReadHeaderBody` (in scope) | 21 game call sites, reads a 4-byte header then the body; concurrently promoted to T3 by the resources area |
| `0x336e4` | Blizzard `CritErrRegionStart` (proposed) | empty DBG-style unit used only as the start of the range `DpmiLockRegion` locks in `CritErrInstall` 0x33764 (0x3379d -> 0x336e4, size to 0x3374c); no callers |
| `0x3374c` | Blizzard `CritErrRegionEnd` (proposed) | end of that locked range (0x337a2 -> 0x3374c); no callers |
| `0x337d0` | Blizzard `CritErrPromptInit` (proposed) | called once from the main init 0x1dc55; calls `CritErrInstall`, draws "A disk error has occurred..." (0x57ec4) and the Abort/Retry item list (0x55584 -> 0x57ee4/0x57ef0) |
| `0x339d0` | Blizzard `PaletteFadeSetup` (proposed) | copies 3*count bytes `palette_cur` 0x5b060 -> `palette_base` 0x5ad60 and arg -> `palette_target` 0x62570, the start/end arrays `PaletteLerp` 0x34c70 interpolates; no callers (dead in the pulled video object) |
| `0x33b5b` | Watcom `initrandnext` (added, libsig) | byte-identical `clib3r(rand) initrandnext_` (6 bytes); returns the seed address `_next` = 0x555c0, which `rand` 0x33b61 dereferences |
| `0x34060` | Blizzard `DpmiFreeMemoryKB` (proposed) | DPMI int 31h AX=0500h, returns the page count in buffer[+0x10] * 4 = KB; caller 0x1da34 compares with 0x540 = 1344 KB and prints "Warcraft needs an additional %uKB of memory" (0x56e48/0x56ebc) |
| `0x34350` | Blizzard `ResourceReadHeaderBody2` (in scope) | duplicate of 0x323e0 called only from 0x1da34 (0x1db13, 0x1dc72); still low confidence in `resources.toml` |
| `0x3b3a0` | Blizzard `VidResetScreenState` (proposed) | called from the video-init wrapper 0x30bd0 right after `VidAllocBackbuffer`; clears the 32 screen layers at 0x5aa90 (0x240 bytes) and resets `dirty_*` to empty |
| `0x3b438` | Watcom `__null_int23_exit_` (added) | one-byte `ret`; exit-module layout `__null_int23_exit_` +0, `exit_` +1, `_exit_` +0x19 matches 0x3b438/0x3b439/0x3b451, and the exit module's three hook data pointers (`___atexit`/`___int23_exit`/`___FPE_handler_exit`) are initialised to it; war.exe's 0x56518/0x5651c/0x56520 all point to 0x3b438 |
| `0x3b8e9` | Watcom `__clock_init` (added, libsig) | byte-identical `clib3r(clock) __clock_init_` (11 bytes); stores `clock_value()` in `_clock_start` 0x62d70 (the value `__clock` 0x3b8f4 subtracts); init-table entry 0x5850e |
| `0x3d040` | Blizzard `DrawBevelPanel` (in scope) | existing low entry in `graphics.toml`; called twice by 0x337d0; HLine/VLine bevel with `ui_color_base`+9/10/11 |
| `0x3d190` | Blizzard `DrawBevelPanelThin` (in scope) | existing low entry in `graphics.toml`; called by 0x337d0; same two-line bevel without the inner fill loop |
| `0x3d2b0` | Blizzard `CritErrDrawItems` (proposed) | only caller 0x337d0; walks the 0x14-byte item list 0x55584 (bitmap + text, "Abort"/"Retry"), centres each text with `TextWidth`/`DrawText` and copies `default_font` into `cur_font` |
| `0x3d469` | Watcom `getpid` (added, libsig) | byte-identical `clib3r(gtpid) getpid_` (6 bytes: `mov eax,__psp; ret`); relocation target 0x56614 (the DB `_psp`; the library name is `__psp`); called by `__MkTmpFile` 0x338df |
| `0x3dbbf` | Watcom sigsy int-1Bh restore body (added, high) | bytes 0x3dbbf..0x3dc7c are offset +0xf2 of the libsig-verified 431-byte `clib3r(sigsy) __restore_int23_` unit at 0x3dacd (the next unit `__restore_int_` starts at 0x3dc7c); entered by `jne 0x3dbbf` from `__restore_int_ctrl_break` 0x3dc81, not a call |
| `0x3dfda` | Watcom `__null_FPE_rtn` (added, high) | `__FPE_handler` 0x56641 is initialised to 0x3dfda; in `clib3r(crwd386)` the `__FPE_handler`/`___FPE_handler` data slot is initialised to that module's own code offset 0, the one-byte `__null_FPE_rtn` |
| `0x3fe34` | Miles AIL digital-audio helper (third party) | only caller 0x392dd (`ail_dig_timer_service`); touches AIL data 0x56648..0x56664, 0x62ad0 and the table 0x3e2b4 |
| `0x4002a` | Miles AIL sample-format converter dispatch (third party) | callers 0x39322/0x3947e/0x39489/0x39828/0x39833/0x39fd8/0x39fe3, all in `ail_dig_*`; `call [cd_3e0b4 + format*4]` |
| `0x40088` | Miles AIL zero-fill helper (third party) | callers 0x392a2/0x39473/0x3981d/0x39fcd (all AIL); `rep stosb/stosd` over `[sample+0x50]` for `[sample+0x4c]` bytes |
| `0x400b4` | Miles AIL converter-table init/lock (third party) | called by `ail_init_dig_globals` 0x38efc; `DpmiLockRegion`-style `fn_303a8(0x3e0b4, 0x400b4)` and `fn_303a8(0x56648, 0x56668)` |
| `0x40900` | Watcom `_init_stk` (added, high: anonymous unit) | byte-identical to the anonymous first unit of `clib3r(stk386)` `< _TEXT+0>` (8 bytes: `mov [SS_seg],ss; ret`); war.exe target 0x566c4 is the start of the stk386 data segment (`00 00` + "Stack Overflow!\r\n"), and init-table entry 0x58526 points to it.  The source name `_init_stk` is from the module's Open Watcom source (`bld/clib/startup/a/stk386.asm`, local data `SS_seg`) |
| `0x40918` | Watcom `__GRO` (added, libsig) | byte-identical `clib3r(stk386) __GRO` (3 bytes, `ret 4`); module layout `__CHK` 0x40908 (16) / `__GRO` 0x40918 (3) / `__STK` 0x4091b matches `stk386` +8/+0x18/+0x1b |
| `0x410f6` | Watcom `tryOSTimeZone` (added, high) | one-byte `ret` at offset 0 of `clib3r(tzset)`; `tzset_` at +1 (0x410f7, instruction-level libsig, 19 bytes) is the next unit and the module layout is exact.  The 10.0a `tzset_` does not call the stub, so the identity is the layout alone |
| `0x420b8` | Watcom `_fpreset` (added, libsig) | byte-identical `clib3r(chk8087) _fpreset_` (10 bytes); reads `__real87` 0x569bd, jumps to `__init_8087_` 0x42087 |
| `0x42102` | Watcom `_do_nothing` (added, high) | the `___Save8087`/`___Rest8087` data (0x569c8/0x569cc) are both initialised to 0x42102; in `clib3r(save8087)` those two data words are initialised by fixups to that module's only code unit, the one-byte `_do_nothing` |

Open items from this triage (all are changes outside this area's files):

* The 12 Blizzard functions want entries in the area that owns the address
  (`resources.toml` for 0x336e4/0x3374c/0x337d0/0x34350/0x3d2b0,
  `graphics.toml` for 0x339d0/0x3b3a0/0x3d040/0x3d190 and the existing
  `ResourceRead*` entries) with the evidence above; the two resource wrappers
  0x318f0/0x323e0 are already T3 there now.  Until then they stay in scope.
* The four AIL helpers are third-party code inside the module range
  `mod_3df40` (0x3df40-0x400e4), which `analysis/modules.toml` lists as
  `runtime`; moving them out of scope needs that range split (the converter
  table 0x3e0b4-0x3fe34 and the mixers 0x3fe34-0x400b4 are already documented
  as "not clib" in the layout table above).  A `[[func]]` entry in
  `clib.toml` would label them "Watcom runtime", which is wrong.
* Two existing data names are one Watcom symbol short of the 10.0a library
  name: `_psp` 0x56614 is the library's `__psp` (imported by `getpid_`), and
  `_RWD_seed` 0x555c0 is the rand module's static `_next`.  Both entries are
  left untouched here; renaming them is a data-name change with the same
  evidence.
* `0x3dbbf` and the earlier `0x2c228`/shared-block cases show the 2026-11-18
  conditional-tail-jump promotion can create basic-block starts (here from
  `__restore_int_ctrl_break` into the body emitted inside `__restore_int23_`'s
  extent).  Discovery is left alone; the entry records the slice as runtime.
* One discovery gap seen here: the far critical-error handler `CritErrHandler`
  0x336fc is a code-pointer target but not a discovered start (0x336e4's
  extent swallows it); `resources.toml` has an entry for it, so the pipeline's
  start list and the symbol database disagree at that address.
