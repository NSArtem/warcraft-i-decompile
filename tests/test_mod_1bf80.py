import os
import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Stub, T4Case

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = path('src/mod_1bf80', 'wait_input_or_timeout_reference.c')

A_DONE = 0x59690
A_TICKS = 0x59692

STUB_ADDRS = []


def test_t3_files_match():
    t4spec.assert_t3_matches(path('src/mod_1bf80'), ['wait_set_done.c', 'wait_tick_down.c'])


def test_reference_still_mismatches():
    t4spec.assert_ref_mismatch(path('src/mod_1bf80'), ['wait_input_or_timeout_reference.c'])


PUMP = {"n": 0}


def _init(emu):
    PUMP["n"] = 0
    emu.alloc(0x100, 16)
    emu.put_u32(A_DONE, 0)
    emu.put_u32(A_TICKS, 0)


def test_wait_input_or_timeout():
    from wc1 import symbols
    by = t4spec.by_link_lenient()

    def addr(link):
        return by[link]["addr"]

    names = ["UiInputInit_", "EvtPump_", "ScreenUpdate_"]
    stubs = [T4Stub(addr(n), log_regs=()) for n in names]
    calls = PUMP

    def pump(emu, log):
        # stand-in for the idle callback (WaitTickDown): the countdown ends
        # the loop; finish after 3 pumps so large tick counts stay cheap
        calls["n"] += 1
        cur = int.from_bytes(emu.read(A_TICKS, 2), "little")
        left = 0 if calls["n"] % 3 == 0 else max(cur - 1, 1)
        emu.write(A_TICKS, left.to_bytes(2, "little"))
        log(left)
        return 0

    stubs.append(T4Stub(addr("UiEventPump_"), fn=pump))
    cases = [
        T4Case(args=(0,), label="zero"),
        T4Case(args=(1,), label="one"),
        T4Case(args=(5,), label="five"),
        T4Case(args=(0x7fff,), label="big"),
    ]
    watch = [(A_DONE, 4)]
    t4spec.run_spec(SRC, "WaitInputOrTimeout_", 0x1bf94, cases,
                    watch=watch, stubs=stubs, out_regs=("eax",),
                    init_emu=_init)
