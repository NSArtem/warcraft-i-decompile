"""Isolated Build A harness: C code sequence plus ONE ASM data piece.

All generated files are under build/e5. Production modules are read/imported,
never patched, monkeypatched or invoked through their writing entry points.
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib
import itertools
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading

from wc1 import analysis, build, emit, le, match, omf, path, symbols
from experiments.build_codegen.e0 import matcher_proto as e0
from . import omf_b3 as b3

OUT = Path(path('build', 'e5'))
ROOT = Path(path())
FLAGS = '-s -ot -ol -4r -zp2'

# Watcom 10.0a's Win32 wcc386 keeps command-line paths in fixed buffers and
# dies with an access violation past them: E7 measured `-i=` failing at 129
# bytes and the source operand at 130 (rev-e5-01 reproduced it compiling the
# E5 fixtures from a 149-character checkout).  Every path E5 hands the
# compiler therefore goes through a short mirror of the checkout, bounded by
# the limit below with a wide margin.
COMPILER_PATH_LIMIT = 112
_MIRROR = {}
_MIRROR_LOCK = threading.Lock()
_SEQ = itertools.count()


def _short_base():
    """A short writable directory; /tmp first so the mirror prefix is bounded."""
    for base in ('/tmp', os.environ.get('TMPDIR'), tempfile.gettempdir()):
        if base and os.path.isdir(base) and os.access(base, os.W_OK):
            return Path(base)
    raise RuntimeError('E5 needs a writable temporary directory for the compiler mirror')


def compiler_root():
    """Short absolute path that mirrors the checkout for compiler arguments.

    The returned directory is `<base>/wc1e5-<checkout hash>/repo`, a symlink to
    the checkout, so `compiler_root() / relative_path` names the same file with
    a bounded prefix.  It is created once per checkout and reused across
    processes (the path itself is deterministic).
    """
    with _MIRROR_LOCK:
        if 'root' not in _MIRROR:
            repo = Path(os.path.realpath(str(ROOT)))
            short = _short_base()/('wc1e5-' + hashlib.sha1(str(repo).encode()).hexdigest()[:8])
            short.mkdir(exist_ok=True)
            root = short/'repo'
            if os.path.islink(root) and Path(os.path.realpath(str(root))) != repo:
                os.unlink(root)
            if not os.path.lexists(root):
                try:
                    os.symlink(repo, root, target_is_directory=True)
                except FileExistsError:
                    pass
            if Path(os.path.realpath(str(root))) != repo:
                raise RuntimeError(f'cannot create the short compiler mirror {root} -> {repo}')
            _MIRROR['root'] = root
    return _MIRROR['root']


def _external(p):
    """Short name for a path outside the checkout (e.g. an overridden OUT)."""
    links = compiler_root().parent/'ext'
    links.mkdir(exist_ok=True)
    link = links/hashlib.sha1(str(p.parent).encode()).hexdigest()[:16]
    if not os.path.lexists(link):
        try:
            os.symlink(p.parent, link, target_is_directory=True)
        except FileExistsError:
            pass
    return link/p.name


def compiler_path(p):
    """The compiler-facing absolute form of p, bounded by COMPILER_PATH_LIMIT."""
    p = Path(os.path.abspath(str(p)))
    root = compiler_root()
    if p.is_relative_to(root):
        out = p
    else:
        try:
            out = root/p.relative_to(Path(os.path.abspath(str(ROOT))))
        except ValueError:
            out = _external(p)
    if len(str(out)) > COMPILER_PATH_LIMIT:
        raise RuntimeError(f'compiler-facing path is {len(str(out))} characters '
                           f'(Watcom 10.0a limit {COMPILER_PATH_LIMIT}): {out}')
    return out


def compile_10a(src, out, flags=None, timeout=180):
    """Compile one file with Watcom 10.0a behind the short mirror.

    wc1.oldcc adds its own `-i=` arguments (src/include and the 10.0a h/)
    derived from WC1_ROOT, so a process with WC1_ROOT set to the mirror does
    the compile: source, output and include paths all stay bounded even when
    the checkout root is 160+ characters.  Production modules are imported,
    never patched.
    """
    src, out = Path(src), Path(out)
    root = compiler_root()
    short_out = compiler_path(out)
    tmp = short_out.with_name(f'{short_out.stem}~{os.getpid()}-{next(_SEQ)}{short_out.suffix}')
    env = dict(os.environ)
    env['WC1_ROOT'] = str(root)
    tools = str(root/'tools')
    env['PYTHONPATH'] = tools + (os.pathsep + env['PYTHONPATH'] if env.get('PYTHONPATH') else '')
    argv = [sys.executable, '-m', 'experiments.build_codegen.e5.wcc10a',
            str(compiler_path(src)), str(tmp)]
    if flags:
        argv.append(flags)
    try:
        r = subprocess.run(argv, capture_output=True, text=True, cwd=str(root),
                           env=env, timeout=timeout + 20)
    except subprocess.TimeoutExpired as e:
        raise match.CompileTimeout(f'error: Watcom 10.0a helper timed out: {src}') from e
    if r.returncode == 78:
        raise match.CompileTimeout(f'error: {r.stderr.strip()}')
    if r.returncode:
        raise SystemExit(f'compile failed (Watcom 10.0a, short mirror): {src}\n'
                         f'{r.stdout}{r.stderr}'.rstrip())
    try:
        os.replace(tmp, out)
    except OSError:             # an output outside the checkout may be another filesystem
        shutil.copyfile(tmp, out)
        os.unlink(tmp)
    return out


def compile_source(src, name, flags=None):
    OUT.mkdir(parents=True, exist_ok=True)
    obj = OUT/(name + '.obj')
    real = ROOT/src
    cc = match.file_cc(str(real))
    if cc == '10.0a':
        compile_10a(real, obj, flags)
    else:
        match.compile_c(str(real), flags, str(obj), cc=cc, quiet=True)
    return obj


def run(args):
    r = subprocess.run(list(map(str, args)), capture_output=True, text=True, timeout=180)
    if r.returncode:
        raise RuntimeError(f'{args}: {r.stdout}\n{r.stderr}')
    return r.stdout


def inputs():
    # Do not populate the production analysis cache.
    p = analysis.run(cache=False)
    funcs, datas, _ = symbols.load()
    db = {e['link_name']: e for t in (funcs, datas) for e in t.values()}
    return p, funcs, datas, db


def data_bases(p, mod, db, code_base, original_index=None):
    checker = e0._Checker(p, mod, db, original_index or e0.OriginalIndex(p))
    ti, text = mod.seg('_TEXT')
    checker.bases[ti] = code_base
    # Canonical named definitions are independent identity evidence.
    for name, (si, off) in list(mod.publics.items()) + list(mod.statics.items()):
        if name in db and mod.segments[si-1].cls in ('DATA', 'BSS'):
            checker.anchor(si, db[name]['addr']-off, dict(symbol=name))
    checker.infer(text, 0, text.length, code_base, True)
    for _ in mod.segments:
        for si, base in list(checker.bases.items()):
            if si != ti:
                s = mod.segments[si-1]
                checker.infer(s, 0, s.length, base, False)
    if checker.anchor_conflicts:
        raise b3.Rejected(f'inconsistent data anchors: {checker.anchor_conflicts}')
    bases = {}
    for si, s in enumerate(mod.segments, 1):
        if s.cls in ('DATA', 'BSS') and s.length:
            if si not in checker.bases:
                raise b3.Rejected(f'unproven data base: {s.name}')
            bases[si] = checker.bases[si]
    return bases


def prepare_baseline(p, funcs, db):
    original_index = e0.OriginalIndex(p)
    by_src = {}
    for e in funcs.values():
        if e.get('src'):
            by_src.setdefault(e['src'], []).append(e)

    def job(item):
        src, fs = item
        obj = compile_source(src, 'baseline_' + src.replace('/', '_')[:-2])
        mod = omf.parse_object(obj)
        cr, _ = build.place(p, src, str(obj), fs)
        # Verify existing code with the production matcher. B3 adds the E0
        # full data-pointer check even for these already admitted T3 objects.
        results = match.match_module(p, mod, db)
        if not all(r[1] == 'MATCH' for r in results):
            raise b3.Rejected(f'baseline code mismatch {src}: {results}')
        bases = data_bases(p, mod, db, cr[0], original_index)
        return dict(src=src, obj=obj, cr=cr, funcs=fs, bases=bases,
                    compiler=match.file_cc(str(ROOT/src)), flags=match.file_cflags(str(ROOT/src)))

    with ThreadPoolExecutor(min(8, os.cpu_count() or 1)) as pool:
        return sorted(pool.map(job, sorted(by_src.items())), key=lambda x:x['cr'])


class AnchorEmitter(emit.Emitter):
    """Add aliases at independently verified addresses without renaming symbols."""
    def __init__(self, *args, anchors=(), **kwargs):
        self.anchors = set(anchors)
        super().__init__(*args, **kwargs)
        # Labels split byte runs. Keep canonical names used by compiled C.
        for a in anchors:
            self.labels.setdefault(a, f'wc1_anchor_{a:05x}')

    def _emit_data(self, lines, start, end, legacy=False):
        begin = len(lines)
        super()._emit_data(lines, start, end, legacy)
        aliases = {self.labels[a]: f'wc1_anchor_{a:05x}' for a in self.anchors}
        for i in range(len(lines)-1, begin-1, -1):
            if lines[i].startswith('GLABEL '):
                name = lines[i].split()[1]
                if name in aliases and name != aliases[name]:
                    lines.insert(i+1, 'GLABEL ' + aliases[name])


def link(p, funcs, datas, db, objects, name, frame_mode='preserve', per_symbols=None,
         thread_transform=None):
    out = OUT/name
    out.mkdir(parents=True, exist_ok=True)
    objects = sorted(objects, key=lambda x:x['cr'])
    cuts = {o['cr'][0]:o['cr'][1] for o in objects}
    if len(cuts) != len(objects):
        raise b3.Rejected('duplicate code ranges')
    for a, b in zip(objects, objects[1:]):
        if a['cr'][1] > b['cr'][0]:
            raise b3.Rejected('overlapping code')
    entries = [e['addr'] for o in objects for e in o['funcs']]
    errors = emit.replaced_interior_refs(p, sorted(cuts.items()), entries)
    if errors:
        raise b3.Rejected(str(errors))
    original_index = e0.OriginalIndex(p)
    proofs, patched = [], []
    for k, o in enumerate(objects):
        raw = o['obj'].read_bytes()
        if thread_transform and o.get('experiment'):
            raw = thread_transform(raw)
        data, proof = b3.rewrite(raw, p, db, o['bases'], frame_mode=frame_mode,
                                 per_symbol=(per_symbols or {}).get(o['src']), original_index=original_index)
        dst = out/f'c_{k:03d}.obj'
        dst.write_bytes(data)
        patched.append(dst)
        if proof['anchors']:
            proofs.append(dict(src=o['src'], compiler=o['compiler'], flags=o['flags'],
                               code_range=list(o['cr']), experimental=o.get('experiment',False), **proof))
    anchors = {a for proof in proofs for a in proof['anchors']}
    names = {e['addr']: e['link_name'] for t in (datas, funcs) for e in t.values()}
    force = {int(l.split()[0],16) for l in (ROOT/'analysis/raw_insns.txt').read_text().splitlines()
             if l.strip() and not l.startswith('#')}
    emitter = AnchorEmitter(p, names=names, force_raw=force, cuts=cuts, entries=entries, anchors=anchors)
    code, data = p.le.obj(1), p.le.obj(2)
    cp, cursor = [], code.base
    for o in objects:
        cs, ce = o['cr']
        cp.append((cursor, cs) if cursor < cs else None)
        cursor = ce
    cp.append((cursor, code.end))
    # Data is emitted exactly once, independent of code ordering.
    dp = [(data.base, data.end)] + [None]*(len(cp)-1)
    asms = emitter.emit_pieces(str(out), cp, dp)

    def assemble(asm):
        obj = Path(asm).with_suffix('.obj')
        run(['nasm','-O0','-f','obj','-I',str(ROOT/'asm')+'/', '-w-number-overflow',
             '-w+error=label-orphan','-o', obj, asm])
        return obj

    with ThreadPoolExecutor(min(8, os.cpu_count() or 1)) as pool:
        asm_objs = list(pool.map(assemble, asms))
    seq = []
    for k, obj in enumerate(asm_objs):
        seq.append(obj)
        if k < len(patched):
            seq.append(patched[k])
    stub = out/'stub.exe'
    stub.write_bytes(p.le.stub)
    exe = OUT/f'war_{name}.exe'
    lnk = out/'war.lnk'
    lnk.write_text('system dos4g\nname '+str(exe)+'\n'+
                   ''.join('file '+str(o)+'\n' for o in seq)+
                   f'option stub={stub}\noption map={out/"war.map"}\noption quiet\n')
    linker = run(['wlink','@'+str(lnk)])
    comparison = subprocess.run([sys.executable,'-m','wc1.compare',path('original/install/war.exe'),str(exe)],
                                capture_output=True,text=True,timeout=60)
    (out/'compare.txt').write_text(comparison.stdout)
    actual = le.LE(exe.read_bytes())
    fx = lambda image: {(f.obj,f.src_off,f.src_type,f.target_obj,f.target_off) for f in image.fixups_unique}
    a, b = fx(p.le), fx(actual)
    ia, ib = p.le.loaded_image(), actual.loaded_image()
    byte_diffs = sum(sum(x != y for x,y in zip(ia[i], ib[i])) for i in ia)
    original_by_va = {p.le.obj(f.obj).base+f.src_off:f for f in p.le.fixups_unique}
    linked_by_va = {actual.obj(f.obj).base+f.src_off:f for f in actual.fixups_unique}
    anchor_records=[]
    for proof in proofs:
        if not proof['experimental']:
            continue
        for change in proof['rewrites']:
            address=proof['code_range'][0]+change['offset']
            old,new=original_by_va[address],linked_by_va[address]
            anchor_records.append(dict(source=address, source_object=new.obj, source_offset=new.src_off,
                original_target_object=old.target_obj, original_target_offset=old.target_off,
                linked_target_object=new.target_obj, linked_target_offset=new.target_off))
    result = dict(anchor_fixup_records=anchor_records, name=name, identical=comparison.returncode==0 and a==b, byte_diffs=byte_diffs,
                  original_fixups=len(a), linked_fixups=len(b), only_original=len(a-b), only_linked=len(b-a),
                  c_functions=len(entries), c_objects=len(objects), data_asm_pieces=1,
                  frame_mode=frame_mode, linker_output=linker.strip(),
                  comparison=comparison.stdout.strip(), proofs=proofs)
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def synthetic():
    """Link untouched 10.0a three-segment C, then B3 + one ASM data provider.

    The first executable is the oracle, not substituted Warcraft bytes. This
    control separately establishes wlink equivalence for arbitrary data layout.
    """
    from types import SimpleNamespace
    obj = OUT/'synthetic.obj'
    compile_10a(ROOT/'experiments/build_codegen/e5/fixtures/three_segments.c', obj, FLAGS)
    runtime = OUT/'synthetic_runtime.obj'
    run(['nasm','-f','obj','-I',str(ROOT/'asm')+'/','-o',runtime,ROOT/'experiments/build_codegen/e5/fixtures/synthetic_runtime.asm'])
    def mini_link(objects, name):
        exe, lnk = OUT/(name+'.exe'), OUT/(name+'.lnk')
        lnk.write_text('system dos4g\noption quiet\nname '+str(exe)+'\n'+
                       ''.join('file '+str(o)+'\n' for o in objects))
        run(['wlink','@'+str(lnk)])
        return exe, le.LE(exe.read_bytes())
    original_path, original = mini_link([obj,runtime], 'synthetic_original')
    image = original.loaded_image()
    fix_at = {original.obj(f.obj).base+f.src_off:(f,original.obj(f.target_obj).base+f.target_off)
              for f in original.fixups_unique}
    p = SimpleNamespace(le=original,image=image,fix_at=fix_at,insns={},functions=[])
    db = {'Probe_':{'addr':original.obj(1).base}}
    mod = omf.parse_object(obj)
    bases = data_bases(p,mod,db,original.obj(1).base)
    # Static symbols receive their independently compiled LPUBDEF boundaries.
    # E0 pointer checks still use the original linker fixups, not these labels.
    for name,(si,off) in mod.statics.items():
        db[name] = dict(addr=bases[si]+off)
    results = []
    for mode in ('preserve','target','external','flat','dgroup'):
        raw, proof = b3.rewrite(obj.read_bytes(),p,db,bases,frame_mode=mode)
        patched = OUT/f'synthetic_{mode}.obj'
        patched.write_bytes(raw)
        # Define canonical data bytes exactly once. Padding is included in
        # the initialized range; the synthetic stack remains in runtime.obj.
        data_obj = original.obj(2)
        data_base = data_obj.base
        init_end = max(bases[si]+s.length for si,s in enumerate(mod.segments,1) if s.cls=='DATA' and s.length)
        bss_end = max(bases[si]+s.length for si,s in enumerate(mod.segments,1) if s.cls=='BSS' and s.length)
        lines = ['%include "wc1.inc"','DATA_SECTION']
        anchors = set(proof['anchors'])
        for a in range(data_base,init_end):
            if a in anchors:
                lines.append(f'GLABEL wc1_anchor_{a:05x}')
            lines.append(f'db {image[2][a-data_base]}')
        lines.append('BSS_SECTION')
        for a in range(init_end,bss_end):
            if a in anchors:
                lines.append(f'GLABEL wc1_anchor_{a:05x}')
            lines.append('resb 1')
        lines += ['STACK_SECTION', 'END_SECTIONS']
        asm = OUT/f'synthetic_provider_{mode}.asm'
        provider = asm.with_suffix('.obj')
        asm.write_text('\n'.join(lines)+'\n')
        run(['nasm','-f','obj','-I',str(ROOT/'asm')+'/','-o',provider,asm])
        linked_path, linked = mini_link([patched,provider,runtime],'synthetic_'+mode)
        c = subprocess.run([sys.executable,'-m','wc1.compare',str(original_path),str(linked_path)],capture_output=True,text=True,timeout=60)
        results.append(dict(compiler='10.0a',flags=FLAGS,frame_mode=mode,identical=c.returncode==0,comparison=c.stdout.strip(),
                            segments={s.name:s.length for s in mod.segments},proof=proof))
    return results
