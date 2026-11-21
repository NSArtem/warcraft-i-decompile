import os
import struct

import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case, T4Stub

pytestmark = pytest.mark.skipif(
    not (os.path.exists(path("original", "install", "war.exe")) and os.environ.get("WATCOM")),
    reason="needs original/ and $WATCOM",
)

SRC = path("src/mod_33520", "critical_error_prompt_reference.c")
_BY = {}
_STATE = {"events": [], "idx_addr": 0}


def _addr(name):
    if not _BY:
        _BY.update(t4spec.by_link_lenient())
    for k in (name + "_", "_" + name, name):
        if k in _BY:
            return _BY[k]["addr"]
    raise KeyError(name)


def _init(emu):
    # Store event index in emulated RAM so cemu.run_pair resets it identically
    # between the original run and the compiled-C run.
    _STATE["idx_addr"] = emu.alloc(16, 16)


def _evt_stub(e, log):
    idx_addr = _STATE["idx_addr"]
    idx = struct.unpack("<I", e.read(idx_addr, 4))[0]
    e.write(idx_addr, struct.pack("<I", idx + 1))
    evs = _STATE["events"]
    ret, ev_type, key = evs[idx] if idx < len(evs) else (1, 0x80, 0x52)
    if ret:
        e.write(e.reg("eax"), struct.pack("<6h", ev_type, 0, 0, 0, 0, key))
    log(ret, ev_type, key)
    return ret


def _cputs(e, log):
    a = e.reg("eax")
    s = e.cstr(a, 64)
    log(a, sum(bytearray(s if isinstance(s, (bytes, bytearray)) else s.encode())))
    return 0


def _mk(installed, vis, events):
    def setup(e):
        e.write(_addr("crit_err_installed"), struct.pack("<h", installed))
        e.write(_addr("cursor_layer_id"), bytes([2]))
        e.write(_addr("layers") + 2 * 9 * 2, struct.pack("<h", vis))
        e.write(_addr("evt_mask"), struct.pack("<H", 0x1234))
        e.write(0x5a8fa, struct.pack("<h", 7))
        e.write(_STATE["idx_addr"], struct.pack("<I", 0))
        _STATE["events"] = list(events)
    return setup


def test_critical_error_prompt():
    stubs = [
        T4Stub(_addr("cputs"), fn=_cputs),
        T4Stub(_addr("BitmapBlit"), log_regs=("eax", "edx", "ebx", "ecx")),
        T4Stub(_addr("BitmapBlitAll"), log_regs=("eax", "edx", "ebx")),
        T4Stub(_addr("LayerInvalidate"), log_regs=("eax",)),
        T4Stub(_addr("EvtPump"), log_regs=()),
        T4Stub(_addr("EvtGet"), fn=_evt_stub),
        T4Stub(_addr("EvtProcess"), log_regs=("eax",)),
        T4Stub(_addr("CursorLayerShow"), log_regs=()),
        T4Stub(_addr("exit"), log_regs=("eax",)),
        T4Stub(_addr("delay"), log_regs=("eax",)),
    ]
    watch = [
        (_addr("evt_mask"), 2),
        (0x5a8fa, 2),
        (_addr("cur_bitmap"), 4),
        (_addr("layers") + 2 * 9 * 2, 2),
    ]

    def init_with_watch(emu):
        _init(emu)
        # Watching idx_addr ensures cemu.run_pair restores it to 0 before the C run
        # and verifies both original and C consumed the exact same number of events.
        watch.append((_STATE["idx_addr"], 4))
    cases = []
    # Direct retry ('R'/'r') across text-mode (installed=1) and graphics-mode (installed=0, cursor vis 0/1)
    for inst in (0, 1):
        for key in (0x52, 0x72):
            for vis in (0, 1):
                cases.append(T4Case(
                    setup=_mk(inst, vis, [(1, 0x80, key)]),
                    label=f"inst={inst} key={key:#x} vis={vis}",
                ))
    # Abort ('A'/'a') calls exit(1); because exit is stubbed, follow with 'R' to exit loop cleanly
    for key in (0x41, 0x61):
        cases.append(T4Case(
            setup=_mk(1, 0, [(1, 0x80, key), (1, 0x80, 0x52)]),
            label=f"abort_{key:#x}",
        ))
    # Polling loop: no event (ret=0) -> non-key event (0x40) -> ignored key (' ') -> 'R'
    cases.append(T4Case(
        setup=_mk(0, 1, [(0, 0, 0), (1, 0x40, 0x52), (1, 0x80, 0x20), (1, 0x80, 0x52)]),
        label="poll_noevent_nonkey_ignored_then_retry",
    ))
    t4spec.run_spec(SRC, "CriticalErrorPrompt_", 0x33520, cases,
                    watch=watch, stubs=stubs, out_regs=(), init_emu=init_with_watch)


def test_ref_mismatch_guard():
    t4spec.assert_ref_mismatch(path("src/mod_33520"), ["critical_error_prompt_reference.c"])
