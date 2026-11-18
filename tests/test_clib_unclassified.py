"""Guard for the 2026-11-19 triage of the last unclassified runtime functions
(docs/subsystems/clib.md, section "Unclassified runtime triage 2026-11-19").

`python3 -m wc1.progress` used to report 28 runtime-kind functions as "not yet
classified".  Twelve are Watcom 10.0a library code and were added to
analysis/symbols/clib.toml; the rest are Blizzard/AIL code and stay in scope
(their evidence is pinned here so a later re-classification cannot silently
drop it).

Two kinds of checks:

* every new `libsig:` claim is re-compared with the 10.0a library unit it
  names (same rule as tests/test_clib_libsig.py: byte level, relocation fields
  resolved);
* the semantic facts used for the entries without a full-unit libsig claim
  (the 1-byte stubs, the sigsy slice) and for the code left in scope are
  asserted against the original: callers, data initialisers, module layout and
  the strings/arguments the functions use.

The 10.0a library tests skip when original/watcom/10.0a/lib386 is absent
(optional part of `make toolchain`).
"""
import os

import pytest
from capstone import x86

from wc1 import analysis, clib_sig, oldcc, path, symbols

HAVE_ORIGINAL = os.path.exists(path("original", "install", "war.exe"))
pytestmark = pytest.mark.skipif(not HAVE_ORIGINAL,
                                reason="original files not extracted")

# (address, library module, unit name, level) - the new clib.toml `libsig:` claims
LIBSIG = [
    (0x30ddb, "strtol", "strtol_", "bytes"),
    (0x33b5b, "rand", "initrandnext_", "bytes"),
    (0x3b8e9, "clock", "__clock_init_", "bytes"),
    (0x3d469, "gtpid", "getpid_", "bytes"),
    (0x40918, "stk386", "__GRO", "bytes"),
    (0x420b8, "chk8087", "_fpreset_", "bytes"),
]

# the 12 entries this triage added to clib.toml (address -> name)
NEW_ENTRIES = {
    0x30ddb: "strtol",
    0x33b5b: "initrandnext",
    0x3b438: "__null_int23_exit_",
    0x3b8e9: "__clock_init",
    0x3d469: "getpid",
    0x3dbbf: "__restore_int_ctrl_break_body",
    0x3dfda: "__null_FPE_rtn",
    0x40900: "_init_stk",
    0x40918: "__GRO",
    0x410f6: "tryOSTimeZone",
    0x420b8: "_fpreset",
    0x42102: "_do_nothing",
}


@pytest.fixture(scope="module")
def prog():
    return analysis.run()


@pytest.fixture(scope="module")
def db():
    funcs, datas, errors = symbols.load(strict=False)
    assert not errors, errors
    return funcs, datas


@pytest.fixture(scope="module")
def modules():
    root = oldcc.root()
    bad = oldcc.check(root, optional=True)
    if bad:
        pytest.skip(f"Watcom 10.0a runtime libraries not installed in {root}: {bad[0]}")
    return clib_sig.load_modules(root)


def _unit(modules, module, name):
    for lib, mod in modules:
        if mod.name != module:
            continue
        for u in clib_sig.code_units(lib, mod):
            if name in u.names:
                return u
    raise AssertionError(f"clib3r.lib({module}) has no unit {name!r}")


def _bymodule(modules, name):
    hits = [mod for _, mod in modules if mod.name == name]
    assert hits, f"library module {name} not found"
    return hits[0]


def _branches(p, target, kinds=None):
    """[(insn address, mnemonic)] of every direct branch/call to target."""
    kinds = kinds or (analysis.COND_JUMPS | {"jmp", "call"})
    out = []
    for a, i in p.insns.items():
        if i.mnemonic in kinds and i.operands and i.operands[0].type == x86.X86_OP_IMM \
                and (i.operands[0].imm & 0xFFFFFFFF) == target:
            out.append((a, i.mnemonic))
    return sorted(out)


def _callers(p, target):
    return [a for a, m in _branches(p, target, {"call"})]


def _refs(p, start, limit):
    return sorted({t for s, (f, t) in p.fix_at.items() if start <= s < limit})


def _extent(p, start):
    f = next((f for f in p.functions if f["start"] == start), None)
    assert f is not None, f"{start:#x} is not a discovered function"
    return f["limit"]


def _cstr(p, addr, n=160):
    d = p.data
    b = bytes(d.data[addr - d.base:addr - d.base + n])
    return b.split(b"\0")[0]


def _imm(p, addr, op=0):
    i = p.insn_at(addr)
    assert i is not None, f"no instruction at {addr:#x}"
    return i.operands[op].imm & 0xFFFFFFFF


# --------------------------------------------------------------- libsig ----

