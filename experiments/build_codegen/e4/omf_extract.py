"""E4: conservative selective OMF32 slice extraction for a `VerifiedRegion`.

Experiment only: no production module is imported for writing, patched or
invoked through its writing entry points.  The input is a whole compilation
unit compiled by Watcom 10.0a; the output contains only the verified `_TEXT`
slice `[obj_lo, obj_hi)` rebased to offset 0, with every relocation converted
into an equivalent representation.

The invariant implemented here is RFC section 6.1 *Post-Codegen Symbolic
Relocation Equivalence*:

  * no opcode, instruction length, register operand or non-address immediate
    byte inside the slice may change (checked again after the transform);
  * `rel8` is never widened; an outgoing `rel8` fails closed;
  * the original binary is only *corroboration*: every transformed field needs
    an independently named target from the symbol database, and the original
    program must agree with it at the mapped address;
  * every transform is recorded in the provenance record.

`omf_extract` also normalizes 16-bit OMF record widths to their 32-bit forms
(`SEGDEF16`->`SEGDEF32`, `LEDATA16`->`LEDATA32`, `PUBDEF16`->`PUBDEF32`,
`LPUBDEF16`->`LPUBDEF32`, `FIXUPP16`->`FIXUPP32`): a representation change with
no semantic content, recorded in the provenance.

Canonical digests: `loadable_digest` hashes a canonical JSON view of the
*loadable* records (segment definitions, data, fixups, publics, statics,
externs, groups).  `THEADR` (0x80), `COMENT` (0x88) and the Watcom debug
segments ($$SYMBOLS/$$TYPES) are deliberately excluded: they embed
compiler-facing paths and are not loadable image content.
"""
from hashlib import sha256
import json
from pathlib import Path
import struct

import capstone
from capstone.x86 import X86_OP_IMM
from wc1 import omf
from wc1.omfpatch import _pack
from experiments.build_codegen.e0.matcher_proto import OriginalIndex, _metadata
from experiments.build_codegen.e3.partial_matcher import VerifiedRegion
from experiments.build_codegen.e5 import omf_b3 as b3

TEXT_SEGMENT = "_TEXT"
LOC32 = 9
CHUNK = 1024            # FIXUPP32 relative offsets are 10 bits wide

# Fail-closed reasons (RFC section 6.2 / E4 contract section 4.1).
OUTGOING_REL8 = "outgoing_rel8"
INTERIOR_TARGET = "interior_target"
AMBIGUOUS_SYMBOL = "ambiguous_symbol"
DATA_LAYOUT_MISMATCH = "data_layout_mismatch"
RELOCATION_TARGET_MISMATCH = "relocation_target_mismatch"
INCOMPLETE_CLOSURE = "incomplete_closure"
UNSUPPORTED = "unsupported_construct"
NOT_VERIFIED = "not_verified_region"

# Order in which competing defects are reported.
SEVERITY = (OUTGOING_REL8, INTERIOR_TARGET, AMBIGUOUS_SYMBOL, INCOMPLETE_CLOSURE,
            RELOCATION_TARGET_MISMATCH, DATA_LAYOUT_MISMATCH, UNSUPPORTED)


class UnsupportedExtractionError(ValueError):
    """Fail-closed extraction rejection with a machine-readable reason."""

    def __init__(self, reason, message, **evidence):
        super().__init__(f"{reason}: {message}")
        self.reason = reason
        self.record = dict(reason=reason, message=message, **evidence)

    def to_dict(self):
        return dict(self.record)


# --------------------------------------------------------------------- records
def read_records(raw):
    """[(type, body)] of one OMF module, checksum-validated, MODEND-terminated."""
    p, out = 0, []
    while p < len(raw):
        if p + 3 > len(raw):
            raise UnsupportedExtractionError(UNSUPPORTED, "truncated record header")
        t = raw[p]
        n = int.from_bytes(raw[p+1:p+3], "little")
        end = p + 3 + n
        if n < 1 or end > len(raw):
            raise UnsupportedExtractionError(UNSUPPORTED, "truncated OMF record")
        if raw[end-1] and sum(raw[p:end]) & 0xFF:
            raise UnsupportedExtractionError(UNSUPPORTED, "bad OMF checksum")
        out.append((t, bytearray(raw[p+3:end-1])))
        p = end
    if not out or out[-1][0] not in (0x8A, 0x8B):
        raise UnsupportedExtractionError(UNSUPPORTED, "missing MODEND")
    return out


def _segdef(body, is32):
    attr = body[0]
    if attr >> 5 == 0:
        raise UnsupportedExtractionError(UNSUPPORTED, "absolute segment unsupported")
    q = 1
    width = 4 if is32 else 2
    length = int.from_bytes(body[q:q+width], "little")
    q += width
    ni, q = omf._idx(body, q)
    ci, q = omf._idx(body, q)
    return attr, length, ni, ci, bytes(body[q:])   # trailing page index, if any


