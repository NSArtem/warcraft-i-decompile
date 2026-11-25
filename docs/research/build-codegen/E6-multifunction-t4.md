# E6 — Multi-function T4 verification with explicit boundaries

Date: 2026-11-25. Baseline: `3ee53aa5d4e7911e7f8d1bb0097de17223c8a559`.
Development branch: `research/build-codegen/e6`.
Contract: `e6-r2-v2`; experimental only. Hardened after Independent Review
Round 1 (`rev-e6-01`, `REQUEST_CHANGES`) by replacement session `dev-e6-02`.

## Finding

The two real consolidated translation units pass differential verification in
Isolated, Group and Integrated modes under the declared scenario contracts.
Options Group/Integrated retain heap addresses for the real compiled callbacks;
the comparison accepts only four explicitly typed pointer slots, with exact
logical targets, preserved equality relations, actual callback execution and
matched effects. All nine negative-control families fail closed
(fourteen variants, including both asymmetric directions, N4a–c, static and
dynamic trailing-code entry bypasses, and callback ABI violations).

**The zero-FIXUPP premise for the real PLAYFLIC pair is refuted.** Watcom 10.0a
emits a direct `call rel32` with **one EXTDEF FIXUPP**, targeting
`IntroLoadCreditLines_`. The original-address stub is still bypassed because
legacy `CModule` resolves the symbol to the local compiled entry. A separate
NASM fixture demonstrates successful entry-hook substitution with **zero**
call fixups. No claim that the real C pair had zero fixups is made.

This supports the verification architecture for the exercised cases. It does
not establish arbitrary multi-function isolation, exhaustive equivalence, or
production readiness, and does not promote any production T4 entry.

## Reproduction and artifacts

Use the already configured Nix shell, with the original game and Watcom 10.0a
available. Run from the repository root:

```sh
pytest -q experiments/build_codegen/e6/test_e6.py
python3 -m experiments.build_codegen.e6.run_e6
python3 -m experiments.build_codegen.e6.run_e6 --check
git diff 3ee53aa -- tools/ src/ analysis/ tests/ Makefile
```

The test suite passes **96 tests**, with no skips or xfails. The CLI runs ten
positive scenarios, fourteen negative variants, two baseline reproductions and
one supplemental zero-fixup positive case. `--check` recomputes and requires
byte-identical JSON; timing, temporary paths, timestamps and current HEAD are
excluded from the artifact.

- [Harness](../../../experiments/build_codegen/e6/mf_cemu.py)
- [Scenario definitions](../../../experiments/build_codegen/e6/scenarios.py)
- [Tests](../../../experiments/build_codegen/e6/test_e6.py)
- [Runner](../../../experiments/build_codegen/e6/run_e6.py)
- [Machine-readable evidence](results/e6/results.json)

The JSON includes source/implementation hashes, parsed-OMF digests, compiler
manifest verification and executable hash, original `war.exe` hash, library
versions, public/static offsets, exact verification ranges, instruction and
function-visit counts, callback events and ABI deltas, dependency logs and
rejection reasons.
The compiled fixtures use Watcom 10.0a with `-s -ot -ol -4r -zp2`.
Compilation is fresh, with temporary objects under E6 that are removed after
parsing; no generated objects or original game bytes are committed.

## Contract and implementation

`VerificationBoundary` explicitly contains link names and original/compiled
`[lo, hi)` ranges. Original ranges come from discovery/partition of the loaded
image. Compiled ownership ranges cover the full contiguous span from each OMF
function symbol to the next symbol in its segment, or to the segment end.
Trailing code after a return and alignment bytes remain owned by that symbol;
entry reachability is recorded separately and never truncates ownership.
Construction checks names, ranges, non-overlap and correspondence to actual
compiled publics. Every boundary
function must execute on both sides in a successful scenario.

`DependencySubstitutionPolicy` maps exact symbol names to original address,
handler, stack-pop count and one of three mechanisms. Symbol/address identity
is checked against the production symbol database. The only trusted built-in
runtime model is the unchanged `0x31789` flat `_memcpy` model.

