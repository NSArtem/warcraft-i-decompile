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
