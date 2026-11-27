import sys, hashlib
from wc1 import oldcc, omf
src = "/tmp/opencode/cn-claude/t/cp/c2.c"
for i in range(4):
    out = f"/tmp/opencode/cn-claude/t/cp/o{i}.obj"
    oldcc.compile_c(src, "-q -zl -zld -bt=dos -s -ot -ol -5r -zp2", out)
    m = omf.parse_object(out)
    for s in m.segments:
        if s.name == "CONST":
            print(i, s.name, s.length, bytes(s.data).hex())
