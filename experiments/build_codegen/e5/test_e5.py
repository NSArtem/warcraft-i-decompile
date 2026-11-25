"""E5 checks: real toolchain/link tests plus fail-closed OMF unit controls."""
from dataclasses import replace
import hashlib
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

import pytest
from wc1 import omf
from wc1.omfpatch import _pack
from . import omf_b3 as b3
from . import build_e5 as build
from .test_omf_b3 import test_all_thread_slots_and_methods, test_undefined_and_truncated_threads_fail_closed


from .controls import pointer_control as make_pointer_control, mutate, leaks


@pytest.fixture(scope='module')
def pointer_control():
    return make_pointer_control()


def test_pointer_bytes_and_relocations_checked_before_emptying(pointer_control):
    p,db,raw,bases = pointer_control
    output, proof = b3.rewrite(raw,p,db,bases)
    assert proof['data_proofs'][0]['metrics']['data_fixups_checked'] == 1
    assert proof['data_proofs'][0]['metrics']['reverse_le_fixups_checked'] == 1
    assert omf.parse_module(output)[0].seg('_DATA')[1].length == 0
    # N1 changes an ordinary byte; N2 changes a relocation's symbolic target.
    for corrupted in (mutate(raw, lambda t,b: b[:-1]+bytes([b[-1]^1]) if t==0xa1 and b.endswith(b'ABCD') else b),
                      mutate(raw, lambda t,b: b.replace(b'good_target',b'evil_target') if t==0x8c else b)):
        with pytest.raises(b3.Rejected,match='E0 data check'):
            b3.rewrite(corrupted,p,db,bases)


def test_missing_reverse_pointer_is_rejected(pointer_control):
    p,db,raw,bases = pointer_control
    # Remove the data FIXUPP, leaving a numerically plausible pointer behind.
    segment = None
    out=[]
    for t,b in b3.records(raw):
        if t==0xa1:
            segment,_=omf._idx(b,0)
        if t==0x9d and segment in bases:
            continue
        out.append(_pack(t,b))
    with pytest.raises(b3.Rejected,match='E0 data check'):
        b3.rewrite(b''.join(out),p,db,bases)


def test_mutable_and_struct_remapping_rejected(pointer_control):
    p,db,raw,bases = pointer_control
    si=next(iter(bases))
    for kind in ('literal','interior_struct','named'):
        with pytest.raises(b3.Rejected):
            b3.rewrite(raw,p,db,bases,per_symbol={si:[b3.Symbol(0,8,0x50000,'made_up',kind)]})


def test_lidata_bad_checksums_and_unsupported_locations(pointer_control):
    p,db,raw,bases=pointer_control
    with pytest.raises(b3.Rejected,match='LIDATA'):
        b3.rewrite(
            b''.join(_pack(0xa3 if t==0xa1 else t,b) for t,b in b3.records(raw)),p,db,bases)
    broken=bytearray(raw);broken[4]^=1
    with pytest.raises(b3.Rejected,match='checksum'):
        b3.rewrite(bytes(broken),p,db,bases)
    def change_loc(t,b):
        if t==0x9d and b and b[0]&128:
            b[0]=(b[0]&0xc3)|(1<<2)
        return b
    with pytest.raises(b3.Rejected):
        b3.rewrite(mutate(raw,change_loc),p,db,bases)


def test_anchor_names_do_not_leak():
    assert leaks() == []


LONG_CHECKOUT_PROBE = """\
import hashlib
from experiments.build_codegen.e5 import build_e5 as b
for src, name in (('experiments/build_codegen/e5/fixtures/native_context.c', 'longpath_native_context'),
                  ('experiments/build_codegen/e5/fixtures/gamedlg_data.c', 'longpath_gamedlg_data')):
    obj = b.compile_source(src, name, b.FLAGS)
    print(name, hashlib.sha256(obj.read_bytes()).hexdigest())
"""


@pytest.fixture(scope='module')
def long_checkout():
    """A >=140-character symlinked checkout path: the rev-e5-01 crash trigger."""
    real = os.path.realpath(str(build.ROOT))
    link = Path(tempfile.gettempdir())/('e5-long-path-' + hashlib.sha1(real.encode()).hexdigest()[:8]
                                        + '-' + 'x'*118)
    assert len(str(link)) >= 140
    if os.path.islink(link) and os.path.realpath(link) != real:
        os.unlink(link)
    if not os.path.lexists(link):
        os.symlink(real, link, target_is_directory=True)
    try:
        yield link
    finally:
        if os.path.islink(link):
            os.unlink(link)


