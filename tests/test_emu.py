"""The emulation harness itself, exercised on functions verified elsewhere."""
import os

import pytest

from wc1 import path

pytestmark = pytest.mark.skipif(not os.path.exists(path("original", "install", "war.exe")),
                                reason="original files not extracted")


def test_strlwr_runs():
    from wc1.emu import Emu
    emu = Emu()
    buf = emu.alloc(64)
    emu.write(buf, b"Hello, WORLD 123\0")
    r = emu.call(0x30E38, buf)
    assert r == buf
    assert emu.cstr(buf) == b"hello, world 123"


def test_strcpy_runs():
    from wc1.emu import Emu
    emu = Emu()
    a, b = emu.alloc(64), emu.alloc(64)
    emu.write(b, b"path.war\0")
    assert emu.call(0x31CEF, a, b) == a
    assert emu.cstr(a) == b"path.war"


def test_interrupts_are_trapped():
    from wc1.emu import Emu, EmuError
    emu = Emu()
    # LoadFile ends up in DOS file I/O: without an interrupt model it must fail loudly
    buf = emu.alloc(0x100)
    name = emu.alloc(16)
    emu.write(name, b"path.war\0")
    with pytest.raises(EmuError):
        emu.call(0x1D330, name, buf, 0, 0x72, stack_args=(0,))


def test_memcpy_stub_is_builtin():
    """The clib memcpy (0x31789) is a segmented ES:EDI copy Unicorn cannot
    execute, so a flat watcall model (eax=dst, edx=src, ebx=n) is
    pre-installed and can be overridden per test."""
    from wc1.emu import Emu
    emu = Emu()
    a, b = emu.alloc(64), emu.alloc(64)
    emu.write(b, bytes(range(64)))
    assert emu.call(0x31789, a, b, 64) == a
    assert emu.read(a, 64) == bytes(range(64))
    emu.write(a, b"stays\0")
    assert emu.call(0x31789, a, b, 0) == a          # n == 0 copies nothing
    assert emu.cstr(a) == b"stays"
    emu.stubs[0x31789] = lambda e: 0x1234
    assert emu.call(0x31789, a, b, 8) == 0x1234     # a test model overrides


def test_flat_gdt_segment_ops_run():
    """The built-in flat 32-bit GDT (CS=0x08, DS/ES/FS/GS/SS=0x10) lets
    segmented clib routines like strlen (0x31d1a) and _fmemset (0x33b41)
    run natively without stubbing."""
    from wc1.emu import DS_SEL, Emu
    emu = Emu()
    buf = emu.alloc(32)
    emu.write(buf, b"warcraft\0")
    assert emu.call(0x31D1A, buf) == 8
    assert emu.call(0x33B41, buf, DS_SEL, ord("X"), 4) == buf
    assert emu.cstr(buf) == b"XXXXraft"


def test_interrupt_call_frame():
    """interrupt=True pushes an x86 32-bit iretd frame so __interrupt handlers
    (e.g. NetSerialIsr 0x202c0) execute and return cleanly to SENTINEL."""
    import struct
    from wc1.emu import Emu
    emu = Emu()
    u = emu.alloc(0x1100)
    emu.put_u32(0x59A70, u)
    emu.write(u, struct.pack("<HH", 0x3F8, 4))
    emu.stubs[0x34850] = lambda e: None  # __GETDS
    emu.stubs[0x349B0] = lambda e: 1     # inp: IIR bit 0 = no interrupt pending
    outs = []
    emu.stubs[0x349BC] = lambda e: outs.append((e.reg("eax"), e.reg("edx")))
    emu.call(0x202C0, interrupt=True)
    assert outs == [(0x20, 0x20)]

