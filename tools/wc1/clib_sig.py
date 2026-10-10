"""Library signature matching of war.exe against Open Watcom 2 runtime libraries.

usage: python3 -m wc1.clib_sig [--json build/clib/libsig.json] [--near] [-v]

For every code segment of every module in the OW2 runtime libraries
(clib3r, math387r, math3r, emu387, noemu387 and the X-32 startup object
cstrtx3r.obj) the segment is split into functions at its public and static
symbols ("units"). Each unit is searched in the original code object at two
levels:

  bytes  every byte identical except relocation fields (as wc1.match does);
  insn   the same instruction sequence: mnemonic, registers, operand sizes,
         scale, immediates and displacements equal, relocation fields compared
         by *target* and internal branches by *instruction index*. This
         accepts alternative encodings of the same instruction (the 1994
         assembler wrote `sub ecx,ecx` as 29 c9 where OW2 writes 2b c9, and
         adds redundant DS: prefixes), nothing else.

At both levels a candidate is accepted only if

  * every absolute relocation of the library code lands on an LE fixup of the
    original and the original has no fixup where the library has none,
  * module-internal references (statics of the same module, its own code
    segment) resolve to one module base,
  * module-local initialised data (CONST/_DATA) resolve to one consistent base
    and their bytes equal the original's (relocation fields masked).

Accepted units yield constraints `link name -> address` for external symbols
(target - addend). They are cross-checked: one address per link name, and a
matched function's address must agree with every relocation naming it.
Constraints for names that are not matched themselves identify further
functions and data ("by relocation"). Units with several candidate positions
are disambiguated by these constraints or reported as ambiguous.

Near matches (--near): unmatched library functions are compared with the
unclaimed original functions in the runtime range by mnemonic-sequence
similarity (a hint, not evidence).
"""
import argparse
import bisect
import difflib
import json
import os
import struct
import sys
from collections import defaultdict

import capstone
from capstone import x86

from . import analysis, omf, path

LIBS = [
    ("clib3r", "dos/clib3r.lib"),
    ("math387r", "math387r.lib"),
    ("math3r", "math3r.lib"),
    ("emu387", "emu387.lib"),
    ("noemu387", "noemu387.lib"),
]
OBJS = [("cstrtx3r", "dos/cstrtx3r.obj")]
MIN_UNMASKED = 8          # byte level: fewer fixed bytes is too ambiguous
MIN_INSNS = 4             # insn level: shorter units are too ambiguous
STRONG_UNMASKED = 12      # fewer fixed bytes: a candidate unless corroborated
RUNTIME_LO = 0x30000      # search window for near matches


def watcom_dir():
    w = os.environ.get("WATCOM")
    if not w:
        raise SystemExit("WATCOM not set (run inside nix develop)")
    return os.path.join(w, "lib386")


def load_modules():
    """[(libname, Module)] for every module of the configured libraries."""
    base = watcom_dir()
    out = []
    for lib, rel in LIBS:
        for m in omf.parse_library(os.path.join(base, rel)):
            out.append((lib, m))
    for lib, rel in OBJS:
        out.append((lib, omf.parse_object(os.path.join(base, rel))))
    return out


class Unit:
    """One function (or anonymous code run) of a library module."""

    def __init__(self, lib, mod, segi, name, off, end, aliases=()):
        self.lib, self.mod, self.segi, self.name = lib, mod, segi, name
        self.aliases = list(aliases)
        self.off, self.end = off, end
        self.seg = mod.segments[segi - 1]
        self.data = bytes(self.seg.data[off:end])
        self.fixups = [f for f in self.seg.fixups if off <= f.offset < end]
        self.mask = bytearray(end - off)
        for f in self.fixups:
            for k in range(f.offset - off, min(f.offset - off + f.size, end - off)):
                self.mask[k] = 1
        self.unmasked = len(self.mask) - sum(self.mask)
        self.key_mod = f"{lib}({mod.name})"
        self.key = f"{self.key_mod}{name}"
        self._insns = False

    @property
    def names(self):
        return [self.name] + self.aliases

    def anchor(self):
        """Longest unmasked run: (offset, bytes)."""
        best, cur = (0, 0), None
        for k, m in enumerate(list(self.mask) + [1]):
            if not m and cur is None:
                cur = k
            elif m and cur is not None:
                if k - cur > best[1]:
                    best = (cur, k - cur)
                cur = None
        return best[0], self.data[best[0]:best[0] + best[1]]


