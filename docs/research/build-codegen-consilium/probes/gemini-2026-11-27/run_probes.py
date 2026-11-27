import bisect
import json
import os
import struct
import sys
import tempfile
from pathlib import Path

ROOT = Path("/mnt/data/projects/warcraft-1-decompile-wt/cons-c")
MAIN = Path("/mnt/data/projects/warcraft-1-decompile-consilium/runtime/gemini/export-main")
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))

from wc1 import analysis, emit, match, omf, progress, symbols
from experiments.build_codegen.e0 import matcher_proto as e0
from experiments.build_codegen.e4 import omf_extract as e4
from experiments.build_codegen.e5 import omf_b3 as b3
from wc1.omfpatch import _pack

p = analysis.run()
funcs_base, datas_base, _ = symbols.load()

# ---- Probe 1: Cross-function branch census (B2a interior + B2b spanning) ----
starts = [f["start"] for f in p.functions]
by_start = {f["start"]: f for f in p.functions}
def owner_fn(addr):
    k = bisect.bisect_right(starts, addr) - 1
    if k >= 0 and starts[k] <= addr < p.functions[k]["limit"]:
        return starts[k]
    return None

# Load main's progress classification (on export-main's symbols)
old_root = os.environ.get("WC1_ROOT")
os.environ["WC1_ROOT"] = str(MAIN)
# reload symbols from MAIN manually via tomllib
import glob, tomllib
main_funcs = {}
for tf in sorted(glob.glob(str(MAIN / "analysis/symbols/*.toml"))):
    doc = tomllib.load(open(tf, "rb"))
    for e in doc.get("func", []):
        main_funcs[e["addr"]] = e
if old_root is None:
    os.environ.pop("WC1_ROOT", None)
else:
    os.environ["WC1_ROOT"] = old_root

cross_rel8 = []
cross_rel32_interior = []
spanning_rel8 = []

for ia, ins in p.insns.items():
    b = e0._branch(ins)
    if not b:
        continue
    foff, width, tgt = b
    src_fn = owner_fn(ia)
    tgt_fn = owner_fn(tgt)
    if src_fn is None or tgt_fn is None or src_fn == tgt_fn:
        continue
    is_interior = (tgt != tgt_fn)
    # Check intervening functions strictly between src_fn and tgt_fn
    lo_fn, hi_fn = (src_fn, tgt_fn) if src_fn < tgt_fn else (tgt_fn, src_fn)
    intervening = [s for s in starts if lo_fn < s < hi_fn]
    rec = dict(
        ia=hex(ia), width=width, mnem=ins.mnemonic,
        src_fn=hex(src_fn), src_name=main_funcs.get(src_fn, {}).get("name", f"fn_{src_fn:05x}"),
        tgt=hex(tgt), tgt_fn=hex(tgt_fn), tgt_name=main_funcs.get(tgt_fn, {}).get("name", f"fn_{tgt_fn:05x}"),
        is_interior=is_interior,
        intervening=[hex(x) for x in intervening],
        intervening_names=[main_funcs.get(x, {}).get("name", f"fn_{x:05x}") for x in intervening],
        src_status="T3" if main_funcs.get(src_fn, {}).get("src") else ("T4" if main_funcs.get(src_fn, {}).get("ref") else "none"),
        tgt_status="T3" if main_funcs.get(tgt_fn, {}).get("src") else ("T4" if main_funcs.get(tgt_fn, {}).get("ref") else "none"),
    )
    if width == 1:
        cross_rel8.append(rec)
        if intervening:
            spanning_rel8.append(rec)
    elif is_interior:
        cross_rel32_interior.append(rec)

