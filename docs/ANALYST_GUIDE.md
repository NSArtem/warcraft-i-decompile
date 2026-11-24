# Analyst guide (humans and agents)

Read `docs/METHODOLOGY.md` first. Everything runs inside the Nix dev shell:
`nix develop -c <command>` (or `nix develop` interactively). Never commit
anything under `original/` or `build/`.

## Facts about the target

* `original/install/war.exe`: LE executable, Watcom C/C++32 (1994) + DOS/4GW.
  Code object 1 at `0x10000` (size `0x3212b`), data object 2 at `0x50000`
  (`0x155f0`; initialised part to `0x5853c`, then BSS; `0x64180..0x655f0` is
  the main stack; `0x635e4..0x64180` a private stack of some interrupt handler — not the AIL timer ISR, which uses 0x56478).
* Every absolute address in the program carries an LE fixup, so pointers vs
  integers are known exactly (`p.fix_at`).
* Calling convention of compiled code: Watcom register (`watcall`): args in
  `eax, edx, ebx, ecx`, further args pushed right-to-left and removed by the
  *callee* (`ret N`; e.g. `InitPaths` pushes LoadFile's 5th argument and never
  pops it). Variadic functions (`printf`-like) take all args on the stack and
  the *caller* pops (`add esp, N` after the call). Return value in `eax`
  (`ax`/`al`). Callees preserve every register they modify except `eax`
  (hence the long push/pop prologues). Link names: functions `name_`, data
  `_name`. Hand-written asm and third-party libraries (AIL) differ: check.
* **Compiler.** war.exe was built with Watcom C/C++ 10.0a
  (docs/subsystems/compiler.md). The project has two compilers: Watcom 10.0a
  (`make toolchain` installs it into `original/watcom/10.0a`, git-ignored like
  the CD; it runs under Wine, about 0.13 s per compile) and Open Watcom 2 in
  `$WATCOM`. A C file chooses its compiler with a second header line
  `/* codegen-compiler: 10.0a */`; without it the file is compiled by OW2. **New
  C targets 10.0a first**; OW2 is the fallback for a file that only matches
  there. Every file in `src/` must compile under **both** (`make compile-check`,
  part of `make verify`). 10.0a also settles most former OW2 near misses: it
  emits the original's `sub esp,0` OD frames and register choices, and it
  promotes byte compares (`and eax,0xff; cmp eax,imm`), so a `test byte` in the
  original is usually a bitfield in the source (compiler.md section 2).
* Codegen comes in three styles, per object file (docs/subsystems/codegen.md,
  `python3 -m wc1.codegen_survey`): OPT (most game code, clib) =
  `wcc386 -s -ot -ol -4r -zp2` (the default); DBG (video/input/resource
  library objects: ebp frame inside the register saves) = OPT + `-d1+`;
  OD (`-s -od -4r -zp2`: `sub esp,0` frames, short jumps; e.g. 0x26b18..0x27661,
  0x30ea0..0x31789) is reproduced by 10.0a only (OW2 writes `sub esp,4`). A C file states
  its flags in a header line `/* codegen-flags: -s -ot -ol -4r -d1+ -zp2 */`,
  read by `wc1.match` and `wc1.build` (`--cflags`/`WC1_CFLAGS` override).
  The OW2 register-order/zero-extension workarounds in codegen.md are
  history for files compiled by 10.0a.

## Tools (python package `tools/wc1`)

