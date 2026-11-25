"""Compile the E1 matrix, audit unmodified OMF with E0, and link closed matches.

Run from the configured Nix development shell:
    python3 -m experiments.build_codegen.e1.run_e1
Only experiment sources/results and disposable build/e1 artifacts are written.
"""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

import capstone
from wc1 import analysis, build, emit, le, match, oldcc, omfpatch
from experiments.build_codegen.e0 import matcher_proto as e0

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
FIXTURES = HERE / 'fixtures'
RESULTS = ROOT / 'docs/research/build-codegen/results/e1'
WORK = ROOT / 'build/e1'
BASE = '7c23d2371e95d8de93f0ba1652c8d44b858da273'
FLAGS = {
    'ot_4r': '-s -ot -ol -4r -zp2',
    'os_4r': '-s -os -ol -4r -zp2',
    'oa_4r': '-s -ot -oa -ol -4r -zp2',
    'ot_5r': '-s -ot -ol -5r -zp2',
    # Follow-up: alias scheduling + original four-byte function alignment.
    'oa_5r': '-s -ot -oa -ol -5r -zp2',
}
GROUPS = {
    'a': [('DialogItemHitTest', 0x16cc8, 0x16d34),
          ('DialogHighlightOn', 0x16d34, 0x16d48),
          ('DialogHighlightOff', 0x16d48, 0x16d5c)],
    'b': [('IntroOpPlaySound', 0x2315c, 0x23170),
          ('IntroOpSyncSound', 0x23170, 0x231cc),
          ('IntroOpWaitSound', 0x231cc, 0x231ec)],
}
INPUTS = [
    'src/mod_16390/dialog_hit_test_reference.c', 'src/include/mod_16390.h',
    'src/playflic/intro_op_play_sound.c', 'src/playflic/intro_op_sync_sound.c',
    'src/playflic/player_reference.c', 'src/include/playflic.h', 'src/include/input.h',
    'experiments/build_codegen/e0/matcher_proto.py',
]
MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def command(argv):
    r = subprocess.run([str(a) for a in argv], cwd=ROOT, text=True,
                       capture_output=True, timeout=120)
    if r.returncode:
        raise RuntimeError(f'{argv}:\n{r.stdout}{r.stderr}')
    return r.stdout


def body(source, name):
    """Extract these small fixtures' public C definitions (balanced braces)."""
    start = re.search(r'^.*\b' + re.escape(name) + r'\([^;]*?\)\s*\{', source, re.M).start()
    pos = source.index('{', start) + 1
    depth = 1
    while depth:
        depth += (source[pos] == '{') - (source[pos] == '}')
        pos += 1
    return source[start:pos] + '\n'


def matrix():
    """Full required controls; exploratory idioms use the successful -5r axis."""
    cases = []
    for group, funcs in GROUPS.items():
        fixture = FIXTURES / f'group_{group}_current.c'
        names = [f[0] for f in funcs]
        orders = [('original', names), ('reversed', names[::-1])]
        orders += [('standalone_' + n, [n]) for n in names]
        if group == 'b':
            orders += [('pair', [names[0], names[2]])]
        for order, selected in orders:
            for flag in FLAGS:
                cases.append(dict(id=f'{group}_current_{order}_{flag}', group=group,
                                  fixture=fixture, names=selected, order=order, flag=flag))
    for fixture in sorted(FIXTURES.glob('group_a_*.c')):
        spelling = fixture.stem.removeprefix('group_a_')
        if spelling == 'current':
            continue
        for flag in FLAGS if spelling == 'interleaved' else ['ot_5r']:
            cases.append(dict(id=f'a_{spelling}_original_{flag}', group='a',
                              fixture=fixture, names=[f[0] for f in GROUPS['a']],
                              order='original', flag=flag))
    names = [f[0] for f in GROUPS['a']]
    for order, selected in [('reversed',names[::-1])] + [('standalone_'+n,[n]) for n in names]:
        for flag in FLAGS:
            cases.append(dict(id=f'a_interleaved_{order}_{flag}',group='a',
                              fixture=FIXTURES/'group_a_interleaved.c',names=selected,
                              order=order,flag=flag))
    return cases


