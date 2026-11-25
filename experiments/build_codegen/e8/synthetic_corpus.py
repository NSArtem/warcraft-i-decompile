"""Corpus A: synthetic ground truth from Watcom 10.0a + the 10.0a `wlink`.

Every CU in `SPEC` is written here, compiled with the original Watcom C/C++
10.0a `wcc386` (via `wc1.oldcc`, under Wine) and linked, in `SPEC` order, with
the original 10.0a `wlink system dos4g` into one DOS/4GW LE executable under
`build/e8/`.  CU membership is therefore a fact of the recipe, and every
function address is cross-checked against the linker `.map`: the module list
gives each object's publics, the object's own `_TEXT`/`CONST`/`_DATA`/`_BSS`
segment sizes and SEGDEF alignment give its extent, and the builder *verifies*
that every map symbol equals the predicted address before any corpus record is
produced.  Nothing in this module infers a boundary from the bytes it later
scores.

The corpus is designed to exercise every edge case the contract requires:

* PARA-aligned CUs that leave 1..15 zero bytes before the next CU (`zero16`);
* CUs whose `_TEXT` is an exact multiple of 16 bytes, so the next CU starts
  with no padding at all (hidden `none16`);
* 16-byte-aligned interior functions (16-aligned `-4r -ot` CUs, plus one
  deliberately aligned interior start inside a byte-packed CU);
* a full codegen-style spectrum: `-ot -4r` (OPT, 16-byte function alignment),
  `-5r`/`-3r` (OPT, 4-byte), `-os` and `-od` (byte packing), `-d1+` (DBG),
  `-oa`, plus adjacent `-4r` and `-5r` OPT CUs;
* two CUs with cross-function shared epilogues (the E1 pattern);
* private strings, a literal pooled between two functions of one CU, a
  literal deliberately duplicated in another CU (no cross-CU pooling), and
  cross-CU `CONST`/`_DATA`/`_BSS` references that pollute the string-window
  and data-staircase heuristics on purpose;
* NASM `align=2` / `align=4` / `align=16` objects linked beside the C objects,
  including internal `align` directives that produce zero padding *inside* a
  single CU (the false-positive path of the zero-gap rules).
"""
import os
import re
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import capstone
from capstone import x86

from wc1 import analysis, codegen_survey, match, modules_scan, oldcc, omf, path
from experiments.build_codegen.e7.common import CORE_FLAGS, compile_short

from . import (EXPERIMENT, SCHEMA, SCRATCH, SPEC_ID, dump_json, sha256_bytes,
               sha256_file)

BASE_CFLAGS = match.BASE_CFLAGS          # "-q -zl -bt=dos" (10.0a spells -q as -zq)
STUB = "binb/wstub.exe"                  # the 10.0a DOS/4GW stub
MARKER = "{NOP}"                         # where a per-function nop pad goes

# ---------------------------------------------------------------------------
# CU specification
# ---------------------------------------------------------------------------
# flags: codegen flags after BASE_CFLAGS. mod16: required _TEXT length mod 16
# (this fixes the zero gap the *next* CU sees). start_mod16: indices of
# functions that must start 16-aligned.  links: none - order in SPEC is the
# link order.

OPT4 = "-s -ot -ol -4r -zp2"
OPT5 = "-s -ot -ol -5r -zp2"
OPT3 = "-s -ot -ol -3r -zp2"
OS4 = "-s -os -ol -4r -zp2"
OD4 = "-s -od -4r -zp2"
DBG4 = "-s -ot -ol -4r -d1+ -zp2"
OA4 = "-s -ot -oa -ol -4r -zp2"

GLOBALS = """
int e8_shared_counter;
int e8_pair_flag;
int e8_shared_table[4] = { 11, 22, 33, 44 };
char e8_text[] = "e8 mutable text";
char e8_class;
"""

EXTERNS = """
extern int e8_shared_counter;
extern int e8_pair_flag;
extern int e8_shared_table[4];
extern char e8_text[];
extern char e8_class;
extern int e8_flag;
void e8_ext(int v);
"""

# The corpus is only valid when these designed cases actually appear; the build
# asserts the counts instead of silently shipping a weaker corpus.
EXPECTED = {
    "boundaries": 15, "same_cu_pairs": 35,
    "zero16_boundaries": 5, "zero4_boundaries": 1, "zero2_boundaries": 1,
    "none16_boundaries": 2, "data16_boundaries": 1,
    "same_cu_none16_candidates": 1, "same_cu_zero16_candidates": 1,
    "same_cu_zero4_candidates": 1,
}