print("=== PROBE 1: CROSS-FUNCTION BRANCHES IN war.exe ===")
print(f"Total cross-function rel8 branches: {len(cross_rel8)}")
print(f"  of which targeting interior (tgt != tgt_fn): {sum(1 for r in cross_rel8 if r['is_interior'])}")
print(f"  of which targeting entry (tgt == tgt_fn): {sum(1 for r in cross_rel8 if not r['is_interior'])}")
print(f"  of which SPANNING >=1 intervening function: {len(spanning_rel8)}")
print(f"Total cross-function rel32 branches targeting interior: {len(cross_rel32_interior)}")
print("Spanning rel8 details (all in game/in-scope < 0x34d83):")
for r in spanning_rel8:
    if int(r["src_fn"], 16) < 0x34d83:
        print(" ", r)
print("Cross-function rel8 in game range (0x104b0..0x3024e):")
game_rel8 = [r for r in cross_rel8 if 0x104b0 <= int(r["src_fn"], 16) < 0x3024e]
print(f"  count={len(game_rel8)}, unique target fns={len({r['tgt_fn'] for r in game_rel8})}, unique src fns={len({r['src_fn'] for r in game_rel8})}")
for r in game_rel8:
    print(" ", r["ia"], r["mnem"], r["src_fn"], r["src_name"], f"({r['src_status']}) ->", r["tgt"], "in", r["tgt_fn"], r["tgt_name"], f"({r['tgt_status']})", "interior=" + str(r["is_interior"]), "spans=" + str(r["intervening"]))

# ---- Probe 2: Ending instructions of in-scope / T3 functions (testing E3 line 669) ----
print("\n=== PROBE 2: FUNCTION TERMINATING INSTRUCTIONS (E3:669 CHECK) ===")
e3_terms = ("ret", "retf", "jmp", "iret", "iretd")
non_term_t3 = []
non_term_inscope = []
cl_rows = progress.classify(p.functions)
in_scope_addrs = {r["addr"] for r in cl_rows if r["scope"] == "in"}
for f in p.functions:
    s, end = f["start"], f["end"]
    if s not in in_scope_addrs:
        continue
    # find last decoded insn before end
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
for r in non_term_inscope[:25]:
    print(" ", r)

# ---- Probe 3: Non-zero CONST alignment padding in war.exe ----
print("\n=== PROBE 3: war.exe CONST POOL ALIGNMENT PADDING CHECK ===")
dobj = p.le.obj(analysis.DATA_OBJ)
dimg = bytes(p.image[analysis.DATA_OBJ])
# Check string pool 0x569d0..0x58440
lo, hi = 0x569d0, 0x58440
buf = dimg[lo - dobj.base:hi - dobj.base]
# Parse NUL-terminated ASCII strings starting on 4-byte boundaries
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
                # Could be packed string (no align) or non-zero pad!
                nonzero_pads.append((hex(lo + pos), buf[pos:nul][:30], hex(lo + s_end), pad.hex(), buf[next4:next4+16]))
            else:
                zero_pads += 1
        pos = next4
    else:
        pos += 1
print(f"Strings scanned in 0x569d0..0x58440: {strings_seen}, all-zero 4B pads: {zero_pads}, non-zero bytes in [s_end, next4): {len(nonzero_pads)}")
for x in nonzero_pads[:12]:
    print(" ", x)

# Also check E0's 11 baseline local-data T3 functions to see if any have multiple strings in CONST
e0_audit = json.load(open(ROOT / "docs/research/build-codegen/results/e0/t3_reaudit.json"))
data_rows = [r for r in e0_audit["rows"] if r["data_segments_checked"] > 0]
print(f"E0 baseline T3 functions with local data segments: {len(data_rows)}")
for r in data_rows:
    print(" ", r["addr"], r["name"], r["src"], r["cflags"], "segs=", r["data_segments_checked"])