def listing(data, base=0, fixups=()):
    """Linear listing plus separate OMF relocations, so raw zero fields are clear."""
    lines = []
    for i in MD.disasm(bytes(data), base):
        lines.append(f'{i.address:08x}: {i.bytes.hex(" "):24} {i.mnemonic:7} {i.op_str}')
    lines += ['  OMF FIXUP ' + json.dumps(asdict(f), sort_keys=True) for f in fixups]
    return '\n'.join(lines) + '\n'


def owner_at(starts, target):
    owners = [s for s in starts if s[0] <= target]
    return owners[-1][1] if owners else None


def epilogue(data, target):
    """Accept only a bounded return tail: register moves/pops then RET.

    Ignore relocation-bearing calls/jumps when looking for cross-function
    sharing; a branch is evidence only when its destination decodes as a
    straight-line epilogue inside another function's storage.
    """
    if not 0 <= target < len(data):
        return False
    for i in MD.disasm(bytes(data[target:target+24]), target):
        if i.mnemonic == 'ret':
            return True
        if i.mnemonic not in ('mov', 'pop', 'leave'):
            return False
    return False


def branch_record(i, starts, data, fixups=()):
    b = e0._branch(i)
    if b is None or i.mnemonic == 'call':
        return None
    field, size, target = b
    relocated = any(f.offset < field+size and field < f.offset+f.size for f in fixups)
    source_owner = owner_at(starts, i.address)
    target_owner = owner_at(starts, target) if 0 <= target < len(data) else None
    shared = (not relocated and source_owner != target_owner and
              target_owner is not None and epilogue(data, target))
    return dict(offset=i.address, function_offset=i.address-next(o for o,n in starts if n==source_owner),
                opcode=i.mnemonic, bytes=bytes(i.bytes).hex(' '), field_size=size,
                target_offset=target, target_function=target_owner,
                target_function_offset=(target-next(o for o,n in starts if n==target_owner)
                                        if target_owner else None),
                relocated=relocated, shared_epilogue=shared)


def original_evidence(p, group):
    funcs = GROUPS[group]
    lo, hi = funcs[0][1], funcs[-1][2]
    data = bytes(p.cbytes[lo-p.code.base:hi-p.code.base])
    starts = [(a-lo, n) for n,a,_ in funcs]
    branches = {n: [] for n,_,_ in funcs}
    for i in MD.disasm(data, 0):
        r = branch_record(i, starts, data)
        if r:
            r['address'] = lo+r['offset']
            r['target_address'] = lo+r['target_offset']
            branches[owner_at(starts, i.address)].append(r)
    return dict(start=lo, end=hi, publics={n:a-lo for n,a,_ in funcs},
                bytes=data.hex(), branches=branches,
                le_fixups=[dict(address=a, target=p.fix_at[a][1])
                           for a in sorted(p.fix_at) if lo <= a < hi])


def padding(data, starts):
    """Preserve suffixes of filler instructions at every physical boundary.

    A tail may instead be a shared jump; walk decoded instructions, never
    search raw bytes for RET (which could occur in an address/immediate).
    """
    rows = []
    for k,(lo,names) in enumerate(starts):
        hi = starts[k+1][0] if k+1 < len(starts) else len(data)
        insns = list(MD.disasm(bytes(data[lo:hi]),lo))
        end = hi
        for i in reversed(insns):
            if i.address+i.size != end or not match.is_filler(bytes(i.bytes)):
                break
            end = i.address
        rows.append(dict(functions=names, offset=end, end=hi, bytes=bytes(data[end:hi]).hex(' '),
                         length=hi-end))
    return rows


