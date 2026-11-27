import os, sys, json
from pathlib import Path

ROOT = Path("/mnt/data/projects/warcraft-1-decompile-wt/cons-c")
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))

from wc1 import analysis, match, omf, symbols
from experiments.build_codegen.e0 import matcher_proto as e0

p = analysis.run()
dobj = p.le.obj(analysis.DATA_OBJ)
dimg = bytes(p.image[analysis.DATA_OBJ])

# Check E2's gamedlg_run_1_aligned_0 CONST strings in war.exe
print("=== PROBE 7a: E2 GAMEDLG CONST strings in war.exe ===")
e2_res = json.load(open(ROOT / "docs/research/build-codegen/results/e2/results.json"))
for k in e2_res:
    print("E2 top key:", k)
for gname, g in e2_res.get("groups", {}).items():
    if "gamedlg" in gname:
        print(f"  group {gname}: funcs={g.get('functions')}")

# Check 0x56b1c (".net") and 0x56b24 (".sav") in war.exe
print("\n=== PROBE 7b: war.exe 0x56b1c..0x56b38 bytes ===")
seg = dimg[0x56b1c - dobj.base:0x56b38 - dobj.base]
print(f"0x56b1c..0x56b38: {seg.hex()}")
# Find which functions reference 0x56b1c and 0x56b24
funcs_db, datas_db, _ = symbols.load()
for addr in (0x56b1c, 0x56b24, 0x56b2c, 0x56ab8, 0x56af4):
    refs = [hex(s) for s, (_, t) in p.fix_at.items() if t == addr]
    print(f"  refs to {hex(addr)}: {refs}")

# Check the 11 E0 baseline T3 files with local data segments: how many strings / bytes in CONST?
print("\n=== PROBE 7c: E0 11 baseline T3 local data segments ===")
os.environ["TMPDIR"] = "/tmp/opencode/cn-gemini"
os.environ["WINEPREFIX"] = str(ROOT / "build/oldcc/wineprefix")
p7_out = Path("/tmp/opencode/cn-gemini/p7")
p7_out.mkdir(parents=True, exist_ok=True)
e0_audit = json.load(open(ROOT / "docs/research/build-codegen/results/e0/t3_reaudit.json"))
seen_src = set()
for r in e0_audit["rows"]:
    if r["data_segments_checked"] > 0 and r["src"] not in seen_src:
        seen_src.add(r["src"])
        src = str(ROOT / r["src"])
        mod = match.compile_c(src, r["cflags"], str(p7_out / (Path(src).stem + ".obj")), cc=r["compiler"])
        segs = [(s.name, s.cls, s.length, bytes(s.data).hex()) for s in mod.segments if s.cls in ("DATA", "BSS") and s.length]
        print(f"  {r['addr']} {r['name']} ({r['src']}): {segs}")

# Compile a 2-string -ot TU with ".net" and ".sav" and compare CONST bytes against war.exe[0x56b1c:0x56b2c]
c_p = p7_out / "net_sav.c"
c_p.write_text('extern void f(const char *); void g(void) { f(".net"); f(".sav"); }\n')
mod_ns = match.compile_c(str(c_p), "-q -zl -bt=dos -s -ot -ol -5r -zp2", str(p7_out / "net_sav.obj"), cc="10.0a")
_, cseg = mod_ns.seg("CONST")
orig_ns = dimg[0x56b1c - dobj.base:0x56b1c - dobj.base + cseg.length]
print("\n=== PROBE 7d: 2-string -ot TU ('.net', '.sav') vs war.exe 0x56b1c ===")
print(f"  compiled CONST ({cseg.length}B): {bytes(cseg.data).hex()}")
print(f"  original war.exe ({len(orig_ns)}B): {orig_ns.hex()}")
diffs = [(i, cseg.data[i], orig_ns[i]) for i in range(min(len(cseg.data), len(orig_ns))) if cseg.data[i] != orig_ns[i]]
print(f"  byte diffs (all inside [5:8] alignment pad!): {diffs}")