def code_units(lib, mod):
    """Split every code segment of mod at its symbols."""
    units = []
    syms = defaultdict(list)
    for n, (si, off) in list(mod.publics.items()) + list(mod.statics.items()):
        syms[si].append((off, n))
    for si, seg in enumerate(mod.segments, 1):
        if seg.cls != "CODE" or not seg.data:
            continue
        pts = sorted(set(syms.get(si, [])))
        offs = sorted({o for o, _ in pts})
        if not offs or offs[0] != 0:
            pts = [(0, f"<{seg.name}+0>")] + pts
            offs = [0] + offs
        done = set()
        for o, n in pts:
            if o in done:
                continue
            done.add(o)
            nxt = [x for x in offs if x > o]
            end = nxt[0] if nxt else len(seg.data)
            if end > o:
                units.append(Unit(lib, mod, si, n, o, end,
                                  sorted(nn for oo, nn in pts if oo == o and nn != n)))
    return units


def _is_filler(i):
    b = bytes(i.bytes)
    return b in analysis.Program.FILLERS or set(b) == {0}


class Matcher:
    def __init__(self, prog=None):
        self.p = prog or analysis.Program()
        self.code = self.p.cbytes
        self.cbase = self.p.code.base
        self._mn_index = None

    # -- byte level ---------------------------------------------------------
    def byte_candidates(self, u):
        ao, ab = u.anchor()
        if len(ab) < 3:
            return []
        out, i = [], self.code.find(ab)
        while i >= 0:
            b = i - ao
            if b >= 0 and b + len(u.data) <= len(self.code):
                out.append(self.cbase + b)
            i = self.code.find(ab, i + 1)
        return out

    def check_bytes(self, u, base):
        o0 = base - self.cbase
        want = self.code[o0:o0 + len(u.data)]
        for k, (g, w) in enumerate(zip(u.data, want)):
            if not u.mask[k] and g != w:
                return False, [f"byte +{k:#x}"], []
        for k in range(len(u.data)):
            if not u.mask[k] and (base + k) in self.p.fix_at:
                return False, [f"original fixup at unmasked +{k:#x}"], []
        local = dict(u.mod.publics)
        local.update(u.mod.statics)
        cons, problems = [], []
        for f in u.fixups:
            a = base + (f.offset - u.off)
            if f.loc not in (9, 13):
                problems.append(f"+{f.offset - u.off:#x}: fixup loc {f.loc} not checked")
                continue
            if not f.self_rel and a not in self.p.fix_at:
                return False, [f"+{f.offset - u.off:#x}: original has no fixup"], []
            addend = struct.unpack_from("<i", u.seg.data, f.offset)[0] + f.disp
            if f.self_rel:
                rel = struct.unpack_from("<i", self.code, a - self.cbase)[0]
                ot = (a + 4 + rel) & 0xFFFFFFFF
            else:
                ot = self.p.fix_at[a][1]
            self._constraint(u, f, (ot - addend) & 0xFFFFFFFF, local, cons, problems)
        cons.append(("seg", (u.key_mod, u.segi), base - u.off))
        ok, why = self._check_segments(u, cons)
        if not ok:
            return False, why, []
        return True, problems, cons

    def _constraint(self, u, f, tgt, local, cons, problems):
        if f.target_kind == "ext":
            if f.target in local:
                si, so = local[f.target]
                cons.append(("seg", (u.key_mod, si), (tgt - so) & 0xFFFFFFFF))
            else:
                cons.append(("ext", f.target, tgt))
        elif f.target_kind == "seg":
            cons.append(("seg", (u.key_mod, f.target), tgt))
        else:
            problems.append(f"target kind {f.target_kind} {f.target} not checked")

    def _check_segments(self, u, cons):
        segbase = {}
        for kind, key, addr in cons:
            if kind == "seg" and segbase.setdefault(key, addr) != addr:
                return False, [f"segment {key} base inconsistent"]
        for (km, si), sb in segbase.items():
            s = u.mod.segments[si - 1]
            if s.cls in ("CODE", "BSS") or not s.data:
                continue
            o = self.p.le.obj_at(sb)
            if o is None:
                return False, [f"segment {s.name} base {sb:#x} outside image"]
            img = self.p.image[o.index]
            have = bytes(img[sb - o.base:sb - o.base + len(s.data)])
            dmask = set()
            for fu in s.fixups:
                dmask.update(range(fu.offset, fu.offset + fu.size))
            bad = [j for j in range(len(s.data)) if j not in dmask and j < len(have)
                   and s.data[j] != have[j]]
            if bad or len(have) < len(s.data):
                return False, [f"segment {s.name} data differs at +{bad[0] if bad else len(have):#x}"]
        return True, []

    # -- instruction level --------------------------------------------------
    def lib_insns(self, u):
        """Decoded instructions of a unit with trailing alignment filler
        (after the last terminator) removed; None if it does not decode."""
        if u._insns is False:
            ins = list(self.p.md.disasm(u.data, 0))
            if not ins or ins[-1].address + ins[-1].size != len(u.data):
                u._insns = None
            else:
                last = max((k for k, i in enumerate(ins) if i.mnemonic in analysis.TERMINATORS),
                           default=len(ins) - 1)
                if all(_is_filler(i) for i in ins[last + 1:]):
                    ins = ins[:last + 1]
                u._insns = ins
        return u._insns

    def insn_candidates(self, u):
        lins = self.lib_insns(u)
        if not lins or len(lins) < MIN_INSNS:
            return []
        if self._mn_index is None:
            idx = defaultdict(list)
            md = self.p.md
            # decode linearly from every address that starts a known
            # instruction (discovered code) - cheap and sufficient
            insns = getattr(self.p, "insns", None)
            if insns is None:
                self.p.discover()
                insns = self.p.insns
            for a, i in insns.items():
                j = insns.get(a + i.size)
                k = insns.get(a + i.size + j.size) if j else None
                if k:
                    idx[(i.mnemonic, j.mnemonic, k.mnemonic)].append(a)
            self._mn_index = idx
        return sorted(self._mn_index.get(tuple(i.mnemonic for i in lins[:3]), []))

    def check_insn(self, u, base):
        """Returns (ok, problems, constraints)."""
        lins = self.lib_insns(u)
        if not lins:
            return False, ["undecodable"], []
        fx = {f.offset - u.off: f for f in u.fixups}
        lidx = {i.address: k for k, i in enumerate(lins)}
        oins, a = [], base
        for _ in lins:
            i = self.p.insn_at(a)
            if i is None:
                return False, ["orig undecodable"], []
            oins.append(i)
            a += i.size
        oidx = {i.address: k for k, i in enumerate(oins)}
        local = dict(u.mod.publics)
        local.update(u.mod.statics)
        cons, problems = [], []
        for k, (li, oi) in enumerate(zip(lins, oins)):
            if li.mnemonic != oi.mnemonic or len(li.operands) != len(oi.operands):
                return False, [f"insn {k}: {li.mnemonic} {li.op_str} / {oi.mnemonic} {oi.op_str}"], []
            lslots = {}
            for o in range(li.address, li.address + li.size):
                if o not in fx:
                    continue
                ro = o - li.address
                if li.disp_size and ro == li.disp_offset:
                    lslots["disp"] = fx[o]
                elif li.imm_size and ro == li.imm_offset:
                    lslots["imm"] = fx[o]
                else:
                    return False, [f"insn {k}: fixup not on an operand field"], []
            oslot = {}
            if oi.disp_size == 4 and oi.address + oi.disp_offset in self.p.fix_at:
                oslot["disp"] = oi.address + oi.disp_offset
            if oi.imm_size == 4 and oi.address + oi.imm_offset in self.p.fix_at:
                oslot["imm"] = oi.address + oi.imm_offset
            branch = li.group(capstone.CS_GRP_JUMP) or li.group(capstone.CS_GRP_CALL)
            for kind in ("disp", "imm"):
                f = lslots.get(kind)
                if f is None:
                    if kind in oslot:
                        return False, [f"insn {k}: original relocates its {kind}"], []
                    continue
                if f.loc not in (9, 13):
                    return False, [f"insn {k}: fixup loc {f.loc}"], []
                addend = struct.unpack_from("<i", u.seg.data, f.offset)[0] + f.disp
                if f.self_rel:
                    if not branch:
                        return False, [f"insn {k}: self-relative non-branch"], []
                    ot = oi.operands[0].imm & 0xFFFFFFFF
                elif kind in oslot:
                    ot = self.p.fix_at[oslot[kind]][1]
                else:
                    return False, [f"insn {k}: original has no fixup"], []
                self._constraint(u, f, (ot - addend) & 0xFFFFFFFF, local, cons, problems)
            for lo, oo in zip(li.operands, oi.operands):
                if lo.type != oo.type or lo.size != oo.size:
                    return False, [f"insn {k}: operands {li.op_str} / {oi.op_str}"], []
                if lo.type == x86.X86_OP_REG:
                    if lo.reg != oo.reg:
                        return False, [f"insn {k}: {li.op_str} / {oi.op_str}"], []
                elif lo.type == x86.X86_OP_IMM:
                    if "imm" in lslots:
                        continue
                    if branch:
                        lt, ot = lo.imm, oo.imm & 0xFFFFFFFF
                        if lt in lidx:
                            if oidx.get(ot) != lidx[lt]:
                                return False, [f"insn {k}: branch target differs"], []
                        else:   # same-segment target outside the unit, no fixup
                            cons.append(("seg", (u.key_mod, u.segi),
                                         (ot - (u.off + lt)) & 0xFFFFFFFF))
                    elif lo.imm & 0xFFFFFFFF != oo.imm & 0xFFFFFFFF:
                        return False, [f"insn {k}: {li.op_str} / {oi.op_str}"], []
                elif lo.type == x86.X86_OP_MEM:
                    lm, om = lo.mem, oo.mem
                    if (lm.segment, lm.base, lm.index, lm.scale) != \
                            (om.segment, om.base, om.index, om.scale):
                        return False, [f"insn {k}: {li.op_str} / {oi.op_str}"], []
                    if "disp" not in lslots and lm.disp != om.disp:
                        return False, [f"insn {k}: {li.op_str} / {oi.op_str}"], []
        cons.append(("seg", (u.key_mod, u.segi), base - u.off))
        ok, why = self._check_segments(u, cons)
        if not ok:
            return False, why, []
        u.orig_size = a - base
        return True, problems, cons


