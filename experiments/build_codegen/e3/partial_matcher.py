"""Region-scoped E0 checks for parsed Watcom OMF modules.

A VerifiedRegion carries matching evidence and any required symbolic rel32
rewrites. Extraction and placement are outside this experiment.
"""
from bisect import bisect_left
from collections import defaultdict
from dataclasses import asdict, dataclass, replace
from hashlib import sha256
import json
import struct

import capstone
from wc1 import le, match, omf

from ..e0.matcher_proto import (
    MatchResult, Obligation, OriginalIndex, _Checker, _branch, _metadata, _overlap, _size,
)


@dataclass(frozen=True)
class CandidateRegion:
    obj_lo: int
    obj_hi: int
    orig_start: int | None


@dataclass(frozen=True)
class DataBoundary:
    """Independent layout evidence supplied by the experiment's input owner.

    Offsets and sizes must come from declarations or layout evidence on both
    sides. They must never be inferred from matched bytes or candidate fixups.
    """
    segment: int
    obj_start: int
    orig_start: int
    size: int
    kind: str
    evidence: str
    symbol: str | None = None


@dataclass(frozen=True)
class VerifiedRegion:
    candidate: CandidateRegion
    orig_end: int
    entries: tuple
    leading_size: int
    trailing_filler_size: int
    obligations: tuple
    data_deps: tuple
    outgoing_refs: tuple
    verification_scope: str
    evidence_digest: str


@dataclass(frozen=True)
class Conditional:
    reason: str


@dataclass(frozen=True)
class Mismatch:
    reason: str


@dataclass(frozen=True)
class Unsupported:
    reason: str


@dataclass
class Evaluation:
    candidate: CandidateRegion
    proof: VerifiedRegion | Conditional | Mismatch | Unsupported
    functions: dict
    result: MatchResult
    segment_bases: dict
    incoming_refs: list
    outgoing_refs: list


@dataclass(frozen=True)
class DataUse:
    fixup: omf.Fixup
    segment: int
    symbol_offset: int
    addend: int
    original_target: int

    @property
    def offset(self):
        return self.symbol_offset + self.addend


