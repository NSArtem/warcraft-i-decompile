"""Isolated E5 Fix B3 prototype. No production tool is modified.

The supported loadable subset is SEGDEF32, LEDATA32 and off32 FIXUPP32.
All eight THREAD slots survive record boundaries, including discarded data.
LIDATA and non-off32 fixups are deliberately rejected before any output.
"""
from dataclasses import dataclass, replace
import struct

from wc1 import omf
from wc1.omfpatch import _pack
from experiments.build_codegen.e0 import matcher_proto as e0


class Rejected(ValueError):
    pass


def index(n):
    if not 0 < n < 0x8000:
        raise Rejected('invalid OMF index')
    return bytes([n]) if n < 128 else bytes([0x80 | (n >> 8), n & 255])


def records(raw):
    p = 0
    while p < len(raw):
        if p + 3 > len(raw):
            raise Rejected('truncated record header')
        t, n = raw[p], int.from_bytes(raw[p+1:p+3], 'little')
        end = p + 3 + n
        if n < 1 or end > len(raw):
            raise Rejected('truncated OMF record')
        # A zero checksum byte is explicitly permitted by OMF (unchecked).
        if raw[end-1] and sum(raw[p:end]) & 255:
            raise Rejected('bad OMF checksum')
        yield t, bytearray(raw[p+3:end-1])
        p = end
    if not raw or t not in (0x8a, 0x8b):
        raise Rejected('missing MODEND')


@dataclass(frozen=True)
class Fix:
    offset: int
    loc: int
    self_rel: bool
    fm: int
    fi: int | None
    tm: int
    ti: int
    disp: int | None

    def encode(self):
        locat = 0x8000 | (0 if self.self_rel else 0x4000) | self.loc << 10 | self.offset
        fd = self.fm << 4 | self.tm | (4 if self.disp is None else 0)
        out = struct.pack('>H', locat) + bytes([fd])
        if self.fm < 3:
            out += index(self.fi)
        out += index(self.ti)
        if self.disp is not None:
            out += struct.pack('<I', self.disp)
        return out


class Threads:
    def __init__(self):
        self.slots = {}
        self.count = 0
        self.uses = 0

    def parse(self, body):
        """Decode one FIXUPP32, retaining F0..F3/T0..T3 across calls."""
        q, out = 0, []

        def byte():
            nonlocal q
            if q >= len(body):
                raise Rejected('truncated FIXUPP32')
            b = body[q]
            q += 1
            return b

        def idx():
            b = byte()
            v = ((b & 127) << 8 | byte()) if b & 128 else b
            if not v:
                raise Rejected('zero index in FIXUPP32')
            return v

        def thread(kind, num):
            self.uses += 1
            if (kind, num) not in self.slots:
                raise Rejected('undefined THREAD')
            return self.slots[kind, num]

        while q < len(body):
            b = byte()
            if not b & 128:
                frame = bool(b & 64)
                method, slot = (b >> 2) & 7, b & 3
                if b & 32 or method not in ((0, 1, 2, 4, 5) if frame else (0, 1, 2)):
                    raise Rejected('unsupported THREAD method')
                datum = idx() if method < 3 else None
                self.slots[frame, slot] = method, datum
                self.count += 1
                continue
            locat = b << 8 | byte()
            loc = (locat >> 10) & 15
            if loc not in omf.LOC_NAMES:
                raise Rejected(f'unsupported OMF location encoding {loc}')
            fd = byte()
            if fd & 128:
                if fd & 64:
                    raise Rejected('reserved frame THREAD bit')
                fm, fi = thread(True, (fd >> 4) & 3)
            else:
                fm = (fd >> 4) & 7
                if fm not in (0, 1, 2, 4, 5):
                    raise Rejected('unsupported frame method')
                fi = idx() if fm < 3 else None
            if fd & 8:
                tm, ti = thread(False, fd & 3)
            else:
                tm, ti = fd & 3, idx()
            if tm not in (0, 1, 2):
                raise Rejected('unsupported target method')
            disp = None
            if not fd & 4:
                disp = int.from_bytes(bytes(byte() for _ in range(4)), 'little')
            out.append(Fix(locat & 1023, loc, not bool(locat & 0x4000), fm, fi, tm, ti, disp))
        return out


