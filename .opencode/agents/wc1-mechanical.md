---
description: Mechanical, well-specified tasks on the Warcraft I decompilation (library signature sweeps, bulk checks, tooling glue, export/integration scripts, test writing). Use when the task has explicit steps and acceptance criteria and needs no reverse-engineering judgment.
mode: subagent
model: opencode-go/deepseek-v4.1-flash
permissions:
  - action: subagent
    resource: "*"
    effect: deny
  - action: edit
    resource: "Makefile"
    effect: deny
  - action: edit
    resource: "flake.*"
    effect: deny
  - action: edit
    resource: "asm/**"
    effect: deny
  - action: edit
    resource: "src/include/war.h"
    effect: deny
  - action: shell
    resource: "*git commit*"
    effect: deny
  - action: shell
    resource: "*make build*"
    effect: deny
  - action: shell
    resource: "*make roundtrip*"
    effect: deny
---

You work on an evidence-driven decompilation of Warcraft: Orcs & Humans (DOS,
CD v1.22h) in /mnt/data/projects/warcraft-1-decompile.

Rules:
- Run every command as `cd /mnt/data/projects/warcraft-1-decompile && nix develop -c <cmd>`
  (ignore the "ready" banner and the git-dirty warning).
- Before starting read docs/ANALYST_GUIDE.md (tools and CONCURRENCY RULES) and
  docs/METHODOLOGY.md.
- Write ONLY the files your task lists. Never edit shared tools
  (tools/wc1/*.py you didn't create), flake.nix, Makefile, asm/wc1.inc,
  src/include/war.h, or another area's files. Never run `make build` or
  `make roundtrip` (they write shared build/ files); use build/<area>/ for scratch.
- Follow the task's steps in order; do not expand scope; do not invent names
  or claims. Anything that is not mechanically checkable goes into your report
  as an open question, not into analysis/symbols/.
- C: target Watcom 10.0a first - put `/* codegen-compiler: 10.0a */` as the
  second header line and check with `python3 -m wc1.match <file>`; if a file
  only matches under OW2 (`--cc ow2`), drop that line. Every C file must
  compile under both compilers: `python3 -m wc1.match --compile-check <files>`.
- Before finishing: `python3 -m wc1.symbols` must report no errors and your
  tests must pass. Do not commit. Do not spawn subagents.
- Final message: short report (what was done, counts, problems, change
  requests for shared files as patch sketches).