SPEC = [
    dict(id="g1_basic", flags=OPT4, mod16=4, funcs=[
        ("e8_g1_sum", "int e8_g1_sum(int *p, int n)\n{\n    int i, s = 0;\n    {NOP}"
                      "    for (i = 0; i < n; i++)\n        s += p[i] * 3;\n    return s;\n}\n"),
        ("e8_g1_clamp", "int e8_g1_clamp(int v, int lo, int hi)\n{\n    {NOP}if (v < lo)\n"
                        "        return lo;\n    if (v > hi)\n        return hi;\n    return v;\n}\n"),
        ("e8_g1_mix", "int e8_g1_mix(int a, int b)\n{\n    {NOP}return (a ^ b) + (a & 7) - (b >> 2);\n}\n"),
        ("e8_g1_tail", "int e8_g1_tail(int a)\n{\n    {NOP}return a * 13 + 101;\n}\n"),
    ]),
    dict(id="g2_basic", flags=OPT4, mod16=12, funcs=[
        ("e8_g2_or", "int e8_g2_or(int a, int b)\n{\n    {NOP}return (a | b) + 17;\n}\n"),
        ("e8_g2_loop", "int e8_g2_loop(int *p, int n)\n{\n    int i, s = 1;\n    {NOP}"
                       "    for (i = 0; i < n; i++)\n        s = s * 2 + p[i];\n    return s;\n}\n"),
        ("e8_g2_tail", "int e8_g2_tail(int a)\n{\n    {NOP}return a - 23;\n}\n"),
    ]),
    dict(id="g3_exact16", flags=OPT4, mod16=0, funcs=[
        ("e8_g3_a", "int e8_g3_a(int a)\n{\n    {NOP}return a * 3 + 29;\n}\n"),
        ("e8_g3_tail", "int e8_g3_tail(int a)\n{\n    {NOP}return a + 31;\n}\n"),
    ]),
    dict(id="g4_exact16_os", flags=OS4, mod16=0, funcs=[
        ("e8_g4_a", "int e8_g4_a(int a, int b)\n{\n    {NOP}return a * b + 37;\n}\n"),
        ("e8_g4_b", "int e8_g4_b(int a)\n{\n    {NOP}return a - 41;\n}\n"),
        ("e8_g4_tail", "int e8_g4_tail(int a)\n{\n    {NOP}return a ^ 43;\n}\n"),
    ]),
    dict(id="g5_os", flags=OS4, mod16=5, funcs=[
        ("e8_g5_a", "int e8_g5_a(int a)\n{\n    {NOP}return a + 47;\n}\n"),
        ("e8_g5_b", "int e8_g5_b(int a, int b)\n{\n    {NOP}return a * 3 - b;\n}\n"),
        ("e8_g5_tail", "int e8_g5_tail(int a)\n{\n    {NOP}return a * 53 + 59;\n}\n"),
    ]),
    dict(id="g6_od", flags=OD4, mod16=7, start_mod16={1}, funcs=[
        ("e8_g6_a", "int e8_g6_a(int a, int b)\n{\n    int r = a + b;\n    {NOP}    r = r * 61;\n    return r;\n}\n"),
        ("e8_g6_b", "int e8_g6_b(int a)\n{\n    int r = a - 67;\n    {NOP}    r = r ^ 71;\n    return r;\n}\n"),
        ("e8_g6_tail", "int e8_g6_tail(int a)\n{\n    {NOP}return a + 73;\n}\n"),
    ]),
    dict(id="g7_dbg", flags=DBG4, mod16=2, data="static int e8_g7_state;\n", funcs=[
        ("e8_g7_a", "int e8_g7_a(int *p, int n)\n{\n    int i, s = 0;\n    {NOP}"
                    "    for (i = 0; i < n; i++)\n        s += p[i] + 79;\n"
                    "    e8_g7_state = s;\n    return s;\n}\n"),
        ("e8_g7_b", "int e8_g7_b(int a, int b)\n{\n    {NOP}e8_g7_state += a;\n"
                    "    return (a & b) + 83 + e8_g7_state;\n}\n"),
        ("e8_g7_tail", "int e8_g7_tail(int a)\n{\n    {NOP}return a - 89;\n}\n"),
    ]),
    dict(id="g8_5r", flags=OPT5, mod16=9, funcs=[
        ("e8_g8_a", "int e8_g8_a(int a, int b)\n{\n    {NOP}return a * 97 + b;\n}\n"),
        ("e8_g8_b", "int e8_g8_b(int *p, int n)\n{\n    int i, s = 0;\n    {NOP}"
                    "    for (i = 0; i < n; i++)\n        s += p[i];\n    return s * 101;\n}\n"),
        ("e8_g8_c", "int e8_g8_c(int a)\n{\n    {NOP}return a ^ 103;\n}\n"),
        ("e8_g8_tail", "int e8_g8_tail(int a)\n{\n    {NOP}return a + 107;\n}\n"),
    ]),
    dict(id="g9_4r", flags=OPT4, mod16=6, funcs=[
        ("e8_g9_a", "int e8_g9_a(int a)\n{\n    {NOP}return a * 109 + 1;\n}\n"),
        ("e8_g9_b", "int e8_g9_b(int a, int b)\n{\n    {NOP}return (a - b) * 113;\n}\n"),
        ("e8_g9_tail", "int e8_g9_tail(int a)\n{\n    {NOP}return a | 127;\n}\n"),
    ]),
    dict(id="g10_3r", flags=OPT3, mod16=3, funcs=[
        ("e8_g10_a", "int e8_g10_a(int a, int b)\n{\n    {NOP}return a * 131 + b;\n}\n"),
        ("e8_g10_b", "int e8_g10_b(int a)\n{\n    {NOP}return a + 137;\n}\n"),
        ("e8_g10_tail", "int e8_g10_tail(int a)\n{\n    {NOP}return a ^ 139;\n}\n"),
    ]),
    dict(id="g11_oa", flags=OA4, mod16=11, funcs=[
        ("e8_g11_a", "int e8_g11_a(int *p, int n, int v)\n{\n    int i, s = 0;\n    {NOP}"
                     "    for (i = 0; i < n; i++)\n        s += p[i] * v;\n    return s;\n}\n"),
        ("e8_g11_b", "int e8_g11_b(int a, int b)\n{\n    {NOP}return (a ^ b) + 149;\n}\n"),
        ("e8_g11_tail", "int e8_g11_tail(int a)\n{\n    {NOP}return a - 151;\n}\n"),
    ]),
    # The E1 shared-epilogue pattern: k1 ends in `xor eax,eax; ret`, and the
    # compiler routes k2/k3's early exit to that return across the function
    # boundary (verified in the build assertions below).
    dict(id="g12_epi4", flags=OPT4, mod16=5, externs="extern int e8_flag;\nvoid e8_ext(int v);\n",
         funcs=[
        ("e8_g12_a", "int e8_g12_a(int a, int b)\n{\n    {NOP}if (a > 10 || b < 2)\n"
                     "        return 0;\n    return 1;\n}\n"),
        ("e8_g12_b", "void e8_g12_b(void)\n{\n    {NOP}if (e8_flag != 0)\n        e8_ext(0);\n}\n"),
        ("e8_g12_c", "void e8_g12_c(void)\n{\n    {NOP}if (e8_flag != 0)\n        e8_ext(1);\n}\n"),
    ]),
    dict(id="g13_epi5", flags=OPT5, mod16=8, externs="extern int e8_flag;\nvoid e8_ext(int v);\n",
         funcs=[
        ("e8_g13_a", "int e8_g13_a(int a, int b)\n{\n    {NOP}if (a > 20 || b < 3)\n"
                     "        return 0;\n    return 1;\n}\n"),
        ("e8_g13_b", "void e8_g13_b(void)\n{\n    {NOP}if (e8_flag != 0)\n        e8_ext(2);\n}\n"),
        ("e8_g13_c", "void e8_g13_c(void)\n{\n    {NOP}if (e8_flag != 0)\n        e8_ext(3);\n}\n"),
    ]),
    dict(id="g14_strings", flags=OS4, mod16=1, funcs=[
        ("e8_g14_a", "int e8_g14_a(void)\n{\n    const char *s = \"e8 shared literal\";\n    {NOP}"
                     "    return s[0] + 157;\n}\n"),
        ("e8_g14_b", "int e8_g14_b(void)\n{\n    const char *s = \"e8 shared literal\";\n    {NOP}"
                     "    return s[0] + 163;\n}\n"),
        ("e8_g14_tail", "int e8_g14_tail(void)\n{\n    const char *s = \"e8 private alpha\";\n    {NOP}"
                        "    return s[2] + 167;\n}\n"),
    ]),
    dict(id="g15_strings2", flags=OS4, mod16=8, funcs=[
        ("e8_g15_a", "int e8_g15_a(void)\n{\n    const char *s = \"e8 shared literal\";\n    {NOP}"
                     "    return s[3] + 173;\n}\n"),
        ("e8_g15_tail", "int e8_g15_tail(void)\n{\n    const char *s = \"e8 private beta\";\n    {NOP}"
                        "    return s[4] + 179;\n}\n"),
    ]),
    # --- hand-written NASM objects -----------------------------------------
    # `align N, db 0` pads with zero bytes, exactly like the linker's padding
    # between objects but *inside* one object: the zero-gap rules then fire on
    # a same-CU pair (designed false positives).
    dict(id="n1_align2", kind="asm", align=2, mod16=15, funcs=[
        dict(name="e8_n1_a", body=["    mov eax, 199", "    ret"]),
        dict(name="e8_n1_b", body=["    mov eax, 211", "    add eax, 1", "    ret"]),
        dict(name="e8_n1_tail", body=["    mov eax, 223", "    ret"]),
    ]),
    dict(id="n2_align4", kind="asm", align=4, mod16=12, funcs=[
        dict(name="e8_n2_a", body=["    mov eax, 227", "    ret"]),
        dict(name="e8_n2_b", pre=["    align 4, db 0"], body=["    mov eax, 229", "    ret"]),
        dict(name="e8_n2_tail", pre=["    align 4, db 0"], body=["    mov eax, 233", "    ret"]),
    ]),
    dict(id="n3_align16", kind="asm", align=16, mod16=12, funcs=[
        dict(name="e8_n3_a", body=["    mov eax, 239", "    ret"]),
        dict(name="e8_n3_b", pre=["    align 16, db 0"], body=["    mov eax, 241", "    ret"]),
        dict(name="e8_n3_tail", pre=["    align 16, db 0"], body=["    mov eax, 251", "    ret"]),
    ]),
    dict(id="g16_globals", flags=OPT4, mod16=10,
         data=GLOBALS + 'static const char e8_incode[] = "e8 incode";\n',
         externs="extern int e8_flag;\nvoid e8_ext(int v);\n",
         funcs=[
        # A static const array goes into 10.0a's _TEXT (the documented in-code
        # data case), so the first function starts at +16: the map still proves
        # the CU start, but the zero-gap rule sees data, not padding.
        ("e8_g16_data", "int e8_g16_data(int i)\n{\n    int v = e8_shared_table[i & 3] + e8_incode[0];\n    {NOP}"
                        "    return v;\n}\n"),
        # references _BSS (high) -> an inversion inside the CU against the
        # _DATA reference above (a designed staircase false positive)
        ("e8_g16_bss", "int e8_g16_bss(int v)\n{\n    const char *s = \"e8 g16 bss\";\n    {NOP}"
                       "    e8_shared_counter = v;\n    e8_class = (char)v;\n"
                       "    return e8_shared_counter + s[0];\n}\n"),
        ("e8_g16_tail", "int e8_g16_tail(int a)\n{\n    {NOP}e8_flag = a;\n    e8_ext(a);\n"
                        "    return a + 181;\n}\n"),
    ]),
    dict(id="g17_uses", flags=OPT4, mod16=14, externs=EXTERNS + "int e8_g17_a(int v);\n", funcs=[
        ("e8_g17_a", "int e8_g17_a(int v)\n{\n    {NOP}e8_shared_counter += v + e8_shared_table[1];\n"
                     "    return e8_shared_counter;\n}\n"),
        # calls the previous function (an intra-CU call locality true positive)
        ("e8_g17_b", "int e8_g17_b(void)\n{\n    const char *s = \"e8 g17 b\";\n    {NOP}"
                     "    return e8_g17_a(3) + e8_text[1] + e8_class + s[0];\n}\n"),
        # the first of the only two readers of e8_pair_flag (cross-CU FP)
        ("e8_g17_tail", "int e8_g17_tail(int a)\n{\n    const char *s = \"e8 g17 t\";\n    {NOP}"
                        "    return a + e8_text[2] + e8_pair_flag * 191 + s[0];\n}\n"),
    ]),
    dict(id="g18_uses2", flags=OPT4, mod16=0, externs=EXTERNS, funcs=[
        # the second (and last) reader of e8_pair_flag: an exclusive-data-sharing
        # false positive across the real g17/g18 CU boundary
        ("e8_g18_a", "int e8_g18_a(int v)\n{\n    const char *s = \"e8 g18 a\";\n    {NOP}"
                     "    e8_pair_flag = v;\n    return e8_pair_flag + s[0];\n}\n"),
        # calls e8_ext in the *next* CU: a call-locality false positive at a boundary
        ("e8_g18_tail", "int e8_g18_tail(int a)\n{\n    {NOP}e8_ext(a);\n"
                        "    return a + e8_text[3] + 193;\n}\n"),
    ]),
    dict(id="g19_helpers", flags=OPT4, mod16=12, data="int e8_flag;\n", externs="extern char e8_class;\n",
         funcs=[
        ("e8_ext", "void e8_ext(int v)\n{\n    {NOP}e8_class = (char)(v + 1);\n}\n"),
        ("e8_help", "int e8_help(int a)\n{\n    const char *s = \"e8 help\";\n    {NOP}"
                    "    return a + 197 + s[0];\n}\n"),
        ("e8_help_tail", "int e8_help_tail(int a)\n{\n    const char *s = \"e8 help tail\";\n    {NOP}"
                         "    return a * 199 + s[0];\n}\n"),
    ]),
]


