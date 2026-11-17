# Speeding up agent-session startup (`nix develop -c make verify`)

Observed 2026-11-15: a fresh session's first `make verify` ran 10+ minutes and
was still stuck on `building '/nix/store/...-open-watcom-v2-unwrapped-...drv'`
(`wmake ... bootstrap=1`). The cost is not the checks themselves but the
toolchain being compiled from source in the local store, restarted on every
interrupted session. The notes below are recommendations, ordered by impact.

Status (2026-11-18): the startup problem is solved by 1 and 2 (the toolchain
is built and pinned; `nix develop` enters in seconds). Still open: 5 (the
remaining cost is `make verify` itself, ~2.5 min: tests ~1 min, round-trip +
match-all + build the rest) and 6; 3, 4 and 7 are low value at present.

## 1. Let the in-progress build finish once (zero effort)

*Status: done (the open-watcom-v2 closure is in the store).*

After the open-watcom-v2 closure (and ghidra etc. for the default shell) is in
the store, `nix develop -c make verify` enters in seconds. Do not kill sessions
mid-build: nix builds are atomic per derivation, so an interrupted Watcom
build starts from zero next time.

## 2. Protect the built toolchain from GC and re-resolution

*Status: applied as an explicit GC root. The `flake.nix` shellHook (both
shells) runs `nix-store --add-root .gcroots/open-watcom --indirect --realise`
on the Watcom store path at every shell entry (`.gcroots/` is git-ignored).
`keep-outputs`/`keep-derivations` are not set in nix.conf; not needed for
the expensive part.*

- `nix.conf`: `keep-outputs = true`, `keep-derivations = true` so GC does not
  delete the realized closure and its `.drv`s.
- Or add an explicit GC root:
  `nix build .#devShells.x86_64-linux.default -o /nix/var/nix/gcroots/wc1-shell`
- On NixOS, include the shell's packages in the system configuration instead;
  that survives any `nix-collect-garbage`.

## 3. Watcom is unfree: no public substitute

*Status: not done; only matters with more than one machine.*

`open-watcom-v2` is unfree, so `cache.nixos.org` will not serve it (binary
caches refuse unfree derivations) and it is compiled from source on every
machine. If more than one machine or worktree needs it, publish a private
cache (cachix, or `nix copy --to ...`) and set `substituters` in `nix.conf`.
The source here is also pinned to a specific unstable revision in
`flake.lock`, so cache keys change whenever inputs are updated.

## 4. Use the lighter `ci` dev shell for verification

*Status: not adopted. `devShells.ci` exists, but AGENTS.md and the agent
definitions use the default shell; with its closure already realised the
gain is small.*

`flake.nix` already defines `devShells.ci` (coreTools only; no ghidra,
dosbox-x, imagemagick, radare2, gdb). Verified: `tests/test_ghidra.py` does
not run Ghidra, and no other `make test`/verify step needs the analysis
tools, so:

    nix develop .#ci -c make verify

is much lighter to realize while still running all five stages. Worth making
this the canonical verify command in `AGENTS.md`.

## 5. Make `verify` itself incremental and parallel

*Status: not done; the most useful remaining item, since the AGENTS.md
commit policy runs `make verify` before every code commit. Parallel
`match-all` is safe; a green-stamp must key on the full tree state so a stale
stamp cannot hide a breakage. Changing the `verify` target needs the user's
approval (AGENTS.md ground rules).*

- Stamp a green run: on success write `git rev-parse HEAD` (plus tree hash) to
  `build/.verify-ok`; make `verify` a no-op when it matches and `build/` and
  sources are untouched. New sessions then pass verify in <1 s.
- Parallelize `match-all`: it currently compiles and compares each `src/*.c`
  one by one; the per-file `wc1.match` calls are independent, so
  `xargs -P "$(nproc)"` uses the 20 cores (machine here reports 20).

## 6. Run verify in the background at session start

*Status: not in AGENTS.md.*

Session agents can start `nix develop .#ci -c make verify` as a background
command (OpenCode shell `background=true`), continue the audit/analysis while
it runs, and gate only the commit on its result. Reflect the pattern in
`AGENTS.md`.

## 7. Update inputs rarely, then warm the store immediately

*Status: not pinned to a release branch, but harmless while inputs are not
updated: flake.lock holds nixos-unstable at 494ce7f (2026-10-05).*

`inputs.nixpkgs.url` floats on `nixos-unstable` (locked only until the next
`nix flake update`). Every update resolves new revisions ⇒ full rebuild of the
chain (Watcom again). Pin to a stable release branch, or update deliberately
and immediately re-run step 1/4 to warm the store.

## Minor: eval-cache lock contention

Concurrent `nix` invocations can block on
`~/.cache/nix/eval-cache-v6/*.sqlite` (`error: ... is busy`). With background
verify running, avoid launching other `nix develop` commands in the same
session, or expect them to queue.
