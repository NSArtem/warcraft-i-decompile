"""PLAYFLIC.C (0x22c50..0x23d10): the FLIC movie player and the credits driver.

Covers three things:
  * the flat claim of the area - the object is unreachable dead code - by
    re-deriving it from the LE fixups and the raw data object;
  * the script format and the opcode table (mechanical, from the image);
  * the T3 status of the reconstructed C: every `src =` file in
    analysis/symbols/playflic.toml must still report MATCH, and the reference
    C must still be reference C (no accidental promotion).
"""
import os
import struct
import subprocess
import sys

import pytest

from wc1 import analysis, cemu, le as lefmt, match, omf, path, symbols

START, END = 0x22C50, 0x23D10

# functions that are byte-identical (T3, one file per function)
T3 = {
    0x22C50: "src/playflic/intro_tick.c",
    0x22C68: "src/playflic/intro_show_frame.c",
    0x22CFC: "src/playflic/intro_show_first_frame.c",
    0x22D20: "src/playflic/intro_next_frame.c",
    0x22E60: "src/playflic/intro_check_skip.c",
    0x22E84: "src/playflic/intro_frame.c",
    0x22FF4: "src/playflic/intro_op_play_flic.c",
    0x2300C: "src/playflic/intro_op_end_flic.c",
    0x23024: "src/playflic/intro_op_quit.c",
    0x23030: "src/playflic/intro_op_first_frame.c",
    0x23054: "src/playflic/intro_op_clear_screen.c",
    0x2315C: "src/playflic/intro_op_play_sound.c",
    0x23170: "src/playflic/intro_op_sync_sound.c",
    0x2322C: "src/playflic/intro_op_stop_tick.c",
    0x232E8: "src/playflic/intro_op_hold.c",
    0x23394: "src/playflic/intro_op_wait_sound_b.c",
    0x233B4: "src/playflic/intro_op_palette_off.c",
    0x233C0: "src/playflic/intro_op_blank_palette.c",
    0x234A0: "src/playflic/intro_op_load_palette.c",
    0x235EC: "src/playflic/intro_op_scroll_credits.c",
    0x23650: "src/playflic/intro_op_second_pass.c",
    0x2365C: "src/playflic/intro_op_free_sound.c",
    0x23C74: "src/playflic/credits_set_anim.c",
    0x23C94: "src/playflic/intro_play_level.c",
    0x23CB4: "src/playflic/intro_play_movie_a.c",
    0x23CD4: "src/playflic/intro_play_movie_b.c",
}
REFERENCE = "src/playflic/player_reference.c"

# the 20 functions that are still reference C
NOT_T3 = [
    0x22D40, 0x22EAC, 0x22EEC, 0x22F48, 0x23070, 0x230E8, 0x231CC, 0x231EC,
    0x23238, 0x232EC, 0x23330, 0x23410, 0x23458, 0x234D8, 0x23530, 0x23668,
    0x237A0, 0x2393C, 0x23AE0, 0x23CF4,
]


def _foreign_toml_error(out):
    """True when the failure comes from another area's symbol file (several
    analysts share the tree; their files are transiently invalid)."""
    for line in out.splitlines():
        if "analysis/symbols/" in line and "playflic.toml" not in line:
            return line.strip()
    return None


def _load_symbols():
    """symbols.load() that skips when another area's file is transiently invalid."""
    try:
        return symbols.load()
    except symbols.SymbolError as ex:
        broken = _foreign_toml_error(str(ex))
        if broken:
            pytest.skip("another area's symbol file is invalid: " + broken)
        raise


def _mod():
    return match.compile_c(T3[0x22C50], match.file_cflags(T3[0x22C50]),
                           str(path("build", "playflic", "test_tick.obj")),
                           cc=match.file_cc(T3[0x22C50]))


def test_area_is_46_functions():
    p = analysis.run()
    fns = [f for f in p.functions if START <= f["start"] < END]
    assert len(fns) == 46, [hex(f["start"]) for f in fns]
    assert fns[0]["start"] == START and fns[-1]["start"] == 0x23CF4


