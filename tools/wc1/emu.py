"""Unicorn harness for running original functions in isolation (T4 tests).

    from wc1.emu import Emu
    emu = Emu()                              # fresh copy of the loaded image
    buf = emu.alloc(256)                     # scratch memory (zeroed)
    emu.write(buf, b"HELLO\\0")
    r = emu.call(0x30e38, buf)               # watcall: eax, edx, ebx, ecx, then stack
    assert emu.read(buf, 6) == b"hello\\0"

Calls run until the function returns to a sentinel address. Unmapped
accesses, interrupts (`int`), port I/O and exceeding `max_insns` raise
EmuError unless handlers are installed (`emu.on_interrupt`, `emu.on_io`), so a
test can never silently depend on DOS/hardware behaviour. `emu.stubs[addr] =
fn(emu) -> eax` replaces a callee (e.g. a clib routine) with a Python model;
the stub returns like a watcall function (stack args, if any, must be
declared in `emu.stub_pops[addr]` in bytes).
"""
import struct

from unicorn import (UC_ARCH_X86, UC_HOOK_CODE, UC_HOOK_INSN, UC_HOOK_INTR,
                     UC_HOOK_MEM_INVALID, UC_MODE_32, Uc, UcError)
from unicorn.x86_const import (UC_X86_INS_IN, UC_X86_INS_OUT, UC_X86_REG_EAX,
                               UC_X86_REG_EBP, UC_X86_REG_EBX, UC_X86_REG_ECX,
                               UC_X86_REG_EDI, UC_X86_REG_EDX, UC_X86_REG_EIP,
                               UC_X86_REG_ESI, UC_X86_REG_ESP)

from . import analysis

SENTINEL = 0x0FFF0000
HEAP_BASE = 0x00800000
HEAP_SIZE = 0x00800000
STACK_TOP = 0x0F000000
STACK_SIZE = 0x00100000
REGS = {"eax": UC_X86_REG_EAX, "ebx": UC_X86_REG_EBX, "ecx": UC_X86_REG_ECX,
        "edx": UC_X86_REG_EDX, "esi": UC_X86_REG_ESI, "edi": UC_X86_REG_EDI,
        "ebp": UC_X86_REG_EBP, "esp": UC_X86_REG_ESP}

_PROGRAM = None


def program():
    global _PROGRAM
    if _PROGRAM is None:
        _PROGRAM = analysis.Program()
    return _PROGRAM


class EmuError(Exception):
    pass


