"""Probe R3-P1 (disposable): the 5 xfailed T4 tests under full paired starting state:
all mapped memory + CPU context (GPRs, EFLAGS, segment regs) snapshotted before the original
call and restored before the C call. Also runs the reverse comparison order check by reporting."""
import sys
sys.path.insert(0, "tests")
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ECX, UC_X86_REG_EDX,
    UC_X86_REG_ESI, UC_X86_REG_EDI, UC_X86_REG_EBP, UC_X86_REG_ESP, UC_X86_REG_EFLAGS,
    UC_X86_REG_CS, UC_X86_REG_DS, UC_X86_REG_ES, UC_X86_REG_SS, UC_X86_REG_FS, UC_X86_REG_GS)
from wc1 import cemu
from wc1.emu import Emu
CPU = [UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ECX, UC_X86_REG_EDX, UC_X86_REG_ESI, UC_X86_REG_EDI,
       UC_X86_REG_EBP, UC_X86_REG_ESP, UC_X86_REG_EFLAGS, UC_X86_REG_DS, UC_X86_REG_ES,
       UC_X86_REG_SS, UC_X86_REG_FS, UC_X86_REG_GS]
_call, _rp = Emu.call, cemu.run_pair
state = {}
def call_w(self, addr, *a, **kw):
    st = state.get(id(self))
    if st is not None:
        if st["n"] == 0:
            st["mem"] = [(b, bytes(self.uc.mem_read(b, e - b + 1))) for b, e, _ in self.uc.mem_regions()]
            st["cpu"] = [(r, self.uc.reg_read(r)) for r in CPU]
        elif st["n"] == 1:
            for b, d in st["mem"]:
                self.uc.mem_write(b, d)
            for r, v in st["cpu"]:
                self.uc.reg_write(r, v)
        st["n"] += 1
    return _call(self, addr, *a, **kw)
def rp_w(emu, *a, **kw):
    state[id(emu)] = {"n": 0}
    try:
        return _rp(emu, *a, **kw)
    finally:
        state.pop(id(emu), None)
Emu.call = call_w
cemu.run_pair = rp_w
import test_playflic_t4 as P, test_mod_2efd0_t4 as M
for mod, name in ((P, "test_intro_op_wait_sound"), (P, "test_intro_op_start_credits"),
                  (P, "test_intro_run_script"), (P, "test_intro_play"), (M, "test_end_screen")):
    try:
        getattr(mod, name)(); print("memcpu", name, "PASS")
    except Exception as e:
        print("memcpu", name, "FAIL", type(e).__name__, str(e)[:200])