def test_new_entries_present(db):
    funcs, _ = db
    for addr, name in NEW_ENTRIES.items():
        assert addr in funcs, f"clib.toml entry missing at {addr:#x}"
        e = funcs[addr]
        assert e["_file"].replace("\\", "/").endswith("clib.toml"), e["_file"]
        assert e["name"] == name, (addr, e["name"])
        assert e["confidence"] in ("verified", "high")


@pytest.mark.parametrize("addr,module,unit,level", LIBSIG,
                         ids=[f"{a:#x}-{u}" for a, m, u, l in LIBSIG])
def test_libsig_new_entry(prog, modules, addr, module, unit, level):
    u = _unit(modules, module, unit)
    m = clib_sig.Matcher(prog)
    if level == "bytes":
        ok, why, _ = m.check_bytes(u, addr)
    else:
        ok, why, _ = m.check_insn(u, addr)
    assert ok, f"{addr:#x} vs clib3r.lib({module}) {unit}: {why}"


def test_strtol_is_the_signed_core_entry(prog):
    o = 0x30ddb - prog.code.base
    assert prog.cbytes[o:o + 8] == bytes.fromhex("51b901000000ebf1")
    i = prog.insn_at(0x30de1)
    assert i.mnemonic == "jmp" and (i.operands[0].imm & 0xFFFFFFFF) == 0x30dd4
    # strtoul 0x30dd1 reaches the same call with ecx=0
    assert prog.cbytes[0x30dd1 - prog.code.base:0x30dd4 - prog.code.base] == bytes.fromhex("5131c9")


def test_initrandnext_returns_the_seed_address(prog, db):
    funcs, datas = db
    assert prog.fix_at[0x33b5c][1] == 0x555c0
    assert datas[0x555c0]["name"] == "_RWD_seed"
    # rand uses the returned pointer: imul edx, dword [eax], 0x41c64e6d
    i = prog.insn_at(0x33b6b)
    assert i.mnemonic == "imul" and "[eax]" in i.op_str


def test_initrandnext_library_layout(modules):
    mod = _bymodule(modules, "rand")
    units = {u.name: u for u in clib_sig.code_units("clib3r", mod)}
    assert (units["initrandnext_"].off, units["rand_"].off, units["srand_"].off) == (0, 6, 0x2a)
    # initrandnext_ names the module-local static seed `_next`; rand_ calls it
    assert {f.target for f in units["initrandnext_"].fixups if f.target_kind == "ext"} == {"_next"}
    assert "initrandnext_" in {f.target for f in units["rand_"].fixups if f.target_kind == "ext"}


def test_clock_init_registered_as_an_init_routine(prog):
    assert prog.fix_at[0x3b8ef][1] == 0x62d70        # _clock_start
    assert prog.fix_at[0x5850e][1] == 0x3b8e9        # init table entry -> __clock_init
    i = prog.insn_at(0x3b8e9)
    assert i.mnemonic == "call" and (i.operands[0].imm & 0xFFFFFFFF) == 0x3b88e  # clock_value


def test_getpid_reads_the_psp_selector(prog, db):
    funcs, datas = db
    assert prog.fix_at[0x3d46a][1] == 0x56614
    assert datas[0x56614]["name"] == "_psp"
    assert _callers(prog, 0x3d469) == [0x338df]      # __MkTmpFile


def test_init_stk_unit_is_byte_identical(prog, modules):
    # 0x40900 is <_TEXT+0>, the anonymous first unit of clib3r.lib(stk386):
    # 8 bytes, one segment relocation.  The 10.0a OMF has no symbol for it, so
    # the clib.toml entry is high (source name) rather than libsig-verified.
    u = _unit(modules, "stk386", "<_TEXT+0>")
    ok, why, _ = clib_sig.Matcher(prog).check_bytes(u, 0x40900)
    assert ok, why


def test_init_stk_saves_ss_at_the_stk386_data_word(prog, modules, db):
    funcs, datas = db
    assert prog.fix_at[0x40903][1] == 0x566c4
    assert prog.fix_at[0x58526][1] == 0x40900        # init table entry
    assert bytes(prog.data.data[0x566c4 - prog.data.base:0x566c4 - prog.data.base + 20]) \
        == b"\x00\x00Stack Overflow!\r\n\x00"
    mod = _bymodule(modules, "stk386")
    # the library has no public symbol before __CHK at +8 (the anonymous unit)
    assert mod.publics["__CHK"] == (1, 8)
    assert mod.publics["__GRO"] == (1, 0x18)
    assert mod.publics["__STK"] == (1, 0x1b)


def test_gro_sits_between_chk_and_stk(prog, db):
    funcs, _ = db
    assert prog.cbytes[0x40918 - prog.code.base:0x4091b - prog.code.base] == b"\xc2\x04\x00"
    assert funcs[0x40908]["name"] == "__CHK"
    assert funcs[0x4091b]["name"] == "__STK"