def compare_images(executable):
    """Use wc1.compare itself, and independently preserve exhaustive diff counts."""
    r = subprocess.run([sys.executable, '-m', 'wc1.compare',
                        str(ROOT/'original/install/war.exe'), str(executable)],
                       capture_output=True, text=True, timeout=120, cwd=ROOT)
    a = le.LE((ROOT/'original/install/war.exe').read_bytes())
    b = le.LE(executable.read_bytes())
    ia, ib = a.loaded_image(), b.loaded_image()
    byte_diffs = 0
    for oa,ob in zip(a.objects,b.objects):
        da, db = bytes(ia[oa.index]), bytes(ib[ob.index])
        byte_diffs += sum(x != y for x,y in zip(da,db))
        byte_diffs += sum(bool(v) for v in da[len(db):]) + sum(bool(v) for v in db[len(da):])
    fixes = lambda image: {(f.obj,f.src_off,f.target_obj,f.target_off) for f in image.fixups_unique}
    fa, fb = fixes(a), fixes(b)
    return dict(status='IDENTICAL' if r.returncode==0 else 'DIFFERENT',
                identical=r.returncode==0, compare_exit_code=r.returncode,
                byte_diffs=byte_diffs, original_fixups=len(fa), linked_fixups=len(fb),
                only_original_fixups=len(fa-fb), only_linked_fixups=len(fb-fa),
                compare_stdout=r.stdout, compare_stderr=r.stderr,
                executable=str(executable.relative_to(ROOT)))


def integrate(p, db, obj, row):
    """One C region + symbolic ASM remainder: production Build A placement path.

    No production symbol changes, no copied repository, no byte/branch editing.
    Only the ordinary SEGDEF BYTE-alignment patch is applied to a private copy.
    E0 RegionMatch is a mandatory guard before placement or linking.
    """
    if row['region_match_verdict']['verdict'] != 'MATCH':
        return dict(status='NOT_ATTEMPTED_REGION_NOT_MATCH', identical=None)
    folder = WORK / 'links' / row['id']
    folder.mkdir(parents=True, exist_ok=True)
    funcs = [db[n+'_'] for n in row['order']]
    cr, anchors = build.place(p, row['source'], str(obj), funcs)
    if anchors:
        raise RuntimeError('E1 fixtures unexpectedly acquired local data anchors')
    cuts, entries, replaced, errors = build.check_placed_plan(
        p, [(row['source'],str(obj),cr,anchors,funcs)])
    if errors:
        return dict(status='PLACEMENT_REJECTED', identical=False, errors=errors)
    linked_obj = folder/'candidate.obj'
    omfpatch.patch(str(obj), str(linked_obj), align='byte')
    code, data = p.le.obj(analysis.CODE_OBJ), p.le.obj(analysis.DATA_OBJ)
    names = {e['addr']:e['link_name'] for e in db.values()}
    raw = ROOT/'analysis/raw_insns.txt'
    force = {int(line.split()[0],16) for line in raw.read_text().splitlines()
             if line.strip() and not line.startswith('#')}
    emitter = emit.Emitter(p, names=names, force_raw=force, cuts=cuts,
                           entries=entries, replaced=replaced)
    pieces = emitter.emit_pieces(str(folder), [(code.base,cr[0]),(cr[1],code.end)],
                                  [(data.base,data.end),None])
    objects = []
    for asm in pieces:
        piece = Path(asm).with_suffix('.obj')
        try:
            command(['nasm','-O0','-f','obj','-I',str(ROOT/'asm')+'/',
                     '-w-number-overflow','-w+error=label-orphan','-o',piece,asm])
        except RuntimeError as error:
            if 'OBJ format can only handle 16- or 32-byte relocations' not in str(error):
                raise
            return dict(status='ASSEMBLY_REJECTED_EXTERNAL_REL8', identical=False,
                        diagnostic=str(error))
        objects.append(piece)
    stub = folder/'stub.exe'
    stub.write_bytes(p.le.stub)
    # Required named outputs for successful original-order primary groups.
    group = row['group']
    primary = row['id'] in ('a_interleaved_original_oa_5r', 'b_current_original_ot_5r')
    executable = WORK/f'war_group_{group}.exe' if primary else folder/'war.exe'
    script = folder/'war.lnk'
    seq = [objects[0],linked_obj,objects[1]]
    script.write_text('system dos4g\n'+f'name {executable}\n'+
                      ''.join(f'file {o}\n' for o in seq)+
                      f'option stub={stub}\noption map={folder / "war.map"}\noption quiet\n')
    command(['wlink',f'@{script}'])
    result = compare_images(executable)
    result.update(code_range=list(cr), policy='single C region plus original symbolic ASM remainder',
                  unpatched_obj_sha256=sha(obj), linked_obj_sha256=sha(linked_obj))
    return result