def all_units(mods):
    return [u for lib, mod in mods for u in code_units(lib, mod)]


def run_matching(prog=None):
    """{unit: [(addr, level, problems, constraints)]} for every unit with a
    hit. Byte-level hits take precedence over instruction-level ones."""
    m = Matcher(prog)
    units = all_units(load_modules())
    hits = {}
    for u in units:
        found = []
        if u.unmasked >= MIN_UNMASKED:
            for b in m.byte_candidates(u):
                ok, probs, cons = m.check_bytes(u, b)
                if ok:
                    found.append((b, "bytes", probs, cons))
        seen = {f[0] for f in found}
        for b in m.insn_candidates(u):
            if b in seen:
                continue
            ok, probs, cons = m.check_insn(u, b)
            if ok:
                found.append((b, "insn", probs, cons))
        if found:
            hits[u] = found
    return m, units, hits


def resolve(hits):
    """Accept unique hits, then disambiguate the rest with the relocation
    constraints of accepted units; uncorroborated short units are demoted
    to `weak` candidates. Returns (accepted {unit: hit},
    ext {name: {addr: [unit keys]}}, ambiguous {unit: [addrs]},
    weak {unit: hit})."""
    accepted, ambiguous = {}, {}
    for u, found in hits.items():
        if len(found) == 1:
            accepted[u] = found[0]
    ext = defaultdict(lambda: defaultdict(list))

    def collect():
        ext.clear()
        for u, (b, lvl, probs, cons) in accepted.items():
            for kind, key, addr in cons:
                if kind == "ext":
                    ext[key][addr].append(u.key)
    for _ in range(3):
        collect()
        changed = False
        for u, found in hits.items():
            if u in accepted:
                continue
            want = {a for n in u.names for a in ext.get(n, {})}
            pick = [f for f in found if f[0] in want]
            if len(pick) == 1:
                accepted[u] = pick[0]
                ambiguous.pop(u, None)
                changed = True
            else:
                ambiguous[u] = [f[0] for f in found]
        if not changed:
            break
    accepted, weak = _split_weak(accepted)
    collect()
    return accepted, ext, ambiguous, weak


