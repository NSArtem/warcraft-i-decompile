"""Reproduce E6 without make, production edits, byte patching or pytest skips.

    python3 -m experiments.build_codegen.e6.run_e6
    python3 -m experiments.build_codegen.e6.run_e6 --check
"""
import argparse
import hashlib
from importlib.metadata import version
import json
from pathlib import Path

from wc1 import cemu, oldcc, path
from .mf_cemu import (FLAGS, HERE, IsolationImpossibleError, VerificationError,
                      compile_fixture, instructions)
from .scenarios import (FIXTURES, FRAME, LOADER, NEGATIVES, baseline_options,
                        baseline_playflic, exercise_negative, inspect_playflic,
                        run_options, run_playflic)

ROOT = HERE.parents[2]
RESULTS = ROOT / 'docs/research/build-codegen/results/e6/results.json'
BASELINE = '3ee53aa5d4e7911e7f8d1bb0097de17223c8a559'


def sha256(filename):
    return hashlib.sha256(Path(filename).read_bytes()).hexdigest()


def reproduce():
    problems = oldcc.check()
    if problems:
        raise RuntimeError('compiler provenance check failed: ' + '; '.join(problems))
    fixtures = {}
    for src in sorted(FIXTURES.iterdir()):
        if src.suffix not in ('.c', '.asm'):
            continue
        mod = compile_fixture(src)
        fixtures[src.name] = dict(source_sha256=sha256(src),
                                 omf_digest=cemu.omf_module_digest(mod),
                                 publics={n: list(v) for n, v in sorted(mod.publics.items())},
                                 statics={n: list(v) for n, v in sorted(mod.statics.items())})
    baseline = dict(options=baseline_options(), playflic=baseline_playflic())
    positives = {}
    for mode in ('isolated', 'group', 'integrated'):
        # Missing audio drivers make Refresh change volumes, and an expired
        # timer makes ApplyTimer change next_apply and apply those volumes.
        positives['options_' + mode] = run_options(mode, absent=3)
        positives['playflic_' + mode] = run_playflic(mode)
    positives['options_group_cancel'] = run_options('group', result=1, absent=3)
    positives['options_group_timer_not_expired'] = run_options('group', clock_step=25)
    positives['playflic_integrated_clear'] = run_playflic('integrated', empty=True)
    positives['playflic_group_terminal'] = run_playflic('group', terminal=True)
    negatives = {}
    for control, reason in NEGATIVES.items():
        expected = IsolationImpossibleError if control in ('N6', 'N7') else VerificationError
        try:
            exercise_negative(control)
        except expected as error:
            if reason not in str(error):
                raise AssertionError(f'{control}: unexpected rejection {error}') from error
            negatives[control] = dict(outcome='rejected', exception=type(error).__name__,
                                      reason=str(error))
        else:
            raise AssertionError(f'{control}: prohibited behavior was accepted')
    no_fixup = compile_fixture(FIXTURES / 'no_fixup_call.asm')
    seg = no_fixup.segments[0]
    calls = [i for i in instructions(seg.data, 0) if i.mnemonic == 'call']
    assert len(calls) == 1
    call_fixups = [f.offset for f in seg.fixups
                   if calls[0].address <= f.offset < calls[0].address + calls[0].size]
    assert call_fixups == []
    supplemental = dict(call_offset=calls[0].address, call_omf_fixups=call_fixups,
                        verification=run_playflic('isolated', fixture='no_fixup_call.asm'))
    return dict(
        experiment='E6', contract_version='e6-r2-v1', baseline_commit=BASELINE,
        conclusion='supported_for_exercised_scenarios_with_conservative_isolation',
        compiler=dict(name='Watcom C32 10.0a', flags=FLAGS,
                      manifest_check='passed',
                      executable_sha256=sha256(Path(oldcc.root()) / 'binb/wcc386.exe')),
        original_war_sha256=sha256(path('original/install/war.exe')),
        libraries={name: version(name) for name in ('unicorn', 'capstone')},
        implementation_sha256={p.name: sha256(p) for p in
                               (HERE / 'mf_cemu.py', HERE / 'scenarios.py', HERE / 'run_e6.py')},
        fixtures=fixtures, real_playflic_call=inspect_playflic(),
        baseline_reproductions=baseline, positive_cases=positives,
        negative_controls=negatives, supplemental_zero_fixup=supplemental,
        counts=dict(positive_cases=len(positives), required_negative_families=7,
                    negative_variants=len(negatives), baseline_reproductions=2,
                    supplemental_positive_cases=1),
        limitations=[
            'Real PLAYFLIC consolidation emits one EXTDEF call fixup, not zero.',
            'Zero-fixup interception is demonstrated separately with a NASM OMF fixture.',
            'Typed correspondence applies only to declared boundary entry-pointer slots.',
            'Unprovable inlining, interior entries and unresolved indirect jumps fail closed.',
            'Trusted in-process Python scenario setup; not a hostile-code sandbox.',
            'Scenario evidence does not establish universal equivalence or production T4 promotion.',
        ])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true',
                        help='reproduce and require byte-identical committed JSON')
    args = parser.parse_args()
    payload = json.dumps(reproduce(), indent=2, sort_keys=True) + '\n'
    if args.check:
        if not RESULTS.exists() or RESULTS.read_text() != payload:
            raise SystemExit('E6 results differ; run without --check to regenerate')
    else:
        RESULTS.parent.mkdir(parents=True, exist_ok=True)
        RESULTS.write_text(payload)
    print(f'E6: 10 positive cases, 10 rejected negative variants, 2 baseline reproductions; '
          f'{"checked" if args.check else "wrote"} {RESULTS.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