def test_do_nothing_is_the_default_save_restore_stub(prog, modules):
    war = {0x569c8, 0x569cc}
    assert {prog.fix_at[a][1] for a in war} == {0x42102}
    mod = _bymodule(modules, "save8087")
    for sym, off in (("___Save8087", 0), ("___Rest8087", 4)):
        si, o = mod.publics[sym]
        assert (si, o) == (4, off)
        fx = [f for f in mod.segments[si - 1].fixups if f.offset == o]
        assert fx and fx[0].target == "_do_nothing_", sym


def test_null_fpe_rtn_is_the_default_fpe_handler(prog, modules):
    assert prog.fix_at[0x56641][1] == 0x3dfda       # __FPE_handler initial value
    mod = _bymodule(modules, "crwd386")
    si, o = mod.publics["__FPE_handler"]
    fx = [f for f in mod.segments[si - 1].fixups if f.offset == o]
    # initialised to this module's own code segment, offset 0 = __null_FPE_rtn
    assert fx and fx[0].target_kind == "seg" and fx[0].target == 1
    units = {u.name: u for u in clib_sig.code_units("clib3r", mod)}
    assert units["__null_FPE_rtn"].off == 0


def test_null_int23_exit_is_the_exit_hook_initialiser(prog, modules):
    assert {prog.fix_at[a][1] for a in (0x56518, 0x5651c, 0x56520)} == {0x3b438}
    mod = _bymodule(modules, "exit")
    units = {u.name: u for u in clib_sig.code_units("clib3r", mod)}
    assert (units["__null_int23_exit_"].off, units["exit_"].off, units["_exit_"].off) \
        == (0, 1, 0x19)
    seg, off = mod.publics["___int23_exit"]
    fx = [f for f in mod.segments[seg - 1].fixups if f.offset == off]
    assert fx and fx[0].target == "__null_int23_exit_"


def test_tryostimezone_is_the_stub_before_tzset(prog, modules):
    assert prog.cbytes[0x410f6 - prog.code.base] == 0xC3
    mod = _bymodule(modules, "tzset")
    units = {u.name: (u.off, u.end - u.off) for u in clib_sig.code_units("clib3r", mod)}
    assert units["tryOSTimeZone_"] == (0, 1)
    assert units["tzset_"] == (1, 19)
    # the 10.0a tzset_ does not call the stub (it uses getenv_ + __parse_tz_)
    assert _callers(prog, 0x410f6) == []
    assert _imm(prog, 0x410f7, 1) == 0x583A0            # getenv(TZ string)


def test_fpreset_reads_the_x87_flag(prog):
    assert prog.fix_at[0x420ba][1] == 0x569bd        # __real87
    i = prog.insn_at(0x420bf)                        # jne __init_8087_
    assert i.mnemonic == "jne" and (i.operands[0].imm & 0xFFFFFFFF) == 0x42087


def test_sigsy_ctrl_break_body_is_a_slice_of_restore_int23(prog, modules):
    unit = _unit(modules, "sigsy", "__restore_int23_")
    assert clib_sig.Matcher(prog).check_bytes(unit, 0x3dacd)[0]
    off = 0x3dbbf - 0x3dacd
    body = _unit(modules, "sigsy", "__restore_int_")
    assert body.off == unit.end                       # next unit starts at +0x1af
    o = 0x3dbbf - prog.code.base
    for k in range(0x3dc7c - 0x3dbbf):
        j = off + k
        if not unit.mask[j]:
            assert unit.data[j] == prog.cbytes[o + k], f"slice byte +{k:#x}"
            assert (0x3dbbf + k) not in prog.fix_at
    # entered by a conditional jump from __restore_int_ctrl_break, not a call
    assert _branches(prog, 0x3dbbf) == [(0x3dca4, "jne")]


# ------------------------------------------------- Blizzard code in scope ----

def test_criterr_region_markers(prog):
    # CritErrInstall locks [0x336e4, 0x3374c] and installs the handler 0x336fc
    assert prog.fix_at[0x3379d][1] == 0x336e4
    assert prog.fix_at[0x337a2][1] == 0x3374c
    assert prog.fix_at[0x337aa][1] == 0x336e4
    assert _callers(prog, 0x312f0).count(0x337ae) == 1        # DpmiLockRegion
    assert _imm(prog, 0x337b5, 1) == 0x336fc                     # _harderr handler
    assert _callers(prog, 0x336e4) == [] and _callers(prog, 0x3374c) == []


