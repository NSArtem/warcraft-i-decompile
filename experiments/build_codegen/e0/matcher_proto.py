"""E0 only: bidirectional normalized addressing obligations, without placement.

Inputs are the production parser's unpatched OMF Module and discovered Program.
FunctionMatch covers a body; RegionMatch additionally covers its entire _TEXT
layout, leading bytes and every nonempty local segment. No production mutation.
"""
from bisect import bisect_left
from dataclasses import asdict, dataclass, field
import struct

import capstone
from wc1 import analysis, match, omf, symbols


@dataclass(frozen=True)
class Obligation:
    kind: str
    src_offset: int
    field_size: int
    target: object
    addend: int
    evaluation_rule: str
    requires_static_resolution: bool
    requires_le_fixup: bool


@dataclass
class MatchResult:
    name: str
    findings: list = field(default_factory=list)
    obligations: list = field(default_factory=list)
    metrics: dict = field(default_factory=lambda: dict(
        leading_bytes_len=0, data_segments_checked=0, data_fixups_checked=0,
        code_fixups_checked=0, reverse_le_fixups_checked=0))
    orig_start: int | None = None
    orig_end: int | None = None

    @property
    def verdict(self):
        # Unknown constructs always fail closed, even alongside proven defects.
        for verdict, category in (("ERROR", "error"),
                                  ("UNSUPPORTED", "unsupported_construct")):
            if any(f["category"] == category for f in self.findings):
                return verdict
        return "MISMATCH" if self.findings else "MATCH"

    def add(self, code, category, offset, orig_addr, message, **evidence):
        self.findings.append(dict(code=code, category=category, offset=offset,
                                  orig_addr=orig_addr, message=message,
                                  evidence=evidence))

    def to_dict(self):
        return dict(asdict(self), verdict=self.verdict)


def load_inputs():
    funcs, datas, _ = symbols.load()
    return analysis.run(), {e["link_name"]: e for t in (funcs, datas) for e in t.values()}


def _size(fu):
    return {0: 1, 1: 2, 2: 2, 3: 4, 4: 1, 5: 2, 9: 4, 11: 6, 13: 4}.get(fu.loc, 4)


def _overlap(a, n, lo, hi):
    return a < hi and a + n > lo


def _metadata(s):
    return (s.name, s.cls) in (("$$SYMBOLS", "DEBSYM"), ("$$TYPES", "DEBTYP"))


def _branch(i):
    """Direct x86 near branches only; do not disassemble embedded jump tables."""
    b = bytes(i.bytes)
    if len(b) == 5 and b[0] in (0xe8, 0xe9):
        k, n = 1, 4
    elif len(b) == 6 and b[0] == 0x0f and 0x80 <= b[1] <= 0x8f:
        k, n = 2, 4
    elif len(b) == 2 and (b[0] == 0xeb or 0x70 <= b[0] <= 0x7f
                          or 0xe0 <= b[0] <= 0xe3):
        k, n = 1, 1
    else:
        return None
    return (i.address + k, n,
            (i.address + len(b) + int.from_bytes(b[k:], "little", signed=True)) & 0xffffffff)


class OriginalIndex:
    """Read-only indexes reused across all 514 audit objects."""
    def __init__(self, p):
        self.p = p
        self.fix_addrs = sorted(p.fix_at)
        self.branches = {}
        self.unsupported_branches = {}
        for i in p.insns.values():
            b = _branch(i)
            if b:
                self.branches[b[0]] = (b[1], b[2], i.address, bytes(i.bytes))
            elif (i.mnemonic in ("call", "jmp", "lcall", "ljmp") or
                  i.mnemonic.startswith("j") or i.mnemonic.startswith("loop")) and (
                      i.op_str.startswith("0x") or i.mnemonic in ("lcall", "ljmp")):
                self.unsupported_branches[i.address] = bytes(i.bytes)
        self.branch_addrs = sorted(self.branches)
        self.functions = {f["start"]: f for f in p.functions}
        self.insn_addrs = sorted(p.insns)

    def fixes(self, lo, hi):
        # Include fields straddling a boundary so slicing cannot conceal one.
        aa = self.fix_addrs
        return [a for a in aa[bisect_left(aa, lo - 5):bisect_left(aa, hi)]
                if a + self.p.fix_at[a][0].size > lo]

    def branches_in(self, lo, hi):
        aa = self.branch_addrs
        return aa[bisect_left(aa, lo):bisect_left(aa, hi)]