def _pubdef_entries(body, q, is32):
    """[(name, offset, type)] from a PUBDEF body at q (16-bit widening tolerated)."""
    for width in ((4,) if is32 else (2, 4)):
        try:
            entries, p = [], q
            while p < len(body):
                name, p = omf._name(body, p)
                off = int.from_bytes(body[p:p+width], "little")
                p += width
                ti, p = omf._idx(body, p)
                entries.append((name, off, ti))
            if p == len(body):
                return entries
        except (IndexError, ValueError, struct.error):
            continue
    raise UnsupportedExtractionError(UNSUPPORTED, "malformed PUBDEF")


def _pubdef(body, is32):
    gi, q = omf._idx(body, 0)
    si, q = omf._idx(body, q)
    frame = None
    if si == 0:
        frame = bytes(body[q:q+2])
        q += 2
    return gi, si, frame, _pubdef_entries(body, q, is32)


def _idx_bytes(n, allow_zero=False):
    if not (0 if allow_zero else 1) <= n < 0x8000:
        raise UnsupportedExtractionError(UNSUPPORTED, f"OMF index out of range: {n}")
    return bytes([n]) if n < 128 else bytes([0x80 | (n >> 8), n & 255])


def _segdef32(attr, length, ni, ci, tail=b""):
    return (bytes([attr]) + struct.pack("<I", length) + _idx_bytes(ni) +
            _idx_bytes(ci) + bytes(tail))


def _pubdef32(gi, si, frame, entries):
    out = bytearray(_idx_bytes(gi) + _idx_bytes(si))
    if frame is not None:
        out += frame
    for name, off, ti in entries:
        out += bytes([len(name)]) + name.encode("latin-1") + struct.pack("<I", off) + _idx_bytes(ti, True)
    return bytes(out)


class RawFix:
    """One expanded FIXUPP subrecord (self-contained, no THREAD slots)."""
    __slots__ = ("offset", "loc", "self_rel", "fm", "fi", "tm", "ti", "disp")

    def __init__(self, offset, loc, self_rel, fm, fi, tm, ti, disp):
        self.offset, self.loc, self.self_rel = offset, loc, self_rel
        self.fm, self.fi, self.tm, self.ti, self.disp = fm, fi, tm, ti, disp

    def encode(self):
        return b3.Fix(self.offset, self.loc, self.self_rel, self.fm, self.fi,
                      self.tm, self.ti, self.disp).encode()

    def as_dict(self):
        return dict(offset=self.offset, loc=self.loc, self_rel=self.self_rel,
                    frame_method=self.fm, frame_index=self.fi,
                    target_method=self.tm, target_index=self.ti,
                    displacement=self.disp)


class Threads:
    """FIXUPP parser that expands THREAD slots and honours the record width."""

    def __init__(self):
        self.slots = {}
        self.definitions = 0
        self.uses = 0

    def parse(self, body, width):
        q, out = 0, []

        def byte():
            nonlocal q
            if q >= len(body):
                raise UnsupportedExtractionError(UNSUPPORTED, "truncated FIXUPP")
            q += 1
            return body[q-1]

        def idx():
            b = byte()
            v = ((b & 127) << 8 | byte()) if b & 128 else b
            if not v:
                raise UnsupportedExtractionError(UNSUPPORTED, "zero index in FIXUPP")
            return v

        def thread(frame, num):
            self.uses += 1
            if (frame, num) not in self.slots:
                raise UnsupportedExtractionError(UNSUPPORTED, "undefined THREAD")
            return self.slots[frame, num]

        while q < len(body):
            b0 = byte()
            if not b0 & 0x80:
                frame = bool(b0 & 0x40)
                method, slot = (b0 >> 2) & 7, b0 & 3
                if b0 & 0x20 or method not in ((0, 1, 2, 4, 5) if frame else (0, 1, 2)):
                    raise UnsupportedExtractionError(UNSUPPORTED, "unsupported THREAD method")
                datum = idx() if method < 3 else None
                self.slots[frame, slot] = (method, datum)
                self.definitions += 1
                continue
            locat = b0 << 8 | byte()
            loc = (locat >> 10) & 15
            if loc not in omf.LOC_NAMES:
                raise UnsupportedExtractionError(UNSUPPORTED, f"unsupported location {loc}")
            fd = byte()
            if fd & 0x80:
                if fd & 0x40:
                    raise UnsupportedExtractionError(UNSUPPORTED, "reserved frame THREAD bit")
                fm, fi = thread(True, (fd >> 4) & 3)
            else:
                fm = (fd >> 4) & 7
                if fm not in (0, 1, 2, 4, 5):
                    raise UnsupportedExtractionError(UNSUPPORTED, "unsupported frame method")
                fi = idx() if fm < 3 else None
            if fd & 0x08:
                tm, ti = thread(False, fd & 3)
            else:
                tm, ti = fd & 3, idx()
            if tm not in (0, 1, 2):
                raise UnsupportedExtractionError(UNSUPPORTED, "unsupported target method")
            disp = None
            if not fd & 4:
                disp = int.from_bytes(bytes(byte() for _ in range(width)), "little")
            out.append(RawFix(locat & 1023, loc, not bool(locat & 0x4000), fm, fi, tm, ti, disp))
        return out


