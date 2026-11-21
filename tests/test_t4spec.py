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


def test_t4spec_rejects_empty_cases():
    with pytest.raises(AssertionError, match="0 test cases"):
        t4spec.run_spec(
            "src/save_score/total_active_men.c",
            "TotalActiveMen_",
            0x24e50,
            cases=(),
            out_regs=("eax",),
            extra={"_game_state": 0x59614},
        )


def test_t4spec_runtime_audit_records_and_catches_bypasses(tmp_path, monkeypatch):
    # 1) Genuine passing run passes audit_t4_log
    log_ok = tmp_path / "ok.jsonl"
    monkeypatch.setenv("WC1_T4_AUDIT_LOG", str(log_ok))
    t4spec.run_spec(
        "src/save_score/total_active_men.c",
        "TotalActiveMen_",
        0x24e50,
        cases=[t4spec.T4Case(mem={0x58e28: struct.pack("<4H", 1, 2, 3, 4)}, label="basic")],
        watch=[(0x58e28, 8)],
        out_regs=("eax",),
        extra={"_game_state": 0x59614},
    )
    ok, info = t4spec.audit_t4_log(
        str(log_ok), ref_rel="src/save_score/total_active_men.c", orig_addr=0x24e50,
    )
    assert ok and info["cases_run"] == 1, info
    # Wrong addr or wrong ref fails audit
    ok_addr, _ = t4spec.audit_t4_log(
        str(log_ok), ref_rel="src/save_score/total_active_men.c", orig_addr=0x99999,
    )
    assert not ok_addr
    ok_src, _ = t4spec.audit_t4_log(
        str(log_ok), ref_rel="src/save_score/other_reference.c", orig_addr=0x24e50,
    )
    assert not ok_src

    # 2) Swallowed AssertionError still leaves diffs_count > 0 in audit log -> rejected
    bad_c = tmp_path / "bad_total.c"
    bad_c.write_text(
        "/* codegen-compiler: 10.0a */\n"
        "unsigned int TotalActiveMen(void) { return 999; }\n"
    )
    log_bad = tmp_path / "bad.jsonl"
    monkeypatch.setenv("WC1_T4_AUDIT_LOG", str(log_bad))
    try:
        t4spec.run_spec(
            str(bad_c), "TotalActiveMen_", 0x24e50,
            cases=[t4spec.T4Case(mem={0x58e28: struct.pack("<II", 1, 2)})],
            out_regs=("eax",),
        )
    except AssertionError:
        pass
    ok_swallow, reason_swallow = t4spec.audit_t4_log(
        str(log_bad), ref_rel=str(bad_c), orig_addr=0x24e50,
    )
    assert not ok_swallow and "suppressed or inverted" in reason_swallow

    # 3) Stubbing orig_addr -> rejected
    log_stub = tmp_path / "stub.jsonl"
    monkeypatch.setenv("WC1_T4_AUDIT_LOG", str(log_stub))
    try:
        t4spec.run_spec(
            "src/save_score/total_active_men.c", "TotalActiveMen_", 0x24e50,
            cases=[t4spec.T4Case(mem={0x58e28: struct.pack("<4H", 0, 0, 0, 0)})],
            stubs=[t4spec.T4Stub(0x24e50, ret=0, log_regs=())],
            out_regs=("eax",),
            extra={"_game_state": 0x59614},
        )
    except AssertionError:
        pass
    ok_stub, reason_stub = t4spec.audit_t4_log(
        str(log_stub), ref_rel="src/save_score/total_active_men.c", orig_addr=0x24e50,
    )
    assert not ok_stub and "stubbed" in reason_stub

    # 4) Overwriting orig_addr code bytes -> rejected
    log_patch = tmp_path / "patch.jsonl"
    monkeypatch.setenv("WC1_T4_AUDIT_LOG", str(log_patch))
    try:
        t4spec.run_spec(
            "src/save_score/total_active_men.c", "TotalActiveMen_", 0x24e50,
            cases=[t4spec.T4Case(setup=lambda e: e.write(0x24e50, b"\x31\xc0\xc3"))],
            out_regs=("eax",),
            extra={"_game_state": 0x59614},
        )
    except AssertionError:
        pass
    ok_patch, reason_patch = t4spec.audit_t4_log(
        str(log_patch), ref_rel="src/save_score/total_active_men.c", orig_addr=0x24e50,
    )
    assert not ok_patch and "overwritten" in reason_patch

    # 5) Observing nothing (out_regs=(), watch=(), stubs=()) -> rejected
    log_noop = tmp_path / "noop.jsonl"
    monkeypatch.setenv("WC1_T4_AUDIT_LOG", str(log_noop))
    t4spec.run_spec(
        "src/save_score/total_active_men.c", "TotalActiveMen_", 0x24e50,
        cases=[t4spec.T4Case()],
        watch=(),
        stubs=(),
        out_regs=(),
        extra={"_game_state": 0x59614},
    )
    ok_noop, reason_noop = t4spec.audit_t4_log(
        str(log_noop), ref_rel="src/save_score/total_active_men.c", orig_addr=0x24e50,
    )
    assert not ok_noop and "observed no" in reason_noop