class _Checker:
    def __init__(self, p, mod, by_link, index):
        self.p, self.mod, self.db, self.idx = p, mod, by_link, index
        self.ti, self.text = mod.seg("_TEXT")
        self.starts = sorted((off, name) for name, (si, off) in
                             list(mod.publics.items()) + list(mod.statics.items())
                             if si == self.ti)
        self.bases = {}
        self.anchor_conflicts = []

    def local_def(self, name):
        return self.mod.statics.get(name, self.mod.publics.get(name))

    def validate_fixups(self, s):
        """Validate storage and supported forms before any verification slicing."""
        r = MatchResult(s.name)
        for fu in s.fixups:
            n = _size(fu)
            if fu.loc != 9:
                r.add("unsupported_location", "unsupported_construct", fu.offset, None,
                      "Only OMF loc 9/off32 is supported", loc=fu.loc, size=n)
            if fu.target_kind not in ("ext", "seg"):
                r.add("unsupported_target", "unsupported_construct", fu.offset, None,
                      "Unsupported relocation target kind", target_kind=fu.target_kind,
                      target=fu.target)
            elif fu.target_kind == "seg" and (not isinstance(fu.target, int) or
                                                not 1 <= fu.target <= len(self.mod.segments)):
                r.add("invalid_segment", "unsupported_construct", fu.offset, None,
                      "Invalid segment index", target=fu.target)
            if not (0 <= fu.offset < s.length and fu.offset + n <= s.length and
                    fu.offset + n <= len(s.data)):
                r.add("fixup_out_of_bounds", "unsupported_construct", fu.offset, None,
                      "Relocation exceeds segment storage", size=n, length=s.length,
                      storage_length=len(s.data), segment=s.name)
        return r.findings

    def check_coverage(self, r, off, end, base):
        f = self.idx.functions.get(base)
        if f and end - off < f["end"] - base:
            r.add("truncated_function", "extent_retry", end, base+end-off,
                  "Compiled extent does not cover the discovered original body",
                  original_fn_end=f["end"], compiled_body_size=end-off)
        boundary = base + end - off
        pos = bisect_left(self.idx.insn_addrs, boundary)
        if pos:
            i = self.p.insns[self.idx.insn_addrs[pos-1]]
            if i.address < boundary < i.address + len(i.bytes):
                r.add("truncated_instruction", "extent_retry", end, boundary,
                      "Compiled extent ends inside an original instruction",
                      instruction_start=i.address, instruction_size=len(i.bytes))

    def original_target(self, a, fu, code):
        if fu.self_rel:
            b = self.idx.branches.get(a) if code else None
            return b[1] if b and b[0] == 4 else None
        orig = self.p.fix_at.get(a)
        return orig[1] if orig else None

    def anchor(self, si, base, source):
        if si in self.bases and self.bases[si] != base:
            item = (si, self.bases[si], base, source)
            if item not in self.anchor_conflicts:
                self.anchor_conflicts.append(item)
        else:
            self.bases[si] = base

    def infer(self, s, lo, hi, base, code):
        for fu in s.fixups:
            if fu.loc != 9 or fu.offset < lo or fu.offset + 4 > hi:
                continue
            local = self.local_def(fu.target) if fu.target_kind == "ext" else None
            if fu.target_kind == "seg":
                si, sym_off = fu.target, 0
            elif local is not None:
                si, sym_off = local
            else:
                continue
            if (fu.offset + 4 > min(s.length, len(s.data)) or
                    not isinstance(si, int) or not 1 <= si <= len(self.mod.segments)):
                continue
            if fu.self_rel and not code:
                continue
            ot = self.original_target(base + fu.offset - lo, fu, code)
            if ot is not None:
                add = struct.unpack_from("<i", s.data, fu.offset)[0] + fu.disp
                self.anchor(si, (ot - add - sym_off) & 0xffffffff,
                            dict(segment=s.name, offset=fu.offset))

    def resolved(self, fu, r, a):
        if fu.target_kind == "ext":
            e = self.db.get(fu.target)
            local = self.local_def(fu.target)
            if local is not None:
                si, sym_off = local
                if (fu.target in self.mod.publics and fu.target in self.mod.statics and
                        self.mod.publics[fu.target] != self.mod.statics[fu.target]):
                    r.add("ambiguous_local_definition", "unsupported_construct", fu.offset, a,
                          "Public and static definitions disagree", target=fu.target)
                    return None
                if not isinstance(si, int) or not 1 <= si <= len(self.mod.segments):
                    r.add("invalid_segment", "unsupported_construct", fu.offset, a,
                          "Local definition has invalid segment index", target=fu.target)
                    return None
                s = self.mod.segments[si-1]
                if _metadata(s):
                    r.add("runtime_reference_to_debug", "unsupported_construct", fu.offset, a,
                          "Runtime external resolves to excluded debug metadata",
                          target=fu.target, segment=s.name)
                    return None
                if si not in self.bases:
                    r.add("unanchored_target", "unsupported_construct", fu.offset, a,
                          "Local definition has no consistent image anchor", target=fu.target)
                    return None
                target = (self.bases[si] + sym_off) & 0xffffffff
                if e is not None and target != e["addr"]:
                    r.add("local_definition_mismatch", "code_reloc_forward", fu.offset, a,
                          "Local definition contradicts its database address",
                          target=fu.target, segment=si, segment_base=self.bases[si],
                          symbol_offset=sym_off, resolved=target, database_addr=e["addr"])
                return target
            if e is None:
                r.add("unresolved_external", "unsupported_construct", fu.offset, a,
                      "External symbol has no database address", target=fu.target)
                return None
            return e["addr"]
        if fu.target_kind == "seg":
            if not isinstance(fu.target, int) or not 1 <= fu.target <= len(self.mod.segments):
                r.add("invalid_segment", "unsupported_construct", fu.offset, a,
                      "Invalid segment index", target=fu.target)
            elif fu.target not in self.bases:
                r.add("unanchored_target", "unsupported_construct", fu.offset, a,
                      "Target segment has no consistent image anchor", target=fu.target)
            else:
                return self.bases[fu.target]
            return None
        r.add("unsupported_target", "unsupported_construct", fu.offset, a,
              "Unsupported relocation target kind", target_kind=fu.target_kind,
              target=fu.target)
        return None

    def check(self, s, lo, hi, base, code, name, region_hi=None):
        r = MatchResult(name, orig_start=base, orig_end=base + hi - lo)
        r.findings.extend(self.validate_fixups(s))
        cat = "code" if code else "data"
        if not 0 <= lo <= hi <= len(s.data):
            r.add("invalid_extent", "error", lo, base, "Extent exceeds compiled segment",
                  lo=lo, hi=hi, length=len(s.data))
            return r
        obj = self.p.le.obj_at(base)
        want = b""
        if obj and base + hi - lo <= obj.end:
            want = bytes(self.p.image[obj.index][base - obj.base:base - obj.base + hi - lo])
        if len(want) != hi - lo:
            r.add("image_extent", cat + "_bytes", lo, base,
                  "Compared extent lies outside one original image object", length=hi-lo)
        fx = [f for f in s.fixups if _overlap(f.offset, _size(f), lo, hi)]
        r.metrics[cat + "_fixups_checked"] = len(fx)
        at = {}
        mask = set()
        for fu in fx:
            a = base + fu.offset - lo
            n = _size(fu)
            at.setdefault(fu.offset, []).append(fu)
            if fu.offset < lo or fu.offset + n > hi:
                r.add("fixup_crosses_extent", "unsupported_construct", fu.offset, a,
                      "Relocation field crosses verification boundary", size=n, lo=lo, hi=hi)
            if fu.loc != 9:
                r.add("unsupported_location", "unsupported_construct", fu.offset, a,
                      "Only OMF loc 9/off32 is supported", loc=fu.loc, size=n)
            if fu.target_kind not in ("ext", "seg"):
                self.resolved(fu, r, a)
            if fu.self_rel and not code:
                r.add("data_self_relative", "unsupported_construct", fu.offset, a,
                      "Self-relative data relocation is unsupported")
            if fu.offset < 0 or fu.offset + n > len(s.data):
                r.add("fixup_out_of_bounds", "unsupported_construct", fu.offset, a,
                      "Relocation exceeds segment storage", size=n)
                continue
            mask.update(range(fu.offset, fu.offset + n))
            if fu.loc != 9 or (fu.self_rel and not code):
                continue
            target = self.resolved(fu, r, a) if fu.target_kind in ("ext", "seg") else None
            add = struct.unpack_from("<i", s.data, fu.offset)[0] + fu.disp
            kind = "rel32_code" if fu.self_rel else "abs_" + cat
            r.obligations.append(dict(asdict(Obligation(
                kind, fu.offset, 4, target, add,
                "target + addend - (src_addr + field_size)" if fu.self_rel else "target + addend",
                True, not fu.self_rel)), origin="compiled", segment=s.name))
            ot = self.original_target(a, fu, code)
            orig = self.p.fix_at.get(a)
            if fu.self_rel:
                if orig is not None or ot is None:
                    r.add("relative_kind_mismatch", cat + "_reloc_forward", fu.offset, a,
                          "Self-relative fixup does not map to an original rel32 branch",
                          original_le_fixup=orig is not None)
            elif orig is None:
                r.add("missing_original_fixup", cat + "_reloc_forward", fu.offset, a,
                      "Absolute OMF fixup lacks an original LE fixup")
            elif orig[0].src_type != 7 or orig[0].size != 4:
                r.add("unsupported_le_kind", "unsupported_construct", fu.offset, a,
                      "Original fixup is not off32", src_type=orig[0].src_type)
            if target is not None and ot is not None and (target + add) & 0xffffffff != ot:
                r.add("relocation_target_mismatch", cat + "_reloc_forward", fu.offset, a,
                      "Resolved OMF target differs from original target",
                      target=target, addend=add, resolved=(target+add) & 0xffffffff,
                      original_target=ot, target_kind=fu.target_kind,
                      symbolic_target=fu.target)
        for off, ff in at.items():
            overlaps = [g.offset for g in fx if g.offset != off and
                        _overlap(g.offset, _size(g), off, off + _size(ff[0]))]
            if len(ff) > 1 or overlaps:
                r.add("overlapping_fixups", "unsupported_construct", off, base+off-lo,
                      "Multiple fixups cover the same field bytes", count=len(ff), overlaps=overlaps)
        # Every differing ordinary byte is evidence. No diagnostic truncation.
        for j, (got, wanted) in enumerate(zip(s.data[lo:hi], want)):
            if lo + j not in mask and got != wanted:
                r.add("byte_mismatch", cat + "_bytes", lo+j, base+j,
                      "Unrelocated byte differs", got=got, want=wanted, segment=s.name)
        for a in self.idx.fixes(base, base + hi - lo):
            orig, target = self.p.fix_at[a]
            off = lo + a - base
            r.metrics["reverse_le_fixups_checked"] += 1
            r.obligations.append(dict(asdict(Obligation(
                "abs_"+cat, off, orig.size, target, 0, "target + addend", True, True)),
                origin="original", segment=s.name))
            if orig.src_type != 7:
                r.add("unsupported_le_kind", "unsupported_construct", off, a,
                      "Original loader fixup is not off32", src_type=orig.src_type)
            ff = at.get(off, [])
            if not any(f.loc == 9 and not f.self_rel and _size(f) == orig.size for f in ff):
                r.add("missing_compiled_absolute_fixup", cat + "_reloc_reverse", off, a,
                      "Original LE obligation lacks a same-kind/size OMF fixup",
                      original_target=target, original_size=orig.size,
                      compiled_fixups=[asdict(f) for f in ff])
        if code:
            self.check_branches(r, s, lo, hi, base, at, region_hi)
        return r

    def check_branches(self, r, s, lo, hi, base, at, region_hi):
        region_base = self.bases.get(self.ti, base-lo)
        region_end = region_base + (len(self.text.data) if region_hi is None else region_hi)
        md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
        for a, encoding in self.idx.unsupported_branches.items():
            if base <= a < base+hi-lo:
                r.add("unsupported_branch_encoding", "unsupported_construct", lo+a-base, a,
                      "Direct branch is outside supported rel8/rel32 encodings",
                      original_encoding=encoding.hex())
        for a in self.idx.branches_in(base, base+hi-lo):
            n, target, ia, ib = self.idx.branches[a]
            off = lo + a - base
            external = not region_base <= target < region_end
            if region_end <= target < region_base + len(self.text.data):
                r.add("trimmed_branch_target", "extent_retry", off, a,
                      "Retained branch targets bytes proposed for trimming",
                      original_target=target, retained_region_end=region_end)
            r.obligations.append(dict(asdict(Obligation(
                "rel32_code" if n == 4 else "rel8_code", off, n, target, 0,
                "target + addend - (src_addr + field_size)", external, False)),
                origin="original", segment=s.name))
            ff = at.get(off, [])
            if external and not any(f.loc == 9 and f.self_rel for f in ff):
                r.add("missing_compiled_relative_fixup" if n == 4 else "external_rel8",
                      "code_reloc_reverse" if n == 4 else "unsupported_construct",
                      off, a, "External relative branch lacks static relocation",
                      original_target=target, field_size=n)
            start = lo + ia - base
            if start < lo or start+len(ib) > hi:
                r.add("branch_crosses_extent", "unsupported_construct", off, a,
                      "Branch instruction crosses verification boundary")
                continue
            ci = next(md.disasm(bytes(s.data[start:start+len(ib)]), ia, 1), None)
            cb = _branch(ci) if ci else None
            if cb is None or cb[0] != a or cb[1] != n or bytes(ci.bytes)[:a-ia] != ib[:a-ia]:
                r.add("branch_encoding_mismatch", "code_reloc_forward", off, a,
                      "Original relative instruction has a different compiled encoding",
                      original_encoding=ib.hex(), compiled_encoding=bytes(s.data[start:start+len(ib)]).hex())
            elif not ff and cb[2] != target:
                r.add("relative_target_mismatch", "code_reloc_forward", off, a,
                      "Intra-segment relative displacement differs",
                      resolved=cb[2], original_target=target)

    def run(self):
        region = MatchResult("_TEXT region")
        for s in self.mod.segments:
            if not _metadata(s):
                region.findings.extend(self.validate_fixups(s))
        if self.text is None or not self.starts:
            region.add("missing_text_publics", "unsupported_construct", None, None,
                       "No _TEXT public/static functions to anchor region")
            return dict(functions={}, region=region.to_dict())
        known = [(off, n, self.db[n]["addr"]) for off, n in self.starts if n in self.db]
        for off, n in self.starts:
            if n not in self.db:
                region.add("unknown_public", "unsupported_construct", off, None,
                           "Public/static has no original address", symbol=n)
        if not known:
            return dict(functions={}, region=region.to_dict())
        rb = known[0][2] - known[0][0]
        self.bases[self.ti] = rb
        region.orig_start, region.orig_end = rb, rb + len(self.text.data)
        for off, n, addr in known:
            if addr - off != rb:
                region.add("public_layout_mismatch", "leading_bytes", off, addr,
                           "Publics disagree on original region base", symbol=n,
                           expected_base=rb, derived_base=addr-off)
        # Infer all anchors before checks, including chains through local data.
        self.infer(self.text, 0, self.starts[0][0], rb, True)
        for k, (off, n) in enumerate(self.starts):
            end = self.starts[k+1][0] if k+1 < len(self.starts) else len(self.text.data)
            if n in self.db:
                self.infer(self.text, off, end, self.db[n]["addr"], True)
        for _ in range(len(self.mod.segments)):
            before = dict(self.bases)
            for si, sb in list(self.bases.items()):
                if si != self.ti:
                    s = self.mod.segments[si-1]
                    self.infer(s, 0, len(s.data), sb, False)
            if before == self.bases:
                break
        # Definitions are constraints too, even if no checked fixup happens to
        # reference them. Never let an inferred anchor override a DB address.
        for n, (si, sym_off) in list(self.mod.publics.items()) + list(self.mod.statics.items()):
            if n in self.db and si in self.bases and not _metadata(self.mod.segments[si-1]):
                target = (self.bases[si] + sym_off) & 0xffffffff
                if target != self.db[n]["addr"]:
                    region.add("local_definition_mismatch", "code_reloc_forward", sym_off,
                               target, "Local definition contradicts its database address",
                               target=n, segment=si, segment_base=self.bases[si],
                               symbol_offset=sym_off, resolved=target,
                               database_addr=self.db[n]["addr"])
        functions = {}
        for k, (off, n) in enumerate(self.starts):
            if n not in self.db:
                continue
            end = self.starts[k+1][0] if k+1 < len(self.starts) else len(self.text.data)
            base = self.db[n]["addr"]
            r = self.check(self.text, off, end, base, True, n)
            self.check_coverage(r, off, end, base)
            f = self.idx.functions.get(base)
            if r.findings and f:
                hi = off + f["end"] - base
                if off < hi < end:
                    filler = match.is_filler(bytes(self.text.data[hi:end]))
                    tailfx = [asdict(fu) for fu in self.text.fixups
                              if _overlap(fu.offset, _size(fu), hi, end)]
                    # A fixup beginning before the discovered end must not be hidden.
                    hidden = [a for a in self.idx.fixes(base+hi-off, base+end-off)
                              if a < f["end"]]
                    if filler and not tailfx and not hidden:
                        region_hi = hi if k+1 == len(self.starts) else None
                        r = self.check(self.text, off, hi, base, True, n, region_hi)
                        self.check_coverage(r, off, hi, base)
                        # Region still checks all bytes at internal boundaries.
                    else:
                        r.add("extent_retry_rejected", "extent_retry", hi, base+hi-off,
                              "Tail is not safely trimmable alignment filler",
                              filler=filler, overlapping_compiled_fixups=tailfx,
                              hidden_original_fixups=hidden, original_fn_end=f["end"], end=end)
            functions[n] = r.to_dict()
        # Whole contiguous region: only its final alignment tail may be trimmed.
        total_end = len(self.text.data)
        last_off, last_name = self.starts[-1]
        last = functions.get(last_name)
        if last and last["verdict"] == "MATCH" and last["orig_end"] < rb+total_end:
            candidate_end = last_off + last["orig_end"] - self.db[last_name]["addr"]
            if last["orig_start"] - last_off == rb:
                total_end = candidate_end
        # Recheck successful bodies against the final retained region, including
        # earlier functions whose branches may target the discarded final tail.
        for k, (off, n) in enumerate(self.starts):
            if n not in self.db:
                continue
            end = min(self.starts[k+1][0] if k+1 < len(self.starts) else total_end, total_end)
            base = self.db[n]["addr"]
            self.check_coverage(region, off, end, base)
            fr = functions[n]
            if fr["verdict"] == "MATCH" and total_end != len(self.text.data):
                hi = off + fr["orig_end"] - base
                rr = self.check(self.text, off, hi, base, True, n, total_end)
                self.check_coverage(rr, off, hi, base)
                functions[n] = rr.to_dict()
        cr = self.check(self.text, 0, total_end, rb, True, "_TEXT", total_end)
        region.findings.extend(f for f in cr.findings if f not in region.findings)
        region.obligations.extend(cr.obligations)
        region.metrics.update(cr.metrics)
        region.orig_end = rb+total_end
        region.metrics["leading_bytes_len"] = self.starts[0][0]
        # Preserve leading classification without dropping original categories.
        for finding in region.findings:
            if finding["offset"] is not None and finding["offset"] < self.starts[0][0]:
                finding["evidence"]["leading_bytes"] = True
        excluded_metadata = []
        for si, s in enumerate(self.mod.segments, 1):
            if si == self.ti:
                continue
            # Watcom -d1+ emits non-loadable symbolic/type records, not local
            # runtime data. wc1.cemu._SKIP_CLASSES documents the same distinction.
            # Keep this narrow: unknown classes still fail closed below, and a
            # runtime reference into metadata is not silently excluded.
            if _metadata(s):
                if si in self.bases:
                    region.add("runtime_reference_to_debug", "unsupported_construct", None,
                               self.bases[si], "Runtime obligation targets debug metadata",
                               segment=s.name, segment_index=si)
                excluded_metadata.append(dict(segment_index=si, name=s.name, cls=s.cls,
                    size=len(s.data), fixups=len(s.fixups), reason="non-loadable Watcom debug metadata"))
                continue
            if s.cls == "CODE" and (s.length or s.data):
                region.add("additional_code_segment", "unsupported_construct", None, None,
                           "Additional executable segments are unsupported in E0 v1",
                           segment=s.name, segment_index=si)
                continue
            if not s.data:
                continue
            sb = self.bases.get(si)
            if sb is None:
                region.add("unanchored_local_segment", "unsupported_construct", None, None,
                           "Nonempty local segment cannot be mapped to original image",
                           segment=s.name, size=len(s.data))
                continue
            dr = self.check(s, 0, len(s.data), sb, False, s.name)
            region.findings.extend(f for f in dr.findings if f not in region.findings)
            region.obligations.extend(dr.obligations)
            region.metrics["data_segments_checked"] += 1
            for key in ("data_fixups_checked", "reverse_le_fixups_checked"):
                region.metrics[key] += dr.metrics[key]
        for si, old, new, source in self.anchor_conflicts:
            region.add("inconsistent_segment_anchor", "code_reloc_forward", source["offset"], None,
                       "Address obligations imply conflicting segment bases", segment=si,
                       first_base=old, conflicting_base=new, source=source)
        if self.mod.comdefs:
            region.add("communal_storage", "unsupported_construct", None, None,
                       "Communal storage placement is not proven", comdefs=self.mod.comdefs)
        return dict(functions=functions, region=region.to_dict(), excluded_metadata=excluded_metadata)


def match_module(p, mod, funcs_by_link, index=None):
    """Return serializable FunctionMatch and RegionMatch with exhaustive findings.

    Malformed inputs raise to the audit boundary, which records ERROR rather
    than fabricating a match. Unsupported parsed constructs get UNSUPPORTED.
    """
    return _Checker(p, mod, funcs_by_link, index or OriginalIndex(p)).run()