def test_compiler_facing_paths_are_bounded():
    """Every path handed to Watcom 10.0a stays under the fixed-buffer limit."""
    for p in (build.ROOT/'experiments/build_codegen/e5/fixtures/native_context.c',
              build.OUT/'baseline_src_gamedlg_defeat_dialog.obj'):
        short = build.compiler_path(p)
        assert len(str(short)) <= build.COMPILER_PATH_LIMIT
        assert os.path.realpath(short) == os.path.realpath(p)


def test_fixtures_compile_from_a_long_checkout_path(long_checkout):
    """rev-e5-01: 10.0a access-violates on a long checkout, so E5 compiles
    through the short mirror; the objects are the same bytes either way."""
    env = dict(os.environ)
    env['WC1_ROOT'] = str(long_checkout)
    env['PYTHONPATH'] = str(long_checkout/'tools')
    r = subprocess.run([sys.executable, '-c', LONG_CHECKOUT_PROBE], capture_output=True,
                       text=True, cwd=str(long_checkout), env=env, timeout=600)
    assert r.returncode == 0, r.stdout + r.stderr
    long_hashes = dict(line.split() for line in r.stdout.splitlines() if line.strip())
    for src, name in (('experiments/build_codegen/e5/fixtures/native_context.c', 'pathcheck_native_context'),
                      ('experiments/build_codegen/e5/fixtures/gamedlg_data.c', 'pathcheck_gamedlg_data')):
        obj = build.compile_source(src, name, build.FLAGS)
        assert long_hashes[name.replace('pathcheck_', 'longpath_')] == \
            hashlib.sha256(obj.read_bytes()).hexdigest()


@pytest.fixture(scope='module')
def results():
    from .run_e5 import run
    return run()


@pytest.mark.parametrize('name',['s1','native_ot_data','s2_real_multi','s3_thread',
                                 's4_flat','s4_dgroup','s4_target','s4_external','per_symbol'])
def test_full_build_a_images_and_every_le_fixup(results,name):
    result=next(x for x in results['scenarios'] if x['name']==name)
    assert result['identical']
    assert result['byte_diffs']==result['only_original']==result['only_linked']==0
    assert result['original_fixups']==result['linked_fixups']==8770
    assert result['c_functions']==results['baseline_c_functions']+1
    assert result['data_asm_pieces']==1
    assert all(p['compiler']=='10.0a' for p in result['proofs'] if p['experimental'])
    for record in result['anchor_fixup_records']:
        assert record['original_target_object']==record['linked_target_object']
        assert record['original_target_offset']==record['linked_target_offset']


def test_legacy_failure_and_native_context(results):
    assert results['legacy_failure']['errors']==["C objects' data anchors are not in code order"]
    defeat,save=results['legacy_failure']['code_order']
    assert defeat['anchors']==[0x56c0c]
    assert save['anchors']==[0x51ea6]
    assert results['save_error_dialog']['os']['region_verdict']=='MATCH'
    assert results['save_error_dialog']['ot']['region_verdict']=='MISMATCH'
    assert results['save_error_dialog']['os']['second_string_offset']==0x22
    assert results['save_error_dialog']['ot']['second_string_offset']==0x24
    assert results['save_error_dialog']['ot_multi_context']['string_stride']==0x22


def test_real_and_synthetic_all_three_segments(results):
    real=next(s for s in results['scenarios'] if s['name']=='s2_real_multi')
    proof=next(p for p in real['proofs'] if p['src'].endswith('/gamedlg_data.c'))
    assert {p['segment_name'] for p in proof['data_proofs']}=={'_DATA','CONST','_BSS'}
    for s in results['synthetic_three_segments']:
        assert s['identical']
        assert all(s['segments'][name]>0 for name in ('_DATA','CONST','_BSS'))


def test_threads_survive_discarded_records_and_expand(results):
    scenario=next(s for s in results['scenarios'] if s['name']=='s3_thread')
    threaded=[p for p in scenario['proofs'] if p['threads']]
    assert len(threaded)==2
    assert all(p['thread_uses']>=2 for p in threaded)
    # Every FIXUPP32 in every rewritten object is self-contained, with no
    # definition or use of any THREAD, including the debug-metadata objects.
    for obj in (build.OUT/'s3_thread').glob('c_*.obj'):
        reader=b3.Threads()
        for t,b in b3.records(obj.read_bytes()):
            if t==0x9d:
                reader.parse(b)
        assert reader.count==reader.uses==0


