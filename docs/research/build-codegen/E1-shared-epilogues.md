# E1 — Shared epilogue reproduction

**Verdict: confirmed for both groups.** Watcom C/C++ 10.0a naturally emits
cross-function epilogue branches, including across an intervening function.
Pure C and suitable compilation context reproduce both complete regions;
E0 accepts every function and each region, and isolated Build A links are
`IDENTICAL`, with zero loaded-image byte differences and all 8,770 LE fixups
preserved. No assembly was inserted into C.

Experiment date: 2026-11-25. Baseline:
`7c23d2371e95d8de93f0ba1652c8d44b858da273`. Branch:
`research/build-codegen/e1`.

## Method and evidence

The runner compiles **97 variants / 196 function observations** from scratch.
It uses the baseline E0 `matcher_proto.match_module` for every FunctionMatch
and RegionMatch. Full findings, normalized obligations, original and compiled
branch bytes/targets, public offsets, padding, OMF fixups and object SHA-256
hashes are in [results.json](results/e1/results.json). Complete original and
compiled linear listings, OMF relocations and link comparison output are in
[disasm_evidence.txt](results/e1/disasm_evidence.txt).

The four requested codegen flag sets are tested for both groups in original
order, reversed order and every individual standalone function. Group B also
gets the pair-only control under every flag set. The readable Group A revision
gets the same standalone/order controls. A fifth flag set,
`-s -ot -oa -ol -5r -zp2`, tests the combination suggested by the independent
alias-scheduling and alignment results. Seventeen additional Group A spelling
probes run under `-s -ot -ol -5r -zp2`; unsuccessful probes are retained.

Common flags are `-q -zl -zld -bt=dos`; 10.0a spells quiet as `-zq`.
`-zld` suppresses dependency timestamp COMENT records. Without it, rewriting
the generated source changes its recorded timestamp and thus the raw OMF
hash on each replay. The parsed module from the dependency-enabled probe
and its `-zld` compilation was equal, including all segments, publics,
statics and fixups. The actual emitted objects are hashed and audited without
post-compilation normalization. Absolute THEADR source paths remain, so
byte-for-byte hash replay uses the assigned worktree location.

The R1 bool is per function's **outgoing** branches: epilogue owners normally
report false, while their callers report true. Branch-byte equality, target
identity, FunctionMatch, RegionMatch and link identity remain separate facts.
In the tables, “not attempted” means the region failed E0 and never entered
placement/linking; it is stored as `identical=null`, with an explicit status.

## Group A: dialog hit test and highlight helpers

The supplied bodies already reproduce sharing in original order under all
four required flag sets. They do not reproduce the full original region.
The `-os` control also aliases both identical highlight functions at one
public offset; that optimization changes layout and cannot establish an
exact original region.

| Supplied bodies, joint flags | On branch | Off branch | Shared epilogue in helpers | FunctionMatch: Hit / On / Off | RegionMatch | Build A |
|---|---|---|---|---|---|---|
| `-ot -ol -4r` | `74 e9` | `74 c9` | true / true | UNSUPPORTED / MISMATCH / MISMATCH | MISMATCH | not attempted |
| `-os -ol -4r` | `74 f5` | `74 f5` (aliased) | true / true | MISMATCH / MISMATCH / MISMATCH | MISMATCH | not attempted |
| `-ot -oa -ol -4r` | `74 e9` | `74 c9` | true / true | UNSUPPORTED / MISMATCH / MISMATCH | MISMATCH | not attempted |
| `-ot -ol -5r` | **`74 f5`** | `74 e1` | true / true | MISMATCH / MISMATCH / MISMATCH | UNSUPPORTED | not attempted |

All rows also include `-s -zp2`. `UNSUPPORTED` is E0's fail-closed verdict for
unproven constructs/obligations in a mismatching layout, not a negative
verdict on the observed compiler optimization. Full diagnostics are retained.

### R6: why `74 f5` differs from original `74 f3`

For the supplied bodies under `-ot -ol -5r`, offsets below are relative to
`DialogItemHitTest`'s `_TEXT` start, which is offset zero in both objects:

