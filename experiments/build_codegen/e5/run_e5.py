"""Reproduce E5 with the real installed toolchain; no production writes.

    python3 -m experiments.build_codegen.e5.run_e5
"""
import json
from wc1 import build as legacy, match, omf
from experiments.build_codegen.e0 import matcher_proto as e0
from . import build_e5 as b
from . import omf_b3 as r
from .controls import negative_controls
from .fixtures import threadify

RESULTS = b.ROOT/'docs/research/build-codegen/results/e5/results.json'


def experiment_object(p, db, src, name, base, flags=b.FLAGS):
    obj = b.compile_source(src,name,flags)
    mod = omf.parse_object(obj)
    return dict(src=src,obj=obj,cr=(base,base+mod.seg('_TEXT')[1].length),
                funcs=[db[n] for n,(si,_) in mod.publics.items() if mod.segments[si-1].cls=='CODE'],
                bases=b.data_bases(p,mod,db,base),experiment=True,
                compiler=match.file_cc(str(b.ROOT/src)),flags=flags)


def stride_probe(p, db):
    results = {}
    for opt in ('os','ot'):
        src='src/gamedlg/save_error_dialog_reference.c'
        obj=b.compile_source(src,'probe_'+opt,b.FLAGS.replace('-ot','-'+opt))
        mod=omf.parse_object(obj)
        s=mod.seg('CONST')[1]
        report=e0.match_module(p,mod,db)
        results[opt]=dict(compiler=match.file_cc(str(b.ROOT/src)), flags=b.FLAGS.replace('-ot','-'+opt),segment='CONST',
                         data_size=s.length,second_string_offset=s.data.find(b'Remote'),
                         region_verdict=report['region']['verdict'],
                         finding_codes=sorted({f['code'] for f in report['region']['findings']}))
    # Real multi-function experimental context. It demonstrates data layout,
    # not in-place code equivalence: wcc386 aligns the second function to 16.
    obj=b.compile_source('experiments/build_codegen/e5/fixtures/native_context.c','native_context',b.FLAGS)
    mod=omf.parse_object(obj)
    results['ot_multi_context']=dict(compiler=match.file_cc(str(b.ROOT/'experiments/build_codegen/e5/fixtures/native_context.c')),flags=b.FLAGS,segment='_DATA',
        string_stride=mod.publics['_e5_remote'][1]-mod.publics['_e5_disk'][1],
        publics={n:list(v) for n,v in mod.publics.items()},
        const_size=mod.seg('CONST')[1].length,
        code_layout_matches=False,
        explanation='SaveErrorDialog then DefeatDialog in source order; native function alignment and original order differ. Layout probe only.')
    return results


