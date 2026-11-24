"""Relocation diagnostics from synthetic OMF modules, without the game or compiler."""
from types import SimpleNamespace

from wc1 import match, omf


BASE = 0x10000


def compare(original, got, fixups, *, original_fixups=None, links=None, extent=None):
    program = SimpleNamespace(
        cbytes=bytes.fromhex(original), code=SimpleNamespace(base=BASE),
        fix_at={BASE + off: (None, addr) for off, addr in (original_fixups or {}).items()},
        functions=[{"start": BASE, "end": BASE + (extent or len(bytes.fromhex(original)))}],
    )
    data = bytearray.fromhex(got)
    mod = omf.Module(segments=[omf.Segment("_TEXT", "CODE", 1, len(data), data, fixups)],
                     publics={"test_": (1, 0)})
    by_link = {"test_": {"addr": BASE}, **{n: {"addr": a} for n, a in (links or {}).items()}}
    strict, = match.match_module(program, mod, by_link)
    return strict, match.diff_function(program, mod, by_link)


def test_unresolved_call_is_not_a_call_to_next_instruction():
    fixups = [omf.Fixup(1, 9, True, "ext", "callee_", 0)]
    strict, diff = compare("e8 00 01 00 00 c3", "e8 00 00 00 00 c3", fixups)
    assert strict[1] == "MISMATCH" and not diff["matched"]
    assert diff["score"] == (0, 0, 0, 0, 0)
    assert diff["unresolved"] == [
        {"symbol": "callee_", "offset": 1, "loc": 9, "self_relative": True,
         "addend": 0, "instruction_offset": 0, "operand": "imm", "original_candidate": BASE + 0x105}]
    assert diff["full_got"][0] == "+0000  call <unresolved callee_>"
    assert "[UNRESOLVED]" in diff["lines"][0]

    strict, diff = compare("e8 00 01 00 00 c3", "e8 00 00 00 00 c3", fixups,
                           links={"callee_": BASE + 0x105})
    assert strict[1] == "MATCH" and diff["matched"] and not diff["unresolved"]
    strict, diff = compare("e8 00 01 00 00 c3", "e8 00 00 00 00 c3", fixups,
                           links={"callee_": BASE + 0x125})
    assert strict[1] == "MISMATCH" and diff["counts"]["imm"] == 1 and not diff["unresolved"]


def test_unresolved_data_displacement_keeps_register_and_literal_differences():
    # mov [ebx + table + 4],0x99 vs mov [eax + table + 4],0x88.
    fixups = [omf.Fixup(2, 9, False, "ext", "_table", 4)]
    strict, diff = compare("c7 83 04 00 05 00 99 00 00 00 83 c0 22 c3",
                           "c7 80 00 00 00 00 88 00 00 00 83 c0 33 c3", fixups,
                           original_fixups={2: 0x50004})
    assert strict[1] == "MISMATCH" and diff["counts"]["reg"] == diff["counts"]["imm"] == 1
    assert diff["unresolved"][0]["original_candidate"] == 0x50000
    assert diff["unresolved"][0]["addend"] == 4
    assert "ebx + 0x50004], 0x99" in diff["first_diff"]
    assert "eax + <unresolved _table>], 0x88" in diff["first_diff"]
    assert "[IMM/REL]" in "\n".join(diff["lines"])

    strict, diff = compare("c7 83 04 00 05 00 99 00 00 00 c3",
                           "c7 83 00 00 00 00 99 00 00 00 c3", fixups,
                           original_fixups={2: 0x50004}, links={"_table": 0x50000})
    assert strict[1] == "MATCH" and diff["matched"] and not diff["unresolved"]


def test_two_unresolved_operands_and_real_opcode_difference():
    fixups = [omf.Fixup(2, 9, False, "ext", "_slot", 0),
              omf.Fixup(6, 9, False, "ext", "callback_", 0)]
    strict, diff = compare("c7 05 00 00 05 00 20 00 01 00 40 c3",
                           "c7 05 00 00 00 00 00 00 00 00 48 c3", fixups,
                           original_fixups={2: 0x50000, 6: 0x10020})
    assert strict[1] == "MISMATCH" and diff["score"] == (1, 0, 0, 0, 0)
    assert "inc eax" in diff["first_diff"] and "dec eax" in diff["first_diff"]
    assert "mov dword ptr [<unresolved _slot>], <unresolved callback_>" in diff["full_got"][0]


def test_unknown_relocation_does_not_mask_local_branch():
    fixups = [omf.Fixup(1, 9, True, "ext", "callee_", 0)]
    strict, diff = compare("e9 01 00 00 00 40 c3", "e9 00 00 00 00 40 c3", fixups)
    assert strict[1] == "MISMATCH" and diff["counts"]["op"] == 1
    assert "[OP/STRUCT]" in diff["first_diff"]


def test_unknown_relocation_is_not_discarded_as_alignment_filler():
    # lea eax,[eax+0] looks like filler until its displacement is linked.
    fixups = [omf.Fixup(3, 9, False, "ext", "_table", 0)]
    strict, diff = compare("c3 90 90 90 90 90 90", "c3 8d 80 00 00 00 00", fixups, extent=1)
    assert strict[1] == "MISMATCH" and not diff["matched"]
    assert [u["symbol"] for u in diff["unresolved"]] == ["_table"]
    assert "lea eax, [eax + <unresolved _table>]" in diff["full_got"][1]
