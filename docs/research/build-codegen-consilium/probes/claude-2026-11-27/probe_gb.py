import sys, traceback
sys.path.insert(0, "tests")
import test_playflic_t4 as T
from wc1 import path, match
for src in (path("src","playflic","zgb.c"), path("src","playflic","player_reference.c")):
    print("== SRC", src)
    import subprocess
    T.SRC = src
    try:
        T.test_intro_op_wait_sound(); print("PASS")
    except AssertionError as e:
        print("FAIL", str(e)[:200])
