"""Compare two LE executables at the loaded-image level.

usage: python3 -m wc1.compare <a.exe> <b.exe>

Reports object layout, entry point / initial stack and the first differences
of each object's loaded image (all fixups applied at the preferred bases).
Exit status 0 iff the loaded images, entry and stack are identical."""
import sys

from . import le as lefmt


def main():
    a, b = (lefmt.LE(open(x, "rb").read()) for x in sys.argv[1:3])
    ok = True
    print(f"{'':10}{'A':>24}{'B':>24}")
    for k in ("entry", "initial_esp"):
        va, vb = getattr(a, k), getattr(b, k)
        print(f"{k:10}{va:>24x}{vb:>24x}{'' if va == vb else '   <-- differs'}")
        ok &= va == vb
    if len(a.objects) != len(b.objects):
        print("object count differs")
        return 1
    ia, ib = a.loaded_image(), b.loaded_image()
    for oa, ob in zip(a.objects, b.objects):
        desc = lambda o: f"{o.base:x}+{o.vsize:x} f={o.flags:x}"
        same_layout = (oa.base, oa.vsize) == (ob.base, ob.vsize)
        print(f"obj{oa.index:<7}{desc(oa):>24}{desc(ob):>24}{'' if same_layout else '   <-- differs'}")
        ok &= same_layout
        da, db = bytes(ia[oa.index]), bytes(ib[ob.index])
        n = min(len(da), len(db))
        diffs = [i for i in range(n) if da[i] != db[i]]
        if len(da) != len(db):
            # trailing bytes beyond the shorter image must be zero (BSS)
            tail = da[n:] if len(da) > n else db[n:]
            if any(tail):
                diffs.append(n)
        if diffs:
            ok = False
            print(f"  {len(diffs)} differing bytes; first at {oa.base + diffs[0]:#x}")
            for d in diffs[:8]:
                print(f"    {oa.base + d:#x}: {da[d:d+8].hex()} vs {db[d:d+8].hex()}")
        else:
            print("  loaded image identical")
    fa = {(f.obj, f.src_off, f.target_obj, f.target_off) for f in a.fixups_unique}
    fb = {(f.obj, f.src_off, f.target_obj, f.target_off) for f in b.fixups_unique}
    print(f"fixups: A={len(fa)} B={len(fb)} only-A={len(fa - fb)} only-B={len(fb - fa)}")
    ok &= fa == fb
    print("IDENTICAL (loaded image, entry, stack, fixups)" if ok else "DIFFERENT")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
