"""Probe Q-B01 (disposable): run the 5 xfailed 'divergence' T4 tests with full paired-state
restoration: snapshot every mapped Unicorn region before the original run, restore it before
the C run. Emu.call is wrapped at class level only for the duration of each run_pair."""
import sys, traceback
sys.path.insert(0, "tests")
from wc1 import cemu
from wc1.emu import Emu
_orig_call = Emu.call
_orig_run_pair = cemu.run_pair
state = {}
def call_wrapper(self, addr, *a, **kw):
    st = state.get(id(self))
    if st is not None:
        if st["n"] == 0:
            st["snap"] = [(b, bytes(self.uc.mem_read(b, e - b + 1))) for b, e, _ in self.uc.mem_regions()]
        elif st["n"] == 1:
            for b, data in st["snap"]:
                self.uc.mem_write(b, data)
        st["n"] += 1
    return _orig_call(self, addr, *a, **kw)
def run_pair_wrapper(emu, *a, **kw):
    state[id(emu)] = {"n": 0}
    try:
        return _orig_run_pair(emu, *a, **kw)
    finally:
        state.pop(id(emu), None)
mode = sys.argv[1]
if mode == "full":
    Emu.call = call_wrapper
    cemu.run_pair = run_pair_wrapper
import test_playflic_t4 as P, test_mod_2efd0_t4 as M
import wc1.t4spec as T
if mode == "full":
    T.cemu.run_pair = run_pair_wrapper
for mod, name in ((P, "test_intro_op_wait_sound"), (P, "test_intro_op_start_credits"),
                  (P, "test_intro_run_script"), (P, "test_intro_play"), (M, "test_end_screen")):
    try:
        getattr(mod, name)(); print(mode, name, "PASS")
    except Exception as e:
        print(mode, name, "FAIL", type(e).__name__, str(e)[:220])