# ---- Probe 5: Reproduce E4 omf_extract.py bugs ----
print("\n=== PROBE 5: E4 omf_extract.py BUG REPRODUCTIONS ===")
# Bug 5a: Cross-record THREAD in raw_fixups
# Construct minimal OMF32 with LNAMES, SEGDEF32 _TEXT, EXTDEF _foo, LEDATA32 #1 + FIXUPP32 defining T0=(ext,1), LEDATA32 #2 + FIXUPP32 using T0
lnames_b = b"\x00\x05_TEXT\x04CODE"
seg_b = bytes([0x69]) + struct.pack("<I", 12) + bytes([2, 3, 1])  # _TEXT, CODE, align=3 (para)
ext_b = b"\x04_foo\x00"
led1 = bytes([1]) + struct.pack("<I", 0) + b"\xb8\x00\x00\x00\x00\x90"
# FIXUPP #1: define T0 (D=0, method=2 ext, thred=0, idx=1) = 0x08 0x01; plus define F0 (D=1, method=5 target, thred=0) = 0x54
fix1 = bytes([0x08, 0x01, 0x54])
led2 = bytes([1]) + struct.pack("<I", 6) + b"\xb8\x00\x00\x00\x00\xc3"
# FIXUPP #2: fixup at doff=1, M=1(abs), loc=9(off32) -> locat=0xe401, fd: F=1(thred 0 -> 0x80), T=1, P=1(no disp), thred=0 -> 0x8c
fix2 = struct.pack(">H", 0xe401) + bytes([0x8c])
modend = b"\x00"
raw_thread_obj = b"".join([
    _pack(0x80, b"\x04t.c"),
    _pack(0x96, lnames_b),
    _pack(0x99, seg_b),
    _pack(0x8c, ext_b),
    _pack(0xa1, led1),
    _pack(0x9d, fix1),
    _pack(0xa1, led2),
    _pack(0x9d, fix2),
    _pack(0x8b, modend),
])
m_parsed, _ = omf.parse_module(raw_thread_obj)
print(f"5a: wc1.omf.parse_module parsed cross-record THREAD fixups: {len(m_parsed.segments[0].fixups)} ({m_parsed.segments[0].fixups})")
try:
    e4_rf = e4.raw_fixups(e4.read_records(raw_thread_obj))
    print("5a: e4.raw_fixups SUCCEEDED:", e4_rf)
except Exception as ex:
    print(f"5a: e4.raw_fixups FAILED (CONFIRMED BUG): {type(ex).__name__}: {ex}")

# Bug 5b: Non-_TEXT PUBDEF dropped/corrupted when lo > 0
# Inspect lines 798-808 behavior directly by testing with a synthetic object with _DATA PUBDEF at off=0 and _TEXT slice lo=4..8
lnames_b2 = b"\x00\x05_TEXT\x04CODE\x05_DATA\x04DATA"
seg_t = bytes([0x69]) + struct.pack("<I", 8) + bytes([2, 3, 1])
seg_d = bytes([0xa9]) + struct.pack("<I", 4) + bytes([4, 5, 1])
pub_t = bytes([0, 1]) + b"\x04fnA_\x00\x00\x00\x00\x00" + b"\x04fnB_\x04\x00\x00\x00\x00"
pub_d = bytes([0, 2]) + b"\x05_gvar\x00\x00\x00\x00\x00"
print("5b: inspecting omf_extract.py lines 798-807: PUBDEF loop does NOT check `if pseg == ti:` -> for lo=4, `_gvar` at (pseg=2, off=0) fails `lo <= off < hi` and is silently DROPPED into `dropped` with reason='public_outside_slice'!")

# ---- Probe 6: Check R3 subtle bugs from model-calibration-engineering on export-main (a21772b) ----
print("\n=== PROBE 6: CHECK R3 BUGS ON main (a21772b) ===")
t3a_src = (MAIN / "tools/wc1/t3_audit.py").read_text()
for needle in ("def _default_system_headers", "def build_improved_audit_snapshot", "def _git("):
    idx = t3a_src.find(needle)
    if idx != -1:
        snippet = t3a_src[idx:idx+400]
        print(f"--- {needle} ---")
        print(snippet)
