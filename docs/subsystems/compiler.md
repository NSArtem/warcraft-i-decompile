# Compiler: war.exe was built with Watcom C/C++ 10.0a

**Verdict:** Watcom C/C++ 10.0 at patch level A (10.0a), or 10.0b, which no
test on war.exe can tell apart (section 3).  Every other obtainable Watcom
version is ruled out.  The project calls the compiler "10.0a" and uses it
alongside Open Watcom 2 (section 4).

The full evidence, tools, candidate table and log are in the research repo
`warcraft-1-decompile-compiler`, branch `compiler`, commit 292764a
(`docs/subsystems/compiler.md` and `docs/COMPILER_HUNT.md` there).  This page
keeps the result and what the main repo needs from it.

## 1. Deciding evidence

Eleven versions were compared: 9.5, 10.0 LA, 10.0 GA, 10.0a, 10.0b, 10.5,
10.5a, 10.6, 10.6a, 11.0 and Open Watcom 2.

* **Runtime library (does not depend on our C).**  190 library functions in
  war.exe are byte-identical to 10.0a's patched libraries.  The next best are
  10.0 GA 176, 10.0 LA 154, 10.5a 83, 10.5 81, 10.6 76, 11.0 57, 9.5 17,
  OW2 8.  The 14 units only 10.0a matches all come from modules that patch A
  replaced (`cstrt386` `_cstart_`, `sigsy`, `grownear`, `timeutil`
  `__isindst_`, `fpeinth`).
* **DOS extender.**  The shipped `dos4gw.exe` (265,420 B, md5
  `ee4033581845b3b8d28c4b7287eb4fc2`) is byte-identical to 10.0a's, and to no
  other version's.  Its "WATCOM patch level .a" trailer is written by BPATCH
  when patch A updates the extender; war.exe itself carries no trailer.
* **Code generation (patch A's compare fix).**  The 10.0a README: "a compare
  of an unsigned type shorter than an int and a constant ... would be done as
  the original type instead of being promoted to an integer."  10.0a/10.0b
  emit `and eax,0xff; cmp eax,imm`; 9.5, 10.0 GA, 10.5, 10.6 and OW2 emit
  `cmp al,imm`.  war.exe's game code has the promoted form 35 times in 17
  modules and the byte form never (outside switch range checks and library
  code).  So no game object was compiled before patch A.
* **Our C.**  10.0a matches 73 of the 75 functions that were T3 under OW2, 18
  of the 87 reference functions (no other version more than 14), and on
  every fair-spelling set (the same 10 or fewer variants for every version)
  it matches a superset of what the others match.  The unoptimised (OD)
  frame `sub esp,0` is reproduced by every version before 11.0, and not by
  OW2/11.0 (`sub esp,4`).

Not decisive: the LE layout (every candidate's wlink writes it) and the MZ
stub (matches no candidate; Watcom ships `wstub.c`, so a custom stub is
normal).

## 2. Two facts that look like contradictions and are not

* **CheatCodeCommand** (0x12a2c) tests the developer-cheat flag with
  `test byte [cheat_flags+3],0x80`.  10.0a produces that from an `unsigned
  char` bitfield (or an `unsigned long` mask), not from a union byte, which
  10.0a promotes to `and eax,0xff`.  CMD.C's real flags are `-s -ot -oa -ol
  -4r -zp2`; with them FogMapObscure and MapViewSetScroll match only under
  10.0a.
* **0x31c12 `pickup_`** (in `_makepath`) has the un-promoted byte compare.
  It is library code: the 10.0a library still carries a `pickup_` built by
  the pre-A compiler, byte-identical from 9.5 to 10.0a.

## 3. 10.0a or 10.0b

Patch B (`c_b.zip`, files dated 1995-01-11) changes only the `-fpd` Pentium
FDIV workaround, math routines recompiled with `-fpd`, and the clib modules
`fsmth386` / `div386`.  war.exe links neither module, has one x87 division
(in the runtime's `__init_80x87`, byte-identical to 10.0a's) and no
`__chipbug` reference; on every C file and flag set the two compilers gave
the same output.  Only an `-fpd` object of the same build or Blizzard's
build records could separate them.  For this project they are the same
compiler.

## 4. How the main repo uses it

* **Install** (user-supplied, like the CD; never committed or downloaded):
  `make toolchain` with `WATCOM10A=<10.0a installation>` or
  `wcc10.0a.tar.gz` in the repo root.  It copies what wc1.oldcc needs into
  `original/watcom/10.0a/` (git-ignored), checks every file against
  `analysis/provenance/watcom10a.sha256`, creates the Wine prefix
  (`build/oldcc/wineprefix`) and runs a smoke compile whose patch-A compare
  promotion proves the right compiler ran.
  * Source of the tarball: https://archive.org/download/compiler-watcom-watcom-c-c-wcc386-10.0a-win32/
    `wcc10.0a.tar.gz`, 9,247,235 B, sha256
    `920a9674d1b10f227ae65171c187212b06d7fc38b263313922615c4f5e9b24a6`
    (compiler and headers; its `wcc386.exe` is byte-identical to the
    patched CD installation's).
  * The runtime libraries are not in the tarball.  They are optional (only
    `wc1.clib_sig --root` reads them) and come from a 10.0a installation:
    the 10.0a CD (WATCOM_C10A.ISO, sha256 `f51ed935...`) with patch A
    (`c_a.infobase.zip`) applied, as the research repo did.
* **Run:** `wc1.oldcc` runs `binnt/wcc386.exe` (which loads
  `binb/wcc386.exe`) under Wine (flake.nix), headless.  About 0.15 s a
  file: Wine's output goes to a file, not a pipe, because the wineserver
  holds an inherited pipe open for seconds.
* **Select per file:** `/* codegen-compiler: 10.0a */` in the header; no
  header means OW2.  wc1.match, the build, wc1.cemu and wc1.codegen_sweep
  follow it; `--cc` overrides it for experiments.
* **Rules** (docs/METHODOLOGY.md T3, docs/GOAL.md): a match under either
  compiler is T3; every C file compiles under both (`make compile-check`);
  `make verify` fails when 10.0a is not installed.  New C is written for
  10.0a first; OW2 remains the compiler anyone can build the source with.
