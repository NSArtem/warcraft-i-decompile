"""Real-compiler scientific controls and deterministic reproduction for E1.

No production tests or verification targets are changed. The session fixture
recompiles every variant and repeats the isolated links, rather than trusting
checked-in verdict strings or object caches.
"""
import hashlib
import json
from pathlib import Path
import re

import pytest
from wc1 import omf
from experiments.build_codegen.e0 import matcher_proto as e0
from . import run_e1 as experiment


@pytest.fixture(scope='module')
def reproduced(tmp_path_factory):
    folder = tmp_path_factory.mktemp('e1_results')
    result = experiment.run(folder)
    return result, folder


@pytest.fixture(scope='module')
def rows(reproduced):
    return {r['id']:r for r in reproduced[0]['variants']}


def shared(row, name):
    return [b for b in row['functions'][name]['exact_branch_encoding']['compiled']
            if b['shared_epilogue']]


def test_required_matrix_is_complete(rows):
    for group, funcs in experiment.GROUPS.items():
        orders = ['original','reversed'] + ['standalone_'+f[0] for f in funcs]
        if group=='b':
            orders += ['pair']
        for order in orders:
            for flag in ('ot_4r','os_4r','oa_4r','ot_5r'):
                assert f'{group}_current_{order}_{flag}' in rows
    for flag in experiment.FLAGS:
        assert f'a_interleaved_original_{flag}' in rows
    assert len(rows)==len(experiment.matrix())


def test_every_observation_has_separate_r1_outcomes(rows):
    for row in rows.values():
        assert set(row['functions'])==set(row['order'])
        assert len(row['obj_sha256'])==64
        for name, observation in row['functions'].items():
            assert isinstance(observation['shared_epilogue_reproduced'],bool)
            assert observation['shared_epilogue_reproduced']==bool(shared(row,name))
            for key in ('function_match_verdict','region_match_verdict'):
                assert observation[key]['verdict'] in ('MATCH','MISMATCH','UNSUPPORTED','ERROR')
                assert isinstance(observation[key]['findings'],list)
                assert isinstance(observation[key]['obligations'],list)
            assert observation['region_match_verdict']==row['region_match_verdict']
            assert observation['build_a_status']==row['build_a_comparison']['status']
            assert observation['build_a_integrated_identical']==row['build_a_comparison']['identical']
            encoding=observation['exact_branch_encoding']
            for b in encoding['compiled']+encoding['original']:
                assert {'bytes','opcode','target_offset','target_function','field_size'}<=b.keys()


@pytest.mark.parametrize('group', ['a','b'])
def test_standalone_has_no_sibling_epilogue(group, rows):
    for name,_,_ in experiment.GROUPS[group]:
        for flag in experiment.FLAGS:
            row=rows[f'{group}_current_standalone_{name}_{flag}']
            assert row['functions'][name]['shared_epilogue_reproduced'] is False


def test_r6_74f5_is_preserved_and_explained_by_two_padding_bytes(rows, reproduced):
    row=rows['a_current_original_ot_5r']
    branch=shared(row,'DialogHighlightOn')[0]
    original=reproduced[0]['original']['a']['branches']['DialogHighlightOn'][0]
    assert branch['bytes']=='74 f5'
    assert original['bytes']=='74 f3'
    assert branch['target_function']=='DialogItemHitTest'
    assert branch['target_offset']==0x83
    assert branch['offset']==0x8c
    assert original['target_offset']==0x69
    assert original['offset']==0x74
    assert branch['target_offset']-(branch['offset']+2)==-11
    assert original['target_offset']-(original['offset']+2)==-13
    assert row['publics']['DialogHighlightOn_']==0x84
    assert row['padding'][0]['bytes']==''
    # Original RET at +0x69 is followed by 8b c0, then On at +0x6c.
    raw=bytes.fromhex(reproduced[0]['original']['a']['bytes'])
    assert raw[0x69:0x6c]==bytes.fromhex('c3 8b c0')
    assert row['functions']['DialogHighlightOn']['function_match_verdict']['verdict']=='MISMATCH'
    assert row['region_match_verdict']['verdict']!='MATCH'
    assert row['build_a_comparison']['identical'] is None