def test_criterr_prompt_init_draws_the_disk_error_dialog(prog, db):
    funcs, datas = db
    assert _callers(prog, 0x337d0) == [0x1dc55]
    callees = {i.operands[0].imm & 0xFFFFFFFF for a, i in prog.insns.items()
               if 0x337d0 <= a < _extent(prog, 0x337d0) and i.mnemonic == "call"}
    assert {0x33764, 0x3d040, 0x3d190, 0x3d2b0} <= callees
    assert _cstr(prog, 0x57ec4) == b"A disk error has occurred..."
    # the item list drawn by 0x3d2b0: two 0x14-byte entries, Abort / Retry
    assert prog.fix_at[0x55560][1] == 0x57ec4
    assert prog.fix_at[0x55584][1] == 0x57ee4 and _cstr(prog, 0x57ee4) == b"@1A@2bort"
    assert prog.fix_at[0x55598][1] == 0x57ef0 and _cstr(prog, 0x57ef0) == b"@1R@2etry"


def test_draw_text_item_list(prog):
    assert _callers(prog, 0x3d2b0) == [0x3387b]
    refs = _refs(prog, 0x3d2b0, _extent(prog, 0x3d2b0))
    assert {0x55444, 0x5ACF0} <= set(refs)          # default_font / cur_font


def test_palette_fade_setup(prog, db):
    funcs, datas = db
    assert _callers(prog, 0x339d0) == []
    assert _refs(prog, 0x339d0, _extent(prog, 0x339d0)) == [0x5AD60, 0x5B060, 0x62570]
    assert [datas[a]["name"] for a in (0x5AD60, 0x5B060, 0x62570)] == \
        ["palette_base", "palette_cur", "palette_target"]


def test_vid_reset_layers_and_dirty_rect(prog, db):
    funcs, datas = db
    assert _callers(prog, 0x3b3a0) == [0x30be0]      # video-init wrapper 0x30bd0
    refs = set(_refs(prog, 0x3b3a0, _extent(prog, 0x3b3a0)))
    assert 0x5AA90 in refs                            # 32 screen layers (32*18 bytes)
    assert {0x5ACD0, 0x5ACD2, 0x5ACD4, 0x5ACD6, 0x5ACD8, 0x5ACDA} <= refs
    assert prog.fix_at[0x3b3e5][1] == 0x5AA90
    assert _imm(prog, 0x3b3dd, 1) == 0x240               # memset(layers, 0, 0x240)


def test_bevel_panel_drawers(prog, db):
    funcs, datas = db
    assert {0x33804, 0x3383E} <= set(_callers(prog, 0x3d040))
    assert _callers(prog, 0x3d190) == [0x33821]
    for a in (0x3D040, 0x3D190):
        assert {0x5AD30, 0x62880} <= set(_refs(prog, a, _extent(prog, a)))


def test_resource_header_body_wrappers(prog):
    assert _callers(prog, 0x34350) == [0x1DB13, 0x1DC72]
    callees = {i.operands[0].imm & 0xFFFFFFFF for a, i in prog.insns.items()
               if 0x34350 <= a < _extent(prog, 0x34350) and i.mnemonic == "call"}
    assert callees == {0x32740}                       # ResourceRead


def test_dpmi_free_memory_query(prog):
    assert _callers(prog, 0x34060) == [0x1DA39]
    assert _imm(prog, 0x34071, 1) == 0x500               # DPMI 0500h buffer
    assert prog.insn_at(0x3409d).mnemonic == "shl" and _imm(prog, 0x3409d, 1) == 2
    assert (prog.insn_at(0x34095).operands[0].imm & 0xFFFFFFFF) == 0x30E7F  # int386x_
    # main init compares the result with 0x540 KB and prints "%uKB of memory"
    i = prog.insn_at(0x1DA40)
    assert i.mnemonic == "cmp" and (i.operands[1].imm & 0xFFFFFFFF) == 0x540
    for s in (0x56E48, 0x56EBC):
        assert b"additional %uKB of memory" in _cstr(prog, s)


def test_ail_digital_audio_helpers_stay_third_party(prog):
    # every caller is inside the Miles AIL code; no Blizzard caller
    expected = {
        0x3FE34: [0x392DD],
        0x4002A: [0x39322, 0x3947E, 0x39489, 0x39828, 0x39833, 0x39FD8, 0x39FE3],
        0x40088: [0x392A2, 0x39473, 0x3981D, 0x39FCD],
        0x400B4: [0x38EFC],
    }
    for a, callers in expected.items():
        assert _callers(prog, a) == callers, hex(a)
        assert all(0x34D83 <= c < 0x3AAC0 for c in callers), hex(a)
    # the conversion dispatch table and the lock-range end marker
    assert set(_refs(prog, 0x4002A, _extent(prog, 0x4002A))) == {0x3E0B4, 0x56648}
    assert prog.fix_at[0x400CC][1] == 0x400B4
    assert {0x3E0B4, 0x56648, 0x56668} <= set(_refs(prog, 0x400B4, _extent(prog, 0x400B4)))
