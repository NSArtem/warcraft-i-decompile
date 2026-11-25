"""E7 contract tests, including recomputation of every committed aggregate."""
import copy
import csv
import json
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace as NS
import sys

import pytest

# The pytest console script does not add cwd to sys.path in the Nix shell.
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))

from . import analyze, calibrate
from .capability_probe import CANDIDATES, PROBE, probe
from .common import (CORE_FLAGS, RESULTS, SCRATCH, STATES, cell_state,
                     configurations, digest, flag_key)


def test_core_grid_and_no_duplicate_configuration():
    configs=configurations(["-s -od -4r -zp2 -d1+", "-s -ot -ol -4r -d1+ -zp1"])
    assert len(CORE_FLAGS)==22
    assert len({flag_key(c['flags']) for c in configs})==len(configs)
    assert len(configs)==23
    assert configs[5]['flags']=="-s -ot -ol -5r -zp2"


@pytest.mark.parametrize("verdict,state",[("MATCH","matched"),("MISMATCH","mismatched"),
                                          ("UNSUPPORTED","matcher_unsupported"),("ERROR","matcher_unsupported")])
def test_five_state_mapping(verdict,state):
    assert cell_state(verdict)==state
    assert set(STATES)=={"matched","mismatched","compile_error","matcher_unsupported","untested"}


def test_every_config_compiled_even_after_match(monkeypatch):
    configs=configurations()[:3]
    rows=[dict(addr=1,source='fake.c',declared_flags=configs[0]['flags'],tier='T3')]
    monkeypatch.setattr(calibrate,'CTX',(None,{}, {},None,configs,SCRATCH/'test'))
    calls=[]
    def compile_(source,flags,obj):
        calls.append(flags)
        return NS()
    monkeypatch.setattr(calibrate,'compile_one',compile_)
    monkeypatch.setattr(calibrate,'dependencies',lambda *a:dict(unresolved_relocations=0))
    monkeypatch.setattr(calibrate,'runtime_key',lambda m:'same-runtime')
    monkeypatch.setattr(calibrate,'evaluate',lambda m,rs:({1:dict(state='matched',score=[0]*5)},dict(whole_object_match=True),{}))
    monkeypatch.setattr(calibrate,'dump',lambda *a:None)
    u,rs=calibrate.audit_unit(('fake.c',rows))
    assert calls==[c['flags'] for c in configs]
    assert rs[0]['compatible_configs']==[c['id'] for c in configs]
    rs[0]['cells']['c01']['score'][0]=7
    assert rs[0]['cells']['c02']['score'][0]==0


def test_compile_error_and_untested_are_not_mismatches(monkeypatch):
    configs=configurations()[:3]
    row=dict(addr=1,source='fake.c',declared_flags=configs[0]['flags'],tier='T4')
    monkeypatch.setattr(calibrate,'CTX',(None,{}, {},None,configs,SCRATCH/'test'))
    def failed(*a):raise SystemExit('controlled compile failure')
    monkeypatch.setattr(calibrate,'compile_one',failed)
    u,rs=calibrate.audit_unit(('fake.c',[row]))
    assert [c['state'] for c in rs[0]['cells'].values()]==['compile_error','untested','untested']
    assert rs[0]['compatible_configs']==[]
    assert u['baseline_dependencies'] is None


def test_dependency_clean_checks_runtime_data_too():
    def fx(name):return NS(target_kind='ext',target=name,offset=0)
    m=NS(segments=[NS(name='_TEXT',cls='CODE',fixups=[fx('known')]),
                   NS(name='CONST',cls='DATA',fixups=[fx('missing')]),
                   NS(name='$$SYMBOLS',cls='DEBSYM',fixups=[fx('metadata')])],publics={},statics={})
    deps=calibrate.dependencies(m,{'known':{}})
    assert deps['unresolved_relocations']==1
    assert deps['unresolved_symbols']==['missing']
    assert len(deps['external_relocations'])==2


def test_runtime_memo_key_preserves_duplicate_segment_names():
    a=NS(name='_DATA',cls='DATA',length=1,data=b'a',fixups=[])
    b=NS(name='_DATA',cls='DATA',length=1,data=b'b',fixups=[])
    mod=NS(segments=[a,b],publics={},statics={},externs=[],comdefs={})
    original=calibrate.runtime_key(mod)
    a.data=b'z'
    assert calibrate.runtime_key(mod)!=original


