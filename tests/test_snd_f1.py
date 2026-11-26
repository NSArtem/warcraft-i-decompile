import os
import struct

import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case

pytestmark = pytest.mark.skipif(
    not (os.path.exists(path("original", "install", "war.exe")) and os.environ.get("WATCOM")),
    reason="needs original/ and $WATCOM",
)

SRC = path("src/snd")
ANIM_TABLE_GLOBAL = 0x53288
# Max word index: (0xfffe >> 1) + 0xff = 0x80fe -> 0x101fe bytes; allocate 0x10200.
TBL_WORDS = 0x8100
TBL_BYTES = TBL_WORDS * 2
OBJ_SIZE = 0x60


def _build_table_bytes():
    words = [((i * 0x137 + 0x29) & 0xFFFF) for i in range(TBL_WORDS)]
    # Header entries (byte offsets into anim_table, shifted right by 1 before indexing):
    # cover even, odd (exercises >> 1 truncation), zero, and near-max (0xfffe).
    offsets = {
        0: 0x0100,
        1: 0x0101,      # odd byte offset
        5: 0x0247,      # odd byte offset
        0x10: 0x0800,
        0x33: 0xFFFE,   # max even byte offset -> base word 0x7fff, + 0xff = 0x80fe
        0x34 + 0: 0x0120,
        0x34 + 1: 0x0121,
        0x34 + 5: 0x0355,
        0x34 + 0x10: 0x0900,
        0x34 + 0x20: 0xFFFE,
    }
    for idx, val in offsets.items():
        words[idx] = val
    return struct.pack(f"<{TBL_WORDS}H", *words)


TBL_DATA = _build_table_bytes()


def test_t3_files_match():
    t4spec.assert_t3_matches(SRC, ["anim_table_free.c", "anim_table_load.c"])


def test_ref_mismatch():
    t4spec.assert_ref_mismatch(SRC, ["bullet_start_anim_reference.c", "unit_start_anim_reference.c"])


def _run_anim_start_t4(ref_file, link_name, orig_addr, type_off, type_vals):
    cases = []
    watch = []
    state = {}

    def init_emu(emu):
        tbl = emu.alloc(TBL_BYTES, 16)
        obj = emu.alloc(OBJ_SIZE, 16)
        emu.write(tbl, TBL_DATA)
        state["tbl"] = tbl
        state["obj"] = obj
        watch.append((obj, OBJ_SIZE))
        for tv in type_vals:
            for anim in (0, 1, 0xFF, 0x100, 0x103, 0xFFFF, 0x12345678):
                def setup(e, tv=tv):
                    e.write(ANIM_TABLE_GLOBAL, struct.pack("<I", state["tbl"]))
                    e.write(state["obj"], b"\xAA" * OBJ_SIZE)
                    e.write(state["obj"] + type_off, bytes([tv]))
                cases.append(T4Case(args=(obj, anim), setup=setup, label=f"t{tv:#x}_a{anim:#x}"))

    t4spec.run_spec(
        os.path.join(SRC, ref_file),
        link_name,
        orig_addr,
        cases,
        watch=watch,
        out_regs=("ebx", "ecx", "esi", "edi"),
        init_emu=init_emu,
    )


def test_unit_start_anim():
    _run_anim_start_t4("unit_start_anim_reference.c", "UnitStartAnim_", 0x26360, 0x1B, (0, 1, 5, 0x10, 0x33))


def test_bullet_start_anim():
    _run_anim_start_t4(
        "bullet_start_anim_reference.c",
        "BulletStartAnim_",
        0x26390,
        0x00,
        (0, 1, 5, 0x10, 0x20),
    )
