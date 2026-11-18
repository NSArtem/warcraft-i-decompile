# Resources: DATA.WAR archive and LZSS

Everything below was checked by running war.exe's own code on the real
`DATA.WAR` (`tests/test_resources_lzss.py`, harness `tools/wc1/resources_emu.py`),
and the Python reader `tools/wc1/resources_war.py` agrees with it on all 583
entries (one-off sweep, 2026-10-10; the test uses a 32-entry sample, ~25 s).
Symbol evidence: `analysis/symbols/resources.toml`.

## Archive format (little-endian)

| Offset | Size | Meaning | Evidence |
|---|---|---|---|
| 0 | u32 | version, must equal `archive_version` (0x18, stored by `main` at 0x1e15e) | OpenArchive 0x344b3 |
| 4 | u32 | entry count (583 in DATA.WAR) | 0x344da |
| 8 | u32[count] | file offset of each entry; `0xFFFFFFFF` = absent | 0x344f6, ResourceSeek 0x34553 |
| offset[i] | u32 | header: bits 0..28 unpacked size, bits 29..31 codec id | ResourceBegin 0x318b4-0x318c8 |
| offset[i]+4 | ... | payload (codec 0: raw bytes, codec 1: LZSS) | |

* The game addresses entries by resource id = table index + 2 (`i = (u16)(id-2)`).
* There is no end sentinel: an entry's stored length is `offset[i+1]-offset[i]`
  and ResourceSeek computes `next - start + 1` from `table[i+1]` (the "+1" and
  the header make the value 5 more than the payload length). For the last
  entry it reads one dword past the GdsAlloc'd table (undefined value). The
  length is only reported to the caller through `packed_len` and the decoder
  never uses it (it is bounded by the unpacked size in the header).
* Codec ids present in DATA.WAR: 0 (41 entries, includes the largest ones,
  e.g. id 546, 572199 bytes) and 1 (542 entries). Codec table slots 2..7 are
  empty (null function pointers).
* An absent entry makes the game stop with `demo failure %d` (id as argument,
  string 0x57f48), which is the shareware-stripped-archive behaviour.
* The other `*.WAR` files on the CD (intros, briefings, endings) are FLC
  animations (magic 0xAF12 at offset 4), opened by a different routine
  (0x1933c), not through this layer.

## LZSS (codec 1), exactly as `LzssDecode` (0x41550) does it