| Command | Purpose |
|---|---|
| `python3 -m wc1.func <addr|name>` | symbolic disassembly of one function, with DB names |
| `python3 -m wc1.xref <addr|name> [--range N]` | callers, pointer refs, callees, data refs |
| `python3 -m wc1.dis <addr> [n]` | raw linear disassembly with fixup annotations |
| `python3 -m wc1.symbols` | validate the symbol database |
| `python3 -m wc1.match src/x.c [--cc ow2\|10.0a\|other]` | T3 check of reconstructed C (flags from the file's `codegen-flags:` header, compiler from `codegen-compiler:`; `--cc` tries the other one) |
| `python3 -m wc1.match --compile-check [files]` | every file (default: all of `src/`) must compile under both compilers |
| `python3 -m wc1.permuter src/x.c [--apply] [--timeout 60] [--wall-budget 900]` | local flag/idiom search toward T3 (0 tokens); stops at the first compile timeout (exit 2) or the wall budget |
| `python3 -m wc1.t3_audit [--dry-run] [--addr HEX] [--limit N] [--jobs N] [--include-unverified] [--output DIR]` | read-only bulk audit: compiles every in-scope T4 reference C under Watcom 10.0a (declared flags, then the `wc1.permuter` 10.0a presets) and reports T3 promotion candidates and ranked near misses to `build/t3_audit/` (JSON, Markdown, CSV); changes no source or TOML |
| `python3 -m wc1.batch_driver` / `python3 -m wc1.overnight [--stall-timeout 1200]` | LLM batch pipeline for one area / the unattended queue runner (`wc1.tui` on a TTY) |
| `python3 -m wc1.oldcc --check` / `make toolchain` | check / install Watcom 10.0a (from `$WATCOM10A`, a directory or `wcc10.0a.tar.gz`) |
| `python3 -m wc1.clib_sig --root original/watcom/10.0a` | library signatures against the 10.0a runtime libraries |
| `python3 -m wc1.analysis` | code discovery statistics |
| `python3 -m wc1.build` | build `build/war.exe` (asm + C linked in place; must be IDENTICAL, docs/subsystems/build.md) |
| `python3 -m wc1.run <exe> --at 10,20 --name tag` | headless DOSBox-X run with screenshots |
| `python3 -m wc1.compare a.exe b.exe` | loaded-image comparison |
| `python3 -m wc1.ghidra_decomp run` / `show <addr|name>` | headless Ghidra export of every function to `build/ghidra/decomp/` (Watcom `__watcall` convention added); `show` prints one. A hint, never evidence |
| `wc1.emu.Emu` (library) | run original functions under Unicorn for T4 difftests (watcall/cdecl calls, stubs, int/IO traps); see `tests/test_emu.py` |
| `wc1.omf` (library) | read OMF objects / Watcom `.lib` files (`$WATCOM/lib386/...`, `original/watcom/10.0a/lib386/...`) |
| `wc1.cemu` (library) | load compiled C (either compiler) next to the original under wc1.emu and `run_pair` them: the T4 harness |
| `wc1.le`, `wc1.analysis` (library) | LE parser; `analysis.run()` → `Program` with `insns`, `functions`, `fix_at`, `image` |

Watcom 10.0a is in `original/watcom/10.0a` (or `$WC1_WATCOM10A`; headers `h/`,
runtime libs `lib386/dos/clib3r.lib` and the math libs).
Open Watcom 2 is in `$WATCOM` (headers `$WATCOM/h`, libs
`$WATCOM/lib386/dos/clib3r.lib`, `$WATCOM/lib386/math387r.lib`, …).
Ghidra and DOSBox-X are on PATH in the dev shell.

Unattended runs are bounded at every level, so a stuck Wine/wcc386 cannot
wedge a night (incident of 2026-11-22, docs/HISTORY.md): a 10.0a compile is
killed after 180 s (`oldcc.OldCCTimeout`, then `wineserver -k`), a permuter
candidate after 60 s and the search after 900 s; batch_driver's pytest runs
are capped at `PYTEST_TIMEOUT` (900 s; the whole process tree is killed) and
beat the worker meta every 60 s.  A compile timeout is a toolchain error,
also inside `match.compile_check` (it raises instead of counting a failure):
batch_driver and the `wc1.match` CLI (so also `make verify`) print
`[TOOLCHAIN ERROR]` and exit 78 (`EXIT_TOOLCHAIN`); overnight then
archives + rolls back the item (`TOOLCHAIN_ERROR`), stops the run before
any LLM repair, marks it FAILED and exits 78.  overnight's stall watchdog
(`--stall-timeout`, default 1200 s, 0 off, at least `PYTEST_TIMEOUT` + 60)
kills a batch_driver that printed nothing and beat no heartbeat for that
long, or a `make verify` that printed nothing (output only: nothing beats
the meta there), SIGUSR1 first (faulthandler dumps its stacks into the log);
it then runs `wineserver -k`, archives + rolls back the item (`STALLED`)
and goes on with the next one.  A permuter search cut short by a timeout
never writes its winner.

`wc1.t3_audit` reads its candidates from `symbols.load` +
`progress.classify` (T4 = `ref` + `ref_verified_by = "difftest:..."`;
`--include-unverified` adds ref-only entries as diagnostics, never as
candidates).  Each ref file is compiled into its own
`build/t3_audit/obj/a<k>/` directory, with the declared `codegen-flags`
first and then the 10.0a presets, stopping at the first set under which the
whole object matches.  Every function ends up as `MATCH_BUILDABLE` (a
promotion candidate: `build.check_t3_buildable` accepts the file),
`MATCH_UNBUILDABLE` (with the reason, e.g. a sibling in the same file still
mismatches), `MISMATCH` (best flags, first difference, score),
`COMPILE_ERROR`, `TOOLCHAIN_ERROR` or `SKIPPED` (invalid entry, a link name
claimed by two entries or missing from the object, not reached, or a compile
error discarded because a parallel compile timed out beside it).  A compile
timeout is a toolchain error, never a mismatch: the run stops with
`[TOOLCHAIN ERROR]` and exit 78, Ctrl-C gives exit 130; both write the
reports marked `aborted`/`interrupted` with the unreached functions
`SKIPPED`.  Old reports are deleted at the start and `report.json` is
checkpointed after each file, so a killed run leaves only a `report.json`
marked `running`, never a stale Markdown/CSV. `attempts[].unresolved` records
all missing external fixups in the audited `_TEXT` function, even when no
corresponding original operand is found or `problems` is truncated. An
`original_candidate` is a same-offset lead, not proof of the target. The
instruction diff labels unresolved operands instead of comparing linker
placeholders as numbers; a zero heuristic score can still be a strict
mismatch. Limitations: the buildability check is
`build.check_t3_buildable` as is, so it compiles the file's siblings with
`os.cpu_count()` workers whatever `--jobs` says, writes
`build/cache/anchors.json`, and reports a compile timeout inside it as a
plain failure (`MATCH_UNBUILDABLE`, not exit 78); the audit passes the ref
file's own directory as an include path, which `wc1.match` on the command
line does not.  Promoting a candidate (header flags, `src =`, a test) is
manual work, done and verified like any other T3.

Wave 4 is split into two stages integrated into `wc1.overnight` and
`wc1.batch_driver`:

- **Wave 4A (`--wave wave4a`, `batch_driver t3-reconcile <group_id>`)**:
  Symbol and dependency reconciliation (`tools/wc1/wave4_deps.py`,
  `tools/wc1/wave4a.py`). Builds a complete dependency inventory from
  `attempts[].unresolved` across all in-scope T4 functions (using an
  incremental per-unit audit state in `build/wave4/audit_state.json`),
  corroborates target addresses against original disassembly/LE fixups and
  cited T4 test fixtures (never identifier spelling alone), groups shared
  callers/interior fields by underlying target, and runs: (0) zero-LLM
  auto-promotions for already `MATCH_BUILDABLE` objects, (1) deterministic
  syntax-aware mechanical rewrites (0 LLM calls) when ABI/types and
  corroboration are proven safe, and (2) bounded fresh-context LLM research
  (`--wave4a-max-calls`, default 2; `0` = mechanical only) for ABI mismatches,
  containing data object fields, missing functions/data, and ambiguous
  targets. Accepts either `PROMOTED` (+T3) or verified intermediate
  `RECONCILED` commits (strictly fewer unresolved relocations, `make verify`
  green, Build A `IDENTICAL`, zero tier regressions, anti-weakening enforced).
- **Wave 4B (`--wave wave4b`, `batch_driver t3-recovery <addr>`)**:
  Codegen recovery (`tools/wc1/wave4.py`). Concentrates on genuine codegen
  differences (flag search then bounded `--wave4-max-calls` LLM repair).
  Functions with unresolved relocations are routed to Wave 4A by default
  (override with `--wave4-include-unresolved` or explicit `--only 0xADDR`).
- **Combined Wave 4 (`--wave wave4`)**: Runs Wave 4A first until its queue
  drains, then automatically transitions to Wave 4B.

Both stages skip completed, clean misses (`NO_IMPROVEMENT` / `AMBIGUOUS`)
under the same inputs (`build/wave4/reconcile_cache/` for 4A,
`build/wave4/retry/` for 4B), keying on resolved sources/includes, matcher
symbol addresses/extents, original `war.exe`, Watcom compiler contents,
model/effort, and call budget — never Git HEAD. Use `--wave4-retry` (with
`--only`) to reconsider cached misses. Established mappings persist in
`build/wave4/mappings.json`, live outcomes in `build/wave4/reconcile_outcomes/`
and `build/wave4/outcomes/`, and structured run metrics in
`build/wave4/metrics.json`.

Run Wave 4 in an exclusive worktree, with no untracked build inputs and
Git hooks that do not mutate the worktree or index. A rejecting hook is
handled, but the runner cannot lock out concurrent writers or validate
changes a successful hook makes inside Git's temporary index. If HEAD
moves during an attempt, the runner refuses to restore over it.

### Runtime T4 audit trust boundary

The runtime T4 oracle audit (`WC1_T4_AUDIT_LOG`) defends against
accidental/opportunistic LLM cheats and mid-run overrides, not a hostile
in-process sandbox (e.g. post-load `cmod.extra` mutation, external stubs
toggling `emu.trace`/`emu.stubs` mid-call, or deliberate env/file forging).
12 legacy hand-written T4 nodes bypass `cemu.run_pair` (list:
docs/HISTORY.md, full-repo 373-node audit).

## Concurrency rules (several analysts work in the same tree)

* **Own files only.** Each analyst gets an area and writes only:
  `analysis/symbols/<area>.toml`, `docs/<area>/...` or `docs/subsystems/<area>.md`,
  `src/<area>/*.c` (or files named in the assignment), `src/include/<area>.h`,
  new tools under `tools/wc1/<area>_*.py` or `tools/<area>/`, and tests
  `tests/test_<area>*.py`.
* Do **not** modify existing shared tools, `flake.nix`, `Makefile`,
  `asm/wc1.inc`, `src/include/war.h` or another area's files. If you need a
  change, describe it in your final report (with a patch sketch).
* Do **not** run `make build`/`make roundtrip` (they write shared files in
  `build/`). For scratch output use `build/<area>/` or the scratch dir you
  were given. `wc1.match` writes only `build/match/<compiler>/<file>.obj`.
* Don't add an address that another area's TOML already names; run
  `python3 -m wc1.symbols` before finishing — it must report no errors.

## Workflow for a function

1. `wc1.func` + `wc1.xref` it; read callers to learn argument meaning.
2. Record name/proto/evidence/confidence in your TOML.
3. Write C in your area's file with `/* codegen-compiler: 10.0a */` as its
   second header line; `wc1.match` until MATCH (if it only matches under OW2,
   `--cc ow2`, drop the header). One function per file where a neighbour in
   the original is not built from C (objects are placed in sequence). Add
   `src = "src/<...>.c"` and `confidence = "verified"`,
   `verified_by = "match: ..."` only when it matches. If T3 is out of reach
   after the attempts docs/GOAL.md section 2 lists, keep the C in
   `src/<area>/<name>_reference.c`, set `ref = ...` and
   `t3_blocker = "<od-frame|regalloc|codegen>: <evidence>"`, and add
   `ref_verified_by = "difftest: tests/<file>.py::<test_name>"` once a test
   runs the compiled C against the original. `make symbols` validates every
   cited `ref_verified_by` node via AST: the test file and node must exist
   under `tests/`, the cited node must not skip or xfail (inline or by
   decorator; put environment gates like `war.exe`/`$WATCOM` in a module-level
   `pytestmark = pytest.mark.skipif(...)`), and the file must mention the
   reference C filename (indirect skips via helpers are caught at runtime by
   `wc1.batch_driver.verify_t4_node` / `make verify`). `make progress` shows
   what each function still needs.
4. Library code: compare with the Watcom 10.0a libraries (`wc1.clib_sig --root
   original/watcom/10.0a`, or `wc1.omf.parse_library`); a byte-identical module
   (modulo relocation fields) is `libsig:` verified.

## Writing evidence

Good: `"prints 'Not enough gold...mine more gold' (0x57158) when gold < cost
(cmp at 0x2a1c4)"`. Bad: `"looks like the gold check"`.