def raw_fixups(recs):
    """{segment index: [RawFix]} aligned with `omf.parse_module`'s fixup lists."""
    by_seg, last = {}, None
    for t, body in recs:
        base_t = t & ~1
        if base_t == 0xA0:                   # LEDATA16/32 (LIDATA rejected earlier)
            seg, q = omf._idx(body, 0)
            width = 4 if t & 1 else 2
            last = (seg, int.from_bytes(body[q:q+width], "little"))
        elif base_t == 0x9C:                 # FIXUPP16/32
            if last is None:
                raise UnsupportedExtractionError(UNSUPPORTED, "FIXUPP before LEDATA")
            seg, base_off = last
            fixes = Threads().parse(body, 4 if t & 1 else 2)
            for fix in fixes:
                fix.offset += base_off       # FIXUPP doff is LEDATA-relative
            by_seg.setdefault(seg, []).extend(fixes)
    return by_seg


def loadable_digest(obj):
    """Path-independent SHA-256 of the loadable OMF content (see module doc)."""
    mod = omf.parse_object(obj) if not isinstance(obj, omf.Module) else obj
    canon = dict(
        segments=[dict(name=s.name, cls=s.cls, align=s.align, length=s.length,
                       data=sha256(bytes(s.data)).hexdigest(),
                       fixups=[dict(offset=f.offset, loc=f.loc, self_rel=f.self_rel,
                                    target_kind=f.target_kind, target=f.target,
                                    disp=f.disp) for f in s.fixups])
                  for s in mod.segments],
        publics=sorted([n, si, off] for n, (si, off) in mod.publics.items()),
        statics=sorted([n, si, off] for n, (si, off) in mod.statics.items()),
        externs=list(mod.externs),
        groups=sorted([i, n] for i, n in mod.groups.items()),
    )
    return sha256(json.dumps(canon, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def text_sha256(data):
    return sha256(bytes(data)).hexdigest()


# ----------------------------------------------------------------- branch scan
def _rel_branch(insn):
    """(field_offset, width, target) for a supported direct near branch."""
    b = bytes(insn.bytes)
    if len(b) == 5 and b[0] in (0xE8, 0xE9):
        k, n = 1, 4
    elif len(b) == 6 and b[0] == 0x0F and 0x80 <= b[1] <= 0x8F:
        k, n = 2, 4
    elif len(b) == 2 and (b[0] == 0xEB or 0x70 <= b[0] <= 0x7F or 0xE0 <= b[0] <= 0xE3):
        k, n = 1, 1
    else:
        return None
    return (insn.address + k, n,
            (insn.address + len(b) + int.from_bytes(b[k:k+n], "little", signed=True)) & 0xFFFFFFFF)


def _is_direct_branch(insn):
    return bool((insn.group(capstone.CS_GRP_JUMP) or insn.group(capstone.CS_GRP_CALL)) and
                insn.operands and insn.operands[0].type == X86_OP_IMM)


class Scan:
    """Independent closure/target evidence for one candidate slice."""

    def __init__(self):
        self.issues = []
        self.branches = []
        self.direct_calls = []
        self.instructions = 0

    def add(self, reason, message, **evidence):
        self.issues.append(dict(reason=reason, message=message, **evidence))

    def raise_first(self):
        if not self.issues:
            return
        rank = {r: i for i, r in enumerate(SEVERITY)}
        worst = min(self.issues, key=lambda i: rank.get(i["reason"], len(rank)))
        extra = {k: v for k, v in worst.items() if k not in ("reason", "message")}
        raise UnsupportedExtractionError(worst["reason"], worst["message"],
                                         issues=self.issues, **extra)


def _symbol_at(mod, text_seg, off):
    names = [n for table in (mod.publics, mod.statics)
             for n, (si, o) in table.items() if si == text_seg and o == off]
    return names[0] if len(names) == 1 else None


def _interior(p, target):
    return target is not None and any(f["start"] < target < f["end"] for f in p.functions)


def scan_slice(raw_or_mod, db, p, lo, hi, base, *, anchored=(), index=None):
    """Scan the compiled slice and return a `Scan` (findings, never raises).

    `anchored` is the set of non-_TEXT segment indices covered by an independent
    data plan (E5 Fix B3); every other nonempty, non-metadata segment fails
    closed with `data_layout_mismatch`.
    """
    mod = raw_or_mod if isinstance(raw_or_mod, omf.Module) else omf.parse_object(raw_or_mod)
    ti, seg = mod.seg(TEXT_SEGMENT)
    text = bytes(seg.data)
    index = index or OriginalIndex(p)
    anchored = set(anchored)
    scan = Scan()

    # Segment closure and relocations owned by retained local data.
    for si, s in enumerate(mod.segments, 1):
        if si == ti or _metadata(s):
            continue
        if s.length and si not in anchored:
            scan.add(DATA_LAYOUT_MISMATCH,
                     "nonempty local data segment has no independently proven base",
                     segment=si, segment_name=s.name, size=s.length)
        if si in anchored:
            continue                      # dropped by the E5 Fix B3 plan
        for f in s.fixups:
            local = (mod.statics.get(f.target, mod.publics.get(f.target))
                     if f.target_kind == "ext" else None)
            if (f.target_kind == "seg" and f.target == ti) or (local and local[0] == ti):
                scan.add(INCOMPLETE_CLOSURE,
                         "retained local data references code the slice does not own",
                         segment=si, offset=f.offset)

    # Independent linear decode: a branch may only leave the slice through a
    # named, database-confirmed rel32 target.
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    fix_by_off = {f.offset: f for f in seg.fixups}
    pos = lo
    while pos < hi:
        insn = next(md.disasm(text[pos:hi], pos, 1), None)
        if insn is None:
            scan.add(UNSUPPORTED, "slice bytes do not decode linearly",
                     offset=pos, byte=text[pos] if pos < len(text) else None)
            break
        scan.instructions += 1
        branch = _rel_branch(insn)
        if branch is None and _is_direct_branch(insn):
            scan.add(UNSUPPORTED, "direct branch outside the supported rel8/rel32 encodings",
                     offset=pos, encoding=bytes(insn.bytes).hex())
        if branch is not None:
            field, width, target = branch
            inside = lo <= target < hi
            scan.branches.append(dict(offset=field, width=width,
                                      target_object_offset=target, in_slice=inside))
            if not inside:
                if width == 1:
                    scan.add(OUTGOING_REL8, "outgoing rel8 cannot be relocated or widened",
                             offset=field, target_object_offset=target)
                elif field not in fix_by_off:
                    scan.direct_calls.append(
                        _direct_call(scan, mod, ti, db, p, index, lo, base, field, target))
        pos += len(insn.bytes)

    _scan_fixups(scan, mod, ti, text, db, p, index, lo, hi, base, anchored)
    return scan


def _direct_call(scan, mod, ti, db, p, index, lo, base, field, target):
    """Classify/resolve an unfixed `call/jmp rel32` whose target left the slice."""
    record = dict(offset=field, target_object_offset=target,
                  original_address=base + field - lo)
    name = _symbol_at(mod, ti, target)
    if name is None:
        # The compiled target has no symbolic identity of its own.  The
        # original binary may only classify the refusal, never supply it.
        br = index.branches.get(base + field - lo)
        original_target = br[1] if br else None
        reason = INTERIOR_TARGET if _interior(p, original_target) else AMBIGUOUS_SYMBOL
        scan.add(reason, "unfixed branch target has no module symbol",
                 offset=field, target_object_offset=target,
                 original_target=original_target)
        return dict(record, symbol=None, reason=reason)
    entry = db.get(name)
    if entry is None:
        scan.add(AMBIGUOUS_SYMBOL,
                 "module symbol has no independent database entry",
                 offset=field, symbol=name, target_object_offset=target)
        return dict(record, symbol=name, reason=AMBIGUOUS_SYMBOL)
    address = entry.get("addr")
    br = index.branches.get(base + field - lo)
    if br is None or br[0] != 4 or br[1] != address:
        scan.add(RELOCATION_TARGET_MISMATCH,
                 "original branch target disagrees with the symbol database",
                 offset=field, symbol=name, database_address=address,
                 original_target=br[1] if br else None)
        return dict(record, symbol=name, reason=RELOCATION_TARGET_MISMATCH)
    return dict(record, symbol=name, target_address=address,
                action="EXTDEF + self-relative FIXUPP32", reason=None)


def _check_original_bytes(scan, mod, ti, text, p, lo, hi, base):
    """Every non-relocated compiled byte must equal the original image byte.

    `RegionMatch` already establishes this for a `VerifiedRegion`, but the
    extractor re-checks it so a stale proof cannot smuggle changed opcodes,
    lengths, registers or non-address immediates into an extraction.
    """
    obj = p.le.obj_at(base)
    if obj is None or base + hi - lo > obj.end:
        scan.add(UNSUPPORTED, "original image does not cover the slice extent",
                 offset=lo, orig_start=base)
        return
    want = bytes(p.image[obj.index][base-obj.base:base-obj.base+hi-lo])
    masked = set()
    for fu in mod.segments[ti-1].fixups:
        if fu.loc == LOC32 and lo <= fu.offset and fu.offset + 4 <= hi:
            masked.update(range(fu.offset, fu.offset + 4))
    diffs = [(i, text[lo+i], want[i]) for i in range(hi-lo) if lo+i not in masked
             and text[lo+i] != want[i]]
    for i, got, expected in diffs[:8]:
        scan.add(UNSUPPORTED, "compiled byte differs from the verified original",
                 offset=lo+i, got=got, want=expected)
    if len(diffs) > 8:
        scan.add(UNSUPPORTED, "compiled bytes differ from the verified original",
                 count=len(diffs))


def _scan_fixups(scan, mod, ti, text, db, p, index, lo, hi, base, anchored):
    _check_original_bytes(scan, mod, ti, text, p, lo, hi, base)
    for fu in mod.segments[ti-1].fixups:
        if not (fu.offset + 4 > lo and fu.offset < hi):
            continue
        if fu.loc != LOC32:
            scan.add(UNSUPPORTED, "only OMF off32 relocations are supported",
                     offset=fu.offset, location=fu.loc)
            continue
        if fu.offset < lo or fu.offset + 4 > hi:
            scan.add(UNSUPPORTED, "relocation field crosses the slice boundary",
                     offset=fu.offset)
            continue
        inline = struct.unpack_from("<i", text, fu.offset)[0]
        addend = (inline + fu.disp) & 0xFFFFFFFF
        original_address = base + fu.offset - lo
        if fu.target_kind == "ext":
            name = fu.target
            local = mod.statics.get(name, mod.publics.get(name))
            if local is not None and local[0] == ti:
                entry = db.get(name)
                if entry is None:
                    scan.add(AMBIGUOUS_SYMBOL, "local code symbol has no database entry",
                             offset=fu.offset, symbol=name)
                    continue
                if lo <= local[1] < hi:
                    # A definition inside the slice must obey the linear map.
                    if entry["addr"] != base + local[1] - lo:
                        scan.add(RELOCATION_TARGET_MISMATCH,
                                 "local definition contradicts its database address",
                                 offset=fu.offset, symbol=name,
                                 database_address=entry["addr"],
                                 expected=base + local[1] - lo)
                    continue
                # A definition outside the slice has no linear object mapping:
                # its identity must come from the database and the original
                # branch at the call site, never from the sibling's object offset.
                if entry["addr"] not in {f["start"] for f in p.functions}:
                    scan.add(AMBIGUOUS_SYMBOL,
                             "sibling code symbol is not an independently discovered function",
                             offset=fu.offset, symbol=name, database_address=entry["addr"])
                    continue
                if not fu.self_rel:
                    scan.add(INCOMPLETE_CLOSURE, "absolute code pointer leaves the slice",
                             offset=fu.offset, symbol=name)
                    continue
                br = index.branches.get(original_address)
                if (br is None or br[0] != 4 or
                        br[1] != (entry["addr"] + addend) & 0xFFFFFFFF):
                    scan.add(RELOCATION_TARGET_MISMATCH,
                             "intra-TU call target disagrees with the original",
                             offset=fu.offset, symbol=name, database_address=entry["addr"],
                             original_target=br[1] if br else None)
                continue
            if local is not None:            # local data definition
                si = local[0]
                if si not in anchored:
                    scan.add(DATA_LAYOUT_MISMATCH,
                             "reference to a local data segment without a proven base",
                             offset=fu.offset, symbol=name, segment=si)
                    continue
                entry = db.get(name)
                if entry is None:
                    scan.add(AMBIGUOUS_SYMBOL, "local data symbol has no database entry",
                             offset=fu.offset, symbol=name)
                    continue
                original = p.fix_at.get(original_address)
                if original is None or original[1] != (entry["addr"] + addend) & 0xFFFFFFFF:
                    scan.add(RELOCATION_TARGET_MISMATCH,
                             "data reference disagrees with the original relocation",
                             offset=fu.offset, symbol=name,
                             database_address=entry["addr"],
                             original_target=original[1] if original else None)
                continue
            entry = db.get(name)             # pure external
            if entry is None:
                scan.add(AMBIGUOUS_SYMBOL, "external symbol has no database entry",
                         offset=fu.offset, symbol=name)
                continue
            expected = (entry["addr"] + addend) & 0xFFFFFFFF
            if fu.self_rel:
                br = index.branches.get(original_address)
                actual = br[1] if br else None
            else:
                orig = p.fix_at.get(original_address)
                actual = orig[1] if orig else None
            if actual != expected:
                scan.add(RELOCATION_TARGET_MISMATCH,
                         "external relocation disagrees with the original",
                         offset=fu.offset, symbol=name, database_address=entry["addr"],
                         resolved=expected, original_target=actual)
        elif fu.target_kind == "seg":
            if not isinstance(fu.target, int) or not 1 <= fu.target <= len(mod.segments):
                scan.add(UNSUPPORTED, "invalid segment relocation target", offset=fu.offset)
                continue
            if fu.target == ti:
                target_off = addend
                if not lo <= target_off < hi:
                    scan.add(INCOMPLETE_CLOSURE,
                             "absolute or relative text reference leaves the slice",
                             offset=fu.offset, target_object_offset=target_off)
                    continue
                expected = base + target_off - lo
                if fu.self_rel:
                    br = index.branches.get(original_address)
                    actual = br[1] if br else None
                    label = "intra-slice branch disagrees with the original"
                else:
                    orig = p.fix_at.get(original_address)
                    actual = orig[1] if orig else None
                    label = "intra-slice absolute field disagrees with the original"
                if actual != expected:
                    scan.add(RELOCATION_TARGET_MISMATCH, label, offset=fu.offset,
                             original_target=actual, expected=expected)
            elif fu.target not in anchored:
                scan.add(DATA_LAYOUT_MISMATCH,
                         "reference to a local data segment without a proven base",
                         offset=fu.offset, segment=fu.target,
                         segment_name=mod.segments[fu.target-1].name)
        else:
            scan.add(UNSUPPORTED, "unsupported relocation target kind",
                     offset=fu.offset, target_kind=fu.target_kind)


# ------------------------------------------------------------------- extraction
def _require_verified(spec, raw, db, p, index, anchored):
    """Return the E3 `VerifiedRegion`; reject otherwise with a precise reason."""
    proof = spec.proof if hasattr(spec, "proof") else spec
    if isinstance(proof, VerifiedRegion):
        return proof
    candidate = getattr(spec, "candidate", None)
    if candidate is not None:
        mod = omf.parse_module(raw)[0]
        scan = scan_slice(mod, db, p, candidate.obj_lo, candidate.obj_hi,
                          candidate.orig_start, anchored=anchored, index=index)
        scan.raise_first()
        findings = getattr(getattr(spec, "result", None), "findings", [])
        raise UnsupportedExtractionError(
            NOT_VERIFIED, "candidate did not pass E3 RegionMatch",
            evaluation=type(proof).__name__.upper() if proof is not None else None,
            finding_codes=sorted({f["code"] for f in findings}))
    raise UnsupportedExtractionError(NOT_VERIFIED, "no VerifiedRegion supplied")


def _chunks(length, fixups):
    """Cut points so no 4-byte fixup field straddles a LEDATA32 boundary."""
    spans = sorted((f.offset, f.offset + 4) for f in fixups)
    cuts, start = [], 0
    while start < length:
        end = min(start + CHUNK, length)
        if end < length:
            for a, b in spans:
                if a < end < b:
                    end = a
                    break
        if end <= start:
            raise UnsupportedExtractionError(UNSUPPORTED, "cannot place a chunk boundary")
        cuts.append((start, end))
        start = end
    return cuts


def extract(compiled_obj, verified_spec, symbol_db, orig_program, *,
            anchored_segments=(), out_path=None, index=None):
    """Extract a `VerifiedRegion` from a whole-TU OMF32 object.

    Returns (object_bytes, provenance).  Every rejection is an
    `UnsupportedExtractionError` carrying one of the RFC section 6.2 reasons.
    `anchored_segments` lists the local data segments covered by an independent
    data plan (E5 Fix B3); the caller applies that plan to the result.
    """
    raw = (Path(compiled_obj).read_bytes()
           if not isinstance(compiled_obj, (bytes, bytearray)) else bytes(compiled_obj))
    recs = read_records(raw)
    if any(t & ~1 == 0xA2 for t, _ in recs):
        raise UnsupportedExtractionError(UNSUPPORTED, "LIDATA is not supported")
    mod = omf.parse_module(raw)[0]
    ti, seg = mod.seg(TEXT_SEGMENT)
    if ti is None:
        raise UnsupportedExtractionError(UNSUPPORTED, "no _TEXT segment")
    if sum(s.name == TEXT_SEGMENT for s in mod.segments) != 1:
        raise UnsupportedExtractionError(UNSUPPORTED, "multiple _TEXT segments")
    if len(seg.data) != seg.length:
        raise UnsupportedExtractionError(UNSUPPORTED, "partially stored _TEXT segment")
    text = bytearray(seg.data)
    raw_by_seg = raw_fixups(recs)
    raw_text = raw_by_seg.get(ti, [])
    if len(raw_text) != len(seg.fixups):
        raise UnsupportedExtractionError(UNSUPPORTED, "fixup stream does not align")

    index = index or OriginalIndex(orig_program)
    proof = _require_verified(verified_spec, raw, symbol_db, orig_program, index,
                              anchored_segments)
    lo, hi = proof.candidate.obj_lo, proof.candidate.obj_hi
    base = proof.candidate.orig_start
    if base is None or not 0 <= lo < hi <= len(text) or proof.orig_end != base + hi - lo:
        raise UnsupportedExtractionError(UNSUPPORTED, "invalid VerifiedRegion extent",
                                         obj_lo=lo, obj_hi=hi, orig_start=base,
                                         orig_end=proof.orig_end)

    scan = scan_slice(mod, symbol_db, orig_program, lo, hi, base,
                      anchored=anchored_segments, index=index)
    scan.raise_first()

    # ---- plan the fixups (values read from the compiled slice) -------------
    planned, dropped, transforms = [], [], []
    for fu, fix in zip(seg.fixups, raw_text):
        if not (fu.offset + 4 > lo and fu.offset < hi):
            dropped.append(dict(offset=fu.offset, reason="outside_slice"))
            continue
        inline = struct.unpack_from("<i", text, fu.offset)[0]
        action = dict(offset=fu.offset - lo, source_offset=fu.offset,
                      self_rel=fix.self_rel, displacement=fix.disp,
                      frame_method=fix.fm, frame_index=fix.fi,
                      inline_before=inline)
        if fu.target_kind == "ext":
            name = fu.target
            local = mod.statics.get(name, mod.publics.get(name))
            if local is not None and local[0] == ti and lo <= local[1] < hi:
                # Rebase the local definition: express it as a segment target so
                # the extracted object does not depend on same-object
                # EXTDEF/PUBDEF resolution.
                fix.tm, fix.ti = 0, ti
                new_inline = inline + local[1] - lo
                struct.pack_into("<i", text, fu.offset, new_inline)
                action.update(kind="local_code_to_segment", symbol=name,
                              local_offset=local[1], inline_after=new_inline,
                              target_method=0, target_index=ti)
            elif local is not None and local[0] == ti:
                action.update(kind="intra_tu_extdef", symbol=name,
                              target_address=symbol_db[name]["addr"],
                              transform="kept EXTDEF + self-relative FIXUPP32")
            elif local is not None:
                action.update(kind="data_anchor", symbol=name, segment=local[0],
                              transform="E5 Fix B3 wc1_anchor_* rewrite")
            else:
                action.update(kind="external", symbol=name)
        elif fu.target_kind == "seg" and fu.target == ti:
            fix.tm, fix.ti = 0, ti
            new_inline = inline - lo
            struct.pack_into("<i", text, fu.offset, new_inline)
            action.update(kind="text_rebase", target_segment=ti,
                          target_object_offset=(inline + fu.disp) & 0xFFFFFFFF,
                          inline_after=new_inline)
        elif fu.target_kind == "seg":
            fix.tm, fix.ti = 0, fu.target
            action.update(kind="data_segment", segment=fu.target)
        else:
            raise UnsupportedExtractionError(UNSUPPORTED, "unsupported relocation kind",
                                             offset=fu.offset, target_kind=fu.target_kind)
        fix.offset = fu.offset - lo
        planned.append(fix)
        transforms.append(action)

    # ---- direct unfixed rel32 calls become EXTDEF + FIXUPP32(self_rel) -----
    added, ext_index = [], {}
    extern_names = list(mod.externs)

    def extern(name):
        if name not in ext_index:
            if name not in extern_names:
                if len(name) > 255:
                    raise UnsupportedExtractionError(UNSUPPORTED, "symbol name too long")
                extern_names.append(name)
                added.append(name)
            ext_index[name] = extern_names.index(name) + 1
        return ext_index[name]

    for call in scan.direct_calls:
        if call.get("reason"):
            continue                       # scan.raise_first already rejected
        ti_ext = extern(call["symbol"])
        before = struct.unpack_from("<i", text, call["offset"])[0]
        struct.pack_into("<I", text, call["offset"], 0)
        fix = RawFix(call["offset"] - lo, LOC32, True, 5, None, 2, ti_ext, None)
        planned.append(fix)
        transforms.append(dict(offset=call["offset"] - lo, source_offset=call["offset"],
                               kind="direct_rel32_to_extdef", symbol=call["symbol"],
                               target_address=call["target_address"],
                               target_object_offset=call["target_object_offset"],
                               inline_before=before, inline_after=0, self_rel=True,
                               displacement=None, frame_method=5, frame_index=None,
                               target_method=2, target_index=ti_ext,
                               transform="EXTDEF + self-relative FIXUPP32"))
    planned.sort(key=lambda f: f.offset)

    # ---- emit the rebased object ------------------------------------------
    length = hi - lo
    chunks = _chunks(length, planned)
    chunk_records = []
    for start, end in chunks:
        block = [(0xA1, bytearray(_idx_bytes(ti)) + struct.pack("<I", start) + text[lo+start:lo+end])]
        encoded = []
        for fix in planned:
            if start <= fix.offset < end:
                offset, fix.offset = fix.offset, fix.offset - start
                encoded.append(fix.encode())
                fix.offset = offset
        if encoded:
            block.append((0x9D, bytearray(b"".join(encoded))))
        chunk_records.append(block)

    out, text_emitted = [], False
    declarations = [(t, body) for t, body in recs if t & ~1 in (0x8C, 0xB4, 0xBC)]
    new_ext_body = b"".join(bytes([len(n)]) + n.encode("latin-1") + b"\x00" for n in added)

    def emit_declarations_and_chunks():
        for d in declarations:
            out.append(d)
        if added:
            out.append((0x8C, bytearray(new_ext_body)))
        for block in chunk_records:
            out.extend(block)

    si = 0
    last_data_seg = None
    for t, body in recs:
        base_t = t & ~1
        if base_t == 0x98:                    # SEGDEF16/32
            si += 1
            attr, seglen, ni, ci, tail = _segdef(body, bool(t & 1))
            out.append((0x99, bytearray(_segdef32(attr, length if si == ti else seglen,
                                                   ni, ci, tail))))
        elif t == 0x96 or t == 0x9A or t in (0x80, 0x88, 0x8A, 0x8B):
            if t in (0x8A, 0x8B) and not text_emitted:
                # Empty slice: declarations still precede the module end.
                emit_declarations_and_chunks()
                text_emitted = True
            out.append((t, body))
        elif base_t in (0x8C, 0xB4, 0xBC):    # hoisted before the first LEDATA
            continue
        elif base_t in (0x90, 0xB6):          # PUBDEF / LPUBDEF
            gi, pseg, frame, entries = _pubdef(body, bool(t & 1))
            kept = [(n, off - lo, typ) for n, off, typ in entries if lo <= off < hi]
            for n, off, typ in entries:
                if not lo <= off < hi:
                    dropped.append(dict(offset=off, reason="public_outside_slice", symbol=n))
            if kept:
                # 0x91/0xB7 are the OMF32 (4-byte offset) PUBDEF/LPUBDEF forms.
                out.append(((0x91 if base_t == 0x90 else 0xB7),
                            bytearray(_pubdef32(gi, pseg, frame, kept))))
        elif base_t == 0xA0:                  # LEDATA16/32
            dseg, q = omf._idx(body, 0)
            width = 4 if t & 1 else 2
            off = int.from_bytes(body[q:q+width], "little")
            last_data_seg = dseg
            if dseg == ti:
                if not text_emitted:
                    emit_declarations_and_chunks()
                    text_emitted = True
                continue
            out.append((0xA1, bytearray(_idx_bytes(dseg)) + struct.pack("<I", off)
                        + bytes(body[q+width:])))
        elif base_t == 0x9C:                  # FIXUPP16/32
            if last_data_seg == ti:
                continue                      # re-emitted per LEDATA32 chunk
            fixes = Threads().parse(body, 4 if t & 1 else 2)
            if fixes:
                out.append((0x9D, bytearray(b"".join(f.encode() for f in fixes))))
        else:
            raise UnsupportedExtractionError(UNSUPPORTED, f"unsupported OMF record {t:#04x}")
    if not text_emitted:
        emit_declarations_and_chunks()

    packed = b"".join(_pack(t, body) for t, body in out)

    # ---- invariants on the produced object --------------------------------
    check = omf.parse_module(packed)[0]
    cti, cseg = check.seg(TEXT_SEGMENT)
    if cti != ti or cseg.length != length or bytes(cseg.data) != bytes(text[lo:hi]):
        raise UnsupportedExtractionError(UNSUPPORTED, "extracted _TEXT differs from the plan",
                                         length=cseg.length, expected=length)
    masked = set()
    for fix in planned:
        masked.update(range(fix.offset, fix.offset + 4))
    ordinary = sum(1 for i in range(length) if i not in masked)
    for i in range(length):
        if i not in masked and cseg.data[i] != seg.data[lo+i]:
            raise UnsupportedExtractionError(UNSUPPORTED, "non-relocated byte changed",
                                             offset=i, got=cseg.data[i],
                                             want=seg.data[lo+i])

    provenance = dict(
        experiment="E4", obj_lo=lo, obj_hi=hi, orig_start=base, orig_end=proof.orig_end,
        entries=[[off, name] for off, name in proof.entries],
        evidence_digest=proof.evidence_digest,
        compiled_slice_sha256=text_sha256(seg.data[lo:hi]),
        transformed_slice_sha256=text_sha256(cseg.data),
        source_object_loadable_sha256=loadable_digest(mod),
        chunks=[dict(object_offset=s, size=e - s) for s, e in chunks],
        chunk_count=len(chunks), max_chunk=max((e - s for s, e in chunks), default=0),
        transforms=transforms, added_extdefs=added, dropped=dropped,
        instructions=scan.instructions, branches=scan.branches,
        direct_calls=[c for c in scan.direct_calls if not c.get("reason")],
        record_normalization="OMF16 records normalized to OMF32 widths",
        invariants=dict(region_match=True, byte_invariant=True,
                        non_relocated_bytes=ordinary, relocated_fields=len(planned)),
    )
    provenance["extracted_object_loadable_sha256"] = loadable_digest(check)
    provenance["extracted_object_bytes"] = len(packed)
    if out_path is not None:
        Path(out_path).write_bytes(packed)
    return packed, provenance


def apply_data_plan(packed, p, db, bases, *, per_symbol=None, frame_mode="preserve"):
    """Apply the E5 Fix B3 data-anchor plan to an extracted slice object.

    Data identity is verified with E5's own E0-based checker before any
    rewrite; a rejected plan is a `data_layout_mismatch` (RFC section 6.2).
    """
    try:
        b3.verify_data(p, omf.parse_module(packed)[0], db, bases,
                       per_symbol or {}, address_bases=bases)
    except b3.Rejected as exc:
        raise UnsupportedExtractionError(DATA_LAYOUT_MISMATCH,
                                         f"E5 Fix B3 data plan: {exc}") from exc
    try:
        return b3.rewrite(packed, p, db, bases, per_symbol=per_symbol,
                          frame_mode=frame_mode)
    except b3.Rejected as exc:
        raise UnsupportedExtractionError(UNSUPPORTED,
                                         f"E5 Fix B3 rewrite: {exc}") from exc