def test_missing_requested_public_is_unsupported_not_first_public_score(monkeypatch):
    row=dict(addr=1,link_name='Requested_')
    mod=NS(publics={'Alternative_a_':(1,0),'Alternative_b_':(1,10)},seg=lambda name:(1,None))
    region=dict(verdict='UNSUPPORTED',findings=[],metrics={},obligations=[],orig_start=None,orig_end=None)
    monkeypatch.setattr(calibrate,'CTX',(None,{}, {},None,[],SCRATCH))
    monkeypatch.setattr(calibrate.e0,'match_module',lambda *a:dict(functions={},region=region))
    monkeypatch.setattr(calibrate.match,'diff_function',lambda *a,**k:{'score':[len(k['name']),0,0,0,0]})
    cells,att,raw=calibrate.evaluate(mod,[row])
    assert cells[1]['state']=='matcher_unsupported' and cells[1]['function'] is None
    assert cells[1]['score'] is None
    assert set(cells[1]['alternative_public_scores'])=={'Alternative_a_','Alternative_b_'}
    assert not att['whole_object_match']


def test_untested_space_is_explicit_and_disjoint():
    configs=configurations()
    space=analyze.untested_space(configs)
    assert len(space['combinations'])==9720-len(configs)
    assert all(x['state']=='untested' for x in space['combinations'])
    assert not ({flag_key(x['flags']) for x in space['combinations']}&{flag_key(c['flags']) for c in configs})


@pytest.fixture(scope='module')
def committed():
    filename=RESULTS/'calibration_matrix.json'
    if not filename.exists():
        pytest.skip('Results are generated in the second E7 atomic commit')
    return json.loads(filename.read_text())


def test_committed_schema_full_s_and_complete_cohorts(committed):
    m=committed
    assert m['schema']==1 and m['experiment']=='E7'
    assert m['summary']['cohorts']['t3']==519
    assert m['summary']['cohorts']['t3_files']==514
    assert m['summary']['cohorts']['t4']==385
    configs={c['id'] for c in m['configurations']}
    assert len({r['addr'] for r in m['functions']})==904
    for r in m['functions']:
        assert set(r['cells'])==configs
        assert set(r['compatible_configs'])=={cid for cid,c in r['cells'].items() if c['state']=='matched'}
        assert all(c['state'] in STATES for c in r['cells'].values())
        if r['tier']=='T3' or r['dependency_clean']:
            assert all(c['state']!='untested' for c in r['cells'].values())
        for c in r['cells'].values():
            if c['state'] in ('matched','mismatched','matcher_unsupported'):
                if c['function'] is None:
                    assert c['state']=='matcher_unsupported' and c['score'] is None
                    assert c['alternative_public_scores'] and 'missing requested public' in c['reason']
                else:
                    assert c['state']==cell_state(c['function']['verdict'])
                    assert len(c['score'])==5
    assert not m['provenance']['production_diff']
    assert m['provenance']['fresh_compiles'] is True
    assert m['explored_space']['untested_combinations']==analyze.untested_space(m['configurations'])
    from wc1 import analysis,symbols
    fs,_,_=symbols.load()
    discovered=calibrate.discover(analysis.run(),fs)
    assert {(r['addr'],r['tier'],r['source'],r['source_sha256']) for r in discovered}=={
        (r['addr'],r['tier'],r['source'],r['source_sha256']) for r in m['functions']}


def test_committed_summary_and_csv_are_exhaustive(committed):
    assert analyze.summarize(committed)==committed['summary']
    units,configs=analyze.index(committed)
    expected={(hex(r['addr']),cid) for r in committed['functions'] if r['tier']=='T4' for cid in r['compatible_configs']}
    with (RESULTS/'t4_new_matches.csv').open() as fh:rows=list(csv.DictReader(fh))
    assert {(r['addr'],r['config']) for r in rows}==expected
    assert len(rows)==len(expected)
    for row in rows:
        a=units[row['source']]['attempts'][row['config']]
        assert row['flags']==configs[row['config']]['flags']
        assert row['buildable_t3']==str(a['buildable'])
        assert row['whole_object_match']==str(a['whole_object_match'])
        assert row['e0_region_match']==str(a['region']['verdict']=='MATCH')
        assert 'placement_check' in a


