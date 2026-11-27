import os, sys, json
from pathlib import Path

ROOT = Path("/mnt/data/projects/warcraft-1-decompile-wt/cons-c")
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))

from wc1 import analysis, match, omf, symbols

p = analysis.run()
dobj = p.le.obj(analysis.DATA_OBJ)
dimg = bytes(p.image[analysis.DATA_OBJ])
os.environ["TMPDIR"] = "/tmp/opencode/cn-gemini"
os.environ["WINEPREFIX"] = str(ROOT / "build/oldcc/wineprefix")
p7_out = Path("/tmp/opencode/cn-gemini/p7")
p7_out.mkdir(parents=True, exist_ok=True)

e0_audit = json.load(open(ROOT / "docs/research/build-codegen/results/e0/t3_reaudit.json"))
print("E0 t3_reaudit keys:", list(e0_audit.keys()))
rows = e0_audit.get("rows") or e0_audit.get("functions") or e0_audit.get("results") or []
seen_src = set()
for r in rows:
    if r.get("data_segments_checked", 0) > 0 and r["src"] not in seen_src:
        seen_src.add(r["src"])
        src = str(ROOT / r["src"])
        mod = match.compile_c(src, r["cflags"], str(p7_out / (Path(src).stem + ".obj")), cc=r["compiler"])
        segs = [(s.name, s.cls, s.length, bytes(s.data)) for s in mod.segments if s.cls in ("DATA", "BSS") and s.length]
        print(f"  {r['addr']} {r['name']} ({r['src']}): {[(n,c,l,d.count(0),d[:40]) for n,c,l,d in segs]}")

# Check which function contains 0x14766/0x1476d/0x14779
funcs_db, _, _ = symbols.load()
for f in p.functions:
    if f["start"] <= 0x14766 < f["end"]:
        e = funcs_db.get(f["start"], {})
        print(f"\nFunction owning 0x14766/0x1476d/0x14779: {hex(f['start'])}..{hex(f['end'])} name={e.get('name')} src={e.get('src')} ref={e.get('ref')}")

# Compile 2-string -ot TU ('.net', '.sav') vs war.exe 0x56b1c
c_p = p7_out / "net_sav.c"
c_p.write_text('extern void f(const char *); void g(void) { f(".net"); f(".sav"); }\n')
mod_ns = match.compile_c(str(c_p), "-q -zl -bt=dos -s -ot -ol -5r -zp2", str(p7_out / "net_sav.obj"), cc="10.0a")
_, cseg = mod_ns.seg("CONST")
orig_ns = dimg[0x56b1c - dobj.base:0x56b1c - dobj.base + cseg.length]
print("\n=== PROBE 7d: 2-string -ot TU ('.net', '.sav') vs war.exe 0x56b1c ===")
print(f"  compiled CONST ({cseg.length}B): {bytes(cseg.data).hex()}")
print(f"  original war.exe ({len(orig_ns)}B): {orig_ns.hex()}")
diffs = [(i, hex(cseg.data[i]), hex(orig_ns[i])) for i in range(min(len(cseg.data), len(orig_ns))) if cseg.data[i] != orig_ns[i]]
print(f"  byte diffs (ALL inside [5:8] alignment pad!): {diffs}")

# Also check E2's gamedlg_run_1_aligned_0 CONST strings!
for fn_name in ("VersionMismatchDialog", "SaveVersionDialog"):
    for a, e in funcs_db.items():
        if e["name"] == fn_name:
            src = str(ROOT / e["src"])
            mod = match.compile_c(src, match.file_cflags(src), str(p7_out / (fn_name + ".obj")), cc=match.file_cc(src))
            segs = [(s.name, s.length, bytes(s.data)) for s in mod.segments if s.cls in ("DATA", "BSS") and s.length]
            print(f"  E2 GAMEDLG {fn_name} ({hex(a)}): {[(n,l,l%4,d) for n,l,d in segs]}")
