"""Segment layout of war.exe's data object (analysis area: DATALAYOUT).

Regenerates the evidence behind analysis/data_layout.toml:

* which Watcom segments the data object 0x50000..0x655f0 consists of and
  where they start/end (_NULL, _DATA, CONST, CONST2, XI, YI, _BSS, STACK);
* for every segment, the per-module partition.  The linker emits each object's
  contribution to a segment contiguously, in link order, and the link order of
  the code object is the module order of analysis/modules.toml.  A data address
  referenced (via LE fixups in code) by exactly one module is an *anchor* for
  that module; the chain of anchors must be non-decreasing in module index when
  read in address order ("staircase").  Globals referenced by several modules
  are polluters; the staircase is therefore the maximum-weight monotone
  assignment (dynamic programming) and anchors that do not fit are reported as
  shared/dropped, never forced.

usage:
    python3 -m wc1.datalayout_scan                # summary
    python3 -m wc1.datalayout_scan --write        # regenerate analysis/data_layout.toml
    python3 -m wc1.datalayout_scan --json build/datalayout/scan.json
"""
import argparse
import bisect
import collections
import json
import struct
import tomllib

from . import analysis, path, symbols

# ---------------------------------------------------------------- constants
DATA_BASE = 0x50000
NULL_END = 0x50004                 # _NULL = 01 01 01 00 (cstart), then _AFTERNULL (0 bytes)
CONST_START = 0x569d4              # first CONST item (module mod_110a0, 'attack:1'); _DATA ends here
CONST2_START = 0x583d4             # clib _IsTable (ctype table, 257 bytes), see segment evidence
STACK_START = 0x64180              # main stack 0x64180..0x655f0 (docs/ANALYST_GUIDE.md)
DATA_END = 0x655f0

# alignment of one module's contribution to each segment (see data_layout.md)
ALIGN = {"_DATA": 4, "CONST": 4, "CONST2": 4, "BSS": 16}
CLUSTER_GAP = 2                    # anchors closer than this belong to one object
GAP_SLICE_MIN = 64                 # cut intervals wider than this become an unattributed slice


def hx(v):
    return f"0x{v:x}"


# ---------------------------------------------------------------- loading
class Ctx:
    def __init__(self):
        self.p = analysis.run()
        self.B = self.p.data.base
        self.dat = self.p.data.data
        self.init_size = self.p.data_init_size
        self.mods = tomllib.load(open(path("analysis/modules.toml"), "rb"))["module"]
        self.ms = [m["start"] for m in self.mods]
        self.refs = collections.defaultdict(set)       # data target -> module idx (code refs)
        self.drefs = collections.defaultdict(set)      # data target -> data source addrs
        self.code_to_data = []                         # (src, target) code fixups into the data object
        for s, (f, t) in self.p.fix_at.items():
            if self.B <= t < self.B + self.p.data.vsize:
                if self.p.in_code(s):
                    self.refs[t].add(self.modof(s))
                    self.code_to_data.append((s, t))
                else:
                    self.drefs[t].add(s)

    def modof(self, a):
        return bisect.bisect_right(self.ms, a) - 1

    def byte(self, a):
        return self.dat[a - self.B]

    def u32(self, a):
        return struct.unpack_from("<I", self.dat, a - self.B)[0]


# ---------------------------------------------------------------- anchors + DP
def anchors(ctx, lo, hi):
    """Clustered anchors in [lo, hi): (first_addr, last_addr, set(modules), weight)."""
    out = []
    for t in sorted(ctx.refs):
        if not lo <= t < hi:
            continue
        S = set(ctx.refs[t])
        if out and t - out[-1][1] <= CLUSTER_GAP:
            out[-1][1] = t
            out[-1][2] |= S
        else:
            out.append([t, t, S])
    res = []
    for a, b, S in out:
        n = len(S)
        w = 1.0 if n == 1 else 0.3 if n <= 3 else 0.0
        res.append((a, b, S, w))
    return res


def staircase(ctx, A):
    """Maximum-weight assignment of a module to each anchor, non-decreasing in address order."""
    n = len(ctx.mods)
    gbest = [(0.0, None)] * n
    pref = [(0.0, None)] * n
    states = []
    for i, (a, b, S, w) in enumerate(A):
        cur = {}
        for m in S:
            sc, pv = pref[m]
            cur[m] = (sc + w, pv)
        states.append(cur)
        for m, (sc, pv) in cur.items():
            if sc > gbest[m][0]:
                gbest[m] = (sc, (i, m))
        run = (0.0, None)
        for m in range(n):
            if gbest[m][0] > run[0]:
                run = gbest[m]
            pref[m] = run
    asg = {}
    ptr = pref[n - 1][1]
    while ptr:
        i, m = ptr
        asg[i] = m
        ptr = states[i][m][1]
    return asg


