"""emit.replaced_interior_refs (the indexed check behind Emitter's
_check_replaced) gives exactly what the original per-range scan gave."""
from capstone import x86

from wc1 import analysis, emit


def _slow(p, ranges, entries):
    """The pre-index implementation, kept as the reference."""
    in_cut = lambda a: any(s <= a < e for s, e in ranges)
    errs = []
    for s, e in ranges:
        inside = lambda t: s < t < e and t not in entries
        for ia, i in p.insns.items():
            if s <= ia < e:
                continue
            if i.mnemonic in emit.REL_BRANCH and i.operands and i.operands[0].type == x86.X86_OP_IMM:
                if inside(i.operands[0].imm & 0xFFFFFFFF):
                    errs.append(f"{ia:#x} branches into the interior of replaced {s:#x}")
        for src, (f, t) in p.fix_at.items():
            if not in_cut(src) and inside(t):
                errs.append(f"{src:#x} references the interior of replaced {s:#x} ({t:#x})")
    return errs


def test_indexed_check_equals_the_scan():
    p = analysis.run()
    fs = sorted(p.functions, key=lambda f: f["start"])
    entries = {f["start"] for f in fs}
    # the reference scan costs ranges x instructions: keep the sets small
    cases = [
        [],
        sorted((f["start"], f["limit"]) for f in fs[::97]),           # disjoint
        sorted([(f["start"], f["limit"]) for f in fs[::200]] * 2),    # duplicates: overlap path
    ]
    # ranges whose interior is entered from outside: the shared epilogues of
    # the intro ops (docs/subsystems/playflic.md)
    tails = sorted((f["start"], f["limit"]) for f in fs if 0x23100 <= f["start"] < 0x23200)
    assert tails
    cases.append(tails)
    for ranges in cases:
        for ent in (entries, set()):
            assert emit.replaced_interior_refs(p, ranges, ent) == _slow(p, ranges, ent)
    assert emit.replaced_interior_refs(p, tails, set())