# ---------------------------------------------------------------------------
# source text
# ---------------------------------------------------------------------------
def _nop_pragmas(counts):
    lines = []
    for k in sorted({c for c in counts if c}):
        seq = " ".join('"nop"' for _ in range(k))
        lines.append("#pragma aux e8_nop%d = %s parm [] modify exact [];" % (k, seq))
    for k in sorted({c for c in counts if c}):
        lines.append("void e8_nop%d(void);" % k)
    return lines


def source_text(cu, nops):
    """The source of one CU with `nops[index]` inline nop bytes added."""
    if cu.get("kind") == "asm":
        lines = ["; E8 synthetic corpus CU %s (generated; do not edit)" % cu["id"],
                 "segment _TEXT public align=%d class=CODE use32" % cu["align"]]
        for i, f in enumerate(cu["funcs"]):
            lines += list(f.get("pre", ()))
            lines += ["global %s" % f["name"], "%s:" % f["name"]]
            body = list(f["body"])
            k = nops.get(i, 0)
            lines += body[:-1] + ["    nop"] * k + body[-1:] if k else body
        return "\n".join(lines) + "\n"
    lines = ["/* E8 synthetic corpus CU %s (generated; do not edit) */" % cu["id"]]
    lines += _nop_pragmas(nops.values())
    if cu.get("data"):
        lines.append(cu["data"].strip("\n"))
    if cu.get("externs"):
        lines.append(cu["externs"].strip("\n"))
    for i, (_name, body) in enumerate(cu["funcs"]):
        k = nops.get(i, 0)
        lines.append(body.replace(MARKER, ("e8_nop%d();\n    " % k) if k else "").rstrip("\n"))
    return "\n\n".join(lines) + "\n"