1. `orig_addr_stub`: ordinary external dependency, resolved by the legacy
   loader to its original address, with the same stub on both executions.
2. `symbol_aware_reloc`: only an explicitly declared dependency **outside**
   the boundary may override EXTDEF/LEXTDEF local-name priority and resolve to
   its original address. This is relocation during object placement. Calls
   without a corresponding fixup also have an entry hook available.
3. `c_entry_hook`: a Unicorn `UC_HOOK_CODE` hook at the compiled sibling entry
   mirrors the original-address stub, including EAX return and `ret N` stack
   cleanup. The code bytes stay intact.

Hooks are forbidden on verified functions. Verified C cannot resolve or
execute into the original implementation of any boundary function. Real
original implementations outside the boundary are legitimate integrated
callees and are recorded separately from substitutions.

The `DialogRun` model is a generator. It reads the supplied parameter block,
yields each actual callback pointer, and resumes after the driver executes
that address under Unicorn. The driver saves the parent CPU context, uses a
separate lower stack area for each callback, validates its ABI, records its
result and restores the parent context. Before callback entry, it seeds
`ebx`, `ecx`, `edx`, `esi`, `edi`, and `ebp` with distinct non-zero values,
sets register arguments, and snapshots the resulting preserved registers.
After return to the sentinel, it requires every preserved register to match
that snapshot and `esp == call_sp + 4 + expected_stack_pop`. The callback
contract declares stack cleanup explicitly (zero for the real Options
callbacks); additional watcall arguments are placed on the callback stack.
Any register clobber or stack imbalance rejects the run **before** restoring
the parent context. Successful register and stack deltas are also compared
between original and C callback sequences and included in the JSON.
This avoids nested `emu_start` calls and avoids replacing the callback with a
Python model in Group/Integrated mode. Hook counts include
both the main invocation and callback bodies. Handlers must capture register
arguments before their first yield, as the caller resumes after stub return.

### R2 pointer identity

The entire 32-byte OptionsParams record is watched twice: before and after
callbacks. The only typed slots are `+0x14` (OptionsRefresh) and `+0x18`
(OptionsApplyTimer) in each snapshot. Each spec requires its particular
logical callback symbol. Correspondence requires exact boundary **entry**
addresses; interior pointers, original addresses on the C side, and other
boundary functions are rejected. There is no callback-execution opt-out.

Before comparing the remaining bytes, the checker compares the complete
pairwise pointer-equality matrix across the four slots, then checks symbol
identity and observed callbacks on both sides. Only these typed four-byte
slots receive correspondence; every other byte remains exact. Callback
identity/order/results, executed boundary functions, stub logs, watched
preferences and parameter effects are also compared. An equal non-pointer
integer elsewhere does not acquire pointer semantics.

### Fail-closed isolation and audit

Static checks decode relocated code at each known reachable instruction start
individually, so an unowned prefix or padding cannot truncate the scan. An
entry-hook dependency must have a reachable direct call/entry transfer from
the verified boundary. A symbol-aware dependency may instead have a reachable
address-taking relocation. Missing references, inlining/eliminated calls,
interior cross-function entries in either direction, cross-function
fallthrough and unresolved indirect jumps prevent isolation. Ownership checks
use the full contiguous spans, including bytes unreachable from the sibling
entry. Direct transfers into unowned executable gaps in compiled CODE segments
also reject isolation. Indirect calls are guarded dynamically. Dynamic hooks
reject execution at any non-entry byte of a substituted sibling's full span,
any unowned compiled CODE byte, and verified-original execution on the C side.
Original substituted interiors remain guarded as well.
`IsolationImpossibleError` recommends Group or Integrated mode.

The audit checks all original CODE bytes, every relocated compiled CODE
segment, source hash, parsed OMF integrity and a final fresh-compile digest.
It rejects boundary stubs, undeclared/preinstalled stubs, policy changes,
asymmetric handler/hook/stack-pop state, method overrides, public redirection,
active `emu.trace`, zero instructions and zero observations. Results are only
returned after every audit and comparison succeeds. Production
`cemu.run_pair`/`t4spec.audit_t4_log` are neither modified nor monkeypatched.
Their broad whole-C-object `c_stubbed` rule remains intact; this prototype
replaces it with an explicit, narrower verification boundary plus mandatory
policy checks for everything outside it.

