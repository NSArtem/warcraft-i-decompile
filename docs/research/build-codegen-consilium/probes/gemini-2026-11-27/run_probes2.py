import glob
import json
import os
import struct
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path("/mnt/data/projects/warcraft-1-decompile-wt/cons-c")
MAIN = Path("/mnt/data/projects/warcraft-1-decompile-consilium/runtime/gemini/export-main")
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))

from wc1 import analysis, match, omf, progress, symbols
from experiments.build_codegen.e0 import matcher_proto as e0
from experiments.build_codegen.e4 import omf_extract as e4
from wc1.omfpatch import _pack

p = analysis.run()
funcs_base, datas_base, _ = symbols.load()
mods = progress.load_modules()

main_funcs, main_datas = {}, {}
for tf in sorted(glob.glob(str(MAIN / "analysis/symbols/*.toml"))):
    doc = tomllib.load(open(tf, "rb"))
    for kind, tbl in (("func", main_funcs), ("data", main_datas)):
        for e in doc.get(kind, []):
            e = dict(e)
            e["link_name"] = symbols.link_name(kind, e); e["_file"] = os.path.relpath(tf, MAIN)
            tbl[e["addr"]] = e

# ---- Probe 2: Function terminating instructions ----
print("=== PROBE 2: FUNCTION TERMINATING INSTRUCTIONS (E3:669 CHECK) ===")
e3_terms = ("ret", "retf", "jmp", "iret", "iretd")
cl_rows = progress.classify([f["start"] for f in p.functions], main_funcs, mods)
in_scope_addrs = {r["addr"] for r in cl_rows if r["scope"] == "in"}
non_term_inscope = []
non_term_t3 = []
for f in p.functions:
    s, end = f["start"], f["end"]
    if s not in in_scope_addrs:
        continue
    ins_in = [a for a in p.insns if s <= a < end]
    last_a = max(ins_in) if ins_in else None
    last_i = p.insns[last_a] if last_a is not None else None
    mnem = last_i.mnemonic if last_i else "NONE"
    if mnem not in e3_terms:
        e = main_funcs.get(s, {})
        rec = (hex(s), e.get("name", f"fn_{s:05x}"), mnem, last_i.op_str if last_i else "", bool(e.get("src")), bool(e.get("ref")))
        non_term_inscope.append(rec)
        if e.get("src"):
            non_term_t3.append(rec)
print(f"In-scope functions NOT ending in {e3_terms}: {len(non_term_inscope)}")
print(f"Main T3 functions NOT ending in {e3_terms}: {len(non_term_t3)}")
for r in non_term_inscope:
    print(" ", r)

# ---- Probe 3: war.exe CONST pool alignment padding + live Watcom 10.0a test ----
print("\n=== PROBE 3: war.exe CONST POOL PADDING CHECK ===")
dobj = p.le.obj(analysis.DATA_OBJ)
dimg = bytes(p.image[analysis.DATA_OBJ])
lo, hi = 0x569d0, 0x58440
buf = dimg[lo - dobj.base:hi - dobj.base]
pos = 0
nonzero_pads = []
zero_pads = 0
strings_seen = 0
while pos < len(buf):
    if 0x20 <= buf[pos] < 0x7f:
        nul = buf.find(b"\x00", pos)
        if nul == -1:
            break
        s_end = nul + 1
        strings_seen += 1
        next4 = (s_end + 3) & ~3
        if next4 > s_end and next4 < len(buf):
            pad = buf[s_end:next4]
            if any(pad):
                nonzero_pads.append((hex(lo + pos), buf[pos:nul][:30], hex(lo + s_end), pad.hex()))
            else:
                zero_pads += 1
        pos = next4
    else:
        pos += 1
print(f"Strings scanned in 0x569d0..0x58440: {strings_seen}, all-zero 4B pads: {zero_pads}, non-zero bytes in [s_end, next4): {len(nonzero_pads)}")
for x in nonzero_pads[:10]:
    print(" ", x)

# Also inspect 0x569d0..0x58440 using actual fixup targets into CONST!
const_targets = sorted({t for s, (_, t) in p.fix_at.items() if lo <= t < hi})
gap_nonzero = []
gap_zero = []
for a, b in zip(const_targets, const_targets[1:]):
    seg = dimg[a - dobj.base:b - dobj.base]
    nul = seg.find(b"\x00")
    if nul != -1 and nul + 1 < len(seg):
        pad = seg[nul + 1:]
        if any(pad):
            gap_nonzero.append((hex(a), seg[:nul][:25], hex(a + nul + 1), len(pad), pad.hex()))
        else:
            gap_zero.append((hex(a), len(pad)))
print(f"Fixup-bounded CONST strings: {len(const_targets)}, gaps with 0-bytes: {len(gap_zero)}, gaps with NON-ZERO bytes: {len(gap_nonzero)}")
for x in gap_nonzero[:12]:
    print(" ", x)

