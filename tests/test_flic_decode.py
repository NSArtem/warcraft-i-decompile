import os
import struct

import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case, T4Stub

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = path('src/flic_decode')

FLAG = 0x517c8
HDR = 0x59440
W = lambda v: struct.pack("<H", v & 0xFFFF)
D = lambda v: struct.pack("<I", v & 0xFFFFFFFF)

WATCH_STATE = [(0x594d0, 0x18), (0x59440, 0x1c), (0x594ea, 2), (FLAG, 2),
               (0x59490, 8)]


def _addr(*names):
    by = t4spec.by_link_lenient()
    for n in names:
        if n in by:
            return by[n]["addr"]
    pytest.skip("symbol not in DB: %s" % (names,))


def test_t3_files():
    files = ['flic_palette_off.c']
    if files:
        t4spec.assert_t3_matches(SRC, files)


def test_ref_files_still_mismatch():
    files = ['flic_close_reference.c', 'flic_next_frame_reference.c',
             'flic_open_reference.c', 'flic_restart_reference.c',
             'flic_rewind_reference.c']
    if files:
        t4spec.assert_ref_mismatch(SRC, files)


def _hdr(magic=0xaf12, w5c=8, w5e=3, w54=0):
    m = {HDR + 4: W(magic), HDR + 0xc: W(w5c), HDR + 0xe: W(w5e),
         HDR + 0x14: W(w54)}
    return m


def _open_case(label, found, read_ok, flag0=0, **kw):
    mem = _hdr(**kw)
    mem[FLAG] = W(flag0)
    mem[0x594ea] = W(0)
    mem[0x59446] = W(0x77)
    return T4Case(args=(0x61000, 0x62000, 0x63000, 5),
                  stack_args=(9,), mem=mem, label=label,
                  regs_in=None)


def test_flic_open():
    fd = _addr("FindDataFile_", "_FindDataFile")
    cases = []
    for found in (0, 0x1234):
        for rd in (0, 1):
            for kw in ({}, {"magic": 0x1234}, {"w5c": 7}, {"w5e": 2},
                       {"w54": 1}):
                cases.append(_open_case("f%x r%d %s" % (found, rd, kw),
                                        found, rd, **kw))
    # stubs are per-run constants, so run each combination separately
    for found in (0, 0x1234):
        for rd in (0, 1, 0x20):
            sub = [c for c in cases if c.label.startswith("f%x r%d" % (found, min(rd, 1)))]
            t4spec.run_spec(
                path('src/flic_decode/flic_open_reference.c'), "FlicOpen_",
                0x1933c, sub, watch=WATCH_STATE,
                stubs=[T4Stub(fd, ret=found, log_regs=("eax",)),
                       T4Stub(0x19020, ret=rd, log_regs=("eax", "edx"))],
                out_regs=("eax",))


def test_flic_close():
    fc = _addr("FileClose_", "_FileClose")
    cases = [T4Case(mem={FLAG: W(v), 0x594e0: D(0x4444)}, label="flag%d" % v)
             for v in (0, 1, 0x100)]
    t4spec.run_spec(
        path('src/flic_decode/flic_close_reference.c'), "FlicClose_", 0x193dc,
        cases, watch=[(FLAG, 2), (0x594e0, 4)],
        stubs=[T4Stub(fc, ret=0, log_regs=("eax",))], out_regs=())


def _seek_cases(off_addr):
    return [T4Case(mem={FLAG: W(v), off_addr: D(o)}, label="f%d o%x" % (v, o))
            for v in (0, 1) for o in (0, 0x80, 0x12345)]


@pytest.mark.parametrize("ret", [0, 1, 0xffff])
def test_flic_rewind(ret):
    t4spec.run_spec(
        path('src/flic_decode/flic_rewind_reference.c'), "FlicRewind_",
        0x193fc, _seek_cases(0x59490), watch=[(FLAG, 2), (0x59490, 4)],
        stubs=[T4Stub(0x19048, log_regs=("eax", "edx")),
               T4Stub(0x192f0, ret=ret, log_regs=())],
        out_regs=("eax",))


@pytest.mark.parametrize("ret", [0, 1, 0xffff])
def test_flic_restart(ret):
    t4spec.run_spec(
        path('src/flic_decode/flic_restart_reference.c'), "FlicRestart_",
        0x19420, _seek_cases(0x59494), watch=[(FLAG, 2), (0x59494, 4)],
        stubs=[T4Stub(0x19048, log_regs=("eax", "edx")),
               T4Stub(0x192f0, ret=ret, log_regs=())],
        out_regs=("eax",))


@pytest.mark.parametrize("ret", [0, 1, 0xffff])
def test_flic_next_frame(ret):
    cases = [T4Case(mem={FLAG: W(v)}, label="flag%d" % v) for v in (0, 1, 2)]
    t4spec.run_spec(
        path('src/flic_decode/flic_next_frame_reference.c'), "FlicNextFrame_",
        0x19450, cases, watch=[(FLAG, 2)],
        stubs=[T4Stub(0x192f0, ret=ret, log_regs=())], out_regs=("eax",))