@dataclass(frozen=True)
class Symbol:
    """Caller-supplied independent object boundary; never inferred by bytes alone.

    CONST literals must include their NUL. Named mutable objects additionally
    require an exact public/static definition and a canonical DB symbol.
    """
    start: int
    size: int
    address: int
    identity: str
    kind: str = 'literal'


def verify_data(p, mod, db, bases, per_symbol=None, original_index=None):
    """Run E0's actual byte AND forward/reverse pointer checks before rewriting.

    Whole segments use one verified base. Per-symbol mode is intentionally a
    partition (no uncovered padding); no field within an object can move.
    """
    per_symbol = per_symbol or {}
    checker = e0._Checker(p, mod, db, original_index or e0.OriginalIndex(p))
    checker.bases = dict(bases)
    proofs = []
    for si, base in bases.items():
        if not 1 <= si <= len(mod.segments):
            raise Rejected('invalid anchored segment')
        s = mod.segments[si-1]
        if s.cls not in ('DATA', 'BSS') or not s.length:
            raise Rejected('only nonempty data segments can be anchored')
        parts = sorted(per_symbol.get(si, ()), key=lambda x: x.start)
        if not parts:
            parts = [Symbol(0, s.length, base, 'whole_segment', 'whole')]
        cursor = 0
        for sym in parts:
            if sym.start != cursor or sym.size <= 0:
                raise Rejected('unverified boundary, padding or overlapping symbols')
            cursor += sym.size
            if sym.kind != 'whole':
                if sym.kind == 'literal':
                    if s.name != 'CONST' or not sym.identity or not s.data[sym.start:cursor].endswith(b'\0'):
                        raise Rejected('mutable content merging or unproven literal boundary')
                    if b'\0' in s.data[sym.start:cursor-1]:
                        raise Rejected('literal boundary contains another object')
                elif sym.kind == 'named':
                    definition = mod.publics.get(sym.identity, mod.statics.get(sym.identity))
                    if definition != (si, sym.start) or db.get(sym.identity, {}).get('addr') != sym.address:
                        raise Rejected('unverified independent canonical symbol')
                    # DB sizes are explicit proof obligations, not inferred from a neighbour.
                    if db[sym.identity].get('size') != sym.size:
                        raise Rejected('unverified named object size')
                else:
                    raise Rejected('unverified interior struct offset remapping')
            r = checker.check(s, sym.start, cursor, sym.address, False, sym.identity)
            if r.verdict != 'MATCH':
                raise Rejected(f'E0 data check {s.name}: {r.verdict}: {r.findings[:3]}')
            proofs.append(r.to_dict())
        if cursor != s.length:
            raise Rejected('data partition does not cover entire segment')
        # Preserve identity: distinct non-overlapping compiled objects may not
        # silently collapse onto one canonical object, even with equal bytes.
        for i, a in enumerate(parts):
            for b in parts[i+1:]:
                if max(a.address, b.address) < min(a.address+a.size, b.address+b.size):
                    raise Rejected('aliasing/pointer identity would change')
    if set(per_symbol) - set(bases):
        raise Rejected('per-symbol mapping without verified segment')
    return proofs


