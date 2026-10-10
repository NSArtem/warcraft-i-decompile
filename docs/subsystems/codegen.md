# Codegen: which compiler configuration reproduces war.exe

Question: why does Open Watcom 2 `wcc386 -q -zl -bt=dos -s -ot` match only `InitPaths`, and what
configuration (flags, source style, compiler) would match more?  Everything here is reproducible
with the tools listed at the end; "match" means the same thing as in `docs/METHODOLOGY.md` T3
(code bytes, relocations and module-local data identical), checked either by `wc1.match` or by
`wc1.codegen_sweep` (same checks, no symbol database needed).

## Summary

1. **war.exe is not one codegen style but three** (plus third-party code), and they follow object
   boundaries, not the "game" / "library" split of `analysis/modules.toml`:

   | Style | What the bytes look like | Where | OW2 can reproduce it? |
   |---|---|---|---|
   | **OPT** | optimised, no frame pointer, minimal register save set, short jumps | 851 of 880 "game" functions, the Watcom C runtime, parts of the video/input library, AIL | **yes** with `-s -ot -ol -4r -zp2` (+ source idioms, section 4); some functions are blocked by register-allocation differences |
   | **DBG** | optimised *body* inside a standard frame `push <saves>; push ebp; mov ebp,esp; [sub esp,N]` ... `[mov esp,ebp] pop ebp; pop <saves>` | 78 functions of the video/input/resource library (67 `runtime`, 11 `resource` kind), 7 game functions that have stack locals or varargs | **yes** with the OPT flags plus **`-d1+`** |
   | **OD** | unoptimised: all six registers saved, `mov ebp,esp`, `sub esp,<exact locals>` as imm32 (also `sub esp,0`), locals/params live on the stack, short jumps | 54 functions: 22 at 0x26b18..0x27661 (sound layer above AIL), 14 in EVT/VID (0x30ea0..0x31789), 18 in file wrappers, key state and retry loops (0x31940, 0x32a80, 0x33520) | **no**: OW2 `-od` differs in 4 systematic ways (section 3) |
   | LEAVE | `push ebp; mov ebp,esp ... leave` | 17 functions of Miles AIL | not Watcom output, not a target |

2. **The default `-s -ot` is only part of the answer.**  Adding `-ol -4r -zp2` keeps `InitPaths`
   matching and fixes loop shape, byte-load idiom (`xor r,r; mov rl,[m]` instead of `movzx`), the
   `shl/sub` multiplications and structure packing.  `-d1+` adds the DBG frame style.  Per-file flags
   are needed because the original mixes styles object by object.
3. **20 functions match in 16 files** (`src/codegen/`, plus `InitPaths`); 12 of them (`TrimAtWhitespace`,
   `SndPlay`, `SndPlayLooped`, `SndStop`, `SetUiColorBase`, `DirtyRectAddBox`, `InitResources`,
   `StoredBegin`, `TextSetColorBase`, `TextSetEscapeColors`, `LzssAllocRing`, `VidAllocBackbuffer`)
   are T3-verified by `wc1.match` and built from C, the others (game code) by
   `wc1.codegen_sweep` (same byte/relocation/data checks, with a name-to-address consistency check
   instead of the symbol database, because callees/data are unnamed there).  3 more functions are
   documented near misses.
4. The residual differences are **backend differences** (register assignment order, constant
   propagation, store forwarding, multiply decomposition, `-od` frame bookkeeping), not flags: the
   original was built by a Watcom 9.5/10.x `wcc386`, OW2 descends from 11.x.  Where the difference is
   only a missed optimisation in the original, a source idiom (`volatile`, a local copy) can steer OW2;
   register-assignment differences cannot be steered.  Section 6 gives the recommendation.

## 1. Survey: `python3 -m wc1.codegen_survey` (-> `build/codegen/survey.txt`, `functions.tsv`)

Per function: leading `push` run, frame (`push ebp; mov ebp,esp`), `sub esp,N` with its encoding
(imm8 / imm32), epilogue form, stack check, jump encodings (rel8 / rel32 / rel32-but-shortable),
start alignment and filler.  All 1704 discovered functions were classified.

Facts that hold for the whole image:

