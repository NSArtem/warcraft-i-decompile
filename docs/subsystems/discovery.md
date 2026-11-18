# Code discovery: starts, audit, and the plausibility vetoes

Discovery (`tools/wc1/analysis.py`) decides which bytes of the code object are
functions.  `analysis/modules.toml` groups the result into objects; the symbol
database gives the functions names and C.  This note records the rules that
keep data and lifted mid-function blocks out of the function list, the audit
that checks them (`tools/wc1/discovery_audit.py`, output
`build/audit/discovery_audit.json`), and the two discovery changes of
2026-11-18 with their before/after lists.

## 1. How a start is found

A start comes from one of:

| origin | rule |
|---|---|
| `entry` | the LE entry point |
| `call` | a direct `call` target |
| `ptr` | a code pointer: a fixup from the data object, or a 32-bit immediate in code (callback tables, `mov [slot], func`) |
| `jump-table` | a `jmp [table+reg*4]` target (an internal label of the switch's function) |
| `gap-scan` | unreferenced ("dead") code the linker kept: gap scan with a strictly validated flow closure |
| `tail` | a conditional/unconditional jump from another function to an address outside that function, entered only by that jump (no fall-through) |

The partition then gives each start the range up to the next start and checks
that no non-call flow crosses a boundary except into another start.

## 2. The two 2026-11-18 vetoes

### 2.1 A tail target inside another function's own flow is a shared label

The tail rule originally accepted any target outside the jumping function's
`[start, limit)` range.  That promotes shared *epilogues*: several functions
end with one `pop`/`ret` block that the compiler merged, reached by conditional
jumps from each of them.  `_partition` now also records each function's
ordinary flow closure (`reach`, excluding jump-table blocks); a tail target
that lies in another function's `reach` is that function's own label and is not
promoted.

### 2.2 Stack balance: a lifted block or data is not an entry point

A candidate that starts with an epilogue or pops the caller's frame is a
block of a neighbouring function (Watcom sometimes lays a block out *before*
its function's entry) or data decoded as code.  `analysis.stack_underflow`
walks the contiguous run from the candidate and reports the first instruction
that takes the running `push`/`pop`/`sub esp` balance below zero; a candidate
with such an instruction is rejected.

* Discovery seeds (`data-ptr`, `code-ptr`, `gap-scan`) are checked before
  their closure is accepted, so a data table cannot swallow the real function
  behind it.
* Tail candidates are checked in `partition()` before they are promoted.
* Exempt: the entry, direct call targets (`_hardresume` is reached by `call`
  and switches stacks), jump-table labels, and every start in an `ail`, `asm`
  or `asm-shared` module (AIL's `0x38aa8` is a gap-scan start with a
  deliberate stack switch).
* `lss esp` / `mov esp` / `leave` end the walk (an explicit stack switch), and
  a `ret`/`jmp` before any underflow passes.

### 2.3 Runtime pieces are not a discovery change

Three starts are real code but not Blizzard code; they stay starts and are
moved out of scope by `analysis/symbols/clib.toml` entries with evidence
(docs/METHODOLOGY.md scope rule):

| address | name in clib.toml | evidence |
|---|---|---|
| 0x3d920 | `__terminate` | calls the `___abort` hook (0x565e4) and falls into `__terminate_abnormal` 0x3d926; dead runtime path |
| 0x401bd | `__MemFree_exit` | shared exit block of `__MemFree` 0x401c2: two `je 0x401bd` inside it, the block is `jmp 0x402c8` (also reached by `jbe 0x402c3`) |
| 0x41819 | `__exit_with_msg` | single `jmp __do_exit_with_msg` (0x34815), no references; the OW2 clib3r `xmsg.c` unit has exactly this shape and the next function 0x4181e is the clib `__fatal_runtime_error` |

## 3. The audit

`python3 -m wc1.discovery_audit` writes one row per discovered start:
origin, module/kind, DB name, number of linear instructions, the stack-underflow
address (`frag`), implausible/segment-overridden instructions, whether the last
instruction falls through, and the first instructions.  It is a report, not a
gate; `tests/test_pipeline.py` pins the specific corrections below and checks
that no non-AIL start has a stack underflow.

Before the vetoes (1714 starts): 7 rows with a stack underflow -
0x18798, 0x1e3ac, 0x24860, 0x2c1b3, 0x38aa8 (AIL), 0x3c461, 0x3d01e (call
target, `lss` switch).  After: 1 row, the AIL exemption 0x38aa8;
0x3d01e is no longer flagged because the walk stops at `lss esp`.

## 4. Before/after (2026-11-18)

`1714 -> 1710` starts; in scope `1047 -> 1040` (the three runtime pieces move
out, five non-functions disappear, one callback appears).

Removed:

| address | was | why |
|---|---|---|
| 0x18798 | `ptr` | a 12-byte data table (`sub [eax],al; ...; pop ss`): underflow at 0x1879c.  Its closure had swallowed the real callback at 0x187a4 |
| 0x1e3ac | `tail` | shared epilogue of fn_1e380 and fn_1e3b4 (`lea eax,[ebx+2]; pop ecx; pop ebx; ret`, reached by `je` 0x1e390 and 0x1e3c4); also underflow at 0x1e3af |
| 0x24860 | `gap-scan` | an unreferenced XOR-0x64 text buffer: 26 bytes decoding to `warcraft\0cd\0version\0` plus 102 bytes of 0x44 (space) padding, no reference in the image; underflow at 0x24868 |
| 0x2c1b3 | `tail` | a block of fn_2c208 laid out before its entry, using its `[esp+4]`/`[esp+8]` parameters, reached only by `jge` 0x2c252; underflow at 0x2c1de |
| 0x3c461 | `tail` | shared epilogue of `far_strnlen` 0x3c442 and `far_wcsnlen` 0x3c466 (`pop es; pop edi; pop esi; pop ecx; ret`, reached by `je` 0x3c458/0x3c45c and 0x3c480/0x3c484); underflow at 0x3c461 |

Added:

| address | why |
|---|---|
| 0x187a4 | the callback `mov dword [0x59420], 0x187a4` (a code pointer from inside fn_18b64's code), no longer swallowed by the 0x18798 data table |

Kept (runtime, now out of scope): 0x3d920, 0x401bd, 0x41819 (section 2.3).
Kept (exceptions): `_hardresume` 0x3d01e (direct call target, `lss esp` stack
switch) and AIL `0x38aa8`.

The 2026-11-18 tail-jump promotion that recovered `ScoreAddForMen` 0x24ee0
(AGENTS hand-off, `docs/subsystems/save_score.md` section 6) still works: the
target is not in any function's ordinary flow and its stack balance is clean.