# Live Watcom 10.0a probe: compile a 2-string -ot C file twice in two dirs under /tmp/opencode/cn-gemini
os.environ["TMPDIR"] = "/tmp/opencode/cn-gemini"
os.environ["WINEPREFIX"] = str(ROOT / "build/oldcc/wineprefix")
pdir = Path("/tmp/opencode/cn-gemini/p3")
pdir.mkdir(parents=True, exist_ok=True)
c_src = pdir / "s.c"
c_src.write_text('extern void f(const char *); void g(void) { f("abc"); f("defgh"); }\n')
o1, o2 = pdir / "a.obj", pdir / "b.obj"
m1 = match.compile_c(str(c_src), "-q -zl -bt=dos -s -ot -ol -5r -zp2", str(o1), cc="10.0a")
c_src2 = pdir / "sub" / "s.c"
c_src2.parent.mkdir(exist_ok=True)
c_src2.write_text(c_src.read_text())
m2 = match.compile_c(str(c_src2), "-q -zl -bt=dos -s -ot -ol -5r -zp2", str(o2), cc="10.0a")
_, c1 = m1.seg("CONST")
_, c2 = m2.seg("CONST")
print(f"Live 10.0a 2-string CONST (-ot -5r): len={len(c1.data)} bytes1={bytes(c1.data).hex()} bytes2={bytes(c2.data).hex()} equal={c1.data == c2.data}")
# Also test a 5-byte string ("abcde" + NUL = 6 bytes -> 2 pad bytes)
c_src3 = pdir / "s2.c"
c_src3.write_text('extern void f(const char *); void g(void) { f("abcde"); f("xyz"); }\n')
m3 = match.compile_c(str(c_src3), "-q -zl -bt=dos -s -ot -ol -5r -zp2", str(pdir / "c.obj"), cc="10.0a")
_, c3 = m3.seg("CONST")
print(f"Live 10.0a 6-byte+4-byte CONST (-ot -5r): len={len(c3.data)} bytes={bytes(c3.data).hex()} gap[6:8]={bytes(c3.data[6:8]).hex()}")

# ---- Probe 4: E0 re-audit of the 20 new T3 functions on main (a21772b) ----
print("\n=== PROBE 4: E0 RE-AUDIT OF 20 NEW T3 FUNCTIONS ON main (a21772b) ===")
base_t3 = {a for a, e in funcs_base.items() if e.get("src")}
main_t3 = {a for a, e in main_funcs.items() if e.get("src")}
new_t3 = sorted(main_t3 - base_t3)
print(f"Baseline T3 count: {len(base_t3)}, main T3 count: {len(main_t3)}, newly added T3: {len(new_t3)}")
main_by_link = {e["link_name"]: e for t in (main_funcs, main_datas) for e in t.values()}
idx = e0.OriginalIndex(p)
# Make short symlink to export-main under /tmp/opencode/cn-gemini/m
short_main = Path("/tmp/opencode/cn-gemini/m")
if short_main.is_symlink() or short_main.exists():
    short_main.unlink()
short_main.symlink_to(MAIN)
p4_out = Path("/tmp/opencode/cn-gemini/p4")
p4_out.mkdir(parents=True, exist_ok=True)
ok_cnt = 0
for a in new_t3:
    e = main_funcs[a]
    rel = e["src"]
    src_p = short_main / rel
    cc = match.file_cc(str(src_p))
    cf = match.file_cflags(str(src_p))
    obj_p = p4_out / f"{a:05x}.obj"
    mod = match.compile_c(str(src_p), cf, str(obj_p), cc=cc, includes=(str(short_main / "src" / "include"),))
    res = e0.match_module(p, mod, main_by_link, index=idx)
    fv = res["functions"].get(e["link_name"], {}).get("verdict", "MISSING")
    rv = res["region"]["verdict"]
    if fv == "MATCH" and rv == "MATCH":
        ok_cnt += 1
    print(f"  0x{a:05x} {e['name']:28s} {cc:5s} {rel:45s} fn={fv} reg={rv} data_segs={res['region']['metrics']['data_segments_checked']} lead={res['region']['metrics']['leading_bytes_len']}")
    if fv != "MATCH" or rv != "MATCH":
        print("    FINDINGS:", res["region"]["findings"][:4])
print(f"New T3 E0 audit summary: {ok_cnt}/{len(new_t3)} MATCH/MATCH")

# ---- Probe 5: E4 omf_extract.py bugs ----
print("\n=== PROBE 5: E4 omf_extract.py BUG REPRODUCTIONS ===")
lnames_b = b"\x00\x05_TEXT\x04CODE"
seg_b = bytes([0x69]) + struct.pack("<I", 12) + bytes([2, 3, 1])
ext_b = b"\x04_foo\x00"
led1 = bytes([1]) + struct.pack("<I", 0) + b"\xb8\x00\x00\x00\x00\x90"
fix1 = bytes([0x08, 0x01, 0x54])
led2 = bytes([1]) + struct.pack("<I", 6) + b"\xb8\x00\x00\x00\x00\xc3"
fix2 = struct.pack(">H", 0xe401) + bytes([0x8c])
raw_thread_obj = b"".join([
    _pack(0x80, b"\x04t.c"), _pack(0x96, lnames_b), _pack(0x99, seg_b),
    _pack(0x8c, ext_b), _pack(0xa1, led1), _pack(0x9d, fix1),
    _pack(0xa1, led2), _pack(0x9d, fix2), _pack(0x8b, b"\x00"),
])
m_parsed, _ = omf.parse_module(raw_thread_obj)
print(f"5a: wc1.omf.parse_module parsed cross-record THREAD fixups: {len(m_parsed.segments[0].fixups)}")
try:
    e4.raw_fixups(e4.read_records(raw_thread_obj))
    print("5a: e4.raw_fixups SUCCEEDED")
except Exception as ex:
    print(f"5a: e4.raw_fixups FAILED (CONFIRMED BUG): {type(ex).__name__}: {ex}")

# ---- Probe 6: Check R3 subtle bugs on main (a21772b) ----
print("\n=== PROBE 6: CHECK R3 BUGS ON main (a21772b) ===")
t3a_src = (MAIN / "tools/wc1/t3_audit.py").read_text()
for needle in ("def _default_system_headers", "def build_improved_audit_snapshot", "def _git("):
    i = t3a_src.find(needle)
    print(f"--- {needle} (pos={i}) ---")
    if i != -1:
        print(t3a_src[i:i+550])
