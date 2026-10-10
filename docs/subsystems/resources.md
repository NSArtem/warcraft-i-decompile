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
  entry it reads one dword past the malloc'd table (undefined value). The
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

* 4096-byte ring buffer `lzss_ring` ([0x5677c], malloc'd once), zeroed at the
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
  inlined (count at +4, pointer at +0, flags at +0xc; the slow path 0x31a18
  handles an empty buffer and, for non-binary streams, CR/^Z bytes). The file
  is opened with a 0x4000-byte buffer (0x1d49f).

## Code path

```
main (0x1e158; stores version 0x18 and the version-error pointer)
 ...
OpenDataArchive 0x1d9d4          string refs: "data.war" 0x52541, "data" 0x5254a,
 |                                "path.war" 0x52538, error text 0x56d70
 +- FindDataFile 0x1d410         fopen exe_dir\data\data.war, else cd_path\...;
 |                               setvbuf(f, NULL, 0x100, 0x4000)
 +- InitResources 0x34040
     +- OpenArchive 0x34480      version/count/offset table -> archive_offsets
     |    +- (atexit) CloseArchive 0x34440
     +- RegisterCodec 0x3b980    copies lzss_codec_desc 0x565d0 into codec_table[1]
          +- LzssAllocRing 0x41530   (descriptor +1)
          +- (atexit) LzssFreeRing 0x41800  (descriptor +0xd)

per resource (about 65 call sites, see below):
ResourceBegin 0x31870(id, &packed_len)   -> unpacked size
 +- ResourceSeek 0x3452c(id)             table lookup + fseek (fatal on absent)
 +- fread header; codec -> res_codec 0x5ad44, size -> res_remaining 0x5ad40
 +- codec_table[codec].begin   (call [codec*17 + 0x56529])
      codec 0: StoredBegin 0x409d4 (empty)   codec 1: LzssReset 0x417cc
ResourceRead 0x32740(dest|NULL, count|0)  -> dest (malloc'd when NULL)
 +- codec_table[codec].decode  (call [codec*17 + 0x5652d])
      codec 0: StoredRead 0x409a0 (fread)    codec 1: LzssDecode 0x41550
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
| 0x41530 / 0x41800 | LzssAllocRing / LzssFreeRing | high |
| 0x409d4 | StoredBegin | medium |
| 0x323e0, 0x34350, 0x318f0 | header+body wrappers | low |

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