class _RegionChecker(_Checker):
    def __init__(self, p, mod, db, index, boundaries):
        super().__init__(p, mod, db, index)
        self.boundaries = boundaries
        self.md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
        self.bindings = {}
        self.outgoing = []
        self.blocked = []

    def definition(self, fu):
        if fu.target_kind == "seg":
            return fu.target, 0
        if fu.target_kind == "ext":
            return self.local_def(fu.target)
        return None

    def resolved(self, fu, r, a):
        if id(fu) in self.bindings:
            return self.bindings[id(fu)]
        return super().resolved(fu, r, a)

    def addend(self, source, fu):
        return struct.unpack_from("<i", source.data, fu.offset)[0] + fu.disp

    def decoded_branch(self, source, off, size):
        insn = next(self.md.disasm(bytes(source.data[off:off+size]), off, 1), None)
        return _branch(insn) if insn else None

    def sibling(self, target):
        names = [name for off, name in self.starts if off == target]
        if len(names) != 1:
            return None, None
        name = names[0]
        entry = self.db.get(name, {})
        addr = entry.get("addr")
        # A data entry, interior address, or ambiguous alias cannot authorize a rewrite.
        if (addr not in self.idx.functions or entry.get("link_name") != name or
                sum(e.get("addr") == addr for e in self.db.values()) != 1):
            return name, None
        return name, addr

    def prepare_branches(self, lo, hi, base, r):
        """Prove outgoing dependencies before making any rel32 field maskable."""
        real = {fu.offset: fu for fu in self.text.fixups if fu.loc == 9 and fu.self_rel}
        virtual = []
        for a in self.idx.branches_in(base, base + hi - lo):
            n, target, ia, ib = self.idx.branches[a]
            start, off = lo + ia - base, lo + a - base
            if start < lo or start + len(ib) > hi:
                continue
            decoded = self.decoded_branch(self.text, start, len(ib))
            if not decoded or decoded[:2] != (off, n):
                continue
            _, _, raw_target = decoded
            external = not base <= target < base + hi - lo
            if off in real:
                fu = real[off]
                local = self.definition(fu)
                if local and local[0] == self.ti:
                    if (fu.target_kind == "ext" and fu.target in self.mod.publics and
                            fu.target in self.mod.statics and
                            self.mod.publics[fu.target] != self.mod.statics[fu.target]):
                        r.add("ambiguous_local_definition", "unsupported_construct", off, a,
                              "Public and static definitions disagree", symbol=fu.target)
                        continue
                    raw_target = local[1] + self.addend(self.text, fu)
                elif external:
                    self.outgoing.append(dict(offset=off, target=target, symbol=fu.target,
                                              encoding="external_fixupp"))
                    continue
                else:
                    continue
            if not external and lo <= raw_target < hi:
                continue
            ref = dict(offset=off, original_target=target, object_target=raw_target,
                       encoding=f"rel{8*n}" if off not in real else "local_fixupp")
            if n == 1:
                ref["reason"] = "outgoing_rel8_dependency"
                self.blocked.append(ref)
                continue
            name, db_addr = self.sibling(raw_target)
            ref["symbol"] = name
            if (ib[0] not in (0xe8, 0xe9) or not external or lo <= raw_target < hi or
                    db_addr is None or target != db_addr):
                ref["reason"] = "blocked_by_sibling_dependency"
                self.blocked.append(ref)
                r.add("unproven_sibling_target", "code_reloc_forward", off, a,
                      "Outgoing near branch lacks an exact independent sibling entry", reference=ref)
                continue
            ref["provider"] = "canonical_original_symbol"
            if off in real:
                fu = real[off]
                if fu.target_kind == "ext" and fu.target != name:
                    r.add("sibling_symbol_mismatch", "code_reloc_forward", off, a,
                          "Named local fixup disagrees with its destination", reference=ref)
                    continue
                self.bindings[id(fu)] = db_addr - self.addend(self.text, fu)
                if fu.target_kind == "ext":
                    ref["encoding"] = "sibling_extdef_fixupp"
                    self.outgoing.append(ref)
                    continue
            else:
                fu = omf.Fixup(off, 9, True, "ext", name, 0)
                self.bindings[id(fu)] = db_addr - self.addend(self.text, fu)
                virtual.append(fu)
            ref["rewrite"] = "EXTDEF + self-relative FIXUPP32"
            self.outgoing.append(ref)
        return virtual

    def check_branches(self, r, s, lo, hi, base, at, region_hi):
        # E0's whole-object branch closure assumes a single linear TEXT base.
        # Retain its reverse obligations and encoding checks using slice bounds.
        end = base + hi - lo
        blocked = {ref["offset"] for ref in self.blocked}
        for a, encoding in self.idx.unsupported_branches.items():
            if base <= a < end:
                r.add("unsupported_branch_encoding", "unsupported_construct", lo+a-base, a,
                      "Direct branch is outside supported rel8/rel32 encodings",
                      original_encoding=encoding.hex())
        for a in self.idx.branches_in(base, end):
            n, target, ia, ib = self.idx.branches[a]
            off, start = lo+a-base, lo+ia-base
            external = not base <= target < end
            r.obligations.append(dict(asdict(Obligation(
                f"rel{8*n}_code", off, n, target, 0,
                "target + addend - (src_addr + field_size)", external and n == 4, False)),
                origin="original", segment=s.name))
            if start < lo or start + len(ib) > hi:
                r.add("branch_crosses_extent", "unsupported_construct", off, a,
                      "Branch instruction crosses the verification boundary")
                continue
            decoded = self.decoded_branch(s, start, len(ib))
            if (not decoded or decoded[:2] != (off, n) or
                    s.data[start:off] != ib[:a-ia]):
                r.add("branch_encoding_mismatch", "code_reloc_forward", off, a,
                      "Original branch has a different compiled encoding")
                continue
            ff = at.get(off, [])
            if ff and not all(n == 4 and f.loc == 9 and f.self_rel for f in ff):
                r.add("branch_fixup_kind", "code_reloc_forward", off, a,
                      "A direct branch field requires a self-relative off32 relocation")
            if external and not ff and off not in blocked:
                r.add("missing_compiled_relative_fixup", "code_reloc_reverse", off, a,
                      "External branch lacks symbolic resolution", original_target=target)
            if not ff and decoded[2] + base - lo != target:
                r.add("relative_target_mismatch", "code_reloc_forward", off, a,
                      "Intra-segment displacement differs", original_target=target,
                      compiled_target=decoded[2])
            if not external and target not in self.p.insns:
                r.add("branch_to_undecoded_target", "unsupported_construct", off, a,
                      "Internal direct branch does not target a decoded instruction")

    def local_uses(self, s, lo, hi, base, r):
        for fu in s.fixups:
            if fu.loc != 9 or not lo <= fu.offset <= hi - 4:
                continue
            local = self.definition(fu)
            if local is None:
                if fu.target_kind == "ext" and not fu.self_rel:
                    target = self.original_target(base+fu.offset-lo, fu, False)
                    if target is not None and self.p.le.obj_at(target) is self.p.code:
                        r.add("external_code_pointer", "unsupported_construct",
                              fu.offset, base+fu.offset-lo,
                              "External absolute code pointers have no slice ownership proof")
                continue
            si, sym_off = local
            if not 1 <= si <= len(self.mod.segments):
                continue  # E0 reports the malformed fixup/definition.
            target_segment = self.mod.segments[si-1]
            if (fu.target_kind == "ext" and fu.target in self.mod.publics and
                    fu.target in self.mod.statics and
                    self.mod.publics[fu.target] != self.mod.statics[fu.target]):
                r.add("ambiguous_local_definition", "unsupported_construct", fu.offset, None,
                      "Public and static definitions disagree", symbol=fu.target)
                continue
            add = self.addend(s, fu)
            if si == self.ti:
                if not fu.self_rel and not self.lo <= sym_off + add < self.hi:
                    r.add("outgoing_text_pointer", "dependency", fu.offset, base+fu.offset-lo,
                          "Absolute TEXT reference leaves the candidate region",
                          target_offset=sym_off+add)
                continue
            if _metadata(target_segment):
                r.add("runtime_reference_to_debug", "unsupported_construct", fu.offset, None,
                      "Runtime relocation targets Watcom debug metadata", segment=si)
            elif fu.self_rel:
                r.add("relative_data_reference", "unsupported_construct", fu.offset, None,
                      "Self-relative reference to local data is unsupported", segment=si)
            elif not 0 <= sym_off + add < target_segment.length:
                r.add("data_target_out_of_bounds", "code_reloc_forward", fu.offset, None,
                      "Local data target exceeds segment storage", segment=si, offset_in_data=sym_off+add)
            else:
                a = base + fu.offset - lo
                target = self.original_target(a, fu, False)
                if target is not None:
                    yield DataUse(fu, si, sym_off, add, target)

    def validate_definitions(self, si, sb, lo, hi, r):
        for names in (self.mod.publics, self.mod.statics):
            for name, (segment, off) in names.items():
                if segment != si or not lo <= off < hi or name not in self.db:
                    continue
                expected = self.db[name]["addr"]
                if sb + off != expected:
                    r.add("local_definition_mismatch", "code_reloc_forward", off, sb+off,
                          "Local definition contradicts its database address",
                          symbol=name, database_addr=expected)

    def boundary_valid(self, b, segment):
        obj = self.p.le.obj_at(b.orig_start)
        return (b.evidence and b.size > 0 and 0 <= b.obj_start and
                b.obj_start+b.size <= min(segment.length, len(segment.data)) and
                obj and not obj.flags & le.OBJ_EXEC and b.orig_start+b.size <= obj.end)

    def bind_symbols(self, si, segment, uses, r):
        """Match exact literal/symbol ranges and check identity in both directions."""
        bounds = [b for b in self.boundaries if b.segment == si]
        relevant = set()
        for use in uses:
            choices = [b for b in bounds if b.obj_start == use.offset]
            if len(choices) != 1 or not self.boundary_valid(choices[0], segment):
                r.add("unproven_data_boundary", "data_bytes", use.fixup.offset, None,
                      "Shifted local data requires a proven standalone boundary",
                      segment=si, object_offset=use.offset, original_target=use.original_target)
                continue
            b = choices[0]
            if b.orig_start != use.original_target:
                r.add("data_identity_mismatch", "data_reloc_forward", use.fixup.offset, None,
                      "Original reference disagrees with the independently proven data identity",
                      expected=b.orig_start, actual=use.original_target, object_offset=use.offset)
                continue
            relevant.add(b)
            if use.fixup.target_kind == "ext" and use.symbol_offset != b.obj_start:
                r.add("interior_symbol_addend", "data_reloc_forward", use.fixup.offset, None,
                      "Named local reference reaches a different object by addend")
                continue
            self.bindings[id(use.fixup)] = b.orig_start - use.addend
        deps = []
        for b in sorted(relevant, key=lambda item: item.obj_start):
            end = b.obj_start + b.size
            obj = self.p.le.obj_at(b.orig_start)
            raw = bytes(segment.data[b.obj_start:end])
            original = bytes(self.p.image[obj.index][b.orig_start-obj.base:b.orig_start-obj.base+b.size])
            if any(other != b and (
                    _overlap(other.obj_start, other.size, b.obj_start, end) or
                    _overlap(other.orig_start, other.size, b.orig_start, b.orig_start+b.size))
                   for other in bounds):
                r.add("data_alias_violation", "data_reloc_forward", b.obj_start, b.orig_start,
                      "Independent boundaries overlap in the compiled or original layout")
            if b.kind == "const_string" and (segment.name, segment.cls) == ("CONST", "DATA"):
                scope = "per_symbol_const"
                if raw[-1:] != b"\0" or b"\0" in raw[:-1]:
                    r.add("invalid_const_literal", "data_bytes", b.obj_start, b.orig_start,
                          "Certified literal must consist of one complete NUL-terminated string")
            elif (b.kind == "mutable" and segment.name in ("_DATA", "_BSS") and b.symbol and
                  self.local_def(b.symbol) == (si, b.obj_start) and
                  self.db.get(b.symbol, {}).get("addr") == b.orig_start):
                scope = "per_symbol_mutable"
            else:
                r.add("unsupported_data_boundary", "unsupported_construct", b.obj_start,
                      b.orig_start, "Boundary does not identify a supported local data object")
                continue
            if raw != original:
                r.add("symbol_data_mismatch", "data_bytes", b.obj_start, b.orig_start,
                      "Proven data object differs byte-for-byte")
            if (any(_overlap(f.offset, _size(f), b.obj_start, end) for f in segment.fixups) or
                    self.idx.fixes(b.orig_start, b.orig_start+b.size)):
                r.add("symbol_pointer_fixup", "unsupported_construct", b.obj_start,
                      b.orig_start, "Per-symbol data containing pointers requires whole-segment proof")
            for name, (segment_index, off) in [*self.mod.publics.items(), *self.mod.statics.items()]:
                if (segment_index == si and b.obj_start <= off < end and
                        (off != b.obj_start or name not in self.db)):
                    r.add("unproven_data_definition", "unsupported_construct", off,
                          b.orig_start+off-b.obj_start,
                          "Local definition within the data boundary lacks an identity proof",
                          symbol=name)
            self.validate_definitions(si, b.orig_start-b.obj_start, b.obj_start, end, r)
            deps.append(dict(data_scope=scope, contents_sha256=sha256(raw).hexdigest(), **asdict(b)))
        return deps

    def check_data(self, text, lo, hi, base, r):
        uses_by_segment = defaultdict(list)
        for use in self.local_uses(text, lo, hi, base, r):
            uses_by_segment[use.segment].append(use)
        scanned = set()
        # Discover transitively referenced segments only through a plausible
        # whole-segment mapping. Per-symbol slices support pointer-free data.
        while pending := sorted(uses_by_segment.keys() - scanned):
            for si in pending:
                scanned.add(si)
                s = self.mod.segments[si-1]
                sb = self.whole_base(si, s, uses_by_segment[si])
                if sb is not None:
                    self.bases[si] = sb
                    for use in self.local_uses(s, 0, len(s.data), sb, r):
                        uses_by_segment[use.segment].append(use)

        deps = []
        for si, uses in sorted(uses_by_segment.items()):
            s = self.mod.segments[si-1]
            r.findings.extend(self.validate_fixups(s))
            sb = self.whole_base(si, s, uses)
            if sb is None or self.bases.get(si) != sb:
                if si in self.bases:
                    r.add("inconsistent_transitive_anchor", "data_reloc_forward", None, sb,
                          "A transitive data reference contradicts the previously inferred base",
                          segment=si)
                deps.extend(self.bind_symbols(si, s, uses, r))
                continue
            dr = self.check(s, 0, s.length, sb, False, s.name)
            r.findings.extend(dr.findings)
            r.obligations.extend(dr.obligations)
            r.metrics["data_segments_checked"] += 1
            for key in ("data_fixups_checked", "reverse_le_fixups_checked"):
                r.metrics[key] += dr.metrics[key]
            self.validate_definitions(si, sb, 0, s.length, r)
            deps.append(dict(data_scope="whole_segment", segment=si, orig_start=sb, size=s.length,
                             contents_sha256=sha256(s.data).hexdigest()))
        return deps

    def whole_base(self, si, s, uses):
        bases = {use.original_target - use.offset for use in uses}
        if len(bases) != 1 or len(s.data) != s.length:
            return None
        sb = next(iter(bases))
        obj = self.p.le.obj_at(sb)
        if not obj or obj.flags & le.OBJ_EXEC or sb+s.length > obj.end:
            return None
        if (s.name, s.cls) == ("CONST", "DATA"):
            # If independent boundaries are supplied, their identities constrain
            # the whole mapping too. Ordinary byte discrepancies can fall back
            # to a proven string slice only when no pool pointers are involved.
            if any(b.segment == si and (sb+b.obj_start != b.orig_start or
                                        b.size <= 0 or b.obj_start+b.size > s.length)
                   for b in self.boundaries):
                return None
            want = bytes(self.p.image[obj.index][sb-obj.base:sb-obj.base+s.length])
            if not s.fixups and want != s.data:
                return None
            return sb
        if (s.name, s.cls) in (("_DATA", "DATA"), ("_BSS", "BSS")):
            # Equal mutable bytes, especially zero-filled BSS, cannot establish
            # identity. Require a named canonical boundary for the full extent.
            if any(b.segment == si and b.obj_start == 0 and b.size == s.length and
                   b.orig_start == sb and b.kind == "mutable" and b.symbol and
                   self.boundary_valid(b, s) and self.local_def(b.symbol) == (si, 0) and
                   self.db.get(b.symbol, {}).get("addr") == sb for b in self.boundaries):
                return sb
        return None

    def check_code_layout(self, lo, hi, base, r):
        end = base + hi - lo
        tables = {jump: (addr, targets) for addr, (jump, targets) in
                  getattr(self.p, "jump_tables", {}).items() if base <= jump < end}
        start = bisect_left(self.idx.insn_addrs, base)
        stop = bisect_left(self.idx.insn_addrs, end)
        covered = set()
        for a in self.idx.insn_addrs[start:stop]:
            insn = self.p.insns[a]
            covered.update(range(a, a+len(insn.bytes)))
            if insn.mnemonic != "jmp" or _branch(insn):
                continue
            table, targets = tables.get(a, (None, ()))
            if (not targets or not base <= table <= end - 4 * len(targets) or
                    any(not base <= t < end or t not in self.p.insns for t in targets) or
                    any(self.p.fix_at.get(table + 4*k, (None, None))[1] != t
                        for k, t in enumerate(targets))):
                r.add("unproven_indirect_jump", "dependency", lo+a-base, a,
                      "Indirect jump has no verified closed in-region jump table")
                continue
            table_end = table + 4*len(targets)
            covered.update(range(table, table_end))
            object_table = lo + table - base
            shared = any(table <= target < table_end and not base <= src < end
                         for src, (_, target) in self.p.fix_at.items())
            for f in self.text.fixups:
                local = self.definition(f)
                if (local and local[0] == self.ti and f.loc == 9 and
                        0 <= f.offset <= len(self.text.data)-4 and not lo <= f.offset < hi):
                    target = local[1] + self.addend(self.text, f)
                    shared |= object_table <= target < object_table+4*len(targets)
            if shared:
                r.add("shared_jump_table", "dependency", object_table, table,
                      "An outside reference uses the candidate's jump table")
        cursor = base
        while cursor < end:
            if cursor in covered:
                cursor += 1
                continue
            stop = cursor + 1
            while stop < end and stop not in covered:
                stop += 1
            off = lo+cursor-base
            prior = bisect_left(self.idx.insn_addrs, cursor)
            prev = self.p.insns[self.idx.insn_addrs[prior-1]] if prior else None
            incoming_fallthrough = (prev is not None and base <= prev.address and
                                    prev.address+len(prev.bytes) == cursor and
                                    prev.mnemonic not in ("ret", "retf", "jmp", "iret", "iretd"))
            if (incoming_fallthrough or self.idx.fixes(cursor, stop) or
                    not match.is_filler(bytes(self.text.data[off:off+stop-cursor]))):
                r.add("unclassified_code_bytes", "unsupported_construct", off, cursor,
                      "Bytes are neither decoded instructions, a verified table, nor isolated filler")
            cursor = stop

    def check_data_aliases(self, deps, text, lo, hi, base, r):
        for i, dep in enumerate(deps):
            a, size = dep["orig_start"], dep["size"]
            if any(_overlap(other["orig_start"], other["size"], a, a+size)
                   for other in deps[:i]):
                r.add("data_alias_violation", "data_reloc_forward", lo, a,
                      "Distinct verified data ranges overlap in the original")
            if dep["data_scope"] != "per_symbol_const":
                continue
            for source, start, stop, addr in [(text, lo, hi, base)] + [
                (self.mod.segments[d["segment"]-1], 0, d["size"], d["orig_start"])
                for d in deps if d["data_scope"] == "whole_segment"
            ]:
                for f in source.fixups:
                    if (f.loc == 9 and not f.self_rel and start <= f.offset <= stop-4 and
                            f.target_kind == "ext" and self.definition(f) is None):
                        original = self.original_target(addr+f.offset-start, f, False)
                        if original is not None and a <= original < a+size:
                            r.add("data_alias_violation", "data_reloc_forward", f.offset, original,
                                  "A separate external object aliases a relocated CONST literal")

    def incoming(self, lo, hi, base):
        """Original and object incoming edges. These do not affect the proof."""
        end = base+hi-lo
        refs = [dict(origin="original", source=a, target=b[1], encoding=f"rel{8*b[0]}")
                for a, b in sorted(self.idx.branches.items())
                if not base <= b[2] < end and base <= b[1] < end]
        refs.extend(dict(origin="original", source=a, target=t, encoding="le_fixup")
                    for a, (_, t) in sorted(self.p.fix_at.items())
                    if not base <= a < end and base <= t < end)
        fixup_offsets = {f.offset for f in self.text.fixups}
        # Diagnostic scan only. Linear decoding of siblings can stop at data.
        for start, stop in ((0, lo), (hi, len(self.text.data))):
            for insn in self.md.disasm(bytes(self.text.data[start:stop]), start):
                branch = _branch(insn)
                if branch and branch[0] not in fixup_offsets and lo <= branch[2] < hi:
                    refs.append(dict(origin="object", source=branch[0], target=branch[2],
                                     encoding=f"rel{8*branch[1]}"))
        for si, s in enumerate(self.mod.segments, 1):
            if _metadata(s):
                continue
            for f in s.fixups:
                if (si == self.ti and lo <= f.offset < hi or f.loc != 9 or
                        not 0 <= f.offset <= len(s.data)-4):
                    continue
                local = self.definition(f)
                if local and local[0] == self.ti:
                    target = local[1] + self.addend(s, f)
                    if lo <= target < hi:
                        refs.append(dict(origin="object", segment=si, source=f.offset,
                                         target=target, encoding="fixupp"))
        return refs

    def validate_module(self, r):
        for si, s in enumerate(self.mod.segments, 1):
            if _metadata(s):
                continue
            if si != self.ti and (s.length or s.data or s.fixups) and (
                    s.name, s.cls) not in (("CONST", "DATA"), ("CONST2", "DATA"),
                                           ("_DATA", "DATA"), ("_BSS", "BSS")):
                r.add("unsupported_runtime_segment", "unsupported_construct", None, None,
                      "Unsupported loadable segment", segment=s.name, segment_class=s.cls)
            # Invalid storage anywhere cannot be assigned safely to a slice.
            r.findings.extend(f for f in self.validate_fixups(s)
                              if f["code"] == "fixup_out_of_bounds")
            for f in s.fixups:
                if f.loc not in omf.LOC_NAMES:
                    r.add("unknown_fixup_width", "unsupported_construct", f.offset, None,
                          "Cannot establish where an unknown fixup field ends", loc=f.loc)
        for names in (self.mod.publics, self.mod.statics):
            for name, (si, off) in names.items():
                if (not 1 <= si <= len(self.mod.segments) or
                        not 0 <= off < self.mod.segments[si-1].length):
                    r.add("invalid_local_definition", "unsupported_construct", off, None,
                          "Local definition exceeds segment bounds", symbol=name)
        if self.mod.comdefs:
            r.add("communal_storage", "unsupported_construct", None, None,
                  "Communal storage placement is unproven")

    def validate_fixups(self, s):
        findings = super().validate_fixups(s)
        if s.name == "_TEXT" and hasattr(self, "lo"):
            # Sound in-bounds fixups belonging wholly to unrelated bodies
            # need not be supported by this slice. Storage faults stay fatal.
            findings = [f for f in findings if f["code"] == "fixup_out_of_bounds" or
                        any(g.offset == f["offset"] and
                            _overlap(g.offset, _size(g), self.lo, self.hi)
                            for g in s.fixups)]
        return findings

    def evaluate(self, candidate):
        lo, limit, base = candidate.obj_lo, candidate.obj_hi, candidate.orig_start
        if base is None:
            r = MatchResult("_TEXT region")
            r.add("missing_entry_anchor", "unsupported_construct", lo, None,
                  "Local code entry has no canonical original address")
            return Evaluation(candidate, Unsupported("missing_entry_anchor"), {}, r, {}, [], [])
        r = MatchResult("_TEXT region", orig_start=base, orig_end=base+limit-lo)
        self.validate_module(r)
        if (self.text is None or self.text.cls != "CODE" or
                sum(s.name == "_TEXT" for s in self.mod.segments) != 1 or
                not 0 <= lo < limit <= min(self.text.length, len(self.text.data)) or
                len(self.text.data) != self.text.length):
            r.add("invalid_extent", "unsupported_construct", lo, base,
                  "Candidate must fit within a unique fully stored _TEXT segment")
            return Evaluation(candidate, Unsupported("invalid_extent"), {}, r, {}, [], [])

        entries = [(off, name) for off, name in self.starts if lo <= off < limit]
        mapped = [(off, name) for off, name in entries
                  if self.db.get(name, {}).get("addr") == base+off-lo]
        extent = max((lo+self.idx.functions[base+off-lo]["end"]-base for off, _ in mapped
                      if base+off-lo in self.idx.functions), default=limit)
        hi = limit
        if lo < extent < limit:
            tail_refs = any(_overlap(f.offset, _size(f), extent, limit) for f in self.text.fixups)
            if match.is_filler(bytes(self.text.data[extent:limit])) and not tail_refs:
                hi = extent
            else:
                r.add("extent_retry_rejected", "extent_retry", extent, base+extent-lo,
                      "Trailing bytes contain code, data, or a relocation")
        if limit < len(self.text.data) and not any(off == limit for off, _ in self.starts):
            # A caller may not submit a manually shortened body and thereby
            # bypass the exact same tail check used by automatic candidates.
            r.add("unverified_compiled_tail", "extent_retry", limit, base+limit-lo,
                  "Candidate input must end at an entry boundary or segment end")
        if entries and lo and not any(off < lo for off, _ in self.starts):
            r.add("unverified_leading_bytes", "leading_bytes", lo, base,
                  "Candidate omits bytes before the object's first entry")
        if lo and not any(off == lo for off, _ in self.starts):
            if base not in getattr(self.p, "jump_tables", {}):
                r.add("unproven_slice_start", "region_layout", lo, base,
                      "Slice starts at neither a compiled entry nor a recognized leading table")
        if not mapped:
            r.add("missing_entry_anchor", "unsupported_construct", lo, base,
                  "No local code entry independently anchors the candidate")

        self.lo, self.hi = lo, hi
        self.bases[self.ti] = base-lo
        end = base+hi-lo
        r.orig_end = end
        mapped_addrs = {base+off-lo for off, _ in mapped}
        for start in self.idx.functions:
            if base <= start < end and start not in mapped_addrs:
                r.add("foreign_original_function", "region_layout", lo+start-base, start,
                      "Candidate crosses an original function entry without its compiled definition")
        for off, name in entries:
            addr = self.db.get(name, {}).get("addr")
            if addr is None or addr not in self.idx.functions:
                r.add("unknown_code_entry", "unsupported_construct", off, None,
                      "Local code entry lacks a discovered original function", symbol=name)
            elif addr != base+off-lo:
                r.add("public_layout_mismatch", "region_layout", off, addr,
                      "Local code entry disagrees with the candidate base", symbol=name,
                      proposed_address=base+off-lo)
            else:
                next_entry = min((o for o, _ in entries if o > off), default=hi)
                self.check_coverage(r, off, min(next_entry, hi), addr)

        for boundary in (base, end):
            pos = bisect_left(self.idx.insn_addrs, boundary)
            if pos:
                prev = self.p.insns[self.idx.insn_addrs[pos-1]]
                if prev.address < boundary < prev.address + len(prev.bytes):
                    r.add("split_instruction", "extent_retry", lo+boundary-base, boundary,
                          "Candidate boundary splits an original instruction")
        pos = bisect_left(self.idx.insn_addrs, end)
        last = self.p.insns[self.idx.insn_addrs[pos-1]] if pos else None
        if (last is None or last.address < base or
                last.mnemonic not in ("ret", "retf", "jmp", "iret", "iretd")):
            r.add("unproven_end_of_control_flow", "dependency", hi, end,
                  "Region end is not a proven terminating instruction")

        virtual = self.prepare_branches(lo, hi, base, r)
        text = replace(self.text, fixups=self.text.fixups+virtual)
        deps = self.check_data(text, lo, hi, base, r)
        self.check_data_aliases(deps, text, lo, hi, base, r)
        if lo == 0 and limit == len(self.text.data):
            verified_whole = {d["segment"] for d in deps if d["data_scope"] == "whole_segment"}
            for si, s in enumerate(self.mod.segments, 1):
                if si != self.ti and s.length and not _metadata(s) and si not in verified_whole:
                    r.add("unverified_whole_object_data", "unsupported_construct", None, None,
                          "Whole-object coverage requires complete local data", segment=si)
        cr = self.check(text, lo, hi, base, True, "_TEXT")
        virtual_offsets = {f.offset for f in virtual}
        for obligation in cr.obligations:
            if obligation["origin"] == "compiled" and obligation["src_offset"] in virtual_offsets:
                obligation["origin"] = "compiled_direct_branch"
                obligation["target"] += obligation["addend"]
                obligation["addend"] = 0
        r.findings.extend(f for f in cr.findings if f not in r.findings)
        r.obligations.extend(cr.obligations)
        r.metrics["code_fixups_checked"] = cr.metrics["code_fixups_checked"] - len(virtual)
        r.metrics["reverse_le_fixups_checked"] += cr.metrics["reverse_le_fixups_checked"]
        r.metrics["leading_bytes_len"] = min((off-lo for off, _ in entries), default=0)
        # A rejected retry already proves the bytes after the discovered body
        # unsafe. Check executable coverage within the discovered extent.
        self.check_code_layout(lo, min(hi, extent), base, r)
        for ref in self.blocked:
            r.add(ref["reason"], "dependency", ref["offset"], base+ref["offset"]-lo,
                  "Cannot isolate region without including the destination", reference=ref)
        functions = self.function_verdicts(mapped, hi, r)
        blockers = [f for f in r.findings if f["category"] == "dependency"]
        if r.verdict in ("UNSUPPORTED", "ERROR"):
            proof = Unsupported(r.verdict)
        elif len(blockers) < len(r.findings):
            proof = Mismatch("region_mismatch")
        elif blockers:
            proof = Conditional(blockers[0]["code"])
        else:
            retained = CandidateRegion(lo, hi, base)
            scope = "whole_object" if lo == 0 and limit == len(self.text.data) else "extracted_slice"
            evidence = dict(candidate=asdict(retained), entries=entries, data=deps,
                            obligations=r.obligations, outgoing=self.outgoing, scope=scope,
                            text_sha256=sha256(text.data[lo:hi]).hexdigest())
            digest = sha256(json.dumps(evidence, sort_keys=True).encode()).hexdigest()
            proof = VerifiedRegion(retained, end, tuple(entries), r.metrics["leading_bytes_len"],
                                   limit-hi, _freeze(r.obligations), _freeze(deps),
                                   _freeze(self.outgoing), scope, digest)
        return Evaluation(candidate, proof, functions, r, self.bases,
                          self.incoming(lo, hi, base), self.outgoing+self.blocked)

    def function_verdicts(self, mapped, hi, r):
        verdicts = {}
        for i, (off, name) in enumerate(mapped):
            remaining = [o for o, _ in mapped[i+1:] if o > off]
            stop = min(remaining, default=hi)
            faults = [f for f in r.findings if f["category"] not in ("dependency", "region_layout")
                      and (f["category"].startswith("data") or f["offset"] is None or
                           off <= f["offset"] < stop or
                           f["code"] in ("extent_retry_rejected", "unverified_compiled_tail",
                                         "truncated_function", "truncated_instruction",
                                         "fixup_out_of_bounds", "local_definition_mismatch"))]
            verdicts[name] = MatchResult(name, findings=faults).verdict
        return verdicts


def _freeze(records):
    return tuple(tuple(sorted(record.items())) for record in records)


def evaluate_region(p, mod, db, candidate, *, index=None, boundaries=()):
    """Evaluate a contiguous slice without using sibling relocation anchors."""
    return _RegionChecker(p, mod, db, index or OriginalIndex(p), boundaries).evaluate(candidate)


def evaluate_module(p, mod, db, *, index=None, boundaries=()):
    """Evaluate each public/local entry and include E0's object-wide control."""
    index = index or OriginalIndex(p)
    checker = _Checker(p, mod, db, index)
    offsets = sorted({off for off, _ in checker.starts})
    limits = dict(zip(offsets, offsets[1:]+[len(checker.text.data)])) if offsets else {}
    candidates = {}
    for off, name in checker.starts:
        lo = 0 if off == offsets[0] else off
        addr = db.get(name, {}).get("addr")
        candidates[name] = CandidateRegion(lo, limits[off], addr-off+lo if addr is not None else None)
    results = {name: evaluate_region(p, mod, db, candidate, index=index, boundaries=boundaries)
               for name, candidate in candidates.items()}
    whole = _Checker(p, mod, db, index)
    whole_result = whole.run()
    return results, whole_result, whole.bases