def test_committed_cu_and_presets_recompute(committed):
    assert json.loads((RESULTS/'cu_hypotheses.json').read_text())==analyze.cu_hypotheses(committed)
    assert json.loads((RESULTS/'proposed_presets.json').read_text())==analyze.presets(committed)
    cu=analyze.cu_hypotheses(committed)
    assert all(not r['boundary_inferred'] for r in cu['modules'])
    assert all(len(r['competing_causes'])==5 for r in cu['modules'] if not r['intersection'])
    p=analyze.presets(committed)
    ranked=p['tier1']+p['tier2']
    totals=committed['summary']['all_tested_t4']
    for key,total in [('marginal_t3_gain','function_matches'),('marginal_buildable_t3_gain','buildable_t3'),
                      ('marginal_score_improvements','score_improvements')]:
        assert sum(r[key] for r in ranked)==totals[total]


def test_committed_buildable_population_linked(committed):
    links=committed['build_a_links']
    assert len(links)>=4 and all(l['compare']=='IDENTICAL' and l['returncode']==0 for l in links)
    assert sum(l['label'].startswith('5r-') for l in links)>=3
    units,configs=analyze.index(committed)
    all_link=next(l for l in links if l['label']=='all-new-buildable')
    buildable_sources={r['source'] for r in committed['functions'] if r['tier']=='T4' and any(units[r['source']]['attempts'][c].get('buildable') for c in r['compatible_configs'])}
    assert set(all_link['selections'])==buildable_sources
    for l in links:
        for source,cid in l['selections'].items():
            a=units[source]['attempts'][cid]
            assert a['buildable'] and a['whole_object_match'] and a['region']['verdict']=='MATCH'


def test_committed_r6_preserves_declared_debug_context(committed):
    evidence=committed['summary']['r6']['evidence']
    assert {r['addr'] for r in evidence}==set(analyze.R6)
    assert all(r['observed_5r_cell']['state']=='matched' and r['observed_5r_cell']['score']==[0]*5 for r in evidence)
    assert sum(r['observed_5r_object']['whole_object_match'] for r in evidence)==11
    assert sum(r['observed_5r_object']['buildable'] for r in evidence)==11
    assert {r['addr'] for r in evidence if r['observed_5r_config']=='c19'}=={0x31fc0,0x34060,0x34480}
    assert {r['addr'] for r in evidence if r['declared_5r_config'] is None}=={0x34480}
    assert next(r for r in evidence if r['addr']==0x34480)['declared_5r_cell']['state']=='untested'


def test_fresh_real_compiler_cells_against_committed(committed,monkeypatch):
    from wc1 import analysis,match,path,symbols
    from experiments.build_codegen.e0 import matcher_proto as e0
    p=analysis.run()
    fs,ds,_=symbols.load()
    by_link={e['link_name']:e for d in (fs,ds) for e in d.values()}
    configs={c['id']:c for c in committed['configurations']}
    units,_=analyze.index(committed)
    monkeypatch.setattr(calibrate,'CTX',(p,fs,by_link,e0.OriginalIndex(p),list(configs.values()),SCRATCH))
    rows=committed['functions']
    cases=[(next(r for r in rows if r['addr']==a),'c06') for a in (0x13c04,0x13c84,0x13dd0)]
    cases.append((next(r for r in rows if r['tier']=='T3' and r['cells']['c01']['state']=='matched' and r['cells']['c11']['state']!='matched'),'c11'))
    cases.append((next(r for r in rows if r['tier']=='T3' and '-d1+' in r['declared_flags']),'c18'))
    cases.append((next(r for r in rows if r['tier']=='T3' and '-od' in r['declared_flags']),'c20'))
    cases.append((next(r for r in rows if r['link_name']=='PathPeekStep_'),'c01'))
    for n,(r,cid) in enumerate(cases):
        obj=SCRATCH/'test-fresh'/f'{n}.obj'
        mod=calibrate.compile_one(r['source'],configs[cid]['flags'],obj)
        cells,att,raw=calibrate.evaluate(mod,[r])
        # JSON normalizes alternative score tuples to lists.
        assert json.loads(json.dumps(cells[r['addr']]))==r['cells'][cid]
        assert att['region']==units[r['source']]['attempts'][cid]['region']
    controls=committed['native_compiler_controls']
    assert len(controls)==1 and controls[0]['compiler']=='ow2'
    assert controls[0]['cell']['state']=='matched' and controls[0]['object']['region']['verdict']=='MATCH'