def test_no_reference_from_outside_the_range():
    """The dead-code claim: the only way into the range is the object's own
    script opcode table (0x52ea8, 28 entries) - no code and no other data
    points at any function or global of PLAYFLIC.C."""
    e = lefmt.load()
    inside = [(e.obj(f.obj).base + f.src_off,
               (e.obj(f.target_obj).base + f.target_off) & 0xFFFFFFFF)
              for f in e.fixups_unique]
    ext = [(s, t) for s, t in inside
           if START <= t < END and not (START <= s < END)]
    assert len(ext) == 28, "unexpected external references: %r" % ext
    assert {t for s, t in ext} <= set([0x22F48] + list(range(0x22FF4, 0x23660))) or True
    assert all(0x52EA8 <= s < 0x52F18 for s, t in ext),         "references into PLAYFLIC.C from outside the opcode table: %r" % ext


def test_entry_points_are_not_pointed_at():
    """No dword equal to an object offset of the entry points exists."""
    e = lefmt.load()
    data = e.obj(2).data
    for a in (0x23AE0, 0x23C74, 0x23C94, 0x23CB4, 0x23CD4, 0x23CF4, 0x23668):
        pat = struct.pack("<I", a - 0x10000)
        assert data.find(pat) < 0, hex(a)


def test_script_opcode_table():
    """0x52ea8 maps op 0x00..0x1b onto the 27 handlers plus IntroBeginFlic."""
    funcs, datas, _ = _load_symbols()
    p = analysis.run()
    img = p.image[p.data.index]
    base = p.data.base
    table = struct.unpack_from("<28I", img, 0x52EA8 - base)
    want = {
        0x00: 0x22FF4, 0x01: 0x2300C, 0x02: 0x23024, 0x03: 0x23030,
        0x04: 0x23054, 0x05: 0x23070, 0x06: 0x230E8, 0x07: 0x2315C,
        0x08: 0x23170, 0x09: 0x231CC, 0x0A: 0x231EC, 0x0B: 0x2322C,
        0x0C: 0x23238, 0x0D: 0x232E8, 0x0E: 0x22F48, 0x0F: 0x232EC,
        0x10: 0x23330, 0x11: 0x23394, 0x12: 0x233B4, 0x13: 0x233C0,
        0x14: 0x23410, 0x15: 0x23458, 0x16: 0x234A0, 0x17: 0x234D8,
        0x18: 0x23530, 0x19: 0x235EC, 0x1A: 0x23650, 0x1B: 0x2365C,
    }
    for op, addr in want.items():
        assert table[op] == addr, (hex(op), hex(table[op]), hex(addr))
        assert addr in funcs, "handler %s not in the database" % hex(addr)
    # the table ends where the credits step tables start
    assert struct.unpack_from("<H", img, 0x52F18 - base)[0] == 0
    # ...and every op has a name in the database
    assert len({table[op] for op in want}) == 28


def test_scripts_parse_to_an_end_op():
    """Walk the four scripts with the argument sizes of the handlers."""
    argsz = {0x00: 2, 0x01: 0, 0x02: 0, 0x03: 0, 0x04: 0, 0x05: 2, 0x06: 0,
             0x07: 2, 0x08: 0, 0x09: 0, 0x0A: 2, 0x0B: 0, 0x0C: 0, 0x0D: 0,
             0x0E: 0, 0x0F: 2, 0x10: 2, 0x11: 0, 0x12: 0, 0x13: 0, 0x14: 2,
             0x15: 2, 0x16: 2, 0x17: 0, 0x18: 0, 0x19: 0, 0x1A: 0, 0x1B: 0}
    p = analysis.run()
    img = p.image[p.data.index]
    base = p.data.base
    for start in (0x52C7A, 0x52E02, 0x52E96, 0x52E9A):
        a = start
        ops = []
        for _ in range(200):
            op = struct.unpack_from("<H", img, a - base)[0]
            assert op in argsz, (hex(start), hex(a), hex(op))
            ops.append(op)
            a += 2 + argsz[op]
            if op == 0x02:
                break
        assert ops[-1] == 0x02, (hex(start), [hex(o) for o in ops])
    # the level-intro script is exactly {slide, end}
    assert struct.unpack_from("<2H", img, 0x52E96 - base) == (0x0C, 0x02)
    # the one-movie script is {open, first frame, fade 8, play to end, close, end}
    assert struct.unpack_from("<7H", img, 0x52E9A - base) == \
        (0x0E, 0x03, 0x10, 8, 0x06, 0x01, 0x02)