class Emu:
    def __init__(self, prog=None, max_insns=50_000_000):
        p = prog or program()
        self.p = p
        self.max_insns = max_insns
        uc = Uc(UC_ARCH_X86, UC_MODE_32)
        self.uc = uc
        for o in p.le.objects:
            size = (o.vsize + 0xFFFF) & ~0xFFFF
            uc.mem_map(o.base, size)
            uc.mem_write(o.base, bytes(p.image[o.index]))
        uc.mem_map(HEAP_BASE, HEAP_SIZE)
        uc.mem_map(STACK_TOP - STACK_SIZE, STACK_SIZE)
        uc.mem_map(SENTINEL, 0x1000)
        uc.mem_write(SENTINEL, b"\xf4")  # hlt, never executed (we stop on fetch)
        self._heap = HEAP_BASE
        self.stubs = {}
        self.stub_pops = {}
        self.on_interrupt = None   # fn(emu, intno) -> None
        self.on_io = None          # fn(emu, port, size, value_or_None) -> value
        self.trace = None          # fn(emu, addr, size)
        uc.hook_add(UC_HOOK_MEM_INVALID, self._bad_mem)
        uc.hook_add(UC_HOOK_INTR, self._intr)
        uc.hook_add(UC_HOOK_INSN, self._in, None, 1, 0, UC_X86_INS_IN)
        uc.hook_add(UC_HOOK_INSN, self._out, None, 1, 0, UC_X86_INS_OUT)
        uc.hook_add(UC_HOOK_CODE, self._code)
        self._count = 0
        self._error = None

    # -- memory -----------------------------------------------------------
    def alloc(self, n, align=16):
        a = (self._heap + align - 1) & ~(align - 1)
        self._heap = a + n
        if self._heap > HEAP_BASE + HEAP_SIZE:
            raise EmuError("emulator heap exhausted")
        return a

    def write(self, a, data):
        self.uc.mem_write(a, bytes(data))

    def read(self, a, n):
        return bytes(self.uc.mem_read(a, n))

    def cstr(self, a, limit=4096):
        b = self.read(a, limit)
        return b[:b.index(0)] if 0 in b else b

    def u32(self, a):
        return struct.unpack("<I", self.read(a, 4))[0]

    def put_u32(self, a, v):
        self.write(a, struct.pack("<I", v & 0xFFFFFFFF))

    def reg(self, name, value=None):
        if value is None:
            return self.uc.reg_read(REGS[name])
        self.uc.reg_write(REGS[name], value & 0xFFFFFFFF)

    # -- hooks ------------------------------------------------------------
    def _bad_mem(self, uc, access, addr, size, value, data):
        self._error = EmuError(f"invalid memory access at {addr:#x} (size {size}) "
                               f"from eip={uc.reg_read(UC_X86_REG_EIP):#x}")
        return False

    def _intr(self, uc, intno, data):
        if self.on_interrupt is None:
            self._error = EmuError(f"interrupt {intno:#x} at eip={uc.reg_read(UC_X86_REG_EIP):#x}")
            uc.emu_stop()
        else:
            self.on_interrupt(self, intno)

    def _in(self, uc, port, size, data):
        if self.on_io is None:
            self._error = EmuError(f"in from port {port:#x}")
            uc.emu_stop()
            return 0
        return self.on_io(self, port, size, None)

    def _out(self, uc, port, size, value, data):
        if self.on_io is None:
            self._error = EmuError(f"out to port {port:#x}")
            uc.emu_stop()
        else:
            self.on_io(self, port, size, value)

    def _code(self, uc, addr, size, data):
        self._count += 1
        if self._count > self.max_insns:
            self._error = EmuError(f"instruction limit exceeded at {addr:#x}")
            uc.emu_stop()
            return
        if self.trace:
            self.trace(self, addr, size)
        if addr in self.stubs:
            ret = self.stubs[addr](self)
            if ret is not None:
                self.reg("eax", ret)
            esp = self.reg("esp")
            raddr = self.u32(esp)
            self.reg("esp", esp + 4 + self.stub_pops.get(addr, 0))
            uc.reg_write(UC_X86_REG_EIP, raddr)

    # -- calls ------------------------------------------------------------
    def call(self, addr, *args, stack_args=(), regs=None, cdecl=False):
        """Call a function. watcall (default): first four args in eax, edx,
        ebx, ecx, `stack_args` pushed right-to-left (callee pops). cdecl:
        all args on the stack, caller pops. Returns eax."""
        self._count = 0
        self._error = None
        sp = STACK_TOP - 0x100
        if cdecl:
            stack = list(args) + list(stack_args)
        else:
            stack = list(stack_args)
            for r, v in zip(("eax", "edx", "ebx", "ecx"), args):
                self.reg(r, v)
        for v in reversed(stack):
            sp -= 4
            self.put_u32(sp, v)
        sp -= 4
        self.put_u32(sp, SENTINEL)
        self.reg("esp", sp)
        for r, v in (regs or {}).items():
            self.reg(r, v)
        try:
            self.uc.emu_start(addr, SENTINEL)
        except UcError as e:
            raise self._error or EmuError(f"{e} at eip={self.uc.reg_read(UC_X86_REG_EIP):#x}")
        if self._error:
            raise self._error
        return self.reg("eax")
