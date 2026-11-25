"""Synthetic oracle and negative controls shared by the runner and pytest."""
from types import SimpleNamespace
import struct
from wc1 import omf
from wc1.omfpatch import _pack
from . import build_e5 as build
from . import omf_b3 as b3


def mutate(raw, callback):
    return b''.join(_pack(t,callback(t,b)) for t,b in b3.records(raw))


def pointer_control():
    build.OUT.mkdir(parents=True,exist_ok=True)
    obj = build.OUT/'pointer.obj'
    build.run(['nasm','-f','obj','-I',str(build.ROOT/'asm')+'/','-o',obj,
               build.ROOT/'experiments/build_codegen/e5/fixtures/pointer.asm'])
    # NASM uses narrow length/offset records for small USE32 segments.
    # Normalize just the representation for this OMF32-only control.
    widened=[]
    for t,b in b3.records(obj.read_bytes()):
        if t==0x98:
            b=b[:3]+bytes(2)+b[3:];t=0x99
        elif t==0xa0:
            _,q=omf._idx(b,0);b=b[:q+2]+bytes(2)+b[q+2:];t=0xa1
        widened.append(_pack(t,b))
    raw = b''.join(widened)
    mod, _ = omf.parse_module(raw)
    si, _ = mod.seg('_DATA')
    # Explicit synthetic oracle, independent of the compiled data: pointer at
    # 0x50000 must resolve to the named symbol at 0x12340, followed by ABCD.
    fix = SimpleNamespace(size=4,src_type=7)
    code = SimpleNamespace(index=1,base=0x10000,end=0x10006)
    data = SimpleNamespace(index=2,base=0x50000,end=0x50008)
    image = {1:bytearray(6),2:bytearray(struct.pack('<I',0x12340)+b'ABCD')}
    le = SimpleNamespace(obj_at=lambda a:code if code.base<=a<code.end else data if data.base<=a<data.end else None)
    p = SimpleNamespace(le=le,image=image,fix_at={0x50000:(fix,0x12340),0x10001:(fix,0x50000)},insns={},functions=[])
    db = dict(Probe_=dict(addr=0x10000),good_target=dict(addr=0x12340),evil_target=dict(addr=0x12344))
    return p,db,raw,{si:0x50000}


def leaks():
    return sorted(str(p.relative_to(build.ROOT))
                  for directory in ('src','analysis','tests')
                  for p in (build.ROOT/directory).rglob('*')
                  if p.is_file() and b'wc1_anchor_' in p.read_bytes())


def negative_controls():
    p, db, raw, bases = pointer_control()
    _, positive = b3.rewrite(raw,p,db,bases)
    byte_bad = mutate(raw,lambda t,b:b[:-1]+bytes([b[-1]^1]) if t==0xa1 and b.endswith(b'ABCD') else b)
    pointer_bad = mutate(raw,lambda t,b:b.replace(b'good_target',b'evil_target') if t==0x8c else b)
    tests = [('N1_byte',byte_bad,{}),('N2_pointer',pointer_bad,{}),
             ('N3_mutable_merge',raw,dict(per_symbol={next(iter(bases)):[b3.Symbol(0,8,0x50000,'unproven')]})),
             ('N3_interior_struct',raw,dict(per_symbol={next(iter(bases)):[b3.Symbol(0,8,0x50000,'unproven','interior_struct')]}))]
    result = {}
    for name, data, options in tests:
        try:
            b3.rewrite(data,p,db,bases,**options)
        except b3.Rejected as exc:
            result[name] = dict(rejected=True,reason=str(exc))
        else:
            raise AssertionError(f'{name} was accepted')
    result['N4_leak'] = dict(occurrences=leaks())
    result['positive_pointer'] = positive['data_proofs'][0]['metrics']
    return result
