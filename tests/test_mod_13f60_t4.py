import struct

import pytest

from wc1 import t4spec, cemu, path

try:
    from wc1.t4spec import T4Stub, T4Case, run_spec
    _ok = True
except Exception:
    _ok = False

pytestmark = pytest.mark.skipif(not _ok, reason="t4spec unavailable")

SRC_CK = path("src", "mod_13f60", "save_file_checksum_reference.c")
SRC_SP = path("src", "mod_13f60", "save_slot_path.c")

FILE_SEEK = 0x31A80
FILE_READ = 0x31ADC
SPRINTF = 0x31BE2
MAKEPATH = 0x31C24

DAT_516AE = 0x516AE
GAME_START_MODE = 0x593D4


def _read_stub_factory(chunks):
    state = {"i": 0}

    def fn(e, log):
        log(e.reg("edx"), e.reg("ebx"), e.reg("ecx"))
        i = state["i"]
        state["i"] += 1
        data = chunks[i] if i < len(chunks) else b""
        n = len(data) // 4
        if n:
            e.write(e.reg("eax"), data)
        return n
    return fn, state


def _checksum_case(chunks, label):
    def setup(emu):
        pass
    return T4Case(args=(0x1234,), setup=setup, label=label)


@pytest.mark.parametrize("chunks", [
    [],
    [struct.pack("<3I", 1, 2, 3)],
    [struct.pack("<50I", *range(50)), struct.pack("<2I", 0xFFFFFFFF, 0x80000000)],
    [struct.pack("<I", 0x7FFFFFFF)],
])
def test_save_file_checksum(chunks):
    # per-run stateful stub: the original and compiled run each need fresh state
    fn, state = _read_stub_factory(chunks)

    def wrapped(e, log):
        return fn(e, log)

    def setup(emu):
        state["i"] = 0
    # reset state between original and compiled runs via seek stub (called first)

    def seek(e, log):
        log(e.reg("eax"), e.reg("edx"), e.reg("ebx"))
        state["i"] = 0
        return 0
    run_spec(SRC_CK, "SaveFileChecksum_", 0x14670,
             [T4Case(args=(0x1234,), label="chunks")],
             stubs=[T4Stub(FILE_SEEK, fn=seek, log_regs=("eax", "edx", "ebx")),
                    T4Stub(FILE_READ, fn=wrapped,
                           log_regs=("edx", "ebx", "ecx"))])


def _sp_case(label, mode, d516, slot):
    def setup(emu):
        emu.write(DAT_516AE, struct.pack("<H", d516))
        emu.write(GAME_START_MODE, struct.pack("<H", mode))
    return T4Case(args=(0x850000, slot), setup=setup, label=label)


def test_save_slot_path():
    def sprintf_fn(e, log):
        sp = e.reg("esp")
        dst = e.u32(sp + 4)
        fmt = e.cstr(e.u32(sp + 8), 64)
        arg = e.u32(sp + 12)
        s = (fmt.decode("ascii") % arg).encode("ascii") + b"\x00"
        e.write(dst, s)
        return len(s) - 1

    def makepath_fn(e, log):
        # _makepath(path=eax, drive=edx, dir=ebx, fname=ecx, ext=[esp+4])
        dst = e.reg("eax")
        ext = e.cstr(e.u32(e.reg("esp") + 4), 64)
        fname = e.cstr(e.reg("ecx"), 64)
        s = fname + b"." + ext + b"\x00"
        e.write(dst, s)
        return 0

    cases = [
        _sp_case("sav0", 0, 0, 0),
        _sp_case("net_flag", 0, 1, 3),
        _sp_case("net_mode", 2, 0, 7),
        _sp_case("mode1", 1, 0, 0xFFFF),
    ]
    run_spec(SRC_SP, "SaveSlotPath_", 0x14740, cases, out_regs=(),
             watch=[(0x850000, 64)],
             stubs=[T4Stub(SPRINTF, fn=sprintf_fn),
                    T4Stub(MAKEPATH, fn=makepath_fn, stack_pop=4)])