| Quantity | Original | Compiled supplied C |
|---|---:|---:|
| Last hit-test `ret` | `+0x69` | `+0x83` |
| Filler following that `ret` | `8b c0` (2 bytes) | empty |
| `DialogHighlightOn` public | `+0x6c` | `+0x84` |
| `je` opcode offset | `+0x74` | `+0x8c` |
| Next IP after `je` | `+0x76` | `+0x8e` |
| Encoded displacement | `0x69 - 0x76 = -13 = f3` | `0x83 - 0x8e = -11 = f5` |

The supplied hit-test body is 132 bytes instead of 106: its final `ret`
moves by 26 bytes, while the following aligned function moves by 24 bytes.
The original has two alignment bytes between `ret` and On; the supplied
body ends at an already aligned boundary. This explains the displacement's
**exact +2 delta**, rather than attributing it vaguely to a different body
length. The `-os` row separately emits `74 f5` with a shorter body, no padding
and aliased helpers; the listings preserve both contexts.

### A3: readable C and independent flag effects

[The revised fixture](../../../experiments/build_codegen/e1/fixtures/group_a_interleaved.c)
stages each coordinate load and its item-coordinate addition, then tests a
single conjunction of the four inside-rectangle conditions. Its locals,
structures and external declarations are ordinary C; it needs no pragma or
inline assembly.

| Revised bodies, joint flags | On / Off branches | FunctionMatch: Hit / On / Off | RegionMatch | Build A |
|---|---|---|---|---|
| `-ot -ol -4r` | `74 ef` / `74 cf` | MISMATCH / MISMATCH / MISMATCH | MISMATCH | not attempted |
| `-ot -oa -ol -4r` | `74 ef` / `74 cf` | **MATCH** / MISMATCH / MISMATCH | MISMATCH | not attempted |
| `-ot -ol -5r` | **`74 f3` / `74 df`** | MISMATCH / **MATCH / MATCH** | MISMATCH | not attempted |
| `-ot -oa -ol -5r` | **`74 f3` / `74 df`** | **MATCH / MATCH / MATCH** | **MATCH** | **IDENTICAL** |

Under `-5r` alone, the hit-test body has the original length but differs
starting at `0x16cd8`: `add ebx,eax; add ebx,ebx` replaces the original
`add eax,ebx` and the following indexed addressing changes. This is the
required R1 intermediate finding: exact helper branches do not prove the
owner or the region. Adding `-oa` makes the owner exact as well.

The successful object has public offsets `0 / 0x6c / 0x80`, internal padding
`8b c0` and `8d 40 00`, and 145 bytes of `_TEXT`. Its closed matched/linkable
interval is **`[0x16cc8,0x16d59)`**. The following three original alignment
bytes remain supplied by ASM.

The assignment's requested endpoint `0x16d5e` crosses into the next function.
The actual next entry is `0x16d5c`, beginning `56 57 83 ec 0c`
(`push esi; push edi; sub esp,0xc`). The original three-function listing
therefore ends at `0x16d5c`, including padding; the evidence also lists the
next prologue explicitly. No next-function bytes are claimed as C output.

In reversed order, sharing can still occur: under `-5r`, On uses `74 f3`
to reach **Off's** return, not the original hit-test return. E0 rejects the
region. Thus the mere presence of `74 f3` is insufficient; relative public
layout and target identity are essential. Every standalone helper lacks a
sibling epilogue and fails the original cross-function-branch obligation.

## Group B: PLAYFLIC sound handlers

The supplied `IntroOpWaitSound` body is already exact in the appropriate
joint context. Its loop calls `SndActiveCount`, tests the result, checks
`intro_abort`, calls `IntroTick`, and returns to the count check. Both exit
branches reuse `mov eax,edx; pop edx; ret` in `IntroOpPlaySound`.