def test_committed_capabilities_and_probe_determinism(committed):
    baseline=json.loads((RESULTS/'capability_db.json').read_text())
    assert digest(baseline)==committed['provenance']['capability_sha256']
    assert baseline['probe_sha256']==digest(PROBE)
    assert {r['flag'] for r in baseline['flags']}==set(CANDIDATES)
    assert 'Usage: wcc386' in baseline['usage_output']
    for r in baseline['flags']:
        assert type(r['supported']) is bool and type(r['observed_codegen_effect']) is bool
        assert r['observed_codegen_effect']==bool(r['diff'])
        assert all(d['description'] and 'baseline_window_hex' in d and 'variant_window_hex' in d for d in r['diff'])
    assert {r['flag'] for r in baseline['flags'] if not r['supported']}=={'-6r','-ob'}
    folder=SCRATCH/'test-determinism'
    assert probe(folder,folder)==baseline


def test_compiler_facing_paths_are_short_and_bounded(monkeypatch):
    """Rev-e7-01 finding 1: only short Z:\\ paths reach wcc386."""
    from . import common
    seen={}
    def fake(src,cflags,out,cc=None,includes=(),timeout=None,quiet=False):
        seen.update(src=str(src),out=str(out),includes=[str(d) for d in includes])
        return NS()
    monkeypatch.setattr(calibrate.match,'compile_c',fake)
    calibrate.compile_one('src/graphics/blit.c','-s -ot -ol -4r -d1+ -zp2',SCRATCH/'test-short'/'cell.obj')
    paths=[seen['src'],seen['out'],*seen['includes']]
    assert all(len(p)<=common.COMPILER_PATH_LIMIT for p in paths), paths
    assert all(Path(p).is_relative_to(common.compiler_root()) for p in paths)
    # A bounded prefix ('/tmp/wc1e7-<8 hex>/repo') cannot itself be a long root.
    assert len(str(common.compiler_root()))<=40
    with pytest.raises(RuntimeError,match='compiler-facing path'):
        common.compiler_path(Path(common.path()) / ('x'*150) / 'deep.c')


def test_long_checkout_path_portability(committed,tmp_path):
    """Rev-e7-01 finding 1: a 154-character checkout root still probes and compiles."""
    from wc1 import path
    repo=Path(os.path.realpath(path()))
    padded=tmp_path
    while len(str(padded))<150:
        padded=padded/('p'*40)
    padded.mkdir(parents=True)
    root=padded/'repo'
    root.symlink_to(repo,target_is_directory=True)
    assert len(str(root))>=154
    scratch=padded/'scratch'
    scratch.mkdir()
    row=next(r for r in committed['functions'] if r['addr']==0x31fc0)
    flags=next(c['flags'] for c in committed['configurations'] if c['id']=='c19')
    runtime=next(u for u in committed['units'] if u['source']==row['source'])['attempts']['c19']['runtime_sha256']
    script=tmp_path/'long_path_check.py'
    script.write_text(
        'import json, sys\n'
        'from pathlib import Path\n'
        'from experiments.build_codegen.e7 import calibrate, capability_probe\n'
        'from experiments.build_codegen.e7.common import RESULTS\n'
        'scratch, source, flags, obj = Path(sys.argv[1]), sys.argv[2], sys.argv[3], Path(sys.argv[4])\n'
        'expected = json.loads((Path(RESULTS) / "capability_db.json").read_text())\n'
        'probed = capability_probe.probe(scratch / "probe-out", scratch / "capability")\n'
        'print("probe_equal", probed == expected)\n'
        'module = calibrate.compile_one(source, flags, obj)\n'
        'print("runtime", calibrate.runtime_key(module))\n')
    env=dict(os.environ,WC1_ROOT=str(root),
             PYTHONPATH=os.pathsep.join([str(repo),str(repo/'tools'),os.environ.get('PYTHONPATH','')]))
    run=subprocess.run([sys.executable,str(script),str(scratch),row['source'],flags,str(scratch/'cell.obj')],
                       cwd=str(root),env=env,capture_output=True,text=True,timeout=300)
    assert run.returncode==0,run.stdout+run.stderr
    assert 'probe_equal True' in run.stdout,run.stdout+run.stderr
    assert f'runtime {runtime}' in run.stdout,run.stdout+run.stderr