def owners_of(ctx, A, asg):
    """Group the assigned anchors into per-module runs (address order)."""
    runs = []
    for i in sorted(asg):
        m = asg[i]
        a, b, S, w = A[i]
        if runs and runs[-1]["module"] == m:
            r = runs[-1]
        else:
            r = {"module": m, "first": a, "last": b, "anchors": 0, "excl": 0, "examples": []}
            runs.append(r)
        r["last"] = max(r["last"], b)
        r["anchors"] += 1
        r["excl"] += 1 if len(S) == 1 else 0
        if len(r["examples"]) < 3 and len(S) == 1:
            r["examples"].append(a)
    return runs


def is_cstr_head(ctx, a):
    """a is the start of a printable NUL-terminated string preceded by NUL or padding."""
    j = a
    while j < ctx.B + ctx.init_size and (32 <= ctx.byte(j) < 127 or ctx.byte(j) in (9, 10, 13)):
        j += 1
    return j > a and ctx.byte(j) == 0


def al_down(v, al):
    return v - v % al


def al_up(v, al):
    return v + (-v) % al


def partition(ctx, seg, lo, hi, al, key):
    """Slices (contiguous, covering [lo, hi)) for one segment."""
    A = anchors(ctx, lo, hi)
    asg = staircase(ctx, A)
    runs = owners_of(ctx, A, asg)
    dropped = [(a, sorted(S)) for i, (a, b, S, w) in enumerate(A) if i not in asg and len(S) == 1]
    shared = [(a, sorted(S)) for i, (a, b, S, w) in enumerate(A) if i not in asg and len(S) > 1]
    slices = []
    # cut estimates between consecutive runs
    cuts = []
    for k in range(len(runs) - 1):
        r0, r1 = runs[k], runs[k + 1]
        lo_c = al_up(r0["last"] + 1, al)                  # smallest aligned address after r0's last anchor byte
        hi_c = al_down(r1["first"], al)                   # largest aligned address <= r1's first anchor
        if hi_c < lo_c:                                   # anchors closer than one alignment unit
            lo_c = hi_c = al_down(r1["first"], al)
            if lo_c <= r0["last"]:
                lo_c = hi_c = r0["last"] + 1
        width = (hi_c - lo_c) // al + 1
        cuts.append({"lo": lo_c, "hi": hi_c, "n": width})
    if key == "CONST":
        # candidates are string heads (item starts), not every aligned address
        for c in cuts:
            heads = [x for x in range(c["lo"], c["hi"] + 1, 4) if is_cstr_head(ctx, x) and ctx.byte(x - 1) != 0x20 or x == c["hi"]]
            heads = sorted(set(x for x in heads if c["lo"] <= x <= c["hi"]))
            c["n"] = max(1, len(heads))
            c["heads"] = heads
    # head
    first_start = al_down(runs[0]["first"], al) if runs else hi
    if first_start > lo:
        slices.append({"module": None, "start": lo, "end": first_start, "n_anchors": 0, "excl": 0,
                       "cut_lo": lo, "cut_hi": lo, "cut_n": 1, "role": "head"})
    cur_start = first_start
    cur_lo, cur_hi, cur_n = first_start, first_start, 1
    for k, r in enumerate(runs):
        if k + 1 < len(runs):
            c = cuts[k]
            nxt_start = c["hi"]
            gap = c["hi"] - c["lo"]
            if gap > GAP_SLICE_MIN:
                end = c["lo"]
                slices.append(mk(r, cur_start, end, cur_lo, cur_hi, cur_n))
                slices.append({"module": None, "start": end, "end": nxt_start, "n_anchors": 0, "excl": 0,
                               "cut_lo": c["lo"], "cut_hi": c["hi"], "cut_n": c["n"], "role": "gap"})
            else:
                slices.append(mk(r, cur_start, nxt_start, cur_lo, cur_hi, cur_n))
            cur_start, cur_lo, cur_hi, cur_n = nxt_start, c["lo"], c["hi"], c["n"]
        else:
            slices.append(mk(r, cur_start, hi, cur_lo, cur_hi, cur_n))
    return {"slices": slices, "dropped": dropped, "shared": shared, "nanchors": len(A), "nassigned": len(asg)}


def mk(r, start, end, cut_lo, cut_hi, cut_n):
    return {"module": r["module"], "start": start, "end": end, "n_anchors": r["anchors"], "excl": r["excl"],
            "first_anchor": r["first"], "last_anchor": r["last"], "examples": r["examples"],
            "cut_lo": cut_lo, "cut_hi": cut_hi, "cut_n": cut_n, "role": "module"}


