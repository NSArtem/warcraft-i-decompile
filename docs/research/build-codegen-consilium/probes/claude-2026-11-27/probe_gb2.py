import sys
sys.path.insert(0, "tests")
import test_playflic_t4 as T
from wc1 import path, t4spec
orig = t4spec.run_spec
def patched(src, fn, addr, cases, watch=(), **kw):
    S = T.scr()
    return orig(src, fn, addr, cases, watch=list(watch) + [(S + 0x10, 4)], **kw)
for src in (path("src","playflic","zgb.c"), path("src","playflic","player_reference.c")):
    T.SRC = src
    t4spec.run_spec = patched
    try:
        T.test_intro_op_wait_sound(); print("PASS with stub-state restored:", src)
    except AssertionError as e:
        print("FAIL", src, str(e)[:160])
