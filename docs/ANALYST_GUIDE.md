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
* Game code was compiled with flags reproduced by `wcc386 -s -ot` (no stack
  checks). Keep `-q -zl -bt=dos -s -ot` unless evidence says otherwise.

## Tools (python package `tools/wc1`)

| Command | Purpose |
|---|---|
| `python3 -m wc1.func <addr|name>` | symbolic disassembly of one function, with DB names |
| `python3 -m wc1.xref <addr|name> [--range N]` | callers, pointer refs, callees, data refs |
| `python3 -m wc1.dis <addr> [n]` | raw linear disassembly with fixup annotations |
| `python3 -m wc1.symbols` | validate the symbol database |
| `python3 -m wc1.match src/x.c` | T3 check of reconstructed C |
| `python3 -m wc1.analysis` | code discovery statistics |
| `python3 -m wc1.build` | build `build/war.exe` (asm + C) |
| `python3 -m wc1.run <exe> --at 10,20 --name tag` | headless DOSBox-X run with screenshots |
| `python3 -m wc1.compare a.exe b.exe` | loaded-image comparison |
| `python3 -m wc1.ghidra_decomp run` / `show <addr|name>` | headless Ghidra export of every function to `build/ghidra/decomp/` (Watcom `__watcall` convention added); `show` prints one. A hint, never evidence |
| `wc1.emu.Emu` (library) | run original functions under Unicorn for T4 difftests (watcall/cdecl calls, stubs, int/IO traps); see `tests/test_emu.py` |
| `wc1.omf` (library) | read OMF objects / Watcom `.lib` files (`$WATCOM/lib386/...`) |
| `wc1.le`, `wc1.analysis` (library) | LE parser; `analysis.run()` → `Program` with `insns`, `functions`, `fix_at`, `image` |

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
  were given. `wc1.match` writes only `build/match/<file>.obj`.
* Don't add an address that another area's TOML already names; run
  `python3 -m wc1.symbols` before finishing — it must report no errors.

## Workflow for a function

1. `wc1.func` + `wc1.xref` it; read callers to learn argument meaning.
2. Record name/proto/evidence/confidence in your TOML.
3. Optionally write C in your area's file; `wc1.match` until MATCH. Add
   `src = "src/<...>.c"` and `confidence = "verified"`,
   `verified_by = "match: ..."` only when it matches.
4. Library code: compare with OW2 libraries (`wc1.omf.parse_library`); a
   byte-identical module (modulo relocation fields) is `libsig:` verified.

## Writing evidence

Good: `"prints 'Not enough gold...mine more gold' (0x57158) when gold < cost
(cmp at 0x2a1c4)"`. Bad: `"looks like the gold check"`.
