from wc1 import analysis
p = analysis.run()
d = p.le.obj(analysis.DATA_OBJ); img = bytes(p.image[analysis.DATA_OBJ])
for a in (0x56b1c, 0x56ab8):
    print(hex(a), img[a-d.base:a-d.base+24].hex())