The trust boundary is the repository's documented trusted in-process Python
setup, not a sandbox against hostile Python mutating Unicorn hooks or forging
expected state. The audit probes deliberately flip code bytes only to test
rejection; byte modification is never an interception mechanism.

## Real-case observations

### GAMEDLG Options family

`options_tu.c` consolidates the unchanged ApplyTimer, Refresh and Dialog bodies
in that order. The legacy run reproduces a watched-pointer mismatch:

| Callback | Original pointer | Compiled pointer in this allocation |
|---|---:|---:|
| OptionsRefresh | `0x1a79c` | `0x800190` |
| OptionsApplyTimer | `0x1a778` | `0x800160` |

Installing a sibling stub in the compiled object also produces the legacy
`c_stubbed` field. A separate legacy run watching preferences avoids the
pointer mismatch, allowing `t4spec.audit_t4_log` to reject specifically with
`compiled C segment range was stubbed during run_pair`. Baseline modules are
constructed from freshly compiled parsed OMF via the legacy prebuilt API;
these are bug reproductions, not positive production T4 proofs.

| Mode | Verified boundary | Substitution / pointer result | Original / C instructions |
|---|---|---|---:|
| Isolated | OptionsDialog | Refresh/Timer explicitly substituted; exact original pointer values; zero normalized slots | 57 / 61 |
| Group | Dialog + Refresh + Timer | Real callbacks at heap entries; four typed corresponding slots | 95 / 99 |
| Integrated | Dialog + Refresh + Timer | Same real callbacks; real downstream SndApplyOptions | 147 / 151 |

These representative CLI cases have both audio drivers absent. The Group and
Integrated callbacks change volumes `48,64 -> 0,0` and `next_apply`
`1025 -> 1055`. Ok copies the changed preferences back; Cancel preserves
`[4,48,64,2,3]`. Expiry uses the strict `t > next_apply` comparison: steps 0 and
25 do not apply, while step 26 does. The pytest matrix covers both buttons,
both race ids, all four driver-presence combinations, network-pending on/off
and timer thresholds.

Integrated stubs only ModalScreen, DialogRun, clock and the sound-volume
boundary functions. `SndApplyOptions` itself executes twice on both sides and
is never stubbed. Callback event logs identify Refresh then ApplyTimer, with
matching return-register observations, and both compiled bodies execute.

### PLAYFLIC pair

`playflic_pair_tu.c` consolidates unchanged IntroLoadCreditLines and IntroFrame
bodies. The parsed OMF has loader offset `0x0`, frame offset `0x110`, a
five-byte direct call at `0x12e`, and one self-relative EXTDEF fixup at `0x12f`
targeting `IntroLoadCreditLines_`. Resolution sends it to the compiled loader;
there is no missing-fixup explanation for this real instance.

Legacy run: the original stub is called once; the C run calls it zero times
and runs the real compiled loader, changing line_timer `5 -> 4` instead.
Both the timer and watched log diverge.

| Mode | Execution | Original / C instructions |
|---|---|---:|
| Isolated | Frame verified; Loader substituted by symmetric entry hook; identical loader log, frame_ready and wrapping tick_count | 10 / 10 |
| Group | Both compiled functions execute; only TextWidth is substituted | 64 / 65 |
| Integrated | Both compiled functions plus real original TextWidth and synthetic valid font | 224 / 225 |
| Integrated clear | Both compiled functions plus real original memset/STOS helpers clearing frame memory | 14096 / 14099 |

Tests also cover timer-zero wrap, running timers, text insertion, empty-line
clearing and the terminal delay marker. The synthetic font and frame image
live in watched scratch memory. Integrated has no explicit dependency stubs
on these paths; only the trusted built-in memcpy model remains installed.

`no_fixup_call.asm` independently supplies a real intra-segment direct call
with zero call fixups. Isolated verification passes with one matching loader
stub invocation on each side. This assembled supplemental fixture is not
presented as compiler output from the real PLAYFLIC C pair.