* 4096-byte ring buffer `lzss_ring` ([0x5677c], GdsAlloc'd once), zeroed at the
  start of every resource by `LzssReset`; write index starts at 0 (not 0xFEE
  as in the classic Okumura LZSS).
* A flag byte governs 8 items, LSB first (kept in `lzss_flags` as `byte|0xff00`
  and shifted right). Bit 1 = literal byte. Bit 0 = match word (2 bytes,
  little-endian): `src = w & 0xfff` (absolute ring position, **not** a
  distance), `len = (w >> 12) + 3` (3..18). Match bytes are copied one at a
  time (overlap with the write position is allowed); every output byte is also
  stored into the ring at the write index.
* The decoder stops when either the requested count or the remaining unpacked
  size (`res_remaining`, [0x5ad40]) hits zero; a match may be cut off, and its
  remaining length is kept in `lzss_match_left` so a following call continues
  it (tested: random chunk sizes of 1..1000 bytes reproduce the same output).
* Input comes through the C runtime `FILE` of the archive with the getc macro
  inlined (count at +4, pointer at +0, flags at +0xc; the slow path is
  `FileGetc` 0x31a18, the library's retrying wrapper around `fgetc`).
  All archive I/O goes through the wrappers `FileOpen`/`FileSeek`/`FileRead`
  (0x31964/0x31a80/0x31adc): they retry after DOS critical errors via the
  abort/retry prompt (`CriticalErrorPrompt` 0x33520); `FileSeek` instead
  stops with `file seek error (%d)`. They are game-library code, not clib
  (the clib `fseek`/`fread` are 0x3bb86/0x3bc82). The file
  is opened with a 0x4000-byte buffer (0x1d49f).

## Code path

```
main (0x1e158; stores version 0x18 and the version-error pointer)
 ...
OpenDataArchive 0x1d9d4          string refs: "data.war" 0x52541, "data" 0x5254a,
 |                                "path.war" 0x52538, error text 0x56d70
 +- FindDataFile 0x1d410         FileOpen exe_dir\data\data.war, else cd_path\...;
 |                               setvbuf(f, NULL, 0x100, 0x4000)
 +- InitResources 0x34040
     +- OpenArchive 0x34480      version/count/offset table -> archive_offsets
     |    +- (atexit) CloseArchive 0x34440
     +- RegisterCodec 0x3b980    copies lzss_codec_desc 0x565d0 into codec_table[1]
          +- LzssAllocRing 0x41530   (descriptor +1)
          +- (atexit) LzssFreeRing 0x41800  (descriptor +0xd)

per resource (about 65 call sites, see below):
ResourceBegin 0x31870(id, &packed_len)   -> unpacked size
 +- ResourceSeek 0x3452c(id)             table lookup + FileSeek (fatal on absent)
 +- FileRead header; codec -> res_codec 0x5ad44, size -> res_remaining 0x5ad40
 +- codec_table[codec].begin   (call [codec*17 + 0x56529])
      codec 0: StoredBegin 0x409d4 (empty)   codec 1: LzssReset 0x417cc
ResourceRead 0x32740(dest|NULL, count|0)  -> dest (GdsAlloc'd when NULL)
 +- codec_table[codec].decode  (call [codec*17 + 0x5652d])
      codec 0: StoredRead 0x409a0 (FileRead)    codec 1: LzssDecode 0x41550
```

`codec_table` (0x56524, 8 slots of 17 bytes): `{u8 id; alloc; begin; decode; free}`
with `alloc` at +1, `begin` at +5, `decode` at +9, `free` at +0xd. Slot 0 is
static (begin = 0x409d4, decode = 0x409a0); slot 1 is filled by RegisterCodec.

Wrappers that read a small header and then the body of one resource:
`ResourceReadHeaderBody` 0x323e0 and the identical copy 0x34350 (reads 4 bytes
into the struct, then the rest to `struct+4`), `ResourceReadHeaderBodyAt4` 0x318f0.

## Function list

| Address | Name | Confidence |
|---|---|---|
| 0x1d9d4 | OpenDataArchive | high |
| 0x1d410 | FindDataFile | medium |
| 0x34040 | InitResources | high |
| 0x34480 | OpenArchive | high |
| 0x34440 | CloseArchive | high |
| 0x3b980 | RegisterCodec | high |
| 0x3452c | ResourceSeek | verified (difftest) |
| 0x31870 | ResourceBegin | verified (difftest) |
| 0x32740 | ResourceRead | verified (difftest) |
| 0x41550 | LzssDecode | verified (difftest) |
| 0x417cc | LzssReset | verified (difftest) |
| 0x409a0 | StoredRead | verified (difftest) |
| 0x41530 / 0x41800 | LzssAllocRing / LzssFreeRing | verified (match) |
| 0x409d4 | StoredBegin | verified (match) |
| 0x323e0 | ResourceReadHeaderBody | verified (match) |
| 0x318f0 | ResourceReadHeaderBodyAt4 | verified (match) |
| 0x34350 | ResourceReadHeaderBody2 (identical copy of 0x323e0) | low (no C) |
| 0x31940 | FileClose | verified (match) |
| 0x31964 | FileOpen | verified (match) |
| 0x319c4 | FileTell | verified (match) |
| 0x31a18 | FileGetc | verified (match) |
| 0x31a80 | FileSeek | verified (match) |
| 0x31adc | FileRead | verified (match) |
| 0x31b54 | FileWrite | verified (match) |
| 0x32540 | GdsOutOfMemory | verified (match) |
| 0x32558 | GdsAlloc | verified (match) |
| 0x32780 | GdsFree | verified (difftest, T4) |

The GDS names/evidence live in `analysis/symbols/graphics.toml` (that file
already owned the addresses); the C is in `src/resources/gds_*.c` and is
tested by `tests/test_resources_files.py`.

## Callers of ResourceBegin (0x31870) by function

Functions are listed by address only; naming them belongs to their areas. A
constant resource id loaded into `eax` just before the call is shown with the
decoded content kind (heuristic, `resources_war.guess_kind`), otherwise the id
is computed. Ids are resource ids (archive index + 2).

| Caller | Call sites (id) |
|---|---|
| 0x13dfc | 0x13e23 (computed); also calls wrapper 0x318f0 at 0x13e32 |
| 0x1599c | 0x159d1; wrapper 0x323e0 at 0x159dd |
| 0x16694 | 0x1669d; ResourceRead 0x166b0 |
| 0x168b4 | 0x1692e; wrapper 0x323e0 at 0x16937 |
| 0x1806c | 0x18074 (0xf5 = 245, 41604 bytes); wrapper 0x323e0 |
| 0x18b64 | 0x18b8b (0x1ce, 99855 bytes, the largest LZSS entry), 0x18c41 (0x1cb palette), 0x18d82 (0x1d3, 2020 bytes) |
| 0x195ac | 0x1966b |
| 0x1ade4 | 0x1ae11 (0x101 palette) |
| 0x1b198 | six sites 0x1b289..0x1b3c9 (computed) |
| 0x1c2bc | 0x1c2d5 |
| 0x1c300 | 0x1c4a4 (computed), 0x1c4dd/0x1c554/0x1c5cb/0x1c650/0x1c6c7/0x1c73e/0x1c7b8 (ids 0x1ab..0x1b1, 9-58 KB) |
| 0x1cb90 | 0x1cbab, 0x1cc60 |
| 0x1da34 | 0x1daef (0x106 palette), 0x1db07 (0xd7), 0x1db1f (0x109), 0x1dc66 (0xd8); wrappers 0x318f0 / 0x34350 |
| 0x1e020 | 0x1e05b (0xdb palette) |
| 0x1f854 | 0x1fa2d, 0x1fa5e (both 0xd9) |
| 0x21d0c | 0x21d27; wrapper 0x323e0 |
| 0x234a0 | 0x234af |
| 0x23ae0 | 0x23b18 (0x106 palette), 0x23b44 (0x107, 64004 bytes = 320x200 image + 4-byte header), 0x23beb (0x108 palette), 0x23c03 (0x106) |
| 0x26320 | 0x26328 (0xd6) |
| 0x26784 | 0x267b9 |
| 0x267fc | 0x268b0 |
| 0x29120 | 0x2914f (0x16b), 0x29181, 0x2919b..0x291fb (0x16c-0x16f, 0x19a, 0x19b), 0x29236, 0x2924e (0x19c) |
| 0x2b4b8 | 0x2b4f2, 0x2b515, 0x2b538, 0x2b550 (0x198), 0x2b568 (0x199) |
| 0x2b8e0 | 0x2b8ea |
| 0x2c3f0 | 0x2c437 (0x106 palette) |
| 0x2fcfc | 0x2fd6a, 0x2fdfc (0x1a2 palette), 0x2fe1e (0x1a4 palette), 0x2fe37 (0x1a3) |

ResourceRead (0x32740) is additionally called from the wrappers 0x318f0,
0x323e0 (21 callers: 0x1599c, 0x168b4, 0x1806c, 0x21d0c, 0x23ae0, 0x29120 x8,
0x2b4b8 x5, 0x2fcfc, and 0x318f0), 0x34350 (called from 0x1da34).

## Not yet known

* What reads or fills the 12-byte entries (ids 208, 210, 211: LZSS of 12
  bytes, tiny: probably small tables) is left to the callers' areas.
* Whether other `*.WAR` readers share the FILE-stream buffering; they use a
  different routine (0x1933c) and are not part of this layer.
* ResourceSeek (0x3452c) does not match OW2 `wcc386 -ot` output: the original
  has a frame pointer and uses edi where OW2 uses esi/ecx. See
  `src/resources/war.c` for the (behaviour-equivalent, non-matching) C.

## 3. Reconstructed C and its T4 difftests

> **Watcom 10.0a (2026-11-18).**  With the original compiler
> (docs/subsystems/compiler.md) six of the ten functions below are T3 and built
> from C, one function per file: LzssReset (`lzss_reset.c`), LzssFreeRing
> (`lzss_free_ring.c`), RegisterCodec (`codec.c`), CloseArchive
> (`close_archive.c`), ResourceRead (`resource_read.c`) and StoredRead
> (`stored.c`), each with `codegen-compiler: 10.0a` and the area's DBG flags.
> Their T4 tests below still run against the same C.  LzssDecode, ResourceSeek,
> OpenArchive and ResourceBegin stay reference C (they mismatch under 10.0a
> too).  The "remaining T3 difference" column is the OW2 history.

The LZSS functions, `RegisterCodec` and `ResourceSeek` have reference C
(`src/resources/{lzss,codec,war}.c`); every one is a register-assignment or
operand-order near miss (no `src =`), so they carry
`ref_verified_by = "difftest: tests/test_resources_lzss.py::test_*"` in
`analysis/symbols/resources.toml` and a `t3_blocker`:

| function | address | T4 test | the remaining T3 difference |
|---|---|---|---|
| LzssDecode | 0x41550 | `test_lzss_decode_c_matches_original` | dest pointer in ecx vs ebx at +0x8 (V3) |
| LzssReset | 0x417cc | `test_lzss_reset_c_matches_original` | zero constant in eax vs edx at +0x6 (V2) |
| LzssFreeRing | 0x41800 | `test_lzss_free_ring_c_matches_original` | save set/zero constant at +0x0 (V2) |
| RegisterCodec | 0x3b980 | `test_register_codec_c_matches_original` | id in ecx vs ebx at +0x0 (V3) |
| ResourceSeek | 0x3452c | `test_resource_seek_c_matches_original` | id kept in esi, address folding at +0x8 (V3/V5) |
| OpenArchive | 0x34480 | `test_open_archive_c_matches_original` | fatal-argument register at +0x3c (V3) |
| CloseArchive | 0x34440 | `test_close_archive_c_matches_original` | save set at +0x3 (V3) |
| ResourceBegin | 0x31870 | `test_resource_begin_c_matches_original` | header split spelling at +0x34 (V2/V3) |
| ResourceRead | 0x32740 | `test_resource_read_c_matches_original` | dest pointer in ecx vs ebx at +0x6 (V3) |
| StoredRead | 0x409a0 | `test_stored_read_c_matches_original` | fatal-argument register at +0x21 (V3) |

The tests run the original and the compiled C on the same inputs under
`wc1.cemu`: the reset/free/register tests compare the written globals and the
stub calls (GdsFree argument, the codec alloc hook, the atexit argument); the
decoder test decodes real DATA.WAR entries through `ArchiveEmu` with the
original `ResourceBegin` positioning the stream for each run, and also with a
match split across chunked calls; the seek test compares the return value,
the modelled FILE position and the `demo failure %d` fatal path.

The archive functions use the same `ArchiveEmu` stdio models:
`test_open_archive_c_matches_original` compares the entry count, the offset
table and the version-mismatch fatal (fresh identical archive images for the
two runs), `test_close_archive_*` the FileClose/GdsFree calls and the cleared
globals, `test_resource_begin_*` the packed length, the header split
(size/codec), the codec-begin side effects (the LZSS reset) and the returned
unpacked size, `test_resource_read_*` the decoded bytes for both codecs with
and without the `dest == 0` allocation, and `test_stored_read_*` the copied
bytes, the unpacked-bytes counter and the `data file error` short-read fatal.
`src/resources/archive.c` uses `-zp1` because the 17-byte codec descriptor is
packed.


## 4. File I/O: the `FILE` record and the wrappers (0x31940..0x31bca)

Everything the game does to a file goes through seven thin wrappers in the
library object 0x31940..0x31bca over the Watcom clib stream functions. They
exist for one reason: the game runs in DOS real mode under DOS/4GW, so a disk
error (drive door open, bad sector) raises INT 24h; the wrappers detect that,
show an abort/retry box and repeat the call instead of failing the load.
All seven are T3 (Watcom 10.0a, `src/resources/file_*.c`).

### The `FILE` record

The stream pointer they take is Watcom 10.0a's `FILE` (`struct __iobuf`,
`original/watcom/10.0a/h/stdio.h`), 4-byte fields on the 32-bit target:

| Offset | Field | Meaning |
|---|---|---|
| +0x00 | `_ptr` | next character in the buffer |
| +0x04 | `_cnt` | characters left in the buffer |
| +0x08 | `_base` | buffer base |
| +0x0c | `_flag` | mode: `_READ` 1, `_WRITE` 2, `_UNGET` 4, `_EOF` 0x10, `_SFERR` 0x20, ... |
| +0x10 | `_handle` | DOS file handle |
| +0x14 | `_bufsize` | buffer size |
| +0x18/+0x19 | `_ungotten`, `_tmpfchar` | ungetc byte, tmpfile number |

The game's own code reads that record directly where speed matters: the
inlined `getc(archive_file)` in `LzssDecode` (0x41586-0x415c5) tests
`_cnt > 0` (+4) and `!(_flag & _UNGET)` (+0xc), takes the byte at `_ptr`
(+0) and bumps `_ptr`/drops `_cnt`. It is the 10.0a `getc` macro
(`original/watcom/10.0a/h/stdio.h`), which also routes a next byte of 0x0d or
0x1a to the real `fgetc` unconditionally; that slow path is `FileGetc`
(0x415ab). The archive is opened "rb" (mode string 0x56c88), so those bytes
come back normally from `fgetc`. `FindDataFile` gives the archive a
0x4000-byte buffer (`setvbuf` call 0x33de1 at 0x1d49f), so most reads never
reach the wrapper.

### The wrappers

| Address | Function | Clib callee | Failure policy |
|---|---|---|---|
| 0x31940 | `FileClose` | `fclose` 0x33887 | none - returns `fclose`'s value (the result is not copied to a temporary, the source discards it) |
| 0x31964 | `FileOpen` | `fopen` 0x33d2c | retry after `CriticalErrorPrompt`, unless `file_open_noprompt` (0x61ea2) is set (optional-file probe) or the handler never fired |
| 0x319c4 | `FileTell` | `ftell` 0x3b9b1 | retry if the position is -1 **or** the handler fired |
| 0x31a18 | `FileGetc` | `fgetc` 0x3b9e1 | save the position with `FileTell`, retry: prompt, `FileSeek(pos, 0)`, read again |
| 0x31a80 | `FileSeek` | `fseek` 0x3bb86 | **no retry**: clears `errno`, and a -1 result is fatal (`file seek error (%d)\n`, 0x57e6c) |
| 0x31adc | `FileRead` | `fread` 0x3bc82 | retry when the item count differs **and** the handler fired; rewind to the saved position first |
| 0x31b54 | `FileWrite` | `fwrite` 0x3be4c | same as `FileRead` |

The protocol, with the addresses:

* `CritErrHandler` 0x336fc is the `_harderr` INT 24h handler: it sets
  `crit_error_flag` (0x61ea0) and calls `_hardresume(_HARDERR_FAIL)`, so the
  failing DOS call returns an error to the clib. `CritErrInstall` 0x33764
  registers it and DPMI-locks the flag (the handler writes it from an
  interrupt).
* Every retrying wrapper stores `crit_error_flag = 0` immediately before the
  clib call (0x31977, 0x319d5, 0x31a34, 0x31afe, 0x31b76) and tests it after,
  which distinguishes "file not found / EOF" from "the handler fired".
  `FileClose` has no error policy (it just closes); `FileSeek` uses `errno`
  instead of the flag.
* When it fired, `CriticalErrorPrompt` 0x33520 saves the screen strip, draws
  "Press 'A' to abort program or 'R' to retry." and waits for a key (`A` exits
  through 0x33f5c). Returning from it means the user chose retry, and the
  wrapper repeats the call - seeking back first for anything that had already
  consumed input (`FileGetc`, `FileRead`, `FileWrite`).
* `file_open_noprompt` 0x61ea2 is a nesting counter raised by `LoadFile`
  (0x1d370), `FindDataFile` (0x1d44b) and 0x1d2a0 around `FileOpen`, so
  probing for optional files (PATH.WAR, save slots) never pops the box.
* `FileSeek` is the exception: the position cannot be "retried" meaningfully,
  so a failed seek is fatal (the message is a 22-byte CONST string; the
  `(%d)` argument is the clib `errno`, cleared just before the call through
  `__get_errno_ptr`).

Codegen: this object is compiled *unoptimized with debug info*
(`-s -od -4r -zp2 -d1+`), so every parameter is homed in a stack slot
(`[ebp-0x10]`, ...) and locals are allocated in reverse declaration order -
`FileGetc` has to declare `int c;` before `long pos;` to get `pos` at
[ebp-8] and `c` at [ebp-0xc]. `FileOpen`'s OR chain compiles to three
separate compares with an early return (0x3198e-0x319b0).
`tests/test_resources_files.py` re-runs `wc1.match` on every file and models
the retry/quiet-probe behaviour with the original code under `wc1.emu`
(`fopen` and `CriticalErrorPrompt` stubbed).

## 5. The GDS heap (0x32540..0x32800)

"GDS" (`GdsAlloc` 0x32558, `GdsFree` 0x32780, `GdsOutOfMemory` 0x32540) is
**not** a DOS memory allocator and has **no free list, no first-fit scan and
no size field**. It is a checked wrapper around the Watcom clib
`malloc`/`free` (0x3ac5c / 0x3ad3f, both byte-identical to the 10.0a
`clib3r.lib`, `wc1.clib_sig`): every block gets an 8-byte signature at each
end so that a buffer overrun or an underrun is caught at `free` time instead
of corrupting the clib heap silently. The actual allocation policy (the
`__MiniHeapRover`/`__nheapbeg` first-fit scan and `__ExpandDGROUP` growth) is
inside `malloc` (0x3ac5c, body 0x3ac7c..0x3ad30) - see
`analysis/symbols/clib.toml`.

Block layout (all offsets from the pointer `malloc` returns; `n` = requested
size):

```
+0x00  "CHECKSIG"            8-byte head guard
+0x08  void *tail             -> +0x0c+n (the tail guard)
+0x0c  user data             n bytes; GdsAlloc returns this address
+0x0c+n "CHECKSIG"           8-byte tail guard
```

so every allocation costs `n + 20` bytes.

* `GdsAlloc(size)` (0x32558): `p = malloc(size + 0x14)`; on NULL it calls
  `gds_nomem_handler` (0x55440, initialised with `GdsOutOfMemory`, so the game
  stops with "out of memory" 0x57e94); it writes the signature to the tail
  guard and copies it to the head (8 chained `p[i] = tail[i] = <sig char>`
  assignments at 0x32578-0x325c2, one byte per signature character), stores
  the tail pointer at +8 and returns `p + 12`. The source spelling matters for
  T3: `tail = p + (size + 12)` is compiled as `lea eax,[ebx+0xc]; add
  eax,edx`, while the unparenthesised `p + size + 12` folds into a
  three-operand `lea` and does not match.
* `GdsFree(p)` (0x32780): `b = p - 12`, `tail = *(void **)(b + 8)`, then both
  guards are compared byte by byte with "CHECKSIG" (16 compares, 0x32797-
  0x3284f). A mismatch executes `int 3` (0x32851, an inline `#pragma aux`
  trap, the same idiom as 0x23cf4 and 0x216f0) and calls
  `FatalError("GDS heap corrupt")` (0x57ea4). On the healthy path both guards
  are overwritten with "GISKCEHC" (the reversed signature, so a double free or
  a use after free is caught the same way) and `free(b)` releases the raw
  block.
* The ~40 allocation and ~60 free sites are listed in
  `analysis/symbols/graphics.toml`; `ResourceRead`'s `dest == NULL` case
  (0x3275c) and `OpenArchive`'s offset table (0x344ec) are among them.

Status: `GdsAlloc` and `GdsOutOfMemory` are T3 (`src/resources/gds_alloc.c`,
`src/resources/gds_out_of_memory.c`, `-s -ot -ol -4r -d1+ -zp2`).
`GdsFree` is T4 reference C (`src/resources/gds_free.c`): the
original allocates a 4-byte frame slot and stores the parameter, then the
computed block pointer, into it (`sub esp,4; mov [ebp-4],eax; lea
edi,[eax-0xc]; mov [ebp-4],edi`), and 10.0a keeps the pointer in `edi` with no
slot for every plausible spelling tried (single local, parameter
reassignment, two locals, struct-pointer decrement; `-od`, `-d1+`, `-d2`
grids). First difference at +0x8. `tests/test_resources_files.py` difftests
it with `wc1.cemu`: healthy block and corrupted guard (int3 + fatal message +
the poisoned bytes) give identical results.
