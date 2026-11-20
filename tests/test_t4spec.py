"""Tests for wc1.t4spec (declarative T4 differential test harness)."""
import os
import struct

import pytest

from wc1 import path, t4spec

pytestmark = pytest.mark.skipif(
    not (os.path.exists(path("original", "install", "war.exe")) and os.environ.get("WATCOM")),
    reason="needs original/ and $WATCOM (nix develop)")


def test_t4spec_passes_existing_reference_function():
    # TotalActiveMen (0x24e50) sums four 16-bit player counts at 0x58e28
    def make_case(rng):
        vals = [rng.randint(0, 500) for _ in range(4)]
        return t4spec.T4Case(mem={0x58e28: struct.pack("<4H", *vals)})

    t4spec.run_spec(
        "src/save_score/total_active_men.c",
        "TotalActiveMen_",
        0x24e50,
        cases=[
            t4spec.T4Case(mem={0x58e28: struct.pack("<4H", 0, 0, 0, 0)}, label="zero"),
            t4spec.T4Case(mem={0x58e28: struct.pack("<4H", 1, 2, 3, 4)}, label="basic"),
        ],
        watch=[(0x58e28, 8)],
        out_regs=("eax",),
        extra={"_game_state": 0x59614},
        rand_cases=10,
        rand_gen=make_case,
    )


def test_t4spec_detects_bug_in_compiled_c(tmp_path):
    bad_c = tmp_path / "bad_total.c"
    bad_c.write_text(
        "/* codegen-compiler: 10.0a */\n"
        "extern unsigned int men_count[2];\n"
        "unsigned int TotalActiveMen(void) { return 999; }\n"
    )
    with pytest.raises(AssertionError):
        t4spec.run_spec(
            str(bad_c),
            "TotalActiveMen_",
            0x24e50,
            cases=[t4spec.T4Case(mem={0x58e28: struct.pack("<II", 1, 2)}, label="mismatch")],
            watch=[(0x58e28, 8)],
            out_regs=("eax",),
        )


def test_t4spec_stub_call_log_verification():
    # SndEvent (0x1b800) with stubbed SndPlay (0x26958) and MsgStrip (0x19edc)
    t4spec.run_spec(
        "src/mod_1b800/snd_event_reference.c",
        "SndEvent_",
        0x1b800,
        cases=[
            t4spec.T4Case(args=(0, 0), label="zero_id"),
            t4spec.T4Case(args=(1, 0), mem={0x532bc: struct.pack("<I", 1)}, label="sfx_on_no_unit"),
        ],
        watch=[(0x532bc, 4), (0x59680, 16)],
        stubs=[
            t4spec.T4Stub(0x26958, ret=0, log_regs=("eax",)),
            t4spec.T4Stub(0x19edc, ret=0, log_regs=("eax", "ebx")),
        ],
        out_regs=(),
    )