def source_path(cu):
    ext = ".asm" if cu.get("kind") == "asm" else ".c"
    return SCRATCH / "src" / (cu["id"] + ext)


def object_path(cu):
    return SCRATCH / "obj" / (cu["id"] + ".obj")


# ---------------------------------------------------------------------------
# compile and assemble
# ---------------------------------------------------------------------------
def _compile(cu, nops):
    src = source_path(cu)
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text(source_text(cu, nops), encoding="utf-8", newline="\n")
    out = object_path(cu)
    out.parent.mkdir(parents=True, exist_ok=True)
    if cu.get("kind") == "asm":
        cmd = ["nasm", "-O0", "-f", "obj", "-w-number-overflow", "-o", str(out), str(src)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"nasm failed for {cu['id']}:\n{r.stdout}{r.stderr}")
        return omf.parse_object(str(out))
    return compile_short(str(src), BASE_CFLAGS + " " + cu["flags"], str(out), cc="10.0a")


def _code_segment(mod, cu):
    segs = [s for s in mod.segments if s.cls == "CODE"]
    if len(segs) != 1:
        raise RuntimeError(f"{cu['id']}: expected one CODE segment, got {[s.name for s in segs]}")
    return segs[0]


def _func_offsets(mod, cu):
    """[(spec name, offset)] in source order, checked against the object."""
    seg = _code_segment(mod, cu)
    by_off = {}
    for name, (si, off) in mod.publics.items():
        if si == mod.segments.index(seg) + 1:
            by_off.setdefault(off, []).append(name)
    order = sorted(by_off)
    if len(order) != len(cu["funcs"]):
        raise RuntimeError(f"{cu['id']}: {len(order)} code publics, spec has {len(cu['funcs'])}")
    for off, names in by_off.items():
        if len(names) != 1:
            raise RuntimeError(f"{cu['id']}: aliased publics at +{off:#x}: {names}")
    return [(cu["funcs"][k].get("name") if cu.get("kind") == "asm" else cu["funcs"][k][0],
             off) for k, off in enumerate(order)]


def _solve_nops(cu):
    """Compile until the required start residues and total length mod 16 hold."""
    nops = {}
    last = len(cu["funcs"]) - 1
    targets = set(cu.get("start_mod16") or ())
    for _ in range(4):
        mod = _compile(cu, nops)
        seg = _code_segment(mod, cu)
        offs = [off for _n, off in _func_offsets(mod, cu)]
        bad = {i: offs[i] % 16 for i in targets if i > 0 and offs[i] % 16}
        total_ok = len(seg.data) % 16 == cu["mod16"] % 16
        if not bad and total_ok:
            return nops
        for i in bad:
            # a function's start moves when the *preceding* function grows
            nops[i - 1] = nops.get(i - 1, 0) + ((16 - offs[i] % 16) % 16)
        if not total_ok:
            # only the last function may grow without moving another function
            nops[last] = nops.get(last, 0) + ((cu["mod16"] - len(seg.data)) % 16)
    offs = [off for _n, off in _func_offsets(_compile(cu, nops), cu)]
    raise RuntimeError(
        f"{cu['id']}: cannot reach mod16={cu['mod16']} start targets={targets}; "
        f"offsets={offs} nops={nops}")