def _split_weak(accepted):
    """Short units (stubs such as `xor edx,edx; call strtod`) and units that
    share their address with a differently named unit match by coincidence
    too easily. They are kept only when corroborated: a strong match calls
    them by name at that address, or every external they reference is itself
    strongly matched at the referenced address. Returns (strong, weak)."""
    at = defaultdict(set)
    for u, hit in accepted.items():
        at[hit[0]].add(frozenset(u.names))
    strong = {u: h for u, h in accepted.items()
              if u.unmasked >= STRONG_UNMASKED and len(at[h[0]]) == 1}
    weak = {u: h for u, h in accepted.items() if u not in strong}
    changed = True
    while changed and weak:
        changed = False
        named = {(n, h[0]) for u, h in strong.items() for n in u.names}
        called = {(key, addr) for u, h in strong.items()
                  for kind, key, addr in h[3] if kind == "ext"}
        for u, h in list(weak.items()):
            exts = [(key, addr) for kind, key, addr in h[3] if kind == "ext"]
            by_caller = any((n, h[0]) in called for n in u.names)
            by_callees = bool(exts) and all(e in named for e in exts)
            rivals = [v for v in weak if v is not u and weak[v][0] == h[0]
                      and set(v.names) != set(u.names)]
            if by_caller and not any((n, h[0]) in called for v in rivals for n in v.names) \
                    or by_callees and not rivals and len(at[h[0]]) == 1:
                strong[u] = weak.pop(u)
                changed = True
    return strong, weak


