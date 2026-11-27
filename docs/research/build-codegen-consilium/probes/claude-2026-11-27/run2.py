from wc1 import oldcc, omf
for src, fl in (("/tmp/opencode/cn-claude/t/cp/longerdirname_x/c2.c", "-q -zl -zld -bt=dos -s -ot -ol -5r -zp2"),
                ("/tmp/opencode/cn-claude/t/cp/c2.c", "-q -zl -bt=dos -s -ot -ol -5r -zp2"),
                ("/tmp/opencode/cn-claude/t/cp/c2.c", "-q -zl -zld -bt=dos -s -ot -ol -4r -zp2")):
    out = "/tmp/opencode/cn-claude/t/cp/ox.obj"
    oldcc.compile_c(src, fl, out)
    m = omf.parse_object(out)
    print(src[-30:], fl[-14:], [bytes(s.data).hex() for s in m.segments if s.name == "CONST"])