def rewrite(raw, p, db, bases, *, per_symbol=None, frame_mode='preserve', original_index=None):
    """Return (rewritten bytes, provenance); bases maps OMF segment -> original VA.

    frame_mode is an experiment knob: preserve, flat, dgroup, target, external.
    The input is never mutated. All checks finish before output is returned.
    """
    if frame_mode not in ('preserve', 'flat', 'dgroup', 'target', 'external'):
        raise Rejected('unknown frame mode')
    recs = list(records(raw))
    # Parser expansion of untrusted LIDATA can allocate arbitrarily. Reject first.
    if any(t & ~1 == 0xa2 for t, _ in recs):
        raise Rejected('unverified LIDATA is unsupported')
    if any(t in (0x98, 0xa0, 0x9c, 0xb0, 0xc2, 0xc3) for t, _ in recs):
        raise Rejected('16-bit records, COMDEF or COMDAT unsupported')
    allowed = {0x80, 0x88, 0x96, 0x99, 0x9a, 0x8c, 0xb4, 0xbc,
               0x90, 0x91, 0xb6, 0xb7, 0x94, 0x95, 0xa1, 0x9d, 0x8a, 0x8b}
    if any(t not in allowed for t, _ in recs):
        raise Rejected('unsupported OMF record')
    preflight = Threads()
    seen_data = False
    for t, body in recs:
        if t == 0xa1:
            seen_data = True
        if seen_data and t == 0x96 and any(rt == 0xbc for rt, _ in recs):
            raise Rejected('CEXTDEF with late LNAMES unsupported')
        if t == 0x9d:
            preflight.parse(body)
    mod, _ = omf.parse_module(raw)
    per_symbol = per_symbol or {}
    code_bases = {}
    for name, (seg, off) in list(mod.publics.items()) + list(mod.statics.items()):
        if name in db:
            b = db[name]['addr'] - off
            if mod.segments[seg-1].cls == 'CODE':
                if seg in code_bases and code_bases[seg] != b:
                    raise Rejected('inconsistent code layout')
                code_bases[seg] = b
            elif seg in bases and bases[seg] != b:
                raise Rejected('canonical data definition contradicts anchor')
    proofs = verify_data(p, mod, db, bases, per_symbol, original_index)
    metadata = {i for i, s in enumerate(mod.segments, 1) if e0._metadata(s)}
    dropping = set(bases) | metadata
    anchors = sorted({sym.address for si in bases for sym in per_symbol.get(si, ())} |
                     {base for si, base in bases.items() if si not in per_symbol})
    # wlink requires even unused LEXTDEFs to resolve. Remove declarations for
    # emptied local data and renumber every surviving external operand.
    removed_ext = {i for i, n in enumerate(mod.externs, 1)
                   if mod.publics.get(n, mod.statics.get(n, (None,)))[0] in dropping}
    ext_map = {old: new for new, old in enumerate(
        (i for i in range(1, len(mod.externs)+1) if i not in removed_ext), 1)}
    ext = {a: len(ext_map)+i for i, a in enumerate(anchors, 1)}
    names = {a: f'wc1_anchor_{a:05x}' for a in anchors}
    extbody = b''.join(bytes([len(names[a])])+names[a].encode()+b'\0' for a in anchors)
    groups = {v: k for k, v in mod.groups.items()}
    threads, output = Threads(), []
    si = 0
    last = None
    rewrites = []
    inserted = False
    declarations, ordinal = [], 0
    for rt, body in recs:
        if rt not in (0x8c, 0xb4, 0xbc):
            continue
        q, kept = 0, bytearray()
        while q < len(body):
            begin = q
            if rt == 0xbc:
                _, q = omf._idx(body, q)
            else:
                _, q = omf._name(body, q)
            _, q = omf._idx(body, q)
            ordinal += 1
            if ordinal not in removed_ext:
                kept += body[begin:q]
        if kept:
            declarations.append((rt, kept))
    for t, body in recs:
        if t in (0x8c, 0xb4, 0xbc):
            continue
        if not inserted and t in (0xa1, 0x9d, 0x8a, 0x8b):
            output.extend(_pack(rt, b) for rt, b in declarations)
            if extbody:
                output.append(_pack(0x8c, extbody))
            inserted = True
        if t == 0x99:
            si += 1
            if body[0] >> 5 == 0:
                raise Rejected('absolute segment unsupported')
            body[0] = (body[0] & 31) | 32  # BYTE alignment
            if si in dropping:
                body[1:5] = bytes(4)
        elif t == 0xa1:
            seg, q = omf._idx(body, 0)
            off = int.from_bytes(body[q:q+4], 'little')
            if q+4 > len(body) or off+len(body)-q-4 > mod.segments[seg-1].length:
                raise Rejected('LEDATA bounds')
            last = (seg, off, body, q+4)
            if seg in dropping:
                continue
        elif t == 0x9d:
            fixes = threads.parse(body)  # including dropped data's thread definitions
            encoded = []
            for f in fixes:
                if last is None:
                    raise Rejected('FIXUPP without LEDATA')
                seg, off, data, q = last
                if seg in metadata:
                    continue
                if f.loc != 9:
                    raise Rejected(f'unsupported loc {f.loc}; E0 verifies off32 only')
                if q+f.offset+4 > len(data):
                    raise Rejected('fixup crosses LEDATA boundary')
                if f.fm < 3:
                    limit = (len(mod.segments), len(mod.groups), len(mod.externs))[f.fm]
                    if not 1 <= f.fi <= limit:
                        raise Rejected('invalid frame index')
                limit = (len(mod.segments), len(mod.groups), len(mod.externs))[f.tm]
                if not 1 <= f.ti <= limit:
                    raise Rejected('invalid target index')
                if seg in bases:
                    continue
                if f.tm == 0 and f.ti in metadata:
                    raise Rejected('runtime reference to debug metadata')
                if f.tm == 2 and f.ti <= len(mod.externs):
                    n = mod.externs[f.ti-1]
                    definition = mod.publics.get(n, mod.statics.get(n))
                    if definition and definition[0] in bases:
                        struct.pack_into('<I', data, q+f.offset,
                                         (struct.unpack_from('<I', data, q+f.offset)[0] + definition[1]) & 0xffffffff)
                        f = replace(f, tm=0, ti=definition[0])
                if f.tm == 0 and f.ti in bases:
                    old = f
                    address = bases[f.ti]
                    if f.ti in per_symbol:
                        add = struct.unpack_from('<i', data, q+f.offset)[0] + (f.disp or 0)
                        parts = [s for s in per_symbol[f.ti] if s.start <= add < s.start+s.size]
                        if len(parts) != 1:
                            raise Rejected('unverified per-symbol target')
                        sym = parts[0]
                        address = sym.address
                        # Preserve explicit disp; move only the inline address field.
                        struct.pack_into('<I', data, q+f.offset, (add-sym.start-(f.disp or 0)) & 0xffffffff)
                    if seg not in code_bases:
                        raise Rejected('unproven retained source address')
                    source = code_bases[seg] + off + f.offset
                    inline = struct.unpack_from('<i', data, q+f.offset)[0]
                    expected = (address + inline + (f.disp or 0)) & 0xffffffff
                    original = p.fix_at.get(source)
                    if f.self_rel or original is None or original[1] != expected:
                        raise Rejected('anchor reference contradicts original addressing obligation')
                    fm, fi = f.fm, f.fi
                    if fm == 2 and frame_mode == 'preserve':
                        if fi not in ext_map:
                            raise Rejected('frame uses removed local external')
                        fi = ext_map[fi]
                    if frame_mode == 'target':
                        fm, fi = 5, None
                    elif frame_mode == 'external':
                        fm, fi = 2, ext[address]
                    elif frame_mode in ('flat', 'dgroup'):
                        group = 'FLAT' if frame_mode == 'flat' else 'DGROUP'
                        if group not in groups:
                            raise Rejected(f'missing {group}')
                        fm, fi = 1, groups[group]
                    elif fm == 0 and fi in bases or fm == 4:
                        raise Rejected('frame tied to emptied/location segment')
                    f = replace(f, tm=2, ti=ext[address], fm=fm, fi=fi)
                    rewrites.append(dict(segment=seg, offset=off+f.offset, address=address,
                                         old_frame=[old.fm, old.fi], frame=[fm, fi],
                                         self_rel=f.self_rel, disp=f.disp))
                else:
                    if f.tm == 2:
                        if f.ti not in ext_map:
                            raise Rejected('unresolved removed local external')
                        f = replace(f, ti=ext_map[f.ti])
                    if f.fm == 2:
                        if f.fi not in ext_map:
                            raise Rejected('frame uses removed local external')
                        f = replace(f, fi=ext_map[f.fi])
                encoded.append(f.encode())
            # Keep records bounded; expanded entries are fully self-contained.
            for k in range(0, len(encoded), 64):
                output.append(_pack(t, b''.join(encoded[k:k+64])))
            continue
        elif t & ~1 in (0x90, 0xb6):
            _, q = omf._idx(body, 0)
            psi, _ = omf._idx(body, q)
            if psi in dropping:
                # Removing data definitions is safe only if never referenced by
                # local EXTDEF (checked above); external providers remain ASM.
                continue
        # Keep LEDATA as a mutable reference until all following fixups are done.
        output.append((t, body))
    packed = b''.join(_pack(*r) if isinstance(r, tuple) else r for r in output)
    return packed, dict(anchors=anchors, threads=threads.count, thread_uses=threads.uses,
                        rewrites=rewrites, data_proofs=proofs, frame_mode=frame_mode,
                        excluded_metadata=sorted(metadata))