* **No stack checks**: no function starts with `cmp esp,[limit]`; `__CHK` (0x4091b) has one caller
  (the clib's own `stackavail`).  So `-s` everywhere.
* **No x87 instructions** outside the FPE runtime (0x41aa8..0x42130): `-fpi/-fp3/-fpi87` cannot be tested
  or discriminated; the game is integer-only.
* Functions are 4-byte aligned with `mov r,r` / `lea r,[r+0]` / `nop` filler, like OW2 `-ot`.
* Style by module kind (counts of functions):

  | kind | n | OPT | DBG | OD | LEAVE |
  |---|---:|---:|---:|---:|---:|
  | game | 880 | 851 | 7 | 22 | 0 |
  | gfx (flic, evt/vid) | 27 | 13 | 0 | 14 | 0 |
  | resource | 31 | 20 | 11 | 0 | 0 |
  | runtime | 573 | 485 | 67 | 18 | 3 |
  | ail | 155 | 137 | 1 | 0 | 17 |
  | asm, asm-shared | 38 | 38 | 0 | 0 | 0 |

  (OD = frame with `sub esp,imm32` although the value fits imm8; DBG = other ebp frames; a frame with
  `sub esp,>=128` needs imm32 anyway and counts as DBG.  The 7 DBG "game" functions are 0x18b64,
  0x1a9a4, 0x1c300, 0x269f0 and 0x2fcfc, which all have stack locals (44, 4, 880, 268 and 812
  bytes), plus 0x30bd0 (a video-init wrapper calling `VidAllocBackbuffer`) and `FatalError` 0x30bf0
  (variadic), which are library objects that `modules.toml` classes as game.)
* **Near jumps that would fit short**: 110 functions (106 in game code) contain a `jcc/jmp rel32`
  whose target is within rel8 range, typically 1..4 bytes short of the limit (e.g. 0x10664, 0x11352).
  A one-pass sizing of forward jumps, not a flag; OW2 `-ot` output matched in all samples so far,
  so it is not a problem in practice.

### Style map of the code object (consecutive runs; tiny bare leaves are neutral)

Game code (0x10010..0x30246) is OPT throughout except five single DBG functions (0x18b64, 0x1a9a4,
0x1c300, 0x269f0, 0x2fcfc) and the OD run 0x26b18..0x27661; the
video/input library and the C runtime interleave from 0x30bd0 to 0x34d83 and the OPT runs there are
the Watcom clib objects (the video library objects are DBG/OD/OPT):

| Range | Style | functions | modules.toml |
|---|---|---:|---|
| 0x10010-0x269e6 | OPT (except DBG 0x18b64, 0x1a9a4, 0x1c300) | ~670 | asm_blit_tiles .. SND.C |
| 0x269f0-0x26b18 | DBG | 1 | mod_269f0 |
| 0x26b18-0x27661 | **OD** | 22 | mod_269f0 |
| 0x27670-0x2fcfb | OPT | 216 | SPELL.C .. mod_2efd0 |
| 0x2fcfc-0x30246 | DBG (880+ bytes of locals) | 1 | mod_2efd0 |
| 0x3024e-0x30bc9 | OPT | 18 | asm_shared_helpers |
| 0x30bd0-0x30c4d | DBG | 2 | mod_30bd0, error_fatal |
| 0x30c50-0x30e9d | OPT | 11 | rt_misc_asm (clib) |
| 0x30ea0-0x30fdf, 0x312d8-0x31789 | **OD** | 15 | gfx_evt_vid, mod_31784 (EVT*/VID* of the Insider's Guide) |
| 0x30fe0-0x312d5 | OPT | 2 | gfx_evt_vid |
| 0x317b0-0x3193d | DBG | 4 | mod_317b0 .. mod_31920 |
| 0x31940-0x31bcf | **OD** | 8 | mod_31940 (fclose/fopen/getc/fseek/fread wrappers) |
| 0x31bcf-0x31d33 | OPT | 8 | mod_31940 (clib: sprintf, strcpy, strlen, ...) |
| 0x31d40-0x31dcc, 0x31f70, 0x31fc0, 0x320f0-0x324dd, 0x32540-0x329c8 | DBG | ~21 | mod_31d40 .. mod_32970 |
| 0x32a80-0x32e7b | **OD** | 5 | mod_32a80 (Key* helpers) |
| 0x32e80-0x331eb, 0x33220-0x33512, 0x339d0-0x33b41 | DBG | 16 | mod_32e80 .. mod_33b00 |
| 0x33520-0x33887 | **OD** | 6 | mod_33520 (retry loops with the abort/retry prompt) |
| 0x33ef0-0x33f75, 0x34040-0x340b1, 0x34260-0x3438a, 0x34440-0x34583, 0x34860-0x3492d, 0x349f0-0x34d83 | DBG | 21 | mod_33ef0 .. mod_34c70, res_init, res_archive |
| 0x34d83-0x3aaac | OPT (137), LEAVE (17), DBG (1) | 155 | Miles AIL |
| 0x3aac0-0x3ac5c, 0x3b181-0x3b3f4, 0x3b360, 0x3b980, 0x3cb10-0x3cce5, 0x3d040-0x3d369, 0x3def0, 0x400e4, 0x409a0, 0x41530-0x4181e | DBG | ~25 | video lib (HLine, GrpFrameInfo, VidAllocBackbuffer, RegisterCodec, RectCopy*, DrawTextCentered, ...), StoredRead, LZSS |
| everything else 0x3ac5c-0x42104 | OPT | ~560 | Watcom clib |

The full run table is in `build/codegen/survey.txt` (86 runs).  Observations for the modules area:

* A "module" is one object file and has one style.  The run map shows the `runtime` kind modules
  containing both library (DBG/OD) and clib (OPT) objects (e.g. `mod_3ac10`: HLine/GrpFrameInfo DBG,
  then malloc/free/lseek/open OPT at 0x3ac5c; `mod_33b00`: DBG blit at 0x33b00 then OPT memset/rand/
  fopen/printf from 0x33b41; `mod_31940`).  The OPT -> DBG/OD switches are real object boundaries.
* The video library therefore consists of several objects compiled with **different flags**
  (`-d1+` objects: primitives, palette, layers, dirty rects, resource archive; `-od` objects:
  EVT/VID, file wrappers, key state, the retry loops) -- the "separately compiled library with other
  flags" suspected in the task, at object granularity.
* 0x269f0 (`mod_269f0`) starts with a DBG function (268 bytes of locals) and then runs OD; the
  boundary is probably 0x26b18, i.e. the sound layer proper starts there.

## 2. Flag sweep (OW2 wcc386, 2026-04-11 build)

Tools: `codegen_sweep` (compile a C file under flag sets, compare every function), `codegen_flags`
(ablation over `src/codegen/`, writes `build/codegen/flags.txt`), `codegen_refs` (the three non-matching
reference files, writes `build/codegen/refs.txt`), `codegen_search` (greedy search).  Samples are the
files in `src/codegen/` (20 matching functions) plus ~60 exploratory functions.

### Per-flag effect

| Flag | Effect on the samples |
|---|---|
| `-s` | required (stack checks); original has none |
| `-ot` | required over `-ox`/`-os` (`-ox` = `-obmiler -s`): `-ox` breaks `TrimAtWhitespace`, `fn_12cd4`, `fn_15558` (inlines `strcpy`), `TextSetColorBase`, `SndPlay*`; `-os` breaks `TrimAtWhitespace`, `fn_12cd4`, `SndPlay*` (smaller compare/loop forms) |
| `-ol` | needed by `TrimAtWhitespace` only: rotates `while(*s)` into test-at-top + test-at-bottom like the original. The original's `for(i=0;i<10;i++)` loops are *not* rotated, which no OW2 mode reproduces |
| `-4r` (or `-5r`) | required: on 486+ OW2 avoids `movzx` (`mov al,[m]; and eax,0xff`, `xor edx,edx; mov dl,..`) and decomposes `x*127` as `shl 7; sub` exactly like the original.  `-3r` and `-6r`/default break `fn_12cd4`, `SndPlay*`, `TrimAtWhitespace`.  `-4r` and `-5r` agree on every sample; `-4r` is weakly preferred: the original uses `lea r,[r+r*2]` (x*3) six times, which `-5r` replaces with `shl/sub` |
| `-zp2` | structure packing: `fn_15558` needs the field at +0x16: `-zp1` and `-zp2` match, `-zp4`/`-zp8` (OW2 default) break it. 558 dword accesses in game code sit at offsets = 2 mod 4, so the packing is 2 (Watcom's own default); PACKET.C (0x214b0..0x21cf0) has dwords at offsets 1 and 3 (0x2176c, 0x21726, 0x21663), i.e. `#pragma pack(1)` there |
| `-d1+` | **produces the DBG layout**: `push edx; push ebp; mov ebp,esp ... pop ebp; pop edx`, stack args via `[ebp+8]`, `push <saves>; push ebp; mov ebp,esp; sub esp,N` for locals. Required by every DBG sample (`SetUiColorBase`, `DirtyRectAddBox`, `InitResources`, `LzssAllocRing`, `StoredBegin`, `VidAllocBackbuffer`) |
| `-d1`, `-d0` | no code change (indifferent for OPT; do not give DBG frames) |
| `-d2`, `-d3` | force unoptimised code (identical to `-od`): break every OPT and DBG sample |
| `-od` | unoptimised, gives the OD *shape* but not the bytes (section 3) |
| `-of`, `-of+` | frame layout `push ebp; mov ebp,esp; push <saves>; ... lea esp,-N[ebp]`: ebp is pushed **first**, the original pushes it **last**. `-of+` breaks every sample (it gives leaf functions a frame too); `-of` breaks the DBG samples that have saves or calls |
| `-ob` | breaks `TrimAtWhitespace`, `fn_12cd4`, `SndPlay*` (block layout) |
| `-or` | breaks `fn_12cd4`, `TextSetColorBase` (instruction reordering) |
| `-oa` | breaks `DirtyRectAddBox` (alias relaxation merges loads) |
| `-oi` | breaks `fn_15558` (inlines strcpy); the original calls `strcpy_` |
| `-oc -oe -oh -ok -om -on -oo -op -ou -oz -zc -ei` | no effect on any sample |
| `-fpi -fp3` | no effect (integer-only code) |

### The reference C of the other areas

`python3 -m wc1.codegen_refs` sweeps `src/audio/sound.c`, `src/graphics/gfx_prim.c` and
`src/resources/war.c` over 75 flag sets each (`build/codegen/refs.txt`):

| Function | Original style | Best OW2 similarity | Why it stays different |
|---|---|---|---|
| `SndShutdownAil` 0x26b18, `MusicStop` 0x26d60, `SndActiveCount` 0x27320 | OD | 0.65 / 0.66 / 0.74 (`-od`) | section 3 |
| `HLine` 0x3ac10, `VLine` 0x32970 | DBG | 0.49 / 0.53 (`-d1+`): prologue now identical (`push ecx; push esi; push ebp; mov ebp,esp; sub esp,4`) | the original spills the zero-extended `y` to `[ebp-4]` and multiplies with a memory operand (`imul edx,[ebp-4]`), puts the loop exit epilogue before the loop body, and reloads `cur_bitmap` in the loop (section 4, V5/V8) |
| `ResourceSeek` 0x3452c | DBG | 0.59 | `esi`/`edi` assigned in the other order; `p++` kept as separate `add eax,4`; address arithmetic via `lea esi,[edx*4]; add eax,esi` instead of folded indexing (V3/V5) |

The three previous analysts' diagnosis ("older Watcom, OW2 cannot reproduce") is right for the
register assignments but the *frame* observations (ebp frame, push order) were configuration, not
version: `-d1+` reproduces them.

## 3. Why `-od` does not reproduce the OD functions

Diff of OW2 `-od` against `SndShutdownAil` (0x26b18), `MusicStop`, `SndActiveCount` shows exactly
four systematic differences, none controlled by any flag (all tried: `-od` combined with every
optimisation letter, `-3r..-6r`, `-of(+)`, `-hw/-hd/-hc`, `-d1/-d2/-d3`, `-zc`, `-zp`):

1. **Frame size**: OW2 always reserves at least 4 bytes: `sub esp,4` where the original has
   `sub esp,0` (SndShutdownAil, MusicStop) and 8 where it has 4 (SndActiveCount).  The original's
   epilogue then omits `mov esp,ebp` when the size is 0 (`pop ebp` directly).
2. **Return value temporary**: OW2 copies the result through a second stack slot
   (`mov [ebp-8],eax; mov eax,[ebp-8]`); the original returns the local directly.
3. **Jump encodings**: OW2 `-od` emits `jcc/jmp rel32` for every branch (also over 2 bytes); the
   original uses rel8 (`74 09`, `eb 0e`).
4. Parameters/expression temporaries are spilled slightly differently (the `push dword [m]` vs
   `mov eax,[m]; push eax` choice in MusicStop; probably a different C expression, not tested further).

(1)-(3) make T3 impossible for OD functions with OW2 regardless of the C; they need the original
compiler, a patched OW2, or assembler-level equivalence tests (T4).

## 4. Where OW2 and the original differ (and what steers them)

Examples are original -> OW2 `-ot -ol -4r -zp2` on the same C.

| # | Difference | Example (original address) | Steerable? |
|---|---|---|---|
| V1 | 16-bit zero extension: `and edx,0xffff` (also `xor r,r; mov rl,..` for bytes) vs `movzx`/`xor ecx,ecx; mov cx,dx; mov edx,ecx` | 0x13954, 0x1a9a4 (`and eax,0xffff` after `add eax,0x170`) | no |
| V2 | scratch value for a 16/32-bit constant store: `edx` (`push edx; xor edx,edx; mov [m],dx; pop edx`, `mov edx,-1` x6) vs `eax` | 0x16cbc, 0x13ef8, 0x14c74, 0x417cc (`LzssReset`), 0x41800 | no (tried: locals of every width, globals, `volatile`, pragmas) |
| V3 | register assignment order: first pointer in `ebx` and divisor in `ecx` vs the reverse (SndApplyOptions 0x2674c); first local `esi`, second `edi` vs `edi`, `esi` (0x1a9a4, ResourceSeek); second 16-bit local in `bx` vs `ax` (0x19f94) | listed | no |
| V4 | `unsigned short` compared as promoted int is **not** narrowed: `xor edx,edx; mov dx,[m]; cmp edx,0xffff` | 0x26958, 0x12cd4, 0x12404 | yes: copy into an `unsigned`/`int` local first (`unsigned d = cfg; if (d != 0xffff)`), see `src/codegen/snd.c`, `mod_12c70.c` |
| V5 | no store->load forwarding / constant propagation: `mov byte [eax],0x43; mov bl,[eax]; mov [edx],bl` (GDS malloc guard 0x32558), `cmp byte [edx],0` re-test after a store of 0 (0x1d798), loop pre-test with a just-zeroed counter (0x12404, 0x417cc) | listed | partly: `volatile` stores stop OW2's forwarding (`TrimAtWhitespace`), loop pre-tests no |
| V6 | adjacent 16-bit stores are **not** merged into one 32-bit store (`mov word [0x5a870],0x140; mov word [0x5a872],0xc8`) | 0x3b360 | yes: `volatile` stores (`mod_3b360.c`) |
| V7 | calls to a variadic stack-convention function are assumed to clobber `eax ebx ecx edx` (callers save `ebx,ecx,edx`), OW2's `__cdecl` assumes `eax ecx edx` | every `FatalError` caller (0x1132c, 0x123cc, 0x1d9d4) | yes: `#pragma aux FatalError "_*" parm caller [] modify [eax ebx ecx edx]` (`src/codegen/codegen.h`) |
| V8 | stack locals / spills in optimised code get an ebp frame (`push <saves>; push ebp; mov ebp,esp; sub esp,N`, `[ebp-N]`) | 0x1a9a4, 0x18b64, 0x1c300, 0x3ac10 | only with `-d1+`, which gives *every* function of the object a frame, so game objects containing one such function need a separate object |
| V9 | multiplication by constants: `lea eax,[edx*8]; add eax,edx` (x*9), `lea eax,[edx*4]; sub eax,edx` then scale 4 (x*12), x*18 as x*9 with scale 2; OW2 emits `imul` for 12/18 and `push edx; shl; add; pop edx` for 9 | 0x31f70, 0x31920 | no. The original also uses `lea r,[x*4]` / `[x*8]` as a shift in 132 places, which OW2 does not emit |
| V10 | loop layout: test at the top, exit epilogue first, body after; `for` loops not rotated | 0x12404, 0x12d2c | no (OW2 `-ol` rotates and drops the pre-test; without `-ol` it jumps to the bottom test) |
| V11 | `-od` frame bookkeeping | section 3 | no |
| V12 | `sete al; and eax,0xff; add eax,0x170` for `(x == 3) + 0x170` vs OW2 spilling the `sete` byte under `-d1+` | 0x1a9a4 | unknown |

V1-V3, V8-V11 are the "backend" differences; V4-V7 turned out to be source-level.

## 5. Matches achieved (`src/codegen/`)

All are `MATCH` under the flags in their `codegen-flags:` header (`python3 -m wc1.codegen_flags`
re-verifies; `tests/test_codegen.py`).  "T3" = also passes `wc1.match <file> --cflags
"-q -zl -bt=dos <flags>"`.  Unnamed callees/data (marked `fn_`/`dat_`) prevent T3; the sweep's
consistency check still covers bytes, relocation structure and CONST contents.

| File (module) | Function | Address | Flags | Check |
|---|---|---|---|---|
| init.c (INIT.C) | `TrimAtWhitespace` | 0x1d798 | OPT | T3 |
| snd.c (SND.C) | `SndPlay`, `SndPlayLooped`, `SndStop` | 0x26958, 0x26988, 0x269b8 | OPT | T3 |
| bullet.c (BULLET.C) | `fn_123cc` (FatalError "bullet:6") | 0x123cc | OPT | sweep |
| mod_110a0.c | `fn_1132c` (FatalError "attack:1") | 0x1132c | OPT | sweep |
| mod_12c70.c | `fn_12cd4` (0..3 counter) | 0x12cd4 | OPT | sweep |
| mod_13e60.c | `fn_13e94` | 0x13e94 | OPT | sweep |
| mod_13f60.c | `fn_15170`, `fn_15230`, `fn_15558` | 0x15170, 0x15230, 0x15558 | OPT (`-zp2` needed) | sweep |
| mod_19470.c | `fn_19478` (LCG, seed 0x50d7c) | 0x19478 | OPT | sweep |
| mod_32030.c | `TextSetColorBase` | 0x32030 | OPT | T3 |
| mod_31dc0.c | `TextSetEscapeColors` | 0x31dc0 | OPT | T3 |
| mod_34380.c | `SetUiColorBase` | 0x34380 | DBG | T3 |
| mod_33a30.c | `DirtyRectAddBox` | 0x33a30 | DBG | T3 |
| res_init.c | `InitResources` | 0x34040 | DBG | T3 |
| mod_409a0.c | `StoredBegin` | 0x409d4 | DBG | T3 |
| res_lzss_alloc.c | `LzssAllocRing` | 0x41530 | DBG | T3 |
| mod_3b360.c | `VidAllocBackbuffer` | 0x3b360 | DBG | T3 |

(`InitPaths`, 0x1d7cc, still matches with these flags: `python3 -m wc1.match src/init.c --cflags
"-q -zl -bt=dos -s -ot -ol -4r -zp2"`.)

`src/codegen/near_misses.c` keeps 3 functions (0x13ef8, 0x14c74, 0x16cbc) that differ only by V2.

Flags: **OPT = `-s -ot -ol -4r -zp2`**, **DBG = OPT + `-d1+`**.

## 6. Version question and recommendation

Evidence for "different compiler generation" (not flags):

* the OD output (section 3) is a bookkeeping difference in the unoptimised code path;
* V1-V3 and V9-V10 appear in short, clean, flag-independent functions (0x16cbc is five instructions);
  the clib comparison does not help: the 8 byte-identical units (`mem_putc`, `tolower`, ...) are too
  simple to hit them, and the other clib functions (atoi 0x324dd, rand 0x33b61) differ in library
  source revision as well, so they are not clean evidence;
* the library objects were built with a debug-info switch whose frame layout equals OW2's `-d1+` (the
  layout `push saves; push ebp; mov ebp,esp` also appears in OW2 `-od`), i.e. the toolchain is close.

So: **flags explain frame style, loop rotation, byte-load idiom, packing; the register allocator,
constant/store propagation, multiply decomposition and `-od` frame handling are version
differences.**  A Watcom 9.5/10.0 `wcc386` is the only way to reach full T3 for the remaining
~20 % of the OPT functions and all OD functions; patching OW2 would mean modifying its register
preference tables (V2/V3), strength reduction (V9) and the `-od` frame allocator (V11) -- we have no
OW2 source in the environment (nothing was downloaded), and V1/V2/V3 look like several small
heuristics, not one switch.  Recommendation:

1. **Adopt per-file flags**: OPT for game modules and the clib, DBG for the video-library objects, and
   `PACKET.C` with `-zp1`.  Everything that is OD stays reference C verified by T4 (difftest), and
   functions that hit V1-V3 are written for equivalence, with the closest C kept (like
   `near_misses.c`).
2. **Keep the source idioms** of section 4 (local copy for promoted compares, `volatile` against
   forwarding/store merging, the `FatalError` pragma) in a shared header once the build supports
   per-file flags.
3. Expect T3 for the simplest functions (setters, wrappers, small loops, FatalError sites), not for
   register-heavy code.  If a Watcom 10.x `wcc386` ever becomes available, put it first
   on `$PATH` and re-run `codegen_flags`/`codegen_refs`: the tools only call `wcc386`.

## 7. Patch sketches (not applied; shared files)

`tools/wc1/match.py` -- per-file flags from the header comment (and keep `--cflags` as override):

```python
FLAGS_RE = re.compile(r"codegen-flags:\s*(.*)")
def file_cflags(src, default):
    m = FLAGS_RE.search(open(src).read())
    return "-q -zl -bt=dos " + m.group(1).strip() if m else default
...
ap.add_argument("--cflags", default=None)
cflags = a.cflags or os.environ.get("WC1_CFLAGS") or file_cflags(a.src, DEFAULT_CFLAGS)
```

`tools/wc1/build.py` (C compilation step): the same lookup per `src = ...` file, default
`-q -zl -bt=dos -s -ot -ol -4r -zp2` (InitPaths verified with it).  Header convention:
`/* codegen-flags: -s -ot -ol -4r -d1+ -zp2 */` in the first lines of the file.

Module granularity: a C file per original object (see the run table); a module with one DBG function
inside OPT code (0x18b64, 0x1a9a4, 0x1c300, 0x2fcfc) needs two objects or stays unmatched.

Names for the library samples are now in the database (`GdsAlloc` 0x32558, `GdsFree` 0x32780,
`text_colors` 0x5ad02, `text_glyph_fn` 0x5ad07, `text_esc_colors` 0x5ad0b, `cursor_save_bm` 0x5ad10)
and those four samples are T3 + `src=`.  The game samples (`bullet.c`, `mod_110a0.c`, `mod_12c70.c`,
`mod_13e60.c`, `mod_13f60.c`, `mod_19470.c`) still need semantic names from the game-logic areas;
0x569d4/0x569e0 are the strings `attack:1` / `bullet:6`.

`docs/ANALYST_GUIDE.md`: replace "Game code was compiled with flags reproduced by `wcc386 -s -ot`" by
the OPT/DBG/OD description and flags of this page.

## 8. Open questions

* Is `-d1+` really what the original used, or the old compiler's `-d2` with optimisation kept?  Same
  bytes for the samples, different spelling; matters only for a Watcom 10 build.
* Which objects of the video library use `-od` and why (EVT/VID, file wrappers, key state, retry
  loops): maybe those were compiled while debugging; the module list should mark them.
* The two game objects with a lone DBG function (0x18b64, 0x1a9a4): are they `#pragma`-compiled
  separately or does the old compiler give an ebp frame to any function with stack locals?  The
  latter fits the five DBG game functions (all have stack locals; 0x30bd0 and `FatalError` are
  library objects) and would mean OPT game code needs a frame-for-locals behaviour OW2 only has under
  `-d1+` (V8).
* The `FatalError` convention (V7): `modify [eax ebx ecx edx]` explains the prologues of all callers
  checked (3); a systematic check over all `0x30bf0` callers would confirm it.

## Reproduce

```
python3 -m wc1.codegen_survey --functions          # build/codegen/survey.txt, functions.tsv
python3 -m wc1.codegen_flags                       # ablation over src/codegen -> build/codegen/flags.txt
python3 -m wc1.codegen_refs                        # reference C of other areas -> build/codegen/refs.txt
python3 -m wc1.codegen_sweep FILE.c --flags "-s -ot -ol -4r -zp2" --diff    # per-function MATCH / diff
python3 -m wc1.codegen_search FILE.c [FILE2.c] --base "-s -ot"             # greedy flag search
python3 -m wc1.match src/codegen/init.c --cflags "-q -zl -bt=dos -s -ot -ol -4r -zp2"   # T3
python3 -m pytest tests/test_codegen.py
```

Samples for the sweep carry `/* @0xADDR ... */` before each function; `build/codegen/` holds scratch.
