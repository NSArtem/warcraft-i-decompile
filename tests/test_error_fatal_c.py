import os
import struct

import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case, T4Stub

pytestmark = pytest.mark.skipif(
    not (os.path.exists(path('original', 'install', 'war.exe')) and os.environ.get('WATCOM')),
    reason='needs original/ and $WATCOM',
)

SRC = path('src/error_fatal', 'fatal_error.c')
DUMMY_HOOK = 0x106e8  # NopCallback, stubbed as fatal_hook target
STR = {}


def test_t3_files_match():
    t4spec.assert_t3_matches(path('src/error_fatal'), ['fatal_error.c'])


def _lookup(name):
    funcs, datas = t4spec.load_lenient()
    for t in (funcs, datas):
        for a, e in t.items():
            if e.get("name") == name:
                return a
    raise KeyError(name)


def _init(emu):
    STR['fmt'] = emu.alloc(64, 16)
    emu.write(STR['fmt'], b"hello %d\x00")


def _va_logger(e, log):
    fmt_ptr = e.reg("eax")
    va_slot = e.reg("edx")
    va_ptr = struct.unpack("<I", e.read(va_slot, 4))[0]
    arg0 = struct.unpack("<I", e.read(va_ptr, 4))[0]
    log(fmt_ptr, arg0)
    return 0


def test_fatal_error():
    stubs = [
        T4Stub(_lookup("__run_atexit"), log_regs=("eax",)),
        T4Stub(_lookup("puts"), log_regs=("eax",)),
        T4Stub(_lookup("vprintf"), fn=_va_logger),
        T4Stub(_lookup("__exit"), log_regs=("eax",)),
        T4Stub(DUMMY_HOOK, fn=_va_logger),
    ]

    def mk_case(use_hook, arg0, label):
        def setup(emu):
            emu.write(0x553b0, struct.pack("<I", DUMMY_HOOK if use_hook else 0))
        return T4Case(args=(STR['fmt'],), stack_args=(arg0,), setup=setup, label=label)

    # Deferred builders via rand_gen so STR['fmt'] is allocated by _init first
    specs = [
        (False, 0, "no_hook_0"),
        (False, 42, "no_hook_42"),
        (True, 0, "with_hook_0"),
        (True, 1337, "with_hook_1337"),
    ]
    it = iter(specs)
    t4spec.run_spec(
        SRC, "_FatalError", 0x30bf0, (),
        stubs=stubs, out_regs=(), cdecl=True,
        init_emu=_init,
        rand_cases=len(specs),
        rand_gen=lambda _rng: mk_case(*next(it)),
    )