def test_group_a_separates_alias_scheduling_from_layout(rows):
    five=rows['a_interleaved_original_ot_5r']
    alias=rows['a_interleaved_original_oa_4r']
    both=rows['a_interleaved_original_oa_5r']
    assert five['functions']['DialogItemHitTest']['function_match_verdict']['verdict']=='MISMATCH'
    assert alias['functions']['DialogItemHitTest']['function_match_verdict']['verdict']=='MATCH'
    for row in (five,both):
        assert [b['bytes'] for b in shared(row,'DialogHighlightOn')]==['74 f3']
        assert [b['bytes'] for b in shared(row,'DialogHighlightOff')]==['74 df']
        assert row['publics']=={'DialogItemHitTest_':0,'DialogHighlightOn_':108,'DialogHighlightOff_':128}
        for name in ('DialogHighlightOn','DialogHighlightOff'):
            assert row['functions'][name]['function_match_verdict']['verdict']=='MATCH'
    assert alias['region_match_verdict']['verdict']=='MISMATCH'
    assert five['region_match_verdict']['verdict']=='MISMATCH'
    assert both['region_match_verdict']['verdict']=='MATCH'
    assert all(f['function_match_verdict']['verdict']=='MATCH' for f in both['functions'].values())


def test_group_b_shares_across_the_intermediate_function_with_exact_wait_body(rows):
    row=rows['b_current_original_ot_5r']
    assert row['publics']=={'IntroOpPlaySound_':0,'IntroOpSyncSound_':20,'IntroOpWaitSound_':112}
    jumps=shared(row,'IntroOpWaitSound')
    assert [(b['offset'],b['bytes'],b['target_offset'],b['target_function']) for b in jumps]==[
        (0x7b,'74 93',0x10,'IntroOpPlaySound'),(0x85,'75 89',0x10,'IntroOpPlaySound')]
    assert row['text_size']==142
    assert row['region_match_verdict']['verdict']=='MATCH'
    assert all(f['function_match_verdict']['verdict']=='MATCH' for f in row['functions'].values())
    assert row['region_match_verdict']['findings']==[]
    assert row['region_match_verdict']['metrics']['reverse_le_fixups_checked']==4
    assert row['padding'][0]['bytes']==''
    assert row['padding'][1]['bytes']=='8b c0'


def test_group_b_4r_padding_expands_one_short_branch(rows):
    for flag in ('ot_4r','oa_4r'):
        row=rows[f'b_current_original_{flag}']
        assert row['publics']['IntroOpSyncSound_']==32
        assert row['publics']['IntroOpWaitSound_']==128
        assert [b['bytes'] for b in shared(row,'IntroOpWaitSound')]==['74 83','0f 85 75 ff ff ff']
        assert row['region_match_verdict']['verdict']!='MATCH'
        assert row['build_a_comparison']['identical'] is None


def test_pair_and_reverse_order_are_negative_exact_region_controls(rows):
    for flag in experiment.FLAGS:
        pair=rows[f'b_current_pair_{flag}']
        reverse=rows[f'b_current_reversed_{flag}']
        assert shared(pair,'IntroOpWaitSound')
        assert not shared(reverse,'IntroOpWaitSound')
        assert pair['region_match_verdict']['verdict']!='MATCH'
        assert reverse['region_match_verdict']['verdict']!='MATCH'
    a=rows['a_current_reversed_ot_5r']
    # Sharing survives, but it targets Off's RET rather than the hit test.
    assert shared(a,'DialogHighlightOn')[0]['target_function']=='DialogHighlightOff'
    assert a['region_match_verdict']['verdict']!='MATCH'


