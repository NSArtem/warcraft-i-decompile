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

    # 5) Observing nothing (out_regs=(), watch=(), stubs=()) or zero-len watch -> rejected
    log_noop = tmp_path / "noop.jsonl"
    monkeypatch.setenv("WC1_T4_AUDIT_LOG", str(log_noop))
    t4spec.run_spec(
        "src/save_score/total_active_men.c", "TotalActiveMen_", 0x24e50,
        cases=[t4spec.T4Case()],
        watch=[(0x58e28, 0)],
        stubs=(),
        out_regs=(),
        extra={"_game_state": 0x59614},
    )
    ok_noop, reason_noop = t4spec.audit_t4_log(
        str(log_noop), ref_rel="src/save_score/total_active_men.c", orig_addr=0x24e50,
    )
    assert not ok_noop and "observed no" in reason_noop

    # 6) Overriding emu.call / emu.reg / emu.read raises CEmuError immediately (Must-Fix #1 & B)
    from wc1 import cemu
    from wc1.emu import Emu
    for attr in ("call", "reg", "read"):
        with pytest.raises(cemu.CEmuError, match="emu methods were overridden"):
            t4spec.run_spec(
                "src/save_score/total_active_men.c", "TotalActiveMen_", 0x24e50,
                cases=[t4spec.T4Case()],
                out_regs=("eax",),
                init_emu=lambda e, a=attr: setattr(e, a, lambda *args, **kw: 0),
                extra={"_game_state": 0x59614},
            )

    # 6b) Redirecting cm.publics to orig_addr raises CEmuError (Must-Fix A)
    emu_pub = Emu()
    cm_pub = cemu.load(emu_pub, "src/save_score/total_active_men.c", extra={"_game_state": 0x59614})
    cm_pub.publics["TotalActiveMen_"] = 0x24e50
    with pytest.raises(cemu.CEmuError, match="original image"):
        cemu.run_pair(emu_pub, 0x24e50, cm_pub, "TotalActiveMen_", out_regs=("eax",))

    # 6c) Forging cm.src to point at ref_rel while running different C fails sha256 audit (Must-Fix A)
    other_c = tmp_path / "other_total.c"
    other_c.write_text(open(path("src/save_score/total_active_men.c")).read() + "\n/* forged */\n")
    log_forge = tmp_path / "forge.jsonl"
    monkeypatch.setenv("WC1_T4_AUDIT_LOG", str(log_forge))
    monkeypatch.delenv("WC1_T4_AUDIT_NONCE", raising=False)
    emu_fg = Emu()
    cm_fg = cemu.load(emu_fg, str(other_c), extra={"_game_state": 0x59614})
    cm_fg.src = path("src/save_score/total_active_men.c")
    cemu.run_pair(emu_fg, 0x24e50, cm_fg, "TotalActiveMen_", out_regs=("eax",))
    ok_fg, reason_fg = t4spec.audit_t4_log(
        str(log_forge), ref_rel="src/save_score/total_active_men.c", orig_addr=0x24e50,
    )
    assert not ok_fg and "sha256" in reason_fg

    # 6d) Passing prebuilt mod= to CModule fails prebuilt audit (Must-Fix A)
    log_pb = tmp_path / "prebuilt.jsonl"
    monkeypatch.setenv("WC1_T4_AUDIT_LOG", str(log_pb))
    emu_pb = Emu()
    pre_mod = cemu.compile_module(str(other_c))
    cm_pb = cemu.CModule(emu_pb, "src/save_score/total_active_men.c",
                         extra={"_game_state": 0x59614}, mod=pre_mod)
    cemu.run_pair(emu_pb, 0x24e50, cm_pb, "TotalActiveMen_", out_regs=("eax",))
    ok_pb, reason_pb = t4spec.audit_t4_log(
        str(log_pb), ref_rel="src/save_score/total_active_men.c", orig_addr=0x24e50,
    )
    assert not ok_pb and "prebuilt" in reason_pb

    # 6e) Overriding cm.call under WC1_T4_AUDIT_LOG raises CEmuError (Must-Fix A)
    emu_cm = Emu()
    cm_ov = cemu.load(emu_cm, "src/save_score/total_active_men.c", extra={"_game_state": 0x59614})
    cm_ov.call = lambda *args, **kw: 0
    with pytest.raises(cemu.CEmuError, match="cmod was tampered"):
        cemu.run_pair(emu_cm, 0x24e50, cm_ov, "TotalActiveMen_", out_regs=("eax",))

    # 6f) Empty _c_ranges raises CEmuError (Must-Fix D)
    emu_er = Emu()
    cm_er = cemu.load(emu_er, "src/save_score/total_active_men.c", extra={"_game_state": 0x59614})
    cm_er._c_ranges = []
    with pytest.raises(cemu.CEmuError, match="outside placed C segments"):
        cemu.run_pair(emu_er, 0x24e50, cm_er, "TotalActiveMen_", out_regs=("eax",))

    # 6g) Stubbing the C entry point inside _c_ranges fails audit (Must-Fix D)
    log_cstub = tmp_path / "cstub.jsonl"
    monkeypatch.setenv("WC1_T4_AUDIT_LOG", str(log_cstub))
    emu_cs = Emu()
    cm_cs = cemu.load(emu_cs, "src/save_score/total_active_men.c", extra={"_game_state": 0x59614})
    emu_cs.write(0x58e28, struct.pack("<4H", 1, 2, 3, 4))
    emu_cs.stubs[cm_cs.fn("TotalActiveMen_")] = lambda e: 10
    assert cemu.run_pair(emu_cs, 0x24e50, cm_cs, "TotalActiveMen_", out_regs=("eax",)) == []
    ok_cs, reason_cs = t4spec.audit_t4_log(
        str(log_cstub), ref_rel="src/save_score/total_active_men.c", orig_addr=0x24e50,
    )
    assert not ok_cs and "compiled C segment range was stubbed" in reason_cs

    # 6h) Active emu.trace hook fails audit (Must-Fix D)
    log_tr = tmp_path / "trace.jsonl"
    monkeypatch.setenv("WC1_T4_AUDIT_LOG", str(log_tr))
    emu_tr = Emu()
    cm_tr = cemu.load(emu_tr, "src/save_score/total_active_men.c", extra={"_game_state": 0x59614})
    emu_tr.trace = lambda e, a, s: None
    cemu.run_pair(emu_tr, 0x24e50, cm_tr, "TotalActiveMen_", out_regs=("eax",))
    ok_tr, reason_tr = t4spec.audit_t4_log(
        str(log_tr), ref_rel="src/save_score/total_active_men.c", orig_addr=0x24e50,
    )
    assert not ok_tr and "emu.trace" in reason_tr

    # 6i) Forging _prebuilt/_src_sha256 or custom cflags fails out-of-process OMF digest check (Should-Fix E)
    alt_c = tmp_path / "alt_total.c"
    alt_c.write_text(
        "/* codegen-compiler: 10.0a */\n"
        "unsigned int TotalActiveMen(void) { return 10; }\n"
    )
    log_omf = tmp_path / "omf.jsonl"
    monkeypatch.setenv("WC1_T4_AUDIT_LOG", str(log_omf))
    emu_omf = Emu()
    cm_omf = cemu.load(emu_omf, str(alt_c))
    cm_omf.src = path("src/save_score/total_active_men.c")
    cm_omf._prebuilt = False
    import hashlib
    cm_omf._src_sha256 = hashlib.sha256(open(path("src/save_score/total_active_men.c"), "rb").read()).hexdigest()
    emu_omf.write(0x58e28, struct.pack("<4H", 1, 2, 3, 4))
    assert cemu.run_pair(emu_omf, 0x24e50, cm_omf, "TotalActiveMen_", out_regs=("eax",)) == []
    ok_omf, reason_omf = t4spec.audit_t4_log(
        str(log_omf), ref_rel="src/save_score/total_active_men.c", orig_addr=0x24e50,
    )
    assert not ok_omf and "OMF digest" in reason_omf

    # 7) Mid-loop exception swallowed (case 0 passes, case 1 raises RuntimeError) -> rejected by run_spec_done check (Must-Fix #2)
    log_mid = tmp_path / "mid.jsonl"
    monkeypatch.setenv("WC1_T4_AUDIT_LOG", str(log_mid))
    def boom_setup(e):
        raise RuntimeError("injected case 1 failure")
    try:
        t4spec.run_spec(
            "src/save_score/total_active_men.c", "TotalActiveMen_", 0x24e50,
            cases=[
                t4spec.T4Case(mem={0x58e28: struct.pack("<4H", 1, 2, 3, 4)}),
                t4spec.T4Case(setup=boom_setup),
            ],
            watch=[(0x58e28, 8)],
            out_regs=("eax",),
            extra={"_game_state": 0x59614},
        )
    except RuntimeError:
        pass
    ok_mid, reason_mid = t4spec.audit_t4_log(
        str(log_mid), ref_rel="src/save_score/total_active_men.c", orig_addr=0x24e50,
    )
    assert not ok_mid and "aborted mid-loop" in reason_mid

    # 8) Same-basename copy at different realpath & wrong func_name & wrong nonce -> all rejected (Must-Fix #4 & #5)
    fake_copy = tmp_path / "total_active_men.c"
    fake_copy.write_text(open(path("src/save_score/total_active_men.c")).read())
    log_nonce = tmp_path / "nonce.jsonl"
    monkeypatch.setenv("WC1_T4_AUDIT_LOG", str(log_nonce))
    monkeypatch.setenv("WC1_T4_AUDIT_NONCE", "secret-nonce-1")
    t4spec.run_spec(
        str(fake_copy), "TotalActiveMen_", 0x24e50,
        cases=[t4spec.T4Case(mem={0x58e28: struct.pack("<4H", 1, 2, 3, 4)})],
        watch=[(0x58e28, 8)],
        out_regs=("eax",),
        extra={"_game_state": 0x59614},
    )
    # Same basename but different realpath MUST fail
    ok_base, _ = t4spec.audit_t4_log(
        str(log_nonce), ref_rel="src/save_score/total_active_men.c",
        orig_addr=0x24e50, expected_nonce="secret-nonce-1",
    )
    assert not ok_base
    # Wrong func_name MUST fail
    ok_fn, _ = t4spec.audit_t4_log(
        str(log_nonce), ref_rel=str(fake_copy), orig_addr=0x24e50,
        func_name="WrongFunc_", expected_nonce="secret-nonce-1",
    )
    assert not ok_fn
    # Wrong nonce MUST fail
    ok_nn, _ = t4spec.audit_t4_log(
        str(log_nonce), ref_rel=str(fake_copy), orig_addr=0x24e50,
        func_name="TotalActiveMen_", expected_nonce="other-nonce",
    )
    assert not ok_nn
    # Exact match passes
    ok_exact, _ = t4spec.audit_t4_log(
        str(log_nonce), ref_rel=str(fake_copy), orig_addr=0x24e50,
        func_name="TotalActiveMen_", expected_nonce="secret-nonce-1",
    )
    assert ok_exact