def slice_conf(seg, s, nxt):
    """Confidence of a module slice from the width of its two cut intervals and its anchor support."""
    if s["module"] is None:
        return "low"
    def cut_conf(n):
        if seg == "BSS":
            return "high" if n == 1 else "medium" if n <= 4 else "low"
        if seg == "CONST":
            return "high" if n == 1 else "medium" if n == 2 else "low"
        return "medium" if n == 1 else "low"
    c0 = cut_conf(s["cut_n"])
    c1 = cut_conf(nxt["cut_n"]) if nxt is not None else c0
    order = ["low", "medium", "high"]
    c = order[min(order.index(c0), order.index(c1))]
    if s["excl"] < 2 and c == "high":
        c = "medium"
    if s["excl"] == 0:
        c = "low"
    return c


# ---------------------------------------------------------------- init/fini tables
def xi_records(ctx, lo, hi):
    out = []
    for a in range(lo, hi, 6):
        ty = ctx.byte(a)
        pr = ctx.byte(a + 1)
        fp = struct.unpack_from("<I", ctx.dat, a + 2 - ctx.B)[0]
        out.append({"addr": a, "type": ty, "prio": pr, "func": fp, "module": ctx.modof(fp)})
    return out


def find_init_tables(ctx):
    funcs, datas, _ = symbols.load(strict=False)
    byname = {e["name"]: e["addr"] for e in funcs.values()}
    ini = byname.get("__InitRtns")
    fin = byname.get("__FiniRtns")
    res = {}
    for name, fa in (("__InitRtns", ini), ("__FiniRtns", fin)):
        if fa is None:
            continue
        fe = next(f["end"] for f in ctx.p.functions if f["start"] == fa)
        for s, (f, t) in sorted(ctx.p.fix_at.items()):
            if fa <= s < fe and ctx.B <= t < ctx.B + ctx.p.data.vsize:
                res.setdefault(name, []).append(t)
    return res


# ---------------------------------------------------------------- alignment statistics
def align_stats(ctx, slices, al):
    ok = n = 0
    for s in slices:
        if s["role"] == "module":
            n += 1
            ok += s["start"] % al == 0
    return ok, n


def build(ctx=None):
    ctx = ctx or Ctx()
    tabs = find_init_tables(ctx)
    xib = min(tabs["__InitRtns"])
    xie = sorted(tabs["__InitRtns"])[1]
    yie = max(tabs["__FiniRtns"])
    segs = [
        ("_NULL", DATA_BASE, NULL_END), ("_DATA", NULL_END, CONST_START), ("CONST", CONST_START, CONST2_START),
        ("CONST2", CONST2_START, xib), ("XI", xib, xie), ("YI", xie, yie), ("_BSS", yie, STACK_START),
        ("STACK", STACK_START, DATA_END),
    ]
    result = {"segments": segs, "tables": {"XIB": xib, "XIE": xie, "YIE": yie}}
    part = {}
    part["_DATA"] = partition(ctx, "_DATA", NULL_END, CONST_START, ALIGN["_DATA"], "_DATA")
    part["CONST"] = partition(ctx, "CONST", CONST_START, CONST2_START, ALIGN["CONST"], "CONST")
    part["_BSS"] = partition(ctx, "BSS", yie, STACK_START, ALIGN["BSS"], "BSS")
    result["part"] = part
    result["xi"] = xi_records(ctx, xib, xie)
    result["yi"] = xi_records(ctx, xie, yie)
    result["ctx"] = ctx
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="write analysis/data_layout.toml")
    ap.add_argument("--json", help="dump the raw result as JSON")
    a = ap.parse_args()
    R = build()
    ctx = R["ctx"]
    for name, lo, hi in R["segments"]:
        print(f"{name:7} {hx(lo)}..{hx(hi)}  {hi - lo:#x}")
    for seg, P in R["part"].items():
        mods_ = [s for s in P["slices"] if s["role"] == "module"]
        print(f"{seg}: {P['nassigned']}/{P['nanchors']} anchors on the staircase, {len(mods_)} module slices, "
              f"{len(P['dropped'])} exclusive anchors dropped, {len(P['shared'])} shared")
    for r in R["xi"] + R["yi"]:
        print(f"  init/fini {hx(r['addr'])}: prio {r['prio']:#x} fn {hx(r['func'])} module {ctx.mods[r['module']]['name']}")
    if a.write:
        from .datalayout_toml import write_toml
        write_toml(R, path("analysis/data_layout.toml"))
        print("wrote analysis/data_layout.toml")
    if a.json:
        out = {k: v for k, v in R.items() if k != "ctx"}
        with open(a.json, "w") as f:
            json.dump(out, f, indent=1, default=str)


if __name__ == "__main__":
    main()
