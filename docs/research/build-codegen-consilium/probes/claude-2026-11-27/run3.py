"""Probe R2-P1: CONST pad determinism with a fresh wineserver per compile, fixed absolute path."""
import os
from wc1 import oldcc, omf
src = "/tmp/opencode/cn-claude/t/cp/c2.c"
env = dict(os.environ); env.setdefault("WINEPREFIX", os.environ["WINEPREFIX"])
for i in range(5):
    oldcc.kill_wineserver(env)
    out = f"/tmp/opencode/cn-claude/t/cp/f{i}.obj"
    oldcc.compile_c(src, "-q -zl -zld -bt=dos -s -ot -ol -5r -zp2", out)
    m = omf.parse_object(out)
    print(i, [bytes(s.data).hex() for s in m.segments if s.name == "CONST"])