def near_matches(m, units, accepted, min_ratio=0.75):
    """Hints: for unmatched library functions, best-scoring unclaimed
    original functions in the runtime range (mnemonic-sequence similarity)."""
    p = m.p
    if not hasattr(p, "functions"):
        p.partition()
    claimed = set()
    for u, hit in accepted.items():
        claimed.add(hit[0])
    addrs = sorted(p.insns)
    oseq = {}
    for f in p.functions:
        if f["start"] < RUNTIME_LO or f["start"] in claimed:
            continue
        i = bisect.bisect_left(addrs, f["start"])
        s = []
        while i < len(addrs) and addrs[i] < f["end"]:
            s.append(p.insns[addrs[i]].mnemonic)
            i += 1
        if len(s) >= 6:
            oseq[f["start"]] = s
    out = []
    done = {n for u in accepted for n in u.names}
    for u in units:
        if u in accepted or u.name in done or len(u.data) < 16:
            continue
        lins = m.lib_insns(u)
        if not lins or len(lins) < 6:
            continue
        useq = [i.mnemonic for i in lins]
        best = []
        for a, s in oseq.items():
            if not (0.67 <= len(s) / len(useq) <= 1.5):
                continue
            sm = difflib.SequenceMatcher(None, useq, s, autojunk=False)
            if sm.real_quick_ratio() < min_ratio or sm.quick_ratio() < min_ratio:
                continue
            r = sm.ratio()
            if r >= min_ratio:
                best.append((r, a))
        best.sort(reverse=True)
        if best:
            out.append((u, best[:3]))
    return out