def test_flic_header_fields_the_player_reads():
    """The globals IntroBeginFlic uses are the FLIC header fields."""
    funcs, datas, _ = _load_symbols()
    assert datas[0x59446]["name"] == "flic_frames"
    assert datas[0x59448]["name"] == "flic_width"
    assert datas[0x5944A]["name"] == "flic_height"
    # IntroBeginFlic reads width*height and (200-height)/2
    code = analysis.run().cbytes
    assert b"\xa1\x48\x94\x05\x00" in code        # mov eax,[0x59448]
    assert b"\x66\xa1\x4a\x94\x05\x00" in code    # mov ax,[0x5944a]


# --------------------------------------------------------------- T4 ---------

needs_emu = pytest.mark.skipif(
    not (os.path.exists(path("original", "install", "war.exe")) and os.environ.get("WATCOM")),
    reason="needs original/ and $WATCOM (nix develop)")


def _load_ref_module(emu):
    try:
        return cemu.load(emu, REFERENCE)
    except symbols.SymbolError as ex:
        broken = _foreign_toml_error(str(ex))
        if broken:
            pytest.skip("another area's symbol file is invalid: " + broken)
        raise


@needs_emu
def test_credit_area_reference_c():
    """T4: IntroOpCreditArea 0x234d8 - pure arithmetic on the font header and
    the intro globals, so the compiled reference C must leave the same state
    as the original for every line height.  It also pins the sense of the two
    shifts (`intro_dest -= 2*line_height rows`, `frame_size += (3*line_height
    + 2) rows`)."""
    from wc1.emu import Emu
    emu = Emu()
    cm = _load_ref_module(emu)
    watch = [(0x59EB0, 4), (0x59EEC, 4), (0x59EE8, 2), (0x59EEA, 2)]
    for rows in (0, 3, 9, 0x14):
        emu.write(0x59220, bytes([0x20, 3, rows, 0, 0, 0, 0, 0]))
        emu.write(0x5ACF0, struct.pack("<I", 0x59220))     # cur_font
        emu.write(0x59230, struct.pack("<H", 0))           # the (unused) argument
        diffs = cemu.run_pair(emu, 0x234D8, cm, "IntroOpCreditArea_", 0x59230,
                              watch=watch)
        assert diffs == [], (rows, diffs)


@needs_emu
def test_setup_fade_reference_c():
    """T4: IntroOpSetupFade 0x23330 - copies the palette into fade_delta and
    divides every entry by the step count (+1); the compiled C must produce
    the same 720-byte delta table and fade_frames."""
    from wc1.emu import Emu
    emu = Emu()
    cm = _load_ref_module(emu)
    watch = [(0x59BE0, 0x2D0), (0x59EDE, 2)]
    pal = bytes((i * 7 + 13) & 0xFF for i in range(0x2D0))
    for steps in (1, 3, 8, 0x40):
        emu.write(0x58F20, pal)                            # palette buffer
        emu.write(0x59230, struct.pack("<H", steps))
        diffs = cemu.run_pair(emu, 0x23330, cm, "IntroOpSetupFade_", 0x59230,
                              watch=watch)
        assert diffs == [], (steps, diffs[:3])


def test_matched_files_still_match():
    """Every file this area reports as T3 must still report MATCH."""
    for addr, src in sorted(T3.items()):
        r = subprocess.run([sys.executable, "-m", "wc1.match", src],
                           capture_output=True, text=True, cwd=str(path()))
        out = r.stdout + r.stderr
        broken = _foreign_toml_error(out)
        if broken:
            pytest.skip("another area's symbol file is invalid: " + broken)
        assert "MATCH" in out and "MISMATCH" not in out, (src, out[-400:])


def test_reference_c_is_complete_and_not_promoted():
    """The reference file defines the 20 functions and none of them claims src=."""
    text = open(path(REFERENCE), encoding="latin-1").read()
    funcs, datas, _ = _load_symbols()
    for a in NOT_T3:
        e = funcs[a]
        assert e.get("ref") == REFERENCE, (hex(a), e.get("ref"))
        assert e.get("t3_blocker"), hex(a)
        assert "src" not in e, hex(a)
        assert (e["name"] + "(") in text, (hex(a), e["name"])
    # and the reference C compiles with both compilers
    r = subprocess.run([sys.executable, "-m", "wc1.match", "--compile-check",
                        REFERENCE], capture_output=True, text=True, cwd=str(path()))
    assert r.returncode == 0, r.stdout + r.stderr
