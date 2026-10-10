#!/usr/bin/env python3
"""Extract the ISO9660 filesystem from the Redump/DIC data track of the
Warcraft: Orcs & Humans CD (v1.22h, MODE1/2352).

Usage: extract_disc.py <track1.bin> <outdir>

Writes <outdir>/WAR1.iso (2048-byte user data) and <outdir>/files/... and a
manifest (<outdir>/MANIFEST.sha256). Pure stdlib, no external tools.
"""
import hashlib, os, struct, sys

RAW, USER, HDR = 2352, 2048, 16

def to_iso(bin_path, iso_path):
    with open(bin_path, "rb") as f, open(iso_path, "wb") as o:
        while True:
            s = f.read(RAW)
            if not s:
                break
            assert len(s) == RAW and s[15] == 1, "expected MODE1 sector"
            o.write(s[HDR:HDR + USER])

def walk(iso, lba, size, path, out):
    iso.seek(lba * USER)
    data = iso.read(size)
    off = 0
    while off < len(data):
        ln = data[off]
        if ln == 0:  # padding to next sector
            off = (off // USER + 1) * USER
            continue
        rec = data[off:off + ln]
        ext = struct.unpack_from("<I", rec, 2)[0]
        dsz = struct.unpack_from("<I", rec, 10)[0]
        flags = rec[25]
        nlen = rec[32]
        name = rec[33:33 + nlen]
        off += ln
        if name in (b"\x00", b"\x01"):
            continue
        name = name.decode("ascii").split(";")[0].rstrip(".")
        p = os.path.join(path, name)
        if flags & 2:
            os.makedirs(os.path.join(out, p), exist_ok=True)
            yield from walk(iso, ext, dsz, p, out)
        else:
            iso.seek(ext * USER)
            blob = iso.read(dsz)
            with open(os.path.join(out, p), "wb") as w:
                w.write(blob)
            yield p, blob

def main():
    bin_path, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    iso_path = os.path.join(outdir, "WAR1.iso")
    to_iso(bin_path, iso_path)
    files = os.path.join(outdir, "files")
    os.makedirs(files, exist_ok=True)
    with open(iso_path, "rb") as iso:
        iso.seek(16 * USER)
        pvd = iso.read(USER)
        assert pvd[1:6] == b"CD001"
        root = pvd[156:156 + 34]
        rlba = struct.unpack_from("<I", root, 2)[0]
        rsz = struct.unpack_from("<I", root, 10)[0]
        entries = sorted(walk(iso, rlba, rsz, "", files))
    with open(os.path.join(outdir, "MANIFEST.sha256"), "w") as m:
        for p, blob in entries:
            m.write(f"{hashlib.sha256(blob).hexdigest()}  {len(blob):>10}  {p}\n")
    print(f"extracted {len(entries)} files")

if __name__ == "__main__":
    main()
