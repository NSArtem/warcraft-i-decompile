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