def run(output=RESULTS):
    output.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    if oldcc.check():
        raise RuntimeError('Watcom 10.0a provenance check failed: '+repr(oldcc.check()))
    p, db = e0.load_inputs()
    index = e0.OriginalIndex(p)
    original = {g:original_evidence(p,g) for g in GROUPS}
    evidence = ['E1 disassembly evidence. Original: loaded preferred-base image.\n'
                'Compiled: unmodified OMF _TEXT offsets; zero relocation fields are NOT final targets.\n'
                'All offsets below are hexadecimal; JSON offsets/addresses are integers.\n']
    for group, orig in original.items():
        evidence += [f'\n=== ORIGINAL GROUP {group.upper()} [{orig["start"]:#x},{orig["end"]:#x}) ===\n',
                     listing(bytes.fromhex(orig['bytes']),orig['start']),
                     'LE FIXUPS '+json.dumps(orig['le_fixups'],sort_keys=True)+'\n']
    evidence += ['\n=== GROUP A NEXT FUNCTION (not part of the three-function region) ===\n',
                 listing(p.cbytes[0x16d5c-p.code.base:0x16d61-p.code.base],0x16d5c)]
    rows = []
    for case in matrix():
        cid, group = case['id'], case['group']
        folder = WORK/cid
        folder.mkdir(exist_ok=True)
        source = folder/'candidate.c'
        include = 'mod_16390.h' if group=='a' else 'playflic.h'
        fixture_text = case['fixture'].read_text()
        text = '#include "'+include+'"\n\n'+'\n'.join(body(fixture_text,n) for n in case['names'])
        source.write_text(text)
        obj = folder/'candidate.obj'
        # -zld suppresses dependency timestamp COMENTs, never code generation.
        flags = match.BASE_CFLAGS+' -zld '+FLAGS[case['flag']]
        mod = match.compile_c(str(source), flags, str(obj), cc='10.0a')
        verdicts = e0.match_module(p,mod,db,index)
        ti, seg = mod.seg('_TEXT')
        # Aliased public functions under -os share one physical range. Keep
        # every name in the result; use the first declared alias for ownership.
        publics = {n:off for n,(si,off) in mod.publics.items() if si==ti}
        offsets = sorted(set(publics.values()))
        starts = [(off,next(n for n in case['names'] if publics[n+'_']==off)) for off in offsets]
        branches = {n:[] for n in case['names']}
        for lo,name in starts:
            hi = next((o for o,_ in starts if o>lo),len(seg.data))
            for insn in MD.disasm(bytes(seg.data[lo:hi]),lo):
                branch = branch_record(insn,starts,seg.data,seg.fixups)
                if branch:
                    for alias in case['names']:
                        if publics[alias+'_']==lo:
                            branches[alias].append(branch)
        functions = {}
        for name in case['names']:
            originals = original[group]['branches'][name]
            functions[name] = dict(
                shared_epilogue_reproduced=any(b['shared_epilogue'] for b in branches[name]),
                exact_branch_encoding=dict(compiled=branches[name], original=originals,
                    shared_branch_bytes_equal=(
                        [b['bytes'] for b in branches[name] if b['shared_epilogue']] ==
                        [b['bytes'] for b in originals if b['shared_epilogue']])),
                function_match_verdict=verdicts['functions'][name+'_'],
                region_match_verdict=verdicts['region'])
        row = dict(id=cid,group=group,flag=case['flag'],flags=flags,
                   effective_10a_flags=oldcc.normalize_flags(flags), order=case['names'],
                   control=case['order'],fixture=str(case['fixture'].relative_to(ROOT)),
                   fixture_sha256=sha(case['fixture']),source=str(source.relative_to(ROOT)),
                   source_sha256=sha(source),obj=str(obj.relative_to(ROOT)),obj_sha256=sha(obj),
                   publics=publics,text_size=len(seg.data),text_bytes=bytes(seg.data).hex(),
                   text_segment=dict(name=seg.name,cls=seg.cls,align=seg.align),
                   omf_fixups=[asdict(f) for f in seg.fixups],
                   padding=padding(seg.data,[(o,[n for n,v in publics.items() if v==o]) for o in offsets]),
                   functions=functions,region_match_verdict=verdicts['region'])
        linked = integrate(p,db,obj,row)
        row['build_a_comparison'] = linked
        for f in functions.values():
            f['build_a_integrated_identical'] = linked['identical']
            f['build_a_status'] = linked['status']
        rows.append(row)
        evidence += [f'\n=== {cid} ===\nFLAGS {flags}\nOMF SHA256 {sha(obj)}\n',
                     'PUBLICS '+json.dumps(publics,sort_keys=True)+'\n',
                     'PADDING '+json.dumps(row['padding'],sort_keys=True)+'\n',
                     listing(seg.data,fixups=seg.fixups),
                     'FUNCTION VERDICTS '+json.dumps({n:f['function_match_verdict']['verdict'] for n,f in functions.items()},sort_keys=True)+'\n',
                     'REGION '+verdicts['region']['verdict']+'\n',
                     'BUILD A '+json.dumps(linked,sort_keys=True)+'\n']
        print(f'{cid}: RegionMatch={verdicts["region"]["verdict"]}, Build A={linked["status"]}', flush=True)
    diff = command(['git','diff',BASE,'--','tools/','src/','analysis/','tests/',
                    'Makefile','flake.nix','AGENTS.md'])
    result = dict(experiment='E1',schema_version=1,baseline=BASE,
                  provenance=dict(compiler='Watcom C/C++ 10.0a',
                      compiler_manifest={rel:digest for digest,rel,required in oldcc.manifest() if required},
                      input_sha256={s:sha(ROOT/s) for s in INPUTS},
                      original_exe_sha256=sha(ROOT/'original/install/war.exe'),
                      dependency_metadata='-zld: compiler suppresses source/header timestamp COMENT records',
                      production_diff=diff),
                  boundaries=dict(group_a_requested_end=0x16d5e,group_a_actual_next_function=0x16d5c,
                      next_function_prologue=bytes(p.cbytes[0x16d5c-p.code.base:0x16d61-p.code.base]).hex(' '),
                      explanation='0x16d5e includes the next function prologue (push esi; push edi); three-function region ends at 0x16d5c.'),
                  flags=FLAGS,original=original,variants=rows,
                  summary=dict(variants=len(rows),function_observations=sum(len(r['functions']) for r in rows),
                      region_matches=sum(r['region_match_verdict']['verdict']=='MATCH' for r in rows),
                      identical_builds=sum(r['build_a_comparison']['identical'] is True for r in rows)))
    (output/'results.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    (output/'disasm_evidence.txt').write_text(''.join(evidence))
    if diff:
        raise RuntimeError('Production paths differ from baseline')
    if any(r['build_a_comparison']['status']=='DIFFERENT' for r in rows):
        raise RuntimeError('A linked image differs; inspect results')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=RESULTS)
    args = parser.parse_args()
    result = run(args.output)
    print(json.dumps(result['summary'],sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