def report(accepted, ext, ambiguous, weak, near=None, verbose=False):
    lines = []
    by_addr = sorted(accepted.items(), key=lambda kv: kv[1][0])
    matched = defaultdict(set)
    for u, hit in by_addr:
        for n in u.names:
            matched[n].add(hit[0])
    lines.append(f"# matches: {len(accepted)} library units "
                 f"({sum(1 for h in accepted.values() if h[1] == 'bytes')} byte-identical)")
    for u, (b, lvl, probs, cons) in by_addr:
        note = f"  [{'; '.join(probs)}]" if probs and verbose else ""
        al = f" (= {', '.join(u.aliases)})" if u.aliases else ""
        lines.append(f"{b:#07x} {len(u.data):5d} {lvl:5}  {u.key}{al}  fixups={len(u.fixups)}{note}")
    lines.append("")
    lines.append("# conflicts (one link name, several addresses)")
    for n in sorted(set(ext) | set(matched)):
        all_a = set(ext.get(n, {})) | matched.get(n, set())
        if len(all_a) > 1:
            lines.append(f"{n}: " + ", ".join(f"{a:#x}" for a in sorted(all_a)))
    lines.append("")
    lines.append("# names derived only from relocations of matched code")
    for n, addrs in sorted(ext.items(), key=lambda kv: min(kv[1])):
        if n in matched:
            continue
        for a, who in sorted(addrs.items()):
            lines.append(f"{a:#07x} {n}  <- {', '.join(sorted(set(who))[:4])}")
    lines.append("")
    lines.append(f"# ambiguous: {len(ambiguous)}")
    for u, addrs in sorted(ambiguous.items(), key=lambda kv: kv[0].key):
        lines.append(f"{u.key}: " + ", ".join(f"{a:#x}" for a in addrs[:8]))
    lines.append("")
    lines.append(f"# weak candidates (short or shared address, uncorroborated; not evidence): {len(weak)}")
    for u, (b, lvl, probs, cons) in sorted(weak.items(), key=lambda kv: kv[1][0]):
        lines.append(f"{b:#07x} {len(u.data):5d} {lvl:5}  {u.key}  unmasked={u.unmasked}")
    if near is not None:
        lines.append("")
        lines.append(f"# near matches (mnemonic similarity, hints only): {len(near)}")
        for u, best in sorted(near, key=lambda x: x[1][0][1]):
            lines.append(f"{u.key} ({len(u.data)} b): " +
                         ", ".join(f"{a:#x}={r:.2f}" for r, a in best))
    return "\n".join(lines)


def to_json(accepted, ext, ambiguous, weak, near):
    return {
        "matches": [{"addr": b, "level": lvl, "size": len(u.data), "lib": u.lib,
                     "module": u.mod.name, "name": u.name, "aliases": u.aliases,
                     "fixups": len(u.fixups), "notes": probs}
                    for u, (b, lvl, probs, cons) in sorted(accepted.items(), key=lambda kv: kv[1][0])],
        "ext": {n: {hex(a): sorted(set(w)) for a, w in addrs.items()} for n, addrs in ext.items()},
        "ambiguous": [{"unit": u.key, "addrs": a} for u, a in ambiguous.items()],
        "weak": [{"addr": b, "level": lvl, "size": len(u.data), "unit": u.key, "unmasked": u.unmasked}
                 for u, (b, lvl, probs, cons) in sorted(weak.items(), key=lambda kv: kv[1][0])],
        "near": [{"unit": u.key, "size": len(u.data), "best": best} for u, best in (near or [])],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=path("build", "clib", "libsig.json"))
    ap.add_argument("--near", action="store_true")
    ap.add_argument("-v", action="store_true")
    a = ap.parse_args()
    prog = analysis.run()
    m, units, hits = run_matching(prog)
    accepted, ext, ambiguous, weak = resolve(hits)
    near = near_matches(m, units, accepted) if a.near else None
    print(report(accepted, ext, ambiguous, weak, near, a.v))
    os.makedirs(os.path.dirname(a.json), exist_ok=True)
    with open(a.json, "w") as f:
        json.dump(to_json(accepted, ext, ambiguous, weak, near), f, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