def run():
    b.OUT.mkdir(parents=True,exist_ok=True)
    print('E5: load original and compile every baseline T3',flush=True)
    p, funcs, datas, db = b.inputs()
    baseline = b.prepare_baseline(p,funcs,db)
    probes = stride_probe(p,db)
    save=experiment_object(p,db,'src/gamedlg/save_error_dialog_reference.c','save_os',0x1aca8,b.FLAGS.replace('-ot','-os'))
    defeat=next(o for o in baseline if o['src']=='src/gamedlg/defeat_dialog.c')
    oldplan=[(o['src'],str(o['obj']),o['cr'],[(a,omf.parse_object(o['obj']).segments[si-1].name) for si,a in o['bases'].items()],o['funcs'])
             for o in (defeat,save)]
    _,_,_,errors=legacy.check_placed_plan(p,oldplan)
    assert "C objects' data anchors are not in code order" in errors
    legacy_result=dict(errors=errors,code_order=[dict(function=o['funcs'][0]['name'],code=o['cr'][0],anchors=list(o['bases'].values())) for o in (defeat,save)])
    scenarios=[]
    def link(objects,name,**kwargs):
        print('E5: link '+name,flush=True)
        result=b.link(p,funcs,datas,db,objects,name,**kwargs)
        assert result['identical'],result['comparison']
        assert result['original_fixups']==result['linked_fixups']==8770
        scenarios.append(result)
    link(baseline+[save],'s1')
    # Native -ot explicit arrays in _DATA; identity is supplied by the named
    # definitions in this fixture and their two independently verified strings.
    native_db=dict(db)
    native_db.update(_e5_disk=dict(addr=0x51ea6),_e5_remote=dict(addr=0x51ec8))
    native=experiment_object(p,native_db,'experiments/build_codegen/e5/fixtures/native_data.c','native_data',0x1aca8)
    print('E5: link native_ot_data',flush=True)
    native_result=b.link(p,funcs,datas,native_db,baseline+[native],'native_ot_data')
    assert native_result['identical'],native_result['comparison']
    scenarios.append(native_result)
    consolidated=experiment_object(p,db,'experiments/build_codegen/e5/fixtures/gamedlg_data.c','gamedlg_data',0x1ab28)
    real_multi=[o for o in baseline if o is not defeat]+[consolidated,save]
    link(real_multi,'s2_real_multi')
    synthetic=b.synthetic()
    assert all(x['identical'] for x in synthetic)
    real_threads=[]
    for o in baseline+[consolidated]:
        reader=r.Threads()
        for t,body in r.records(o['obj'].read_bytes()):
            if t==0x9d:
                reader.parse(body)
        if reader.count:
            real_threads.append(dict(src=o['src'],definitions=reader.count,uses=reader.uses))
    link(real_multi,'s3_thread',thread_transform=threadify)
    for mode in ('flat','dgroup','target','external'):
        link(real_multi,'s4_'+mode,frame_mode=mode,thread_transform=threadify)
    # Partition the already fully verified CONST segment into its two literal
    # objects. No mutable merging and no invisible/unverified padding.
    mod=omf.parse_object(save['obj']);si,s=mod.seg('CONST')
    second=s.data.find(b'Remote')
    parts=[r.Symbol(0,second,0x51ea6,'SaveErrorDialog: local error literal'),
           r.Symbol(second,s.length-second,0x51ec8,'SaveErrorDialog: remote error literal')]
    link(baseline+[save],'per_symbol',per_symbols={save['src']:{si:parts}})
    negatives=negative_controls()
    assert negatives['N4_leak']['occurrences']==[]
    production_paths=['tools/wc1','src','analysis','tests','asm','Makefile','flake.nix','AGENTS.md']
    changed=b.run(['git','diff','--name-only','1abb053c112332ec901a8961dc918bdcc25d73c4','--',*production_paths]).splitlines()
    assert changed==[],changed
    results=dict(production_changed_paths=changed, experiment='E5',baseline='1abb053c112332ec901a8961dc918bdcc25d73c4',
        baseline_c_objects=len(baseline),baseline_c_functions=sum(len(o['funcs']) for o in baseline),
        legacy_failure=legacy_result,save_error_dialog=probes,scenarios=scenarios,
        synthetic_three_segments=synthetic,real_thread_scan=dict(objects=len(baseline)+1,found=real_threads),
        negative_controls=negatives,
        conclusions=dict(whole_segment='SUPPORTED in the verified off32/LEDATA32 subset',
            per_symbol='SUPPORTED for a full partition of verified independent CONST literals; no layout compensation',
            native_ot='Explicit _DATA arrays reproduce 0x22 stride and link IDENTICAL; canonical literal source still needs -os',
            frames='FLAT, DGROUP, Target and EXTDEF all reproduce the exact LE object/offset set',
            production_changes=len(changed),production_ready=False))
    RESULTS.parent.mkdir(parents=True,exist_ok=True)
    RESULTS.write_text(json.dumps(results,indent=2,sort_keys=True)+'\n')
    print(f'E5: {len(scenarios)} Warcraft links IDENTICAL; synthetic 5/5; negative controls rejected',flush=True)
    return results


if __name__=='__main__':
    run()
