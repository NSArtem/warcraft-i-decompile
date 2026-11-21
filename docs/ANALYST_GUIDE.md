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
