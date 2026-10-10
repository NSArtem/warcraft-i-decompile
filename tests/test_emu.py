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