# ---------------------------------------------------------------------------
# link with the original 10.0a wlink
# ---------------------------------------------------------------------------
def _wine(win_argv, cwd, timeout=180):
    env = oldcc.wine_env()
    oldcc.ensure_prefix(env)
    env["WATCOM"] = oldcc.win_path(oldcc.root())
    exe = win_argv[0]
    argv = [oldcc.find_wine(), oldcc.win_path(exe)] + [oldcc.win_path(a) if os.path.isabs(a) else a
                                                       for a in win_argv[1:]]
    return subprocess.run(argv, env=env, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def link(objs, exe, mapfile, cwd=None):
    cwd = Path(cwd or SCRATCH)
    cwd.mkdir(parents=True, exist_ok=True)
    stub = oldcc.win_path(os.path.join(oldcc.root(), STUB))
    lnk = cwd / (Path(exe).stem + ".lnk")
    lines = [
        "system begin dos4g",
        "  option osname='DOS/4G'",
        "  option stub=%s" % stub,
        "  format os2 le",
        "end",
        "system dos4g",
        "name %s" % Path(exe).name,
    ]
    for o in objs:
        lines.append("file %s" % Path(o).relative_to(cwd).as_posix())
    lines += ["option map=%s" % Path(mapfile).name, "option quiet", "option stack=4096"]
    lnk.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    linker = os.path.join(oldcc.root(), "binnt", "wlink.exe")
    r = _wine([linker, "@" + str(lnk)], cwd=str(cwd))
    if r.returncode != 0 or not (cwd / Path(exe).name).exists():
        raise RuntimeError(f"wlink (10.0a) failed:\n{r.stdout}\n{r.stderr}")
    return cwd / Path(exe).name, cwd / Path(mapfile).name


_SEG_ROW = re.compile(r"^(\S+)\s+(\S+)(?:\s+(\S+))?\s+([0-9a-fA-F]{4}):([0-9a-fA-F]{8})\s+([0-9a-fA-F]{8})\s*$")
_SYM_ROW = re.compile(r"^([0-9a-fA-F]{4}):([0-9a-fA-F]{8})[*+]?\s+(\S+)\s*$")
_MOD_ROW = re.compile(r"^Module: (\S+?)\((.*)\)\s*$")


def parse_map(text):
    """{'segments': [(name, cls, group, seg, off, size)], 'modules': [(obj, {sym: (seg, total)})]}"""
    segments, modules, cur = [], [], None
    in_map = False
    for line in text.splitlines():
        m = _MOD_ROW.match(line.strip())
        if m:
            in_map = True
            cur = {"obj": m.group(1), "syms": {}}
            modules.append(cur)
            continue
        if not in_map:
            m = _SEG_ROW.match(line.strip())
            if m:
                name, cls, group, seg, off, size = m.groups()
                if name != "Segment":
                    segments.append((name, cls, group, int(seg, 16), int(off, 16), int(size, 16)))
            continue
        m = _SYM_ROW.match(line.strip())
        if m and cur is not None:
            seg, off, sym = m.groups()
            cur["syms"][sym] = (int(seg, 16), int(off, 16))
    if not modules:
        raise RuntimeError("linker map has no module listing")
    return {"segments": segments, "modules": modules}


def _align_bytes(code):
    # OMF SEGDEF alignment codes: 1 byte, 2 word, 3 paragraph, 4 page, 5 dword.
    return {1: 1, 2: 2, 3: 16, 4: 256, 5: 4}.get(code, 1)


def _align_up(v, a):
    return (v + a - 1) // a * a


def placements(modules_by_id, mapinfo, code_base=0):
    """Ground-truth placement of every object's code and data contributions.

    Derived from the recipe (link order + each object's own SEGDEF size and
    alignment) and *verified* against every symbol the linker map lists.
    Returns ({cu_id: code_extent}, {cu_id: [(seg_name, lo, hi)]}, segment spans).
    """
    seg_names = [s[0] for s in mapinfo["segments"]]
    if not seg_names or seg_names[0] != "_TEXT":
        raise RuntimeError(f"unexpected map segment table: {mapinfo['segments']}")
    spans = {}
    for name, cls, group, seg, off, size in mapinfo["segments"]:
        spans.setdefault(name, []).append((seg, off, off + size))
    # code: every object contributes its CODE segment, placed at its own alignment
    cursor, code_spans, syms_by_id = 0, {}, {}
    for m in mapinfo["modules"]:
        cu = modules_by_id.get(Path(m["obj"]).stem)
        if cu is None:
            raise RuntimeError(f"map module {m['obj']} is not in the recipe")
        mod = cu["mod"]
        seg = _code_segment(mod, cu)
        align = _align_bytes(seg.align)
        base = _align_up(cursor, align)
        code_spans[cu["id"]] = (base, base + len(seg.data))
        syms_by_id[cu["id"]] = m["syms"]
        cursor = base + len(seg.data)
    if spans.get("_TEXT") and len(spans["_TEXT"]) == 1:
        seg, lo, hi = spans["_TEXT"][0]
        if (lo, hi) != (0, cursor):
            raise RuntimeError(f"map _TEXT span {(lo, hi)} != predicted {(0, cursor)}")
    # data: one DGROUP object; each segment name has its own fixed start offset
    # (the map's segment table) and is filled in module order
    data_cursor = {}
    for name, cls, group, seg, off, size in mapinfo["segments"]:
        if name != "_TEXT":
            data_cursor[name] = off
    data_spans = {cu["id"]: [] for cu in modules_by_id.values()}
    for m in mapinfo["modules"]:
        cu = modules_by_id[Path(m["obj"]).stem]
        for s in cu["mod"].segments:
            if s.cls == "CODE" or s.cls not in ("DATA", "BSS"):
                continue
            name = s.name
            if name not in data_cursor:
                if len(s.data):
                    raise RuntimeError(f"{cu['id']}: data segment {name} absent from the map")
                continue
            a = _align_bytes(s.align)
            base = _align_up(data_cursor[name], a)
            data_spans[cu["id"]].append((name, base, base + len(s.data)))
            data_cursor[name] = base + len(s.data)
    # verify every symbol the map lists
    for m in mapinfo["modules"]:
        cu = modules_by_id[Path(m["obj"]).stem]
        mod = cu["mod"]
        want = {}
        code_seg = _code_segment(mod, cu)
        code_index = mod.segments.index(code_seg) + 1
        for name, (si, off) in mod.publics.items():
            if si == code_index:
                want[name] = code_spans[cu["id"]][0] + off
        for name, (si, off) in mod.publics.items():
            if si == code_index:
                continue
            seg = mod.segments[si - 1]
            for sname, lo, hi in data_spans[cu["id"]]:
                if sname == seg.name:
                    want[name] = lo + off
                    break
        for sym, (seg, off) in m["syms"].items():
            if sym not in want:
                raise RuntimeError(f"{cu['id']}: map symbol {sym} not predicted")
            if want[sym] != off:
                raise RuntimeError(f"{cu['id']}: map symbol {sym} at {off:#x}, "
                                   f"recipe predicts {want[sym]:#x}")
        # every predicted public must be listed
        listed = {s for s in m["syms"]}
        missing = sorted(set(want) - listed)
        if missing:
            raise RuntimeError(f"{cu['id']}: map lacks predicted symbols {missing}")
    # segment spans in the data object: base is a map address
    data_object = {}
    for name, cls, group, seg, off, size in mapinfo["segments"]:
        if name == "_TEXT":
            continue
        data_object[name] = (seg, off, off + size)
    code_spans = {k: (lo + code_base, hi + code_base) for k, (lo, hi) in code_spans.items()}
    data_spans = {k: [(n, lo, hi) for n, lo, hi in v] for k, v in data_spans.items()}
    return code_spans, data_spans, data_object


# ---------------------------------------------------------------------------
# decode helpers
# ---------------------------------------------------------------------------
def _md():
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    return md


def decode_range(md, data, base, lo, hi):
    """Linear decode of [lo, hi); raises if the bytes do not decode exactly."""
    out, a = [], lo
    while a < hi:
        ins = next(md.disasm(bytes(data[a - base:a - base + 16]), a, 1), None)
        if ins is None or a + ins.size > hi:
            raise RuntimeError(f"cannot decode at {a:#x} in [{lo:#x}, {hi:#x})")
        out.append(ins)
        a += ins.size
    return out


def populate_insns(prog, functions):
    """Decode every ground-truth function body into `prog.insns`.

    `codegen_survey.feat` (the production style signal) reads `Program.insns`;
    for the synthetic image the exact function extents are known, so the index
    is built from them instead of from the discovery heuristics.
    """
    md = _md()
    index = {}
    for f in functions:
        insns = decode_range(md, prog.cbytes, prog.code.base, f["start"], f["end"])
        be = body_end(insns, f["end"])
        for i in insns:
            if i.address < be:
                index[i.address] = i
        f["body_end"] = be
        f["size"] = be - f["start"]
        tail = prog.cbytes[be - prog.code.base:f["end"] - prog.code.base]
        if tail and any(tail) and prog._skip_filler(be, f["end"]) != f["end"]:
            raise RuntimeError(f"{f['name']}: unexpected non-filler tail {tail.hex()} after {be:#x}")
    prog.insns = index
    return prog


def program(corpus):
    """`analysis.Program` of the built corpus with the ground-truth insn index."""
    prog = analysis.Program(corpus["_exe"])
    funcs = [dict(f) for f in corpus["functions"]]
    populate_insns(prog, funcs)
    for src, got in zip(corpus["functions"], funcs):
        src["body_end"] = got["body_end"]
    return prog


def body_end(insns, end):
    """End of the last terminator instruction (production: a function body ends there)."""
    terms = [i.address + i.size for i in insns if i.mnemonic in analysis.TERMINATORS]
    return max(terms) if terms else end


# ---------------------------------------------------------------------------
# the build
# ---------------------------------------------------------------------------
def _digest_spec():
    payload = []
    for cu in SPEC:
        payload.append(dict(id=cu["id"], kind=cu.get("kind", "c"), flags=cu.get("flags"),
                            align=cu.get("align"), mod16=cu["mod16"],
                            start_mod16=sorted(cu.get("start_mod16") or ()),
                            source=source_text(cu, {}),
                            names=[f.get("name") if isinstance(f, dict) else f[0] for f in cu["funcs"]]))
    return sha256_bytes((SPEC_ID + "\n" + repr(payload)).encode())


def build(force=False):
    """Build (or reuse) the corpus; returns the corpus record (JSON-serializable)."""
    from . import digest as json_digest
    spec = _digest_spec()
    cached = SCRATCH / "corpus.json"
    exe = SCRATCH / "e8synth.exe"
    if not force and cached.exists() and exe.exists():
        rec = __import__("json").loads(cached.read_text(encoding="utf-8"))
        if rec.get("spec_sha256") == spec and all("limit" in f for f in rec.get("functions", ())):
            rec["_exe"] = str(exe)
            return rec
    SCRATCH.mkdir(parents=True, exist_ok=True)
    (SCRATCH / "src").mkdir(exist_ok=True)
    (SCRATCH / "obj").mkdir(exist_ok=True)
    plan = {}
    mods = {}
    for cu in SPEC:
        plan[cu["id"]] = _solve_nops(cu)
        mods[cu["id"]] = _compile(cu, plan[cu["id"]])
        cu["mod"] = mods[cu["id"]]
    objs = [object_path(cu) for cu in SPEC]
    exe_path, map_path = link(objs, exe, SCRATCH / "e8synth.map")
    mapinfo = parse_map(map_path.read_text(encoding="utf-8", errors="replace"))
    by_id = {cu["id"]: cu for cu in SPEC}
    prog = analysis.Program(str(exe_path))
    if not prog.code.base == 0x10000:
        raise RuntimeError(f"unexpected code base {prog.code.base:#x}")
    code_spans, data_spans, data_object = placements(by_id, mapinfo, prog.code.base)
    expected_size = max(hi for _lo, hi in code_spans.values()) - prog.code.base
    if prog.code.vsize != expected_size:
        raise RuntimeError(f"code object {prog.code.vsize:#x} != recipe {expected_size:#x}")

    md = _md()
    funcs, cus = [], []
    for cu in SPEC:
        start, end = code_spans[cu["id"]]
        fns = []
        for name, off in _func_offsets(mods[cu["id"]], cu):
            s = start + off
            nxt = next((start + o for n, o in _func_offsets(mods[cu["id"]], cu) if start + o > s), end)
            fns.append({"start": s, "end": nxt, "name": name.rstrip("_"), "cu": cu["id"]})
        fns.sort(key=lambda f: f["start"])
        fns[-1]["end"] = end
        funcs.extend(fns)
        cus.append({"id": cu["id"], "kind": cu.get("kind", "c"), "flags": cu.get("flags"),
                    "compiler": "10.0a", "align": cu.get("align"),
                    "start": start, "end": end, "functions": [f["start"] for f in fns],
                    "nops": plan[cu["id"]], "source_sha256": sha256_bytes(
                        source_text(cu, plan[cu["id"]]).encode())})
    funcs.sort(key=lambda f: f["start"])
    if len({f["start"] for f in funcs}) != len(funcs):
        raise RuntimeError("two functions share a start address")

    # bodies, gaps and the instruction index that the production style survey needs
    populate_insns(prog, funcs)
    for k, f in enumerate(funcs):
        f["limit"] = funcs[k + 1]["start"] if k + 1 < len(funcs) else prog.code.base + prog.code.vsize

    labels = []
    for i in range(1, len(funcs)):
        a, b = funcs[i - 1], funcs[i]
        gap, glen = modules_scan.gap_kind(prog, a["body_end"], b["start"])
        labels.append({"i": i, "prev": a["start"], "cur": b["start"],
                       "truth": "boundary" if a["cu"] != b["cu"] else "same_cu",
                       "gap_kind": gap, "gap_len": glen,
                       "rule": modules_scan.rule_of(b["start"], gap, glen),
                       "evidence": f"{a['cu']} -> {b['cu']}" if a["cu"] != b["cu"]
                                   else f"inside {a['cu']}"})

    cases = _designed_cases({"functions": funcs, "labels": labels})
    for key, want in EXPECTED.items():
        if key in ("boundaries", "same_cu_pairs"):
            continue
        got = cases["checks"].get(key, 0)
        if got < want:
            raise RuntimeError(f"designed case {key}: {got} < {want} ({cases['checks']})")

    data_base, _data_end = prog.data.base, prog.data.base + prog.data.vsize
    const_ranges, private_ranges = [], []
    for name, (seg, lo, hi) in sorted(data_object.items()):
        if hi == lo:
            continue
        base = data_base if len({s for s, _l, _h in data_object.values()}) == 1 else None
        if base is None:
            # map offsets are relative to the merged data object
            base = data_base
        lo_a, hi_a = base + lo, base + hi
        if name.upper().startswith("CONST"):
            const_ranges.append([lo_a, hi_a])
        else:
            private_ranges.append([lo_a, hi_a])
    corp = {
        "schema": SCHEMA, "experiment": EXPERIMENT,
        "id": "synthetic", "kind": "corpus_a_synthetic_watcom10a_wlink",
        "caveat": ("CU ownership and function extents are facts of the build recipe, verified "
                   "against the 10.0a wlink map before any signal is computed."),
        "spec_sha256": spec, "source_spec": SPEC_ID,
        "linker": {"name": "wlink", "version": "10.0 (Watcom, 1994)", "system": "dos4g"},
        "compiler": {"name": "wcc386", "version": "10.0a", "base_flags": BASE_CFLAGS},
        "image": {
            "code_base": prog.code.base, "code_size": prog.code.vsize,
            "data_base": prog.data.base, "data_size": prog.data.vsize,
            "text_sha256": sha256_bytes(prog.cbytes[:prog.code.vsize]),
            "data_sha256": sha256_bytes(prog.image[analysis.DATA_OBJ]),
        },
        "cus": cus, "functions": funcs,
        "ranges": {"const": const_ranges, "data": private_ranges},
        "labels": labels,
        "_exe": str(exe_path),
    }
    dump_json(cached, corp)
    return corp


# ---------------------------------------------------------------------------
# S(f): the 26 E7 configurations, compiled per CU and compared per function
# ---------------------------------------------------------------------------
def _masked(data, base, lo, hi, masks, insns, end):
    """Bytes [lo, hi) with relocation fields and out-of-function branch targets zeroed.

    `masks` are (offset, size) pairs in the same address space as `lo`/`hi`.
    """
    buf = bytearray(data[lo - base:hi - base])
    for a, size in masks:
        if lo <= a < hi:
            for k in range(min(size, hi - a)):
                buf[a - lo + k] = 0
    for i in insns:
        if i.address < lo or i.address >= hi:
            continue
        if i.mnemonic != "call" and i.mnemonic != "jmp" and not i.mnemonic.startswith("j"):
            continue
        if not i.operands or i.operands[0].type != x86.X86_OP_IMM:
            continue
        t = i.operands[0].imm & 0xFFFFFFFF
        if lo <= t < end:
            continue
        if i.size in (5, 6):
            for k in range(4):
                j = i.address - lo + i.size - 4 + k
                if 0 <= j < len(buf):
                    buf[j] = 0
        elif i.size == 2:
            buf[i.address - lo + 1] = 0
    return bytes(buf)


def _linked_body(prog, f):
    insns = [prog.insns[a] for a in sorted(prog.insns) if f["start"] <= a < f["body_end"]]
    masks = [(a, fx.size) for a, (fx, _t) in prog.fix_at.items()
             if f["start"] <= a < f["body_end"]]
    return _masked(prog.cbytes, prog.code.base, f["start"], f["body_end"], masks, insns,
                   f["body_end"])


def _object_body(mod, seg_index, lo, hi, md):
    seg = mod.segments[seg_index]
    insns = decode_range(md, seg.data, 0, lo, seg_end := min(hi, len(seg.data)))
    end = body_end(insns, seg_end)
    masks = [(fx.offset, fx.size) for fx in seg.fixups if lo <= fx.offset < end]
    return _masked(seg.data, 0, lo, end, masks, insns, end)


def sf_table(corpus, force=False):
    """S(f) = configuration ids whose compilation reproduces the function bytes."""
    from . import digest as json_digest
    cache = SCRATCH / "sf.json"
    key = json_digest({"spec": corpus["spec_sha256"], "text": corpus["image"]["text_sha256"],
                       "configs": CORE_FLAGS})
    if not force and cache.exists():
        rec = __import__("json").loads(cache.read_text(encoding="utf-8"))
        if rec.get("key") == key:
            return rec["sf"]
    md = _md()
    by_cu = {c["id"]: c for c in corpus["cus"]}
    funcs = corpus["functions"]
    prog = program(corpus)
    linked = {}
    for f in funcs:
        linked[f["start"]] = _linked_body(prog, f)
    # hand-written NASM CUs are not compiled by wcc386: the flag-compatibility
    # signal simply does not apply to them (empty S(f), reported as such)
    work = [(cu, cfg) for cu in SPEC if cu.get("kind") != "asm" for cfg in CORE_FLAGS]
    outdir = SCRATCH / "sf"
    outdir.mkdir(parents=True, exist_ok=True)

    def one(job):
        cu, cfg = job
        out = outdir / f"{cu['id']}.{CORE_FLAGS.index(cfg):02d}.obj"
        try:
            mod = compile_short(str(source_path(cu)), BASE_CFLAGS + " " + cfg, str(out),
                                cc="10.0a", quiet=True)
        except SystemExit as e:      # a config that cannot compile this source
            return cu["id"], cfg, {"error": str(e).splitlines()[0][:120]}
        seg_index = mod.segments.index(_code_segment(mod, cu))
        offs = {}
        for name, (si, off) in mod.publics.items():
            if si == seg_index + 1:
                offs[name] = off
        res = {}
        for f in corpus["functions"]:
            if f["cu"] != cu["id"]:
                continue
            want = f["name"] if cu.get("kind") == "asm" else f["name"] + "_"
            off = offs.get(want)
            if off is None:
                res[f["start"]] = None
                continue
            hi = min([o for o in offs.values() if o > off] + [len(mod.segments[seg_index].data)])
            try:
                got = _object_body(mod, seg_index, off, hi, md)
            except RuntimeError:
                res[f["start"]] = None
                continue
            res[f["start"]] = got == linked[f["start"]]
        return cu["id"], cfg, res

    sf = {str(f["start"]): [] for f in funcs}
    errors = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        for _cu, cfg, res in ex.map(one, work):
            cid = f"c{CORE_FLAGS.index(cfg) + 1:02d}"
            if "error" in res:
                errors.append({"config": cid, "error": res["error"]})
                continue
            for start, ok in res.items():
                if ok:
                    sf[str(start)].append(cid)
    for k in sf:
        sf[k].sort()
    dump_json(cache, {"key": key, "sf": sf, "config_errors": errors})
    return sf


# ---------------------------------------------------------------------------
# the committed manifest (path-free projection of the corpus)
# ---------------------------------------------------------------------------
def manifest(corpus, sf=None):
    def fn(f):
        out = {k: f[k] for k in ("start", "end", "name", "cu", "body_end", "size")}
        if sf is not None:
            out["S"] = sf.get(str(f["start"]), [])
        return out
    return {
        "schema": SCHEMA, "experiment": EXPERIMENT,
        "corpus": "A (synthetic)", "id": "synthetic_manifest",
        "provenance": {
            "compiler": corpus["compiler"], "linker": corpus["linker"],
            "source_spec": corpus["source_spec"], "spec_sha256": corpus["spec_sha256"],
            "ground_truth": ("CU membership from the build recipe; every function and data "
                             "address verified against the 10.0a wlink map"),
        },
        "image": corpus["image"],
        "configuration_ids": [f"c{k + 1:02d}" for k in range(len(CORE_FLAGS))],
        "configurations": [{"id": f"c{k + 1:02d}", "flags": c} for k, c in enumerate(CORE_FLAGS)],
        "cus": [{k: cu[k] for k in ("id", "kind", "flags", "compiler", "align", "start", "end",
                                    "functions", "nops", "source_sha256")} for cu in corpus["cus"]],
        "functions": [fn(f) for f in corpus["functions"]],
        "ranges": corpus["ranges"],
        "labels": corpus["labels"],
        "designed_cases": _designed_cases(corpus),
    }


def _designed_cases(corpus):
    """Self-checks that the corpus really contains the edge cases it claims."""
    by_start = {f["start"]: f for f in corpus["functions"]}
    rules, checks = {}, {}

    def count(rule):
        n = sum(1 for lab in corpus["labels"] if lab["rule"] == rule and lab["truth"] == "boundary")
        return n

    for rule in ("zero16", "zero4", "zero2", "none16"):
        rules[rule] = count(rule)
    checks["zero16_boundaries"] = rules["zero16"]
    checks["zero4_boundaries"] = rules["zero4"]
    checks["zero2_boundaries"] = rules["zero2"]
    checks["none16_boundaries"] = rules["none16"]
    checks["same_cu_none16_candidates"] = sum(
        1 for lab in corpus["labels"] if lab["rule"] == "none16" and lab["truth"] == "same_cu")
    checks["same_cu_zero16_candidates"] = sum(
        1 for lab in corpus["labels"] if lab["rule"] == "zero16" and lab["truth"] == "same_cu")
    checks["same_cu_zero4_candidates"] = sum(
        1 for lab in corpus["labels"] if lab["rule"] == "zero4" and lab["truth"] == "same_cu")
    checks["data16_boundaries"] = sum(
        1 for lab in corpus["labels"] if lab["rule"] == "data16" and lab["truth"] == "boundary")
    checks["boundaries"] = sum(1 for lab in corpus["labels"] if lab["truth"] == "boundary")
    checks["same_cu_pairs"] = sum(1 for lab in corpus["labels"] if lab["truth"] == "same_cu")
    return {"checks": checks, "boundaries_by_rule": {k: v for k, v in rules.items() if v}}