def test_per_symbol_addends_and_provenance(results):
    scenario=next(s for s in results['scenarios'] if s['name']=='per_symbol')
    proof=next(p for p in scenario['proofs'] if 'save_error_dialog_reference' in p['src'])
    assert proof['anchors']==[0x51ea6,0x51ec8]
    assert [p['data_scope'] for p in proof['data_proofs']]==['per_symbol','per_symbol']
    # Locate the rewritten C object by public, independent of its sequence id.
    found=[]
    for obj in (build.OUT/'per_symbol').glob('c_*.obj'):
        mod=omf.parse_object(obj)
        if 'SaveErrorDialog_' in mod.publics:
            text=mod.seg('_TEXT')[1]
            refs=[f for f in text.fixups if f.target_kind=='ext' and f.target.startswith('wc1_anchor_')]
            found=[(f.target,struct.unpack_from('<I',text.data,f.offset)[0]) for f in refs]
    assert found==[('wc1_anchor_51ea6',0),('wc1_anchor_51ec8',0)]


def test_negative_control_results(results):
    controls=results['negative_controls']
    assert all(controls[name]['rejected'] for name in ('N1_byte','N2_pointer','N3_mutable_merge','N3_interior_struct'))
    assert controls['N4_leak']['occurrences']==[]
    assert controls['positive_pointer']['data_fixups_checked']==1


def test_explicit_displacement_and_inline_addend_preserved(pointer_control):
    p,db,raw,bases=pointer_control
    current=None
    chunks=[]
    for t,body in b3.records(raw):
        if t==0xa1:
            current,q=omf._idx(body,0)
            if current==1:
                struct.pack_into('<i',body,q+4+1,-4)
        if t==0x9d and current==1:
            fixes=b3.Threads().parse(body)
            body=b''.join(replace(f,disp=4).encode() for f in fixes)
        chunks.append(_pack(t,body))
    changed=b''.join(chunks)
    output,proof=b3.rewrite(changed,p,db,bases)
    mod=omf.parse_module(output)[0]
    text=mod.seg('_TEXT')[1]
    assert text.fixups[0].disp==4
    assert struct.unpack_from('<i',text.data,1)[0]==-4
    assert proof['rewrites'][0]['disp']==4


def test_aliasing_and_uncovered_boundaries_rejected():
    from types import SimpleNamespace
    s=omf.Segment('CONST','DATA',1,8,bytearray(b'ABC\0ABC\0'))
    mod=omf.Module(segments=[s])
    obj=SimpleNamespace(index=2,base=0x50000,end=0x50008)
    p=SimpleNamespace(le=SimpleNamespace(obj_at=lambda _:obj),
                      image={2:s.data},fix_at={},insns={},functions=[])
    for parts in ([b3.Symbol(0,4,0x50000,'a'),b3.Symbol(4,4,0x50000,'b')],
                  [b3.Symbol(0,4,0x50000,'a')]):
        with pytest.raises(b3.Rejected):
            b3.verify_data(p,mod,{}, {1:0x50000},{1:parts})


def test_retained_data_fixup_can_target_emptied_const():
    from types import SimpleNamespace
    obj=build.OUT/'retained_data.obj'
    build.run(['nasm','-f','obj','-I',str(build.ROOT/'asm')+'/','-o',obj,
               build.ROOT/'experiments/build_codegen/e5/fixtures/retained_data.asm'])
    out=[]
    for t,b in b3.records(obj.read_bytes()):
        if t==0x98:
            b=b[:3]+bytes(2)+b[3:];t=0x99
        elif t==0xa0:
            _,q=omf._idx(b,0);b=b[:q+2]+bytes(2)+b[q+2:];t=0xa1
        out.append(_pack(t,b))
    raw=b''.join(out)
    mod=omf.parse_module(raw)[0]
    di,_=mod.seg('_DATA');ci,_=mod.seg('CONST')
    code=SimpleNamespace(index=1,base=0x10000,end=0x10006)
    data=SimpleNamespace(index=2,base=0x50000,end=0x50008)
    fix=SimpleNamespace(size=4,src_type=7)
    p=SimpleNamespace(le=SimpleNamespace(obj_at=lambda a:code if a<0x50000 else data),
        image={1:bytearray(6),2:bytearray(struct.pack('<I',0x50004)+b'ABCD')},
        fix_at={0x10001:(fix,0x50000),0x50000:(fix,0x50004)},insns={},functions=[])
    output,proof=b3.rewrite(raw,p,{'Probe_':dict(addr=0x10000)},{ci:0x50004},retained_bases={di:0x50000})
    new=omf.parse_module(output)[0]
    assert new.seg('CONST')[1].length==0
    assert new.seg('_DATA')[1].length==4
    assert new.seg('_DATA')[1].fixups[0].target=='wc1_anchor_50004'
    assert len(proof['data_proofs'])==2


def test_weak_external_comments_rejected_before_renumbering(pointer_control):
    p,db,raw,bases=pointer_control
    changed=mutate(raw,lambda t,b: bytes([b[0],0xa8])+b[2:] if t==0x88 else b)
    with pytest.raises(b3.Rejected,match='COMENT'):
        b3.rewrite(changed,p,db,bases)
