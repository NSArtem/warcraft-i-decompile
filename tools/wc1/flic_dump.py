"""Dump the PLAYFLIC.C data: the intro-script opcode table, the animation
step tables, the FLIC handle table and the string records (read from the
loaded image, so LE relocations are applied).

usage: python3 -m wc1.flic_dump [table]

  table (default: all)
    ops      the 256-entry script opcode table at 0x52ea8
    steps    the credit/animation step tables 0x52f18..0x53094
    fl     the FLIC handle table at 0x52bdc and the picture table 0x52d18
    str      the script string records 0x52c6c, 0x52c7a, 0x52e02, 0x52e96,
            0x52e9a and the header/state globals
"""
import struct
import sys

from . import analysis

OP_TABLE = 0x52EA8       # 256 dwords, indexed by the script opcode byte
OP_COUNT = 0x100
STEP_TABLES = {          # credits animation tables (word entries)
    0x52F18: "steps1",   # 0x52f18..0x52f40 (20) variant A, layer 15
    0x52F40: "frames1",  # 0x52f40..0x52f7c (30)
    0x52F7C: "steps2",   # 0x52f7c..0x52fa4 (20) variant A, layer 16
    0x52FA4: "frames2",  # 0x52fa4..0x52ff4 (40)
    0x52FF4: "steps3",   # 0x52ff4..0x5301c (20) variant B, layer 16
    0x5301C: "frames3",  # 0x5301c..0x5306c (40)
    0x5306C: "steps4",   # 0x5306c..0x53094 (20) variant B, layer 17
    0x53094: "frames4",  # 0x53094..0x530e4 (40)
}
FLIC_HANDLES = 0x52BDC    # 21 dwords? indexed by the flic id word
PICTURES = 0x52D18        # stride 6: word count, word pad, dword record ptr
STRINGS = {
    0x52C6C: "credits roll (0x23668 arg)",
    0x52C7A: "epilogue script (0x23b70)",
    0x52E02: "finale script (0x23b69)",
    0x52E96: "intro script (0x23c9d)",
    0x52E9A: "level intro script (0x23cc5/0x23ce5)",
}


def main():
    p = analysis.run()
    img = p.image[p.data.index]
    base = p.data.base

    def raw(a, n):
        return img[a - base:a - base + n]

    def w(a):
        return struct.unpack_from("<H", raw(a, 2))[0]

    def dw(a):
        return struct.unpack_from("<I", raw(a, 4))[0]

    def text(a, n=80):
        b = raw(a, n).split(b"\0")[0]
        return b.decode("latin-1")

    what = sys.argv[1] if len(sys.argv) > 1 else "all"

    if what in ("ops", "all"):
        print("== script opcode table 0x%x (handler addresses, 0 = no op) ==" % OP_TABLE)
        seen = set()
        for i in range(OP_COUNT):
            h = dw(OP_TABLE + 4 * i)
            if h:
                seen.add(h)
                print("  op %02x -> 0x%06x" % (i, h))
        print("  distinct handlers: %d, unused ops: %d"
              % (len(seen), OP_COUNT - len(seen)))
        rest = [i for i in range(OP_COUNT) if not dw(OP_TABLE + 4 * i)]
        print("  unused opcodes:", " ".join("%02x" % i for i in rest))

    if what in ("steps", "all"):
        print("== step tables ==")
        keys = sorted(STEP_TABLES)
        for idx, a in enumerate(keys):
            end = keys[idx + 1] if idx + 1 < len(keys) else 0x530E4
            vals = [w(a + 2 * i) for i in range((end - a) // 2)]
            print("  0x%05x %-8s %d words: %s"
                  % (a, STEP_TABLES[a], len(vals), " ".join("%d" % v for v in vals)))

    if what in ("fl", "all"):
        print("== movie name table 0x%x ==" % FLIC_HANDLES)
        for i in range(8):
            print("  [%d] 0x%08x" % (i, dw(FLIC_HANDLES + 4 * i)))
        print("== picture table 0x%x (stride 6) ==" % PICTURES)
        for i in range(12):
            cnt = w(PICTURES + 6 * i)
            ptr = dw(PICTURES + 6 * i + 2)
            print("  [%d] count=%d ptr=0x%06x %r" % (i, cnt, ptr, text(ptr, 24)))
            if cnt in (0, 0xFFFF):
                break

    if what in ("str", "all"):
        print("== string records and state ==")
        for a, label in sorted(STRINGS.items()):
            print("  0x%05x %-28s %r" % (a, label, text(a, 60)))
        for a, label in ((0x59EB0, "dest surface"), (0x59EB4, "tick fn"),
                         (0x59EB8, "pictures[0..2]"), (0x59EC4, "buf A"),
                         (0x59EC8, "buf B"), (0x59ECC, "x offsets"),
                         (0x59ED2, "step D"), (0x59ED4, "step C"),
                         (0x59ED6, "pal C"), (0x59ED8, "pal D"),
                         (0x59EDA, "step B"), (0x59EDC, "step shown"),
                         (0x59EDE, "flic id"), (0x59EE0, "frame#"),
                         (0x59EE2, "countdown"), (0x59EE4, "multi on"),
                         (0x59EE6, "abort req"), (0x59EE8, "picture idx"),
                         (0x59EEA, "width*height"), (0x59EEC, "timer"),
                         (0x59EEE, "second pass"), (0x59EF0, "frame"),
                         (0x59EF2, "loaded"), (0x59EF4, "pic width"),
                         (0x59EF6, "flic sel"), (0x59EF8, "tick"),
                         (0x59EFA, "abort"), (0x59EFC, "frame ready")):
            print("  0x%05x %-20s dword=0x%08x word=0x%04x"
                  % (a, label, dw(a), w(a)))


if __name__ == "__main__":
    main()