@pytest.mark.parametrize('cid', ['a_interleaved_original_oa_5r','b_current_original_ot_5r'])
def test_closed_region_build_a_is_identical(cid, rows):
    build=rows[cid]['build_a_comparison']
    assert build['status']=='IDENTICAL'
    assert build['identical'] is True
    assert build['compare_exit_code']==0
    assert build['byte_diffs']==build['only_original_fixups']==build['only_linked_fixups']==0
    assert build['original_fixups']==build['linked_fixups']==8770
    assert 'IDENTICAL (loaded image, entry, stack, fixups)' in build['compare_stdout']
    assert (experiment.ROOT/build['executable']).is_file()


def test_individual_matches_are_not_claimed_as_integrated_groups(rows):
    standalone=rows['b_current_standalone_IntroOpPlaySound_ot_5r']
    assert standalone['region_match_verdict']['verdict']=='MATCH'
    assert standalone['build_a_comparison']['status']=='PLACEMENT_REJECTED'
    sync=rows['b_current_standalone_IntroOpSyncSound_ot_5r']
    assert sync['region_match_verdict']['verdict']=='MATCH'
    assert sync['build_a_comparison']['status']=='ASSEMBLY_REJECTED_EXTERNAL_REL8'
    assert standalone['build_a_comparison']['identical'] is False
    assert sync['build_a_comparison']['identical'] is False


def test_integration_is_guarded_by_e0_region_match():
    row={'region_match_verdict':{'verdict':'UNSUPPORTED'}}
    assert experiment.integrate(None,None,None,row)=={
        'status':'NOT_ATTEMPTED_REGION_NOT_MATCH','identical':None}


def test_preserved_objects_and_e0_verdicts_are_unmodified(rows):
    p,db=e0.load_inputs()
    index=e0.OriginalIndex(p)
    for row in rows.values():
        obj=experiment.ROOT/row['obj']
        assert hashlib.sha256(obj.read_bytes()).hexdigest()==row['obj_sha256']
        module=omf.parse_object(str(obj))
        fresh=e0.match_module(p,module,db,index)
        assert fresh['region']==row['region_match_verdict']
        for name,f in row['functions'].items():
            assert fresh['functions'][name+'_']==f['function_match_verdict']


def test_fixtures_are_pure_c_and_current_bodies_are_faithful():
    for fixture in experiment.FIXTURES.glob('*.c'):
        assert not re.search(r'\b__asm\b|#\s*pragma\s+aux',fixture.read_text())
    mapping={
        'a':[('src/mod_16390/dialog_hit_test_reference.c',n) for n,_,_ in experiment.GROUPS['a']],
        'b':[('src/playflic/intro_op_play_sound.c','IntroOpPlaySound'),
             ('src/playflic/intro_op_sync_sound.c','IntroOpSyncSound'),
             ('src/playflic/player_reference.c','IntroOpWaitSound')]}
    for g,entries in mapping.items():
        fixture=(experiment.FIXTURES/f'group_{g}_current.c').read_text()
        for path,name in entries:
            assert experiment.body(fixture,name)==experiment.body((experiment.ROOT/path).read_text(),name)


def test_results_and_disassembly_reproduce_byte_for_byte(reproduced):
    _,folder=reproduced
    # The harness commit also works before empirical artifacts are committed.
    for name in ('results.json','disasm_evidence.txt'):
        saved=experiment.RESULTS/name
        if saved.exists():
            assert (folder/name).read_bytes()==saved.read_bytes(),name


def test_production_is_unchanged_and_boundary_correction_is_explicit(reproduced):
    result,_=reproduced
    assert result['provenance']['production_diff']==''
    assert experiment.command(['git','diff',experiment.BASE,'--','tools/','src/','analysis/',
                               'tests/','Makefile','flake.nix','AGENTS.md'])==''
    assert result['boundaries']['group_a_actual_next_function']==0x16d5c
    assert result['boundaries']['group_a_requested_end']==0x16d5e