## Required negative controls

| Control | Concrete attempt | Observed rejection |
|---|---|---|
| N1 | Stub OptionsRefresh inside Group boundary | `boundary_stubbed` |
| N2 | Add undeclared TextWidth stub | `undeclared_stub` |
| N3 | Remove original stub while C entry hook remains, or remove C hook while original stub remains | `asymmetric_substitution` in both directions |
| N4a | Compile wrong C with Refresh/Timer initializers swapped; execute supplied callbacks | `incorrect_pointer_normalization: logical target mismatch` |
| N4b | Original snapshot pointers alias; C after-snapshot breaks that relation | `incorrect_pointer_normalization: broken aliasing` |
| N4c | Change a non-pointer byte in the watched parameter snapshot | `non_pointer_memory_diff` |
| N5 | Request original-address relocation override for verified OptionsRefresh | `verified_c_redirected_to_orig` |
| N6 | NASM branch enters substituted sibling at entry + 1 | `IsolationImpossibleError: interior_entry_bypass` |
| N6_trailing | Exact review reproducer: loader is `ret; mov word [_line_timer],7; ret`; Frame jumps to loader + 1 | `IsolationImpossibleError: interior_entry_bypass` during static checking |
| N6_trailing_dynamic | Same early-return loader, reached at + 1 by an indirect call; a separate direct entry call establishes the static reference | `IsolationImpossibleError: dynamic interior_entry_bypass` before the trailing store executes |
| N7 | Watcom pragma-aux inlines the static helper, retaining its unreachable entry | `IsolationImpossibleError: inlined/eliminated callee ... no entry reference` |
| N8 | Compiled Refresh retains its effects but adds an inline `xor ebx,ebx`, with a deliberately false pragma clobber declaration | `callback_register_clobber: c: ebx` before parent context restoration |
| N9 | Compiled Refresh has no stack arguments but returns with `ret 4` | `callback_stack_cleanup: c` before parent context restoration |

N7's caller disassembles to `mov eax,7; add eax,3; ret`; there is no call even
though the helper still has an LPUBDEF. It demonstrates why finding an entry
symbol alone cannot prove isolation. Additional tests cover entry/interior
stubs in both address spaces, public redirection, original/C byte tampering,
trace hooks, zero instructions/observations, untyped pointer differences,
missing callback execution and changed source provenance. Review-hardening
tests also check both callback failures in Group and Integrated modes, each
of the six preserved registers independently, valid and invalid `ret N` with
and without a fifth stack argument, and direct/indirect transfers into an
unowned executable prefix. The trailing-code tests prove that loader entry
reachability contains only the first `ret` while ownership extends to segment
end; neither static nor dynamic rejection modifies code or disables a checker.

The two HIGH review findings are resolved by independent checks before the
previously lossy operations: callback ABI validation precedes context restore,
and ownership classification precedes entry-only substitution. The result
artifact records the new rejections and callback ABI observations; the
fresh runner's `--check` requires identical JSON bytes.

## Limits and production implications

The prototype is deliberately conservative and supports the flat 32-bit
relocation subset already handled by cemu (off32 EXTDEF/LEXTDEF and segment
references). It does not establish general indirect-control-flow analysis,
shared-epilogue partitioning, function-pointer arithmetic, data-pointer
correspondence, different stack-layout correspondence or arbitrary inline
recovery. It can reject otherwise valid programs rather than infer isolation.
Finite watched-state scenarios have the ordinary T4 coverage limits.

Integrated mode is demonstrated by concrete downstream execution, not by a
label that automatically supplies a complete game environment. Real original
callees outside the boundary are not newly verified C. The original game,
compiler inputs, production tools, source, symbols, tests, gates and AGENTS.md
remain unchanged. `make verify`, production promotions and merging to main
are outside this isolated experiment's assignment.

A production proposal should preserve these boundary/policy/typed-pointer
obligations, retain fresh provenance checks, and independently review callback
continuations and conservative CFG handling. E6 supplies evidence for that
proposal; it does not silently change the production audit contract.