| Joint flags | WaitSound shared branches | Shared epilogue | FunctionMatch: Play / Sync / Wait | RegionMatch | Build A |
|---|---|---|---|---|---|
| `-ot -ol -4r` | `74 83`, `0f 85 75 ff ff ff` | true | MATCH / MATCH / MISMATCH | UNSUPPORTED | not attempted |
| `-ot -oa -ol -4r` | `74 83`, `0f 85 75 ff ff ff` | true | MATCH / MATCH / MISMATCH | UNSUPPORTED | not attempted |
| `-os -ol -4r` | `74 9d`, `75 93` | true | MISMATCH / MISMATCH / MISMATCH | MISMATCH | not attempted |
| `-ot -ol -5r` | **`74 93`, `75 89`** | **true** | **MATCH / MATCH / MATCH** | **MATCH** | **IDENTICAL** |
| `-ot -oa -ol -5r` | **`74 93`, `75 89`** | **true** | **MATCH / MATCH / MATCH** | **MATCH** | **IDENTICAL** |

Under `-4r`, public offsets are `0 / 0x20 / 0x80`, versus original
`0 / 0x14 / 0x70`: extra padding shifts Sync by 12 bytes and Wait by 16.
The first shared branch remains short with a changed displacement; the
second exceeds rel8 range and becomes a six-byte conditional branch.
The optimization is present, while exact encoding and region matching fail.

Under `-5r`, public offsets are exactly `0 / 0x14 / 0x70`. Sync's body ends
at `+0x6e`; `8b c0` fills the two bytes before Wait. The closed object is
142 bytes, **`[0x2315c,0x231ea)`**, followed by two untouched ASM alignment
bytes. The exact reproduced branches are:

```text
0x231d7: 74 93    je  0x2316c
0x231e1: 75 89    jne 0x2316c
0x2316c: 89 d0    mov eax,edx
0x2316e: 5a       pop edx
0x2316f: c3       ret
```

Both jumps cross the entire intervening `IntroOpSyncSound` function.
Standalone WaitSound emits its own return tail and cannot reproduce these
sibling branches. The pair-only control still shares the epilogue, but
omitting Sync changes Wait's public offset and yields different branch
bytes (`74 ef` / `75 e5` under `-5r`); E0 rejects the region. Reversed-order
WaitSound does not share PlaySound's epilogue, and all reversed regions fail.

## Isolated Build A integration and R1 totals

Only E0 RegionMatch objects enter the production `build.place`,
`check_placed_plan`, `emit.Emitter`, NASM and wlink machinery. Each isolated
executable uses one compiled candidate region plus the original symbolic ASM
remainder. These are per-region integration proofs; the runner does not
replace or rebuild the repository's entire existing T3 inventory. A private
object copy receives only Build A's normal SEGDEF BYTE alignment adjustment.
The audited compiler object is retained unchanged under `build/e1/`.

| Primary link | Result | Loaded-image byte diffs | Original / linked LE fixups | Fixups only in either side |
|---|---|---:|---:|---:|
| `build/e1/war_group_a.exe` | IDENTICAL | 0 | 8770 / 8770 | 0 / 0 |
| `build/e1/war_group_b.exe` | IDENTICAL | 0 | 8770 / 8770 | 0 / 0 |

Across 97 variants, 84 regions fail E0 and are not integrated. Thirteen
regions pass E0: three links are IDENTICAL (Group A once, Group B twice),
six standalone placements are rejected for incoming interior references,
and four standalone SyncSound insertions reach NASM but are rejected because
remaining original rel8 branches span separate ASM objects. These negative
controls show why even RegionMatch requires a separate global placement/link
result. No rejected control is counted as a successful integrated build.

**Scientific conclusion:** compilation context is sufficient to explain and
reproduce these shared epilogues. Exact reconstruction also requires matching
C bodies, compatible codegen flags, original ordering and padding. Group A
separates those effects; Group B proves sharing across an intermediate
function. These results support joint compilation for these groups, without
establishing that every other mismatch in a larger CU has the same cause.

## Reproduction

From the assigned worktree, inside its configured development shell:

```sh
python3 -m experiments.build_codegen.e1.run_e1
pytest -q experiments/build_codegen/e1/test_e1.py
python3 -m wc1.compare original/install/war.exe build/e1/war_group_a.exe
python3 -m wc1.compare original/install/war.exe build/e1/war_group_b.exe
```

The targeted suite passes **17/17** tests and repeats the entire matrix and
all integration attempts, reaudits raw objects with E0, and verifies both
preserved artifacts byte-for-byte. Production paths, gates, symbols and tests
have no changes from the baseline. Full `make verify` is deliberately not
invoked, as required by the E1 assignment.
