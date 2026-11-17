# Project goal and definition of done

**Goal:** readable C source for all of Blizzard's own code in *Warcraft: Orcs &
Humans* (DOS, CD v1.22h `war.exe`), where every function is either proven to be
the original (T3) or proven to behave like it (T4), plus two builds that use that
C.  The tiers are defined in `docs/METHODOLOGY.md`.

Progress is measured by `python3 -m wc1.progress` (`make progress`).  The goal
is met when all three gates in section 4 pass.  Scope, the definition of done
and the gates change only with the user's approval (AGENTS.md ground rules).

## 1. Scope

Every function found by code discovery (`wc1.analysis`, 1714) is either in or
out of scope.  `wc1.progress` applies these rules:

| Out of scope | Rule | Why |
|---|---|---|
| Miles AIL | module kind `ail` (analysis/modules.toml) | third-party sound library, not Watcom C |
| Hand-written asm | module kind `asm` / `asm-shared` | never was C; stays named asm |
| Watcom runtime | entry in `analysis/symbols/clib.toml`, or the library table objects `int_stub_table` / `cstrtx_begtext` | the compiler's library: linked, not decompiled |

Everything else is in scope: game code plus Blizzard's video, input, event and
resource libraries.  A runtime-kind function that nobody has identified yet stays
**in scope** and is reported as "not yet classified".  Identifying it as Watcom
runtime (an entry in clib.toml with libsig or semantic evidence) moves it out.

Snapshot 2026-11-18: 1047 in scope (game 885, runtime 122 of which 48
unclassified, gfx 27, resource 13); 667 out (Watcom runtime 473, AIL 156, asm 38).

## 2. Per-function definition of done

An in-scope function is **done** when it has

1. **a semantic name**: an entry in `analysis/symbols/*.toml` with a name that is
   not an address placeholder (`fn_1234`) and confidence verified/high/medium,
   with evidence (METHODOLOGY rules); **and**
2. **C that is proven correct**, one of:
   * **T3**: `src = "src/..."`, `wc1.match` reports MATCH, built from C; or
   * **T4**: `ref = "src/..._reference.c"` holding the C, plus
     `ref_verified_by = "difftest: tests/...::test_x"`, a test that runs **the
     compiled reference C and the original under wc1.emu on the same inputs** and
     compares the results and memory effects, plus
     `t3_blocker = "<category>: <evidence>"` saying why T3 is out of reach.

`wc1.symbols` validates these fields: `src` and `ref` are exclusive, `ref` must
exist and define the function, `ref_verified_by` must be a `difftest:`, and
`t3_blocker` must use a known category.

**A test of the original against a Python model is not T4 for C.**  It verifies
the *claim* (name and semantics) and belongs in `verified_by`, as today.  T4
needs the compiled C itself to run against the original.  Today no reference C
is run that way (milestone M1), so the 28 existing reference functions count as
"reference C, not checked yet".

### T3 first, T4 as a documented fallback

Try for T3 before settling for T4:

1. compile with the object's codegen style (`codegen-flags:` header; OPT, or DBG
   with `-d1+`; docs/subsystems/codegen.md);
2. try the source idioms in codegen.md section 4 and the area notes (unsigned
   mask locals, reusing a local, `volatile`, local copies, statement order);
3. record in the evidence which spellings were tried and the first differing
   instruction (address in the original).

Then set `ref` and `t3_blocker` with one of these categories:

| t3_blocker | Meaning |
|---|---|
| `od-frame` | unoptimised OD-style object (all registers saved, `sub esp,imm32`); OW2 `-od` differs systematically (codegen.md section 3) |
| `regalloc` | same instruction sequence, different register assignment (codegen.md V2/V3); source cannot steer it |
| `codegen` | another backend difference (constant propagation, store forwarding, multiply decomposition, scheduling); evidence names the first difference |

Near-miss guards stay in the area tests: a reference file must fail to match,
so a newly matching one gets promoted to `src`.

### Readability (reviewed, not machine-checked beyond names)

* Parameters and locals have meaningful names; the DB `proto` matches the C.
* Known record layouts are structs in `src/include/<area>.h` (e.g. the 0x5c-byte
  unit record), not raw pointer arithmetic.
* Globals are used through their DB names (externs), never through addresses.
* Matching idioms (`volatile`, a local copy, an odd type) get a one-line
  comment saying they are there for code generation.

## 3. Milestones

* **M1: T4 harness.**  Let `wc1.emu` run compiled C: load the wcc386 object into
  the emulator, resolve its relocations against the symbol DB, call it like the
  original.  Then turn the 28 existing reference functions into T4 (or T3).  Until
  M1 exists, T4 is 0 by construction.
* **M2: area coverage (the bulk of the work).**  Game areas by
  analysis/modules.toml ranges, one analyst per area (AGENTS.md step 3), and
  classifying the unidentified runtime functions.  `make progress` lists what
  is missing per function (`--todo N`, `--kind game`).
* **M3: all-C build and T5.**
  *Build A* (exists, `make build`): T3 C linked in place plus asm; must stay
  byte-identical.
  *Build B* (to write): every in-scope function from C (`src` or `ref`), the
  out-of-scope code from asm/libraries, linked by symbol rather than in place.
  It cannot be byte-identical; it must pass a **T5 scenario set** under `wc1.run`.
  The set is still to be defined: at least boot to the main menu, start a
  mission for each side and a scripted input replay, compared with the
  original under the same input.
* **M4 (optional): original compiler.**  With a user-supplied Watcom C/C++ 10.x,
  re-run `wc1.match` on every `ref` file; matches become T3.  Not required for
  the goal.

## 4. Gates (the goal is met when all three pass)

`make goal` runs all three and prints PASS/FAIL per gate; it exits 0 only when
the project is done.

1. `python3 -m wc1.progress --check` exits 0: every in-scope function is done.
2. `make verify` is green: symbols, round-trip, every `src` matches, Build A
   IDENTICAL, all tests (including every `ref_verified_by` difftest).
3. Build B passes the T5 scenario set.  Not defined yet (M3): `make goal`
   reports it as FAIL until M3 adds the command; update the Makefile target
   and this section then.

## 5. Autonomous runs (OpenCode `/goal`)

How the work proceeds (order, delegation, commits, hand-off) is in AGENTS.md,
which OpenCode loads into every session, so the objective only needs the
finish line:

    /goal Make `make goal` pass.

Keep the finish line in the objective itself.  OpenCode's `/goal` judges
"done" after every turn from the objective text, and that text is what it
re-injects after the conversation is compacted; a bare "work towards
docs/GOAL.md" would count any progress as done.

What to expect (OpenCode 2.2.6):
* it pauses after 50 rounds, after 3 rounds without progress, when the server
  restarts, or when you press Esc; `/goal` shows the reason, `/goal resume`
  continues (and resets the round count);
* gate 3 is undefined until M3, so a run eventually stops "blocked" there:
  that is the point where the T5 scenario set needs to be decided with the user.
