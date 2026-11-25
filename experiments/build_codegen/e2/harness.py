"""Inventory, source-only consolidation, and independently observable code evidence.

All match verdicts come from the approved E0 matcher, unmodified. Body signatures
are diagnostics, never substitute match verdicts. OMF modules are never patched.
"""
from collections import Counter
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path

import capstone
from wc1 import match, path, symbols
from experiments.build_codegen.e0.matcher_proto import match_module

BASELINE = "7c23d2371e95d8de93f0ba1652c8d44b858da273"
ROOT = Path(path())
HERE = Path(__file__).resolve().parent
SCRATCH = HERE / ".scratch"
RESULTS = ROOT / "docs/research/build-codegen/results/e2"
AREAS = ("gamedlg", "playflic", "status")
FLAGS = match.DEFAULT_CFLAGS
VARIANTS = {
    "native": FLAGS,
    "cpu3": FLAGS.replace("-4r", "-3r"),
    "cpu5": FLAGS.replace("-4r", "-5r"),
    "size": FLAGS.replace("-ot", "-os"),
    "no_ol": FLAGS.replace(" -ol", ""),
    "alias": FLAGS + " -oa",
    "register": FLAGS + " -or",
    "debug": FLAGS + " -d1+",
}
STALE = ("CanBuildBlacksmith", "CanBuildChurch", "CanBuildStable",
         "CanBuildTower", "CanRebuildTownHall")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def dump(filename, value):
    filename.parent.mkdir(parents=True, exist_ok=True)
    filename.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def inventory():
    funcs, datas, _ = symbols.load()
    entries = []
    for area in AREAS:
        for e in sorted(funcs.values(), key=lambda e: e["addr"]):
            if e.get("src", "").startswith(f"src/{area}/"):
                entries.append(dict(area=area, addr=e["addr"], name=e["name"],
                    link_name=e["link_name"], src=e["src"],
                    compiler=match.file_cc(path(e["src"])),
                    flags=match.file_cflags(path(e["src"])),
                    source_sha256=sha(Path(path(e["src"])).read_bytes())))
    selected = {e["src"] for e in entries}
    excluded = []
    for area in AREAS:
        for src in sorted((ROOT / "src" / area).glob("*.c")):
            rel = str(src.relative_to(ROOT))
            if rel in selected:
                continue
            owners = [dict(name=e["name"], addr=e["addr"],
                           field="ref" if e.get("ref") == rel else "other")
                      for e in funcs.values() if e.get("ref") == rel or
                      e.get("src", "").split(":")[0] == rel]
            excluded.append(dict(src=rel, entries=owners,
                reason="No exact src= owner: reference/unwired draft, not a standalone built T3"))
    db = {e["link_name"]: e for table in (funcs, datas) for e in table.values()}
    return entries, excluded, db


def header_overlay():
    """Reconcile only five unused stale declarations, outside production.

    Controls compile the original T3 files under BOTH headers and must have
    identical body signatures and E0 verdicts. No function body is edited.
    """
    dest = SCRATCH / "include"
    dest.mkdir(parents=True, exist_ok=True)
    original = (ROOT / "src/include/status.h").read_text()
    text = original
    for name in STALE:
        old = f"unsigned short {name}(short is_unit);"
        assert text.count(old) == 1
        text = text.replace(old, f"unsigned short {name}(void);")
    (dest / "status.h").write_text(text)
    return dest, dict(original_sha256=sha(original.encode()),
                     overlay_sha256=sha(text.encode()), declarations=list(STALE),
                     transformation="(short is_unit) declaration -> (void); definitions unchanged")


def consolidate(entries, filename, substitutions=None):
    """Concatenate complete source files, retaining provenance and code order.

    A perturbed source is an experimental copy; only that file is substituted.
    Watcom resolves quoted source inclusions relative to its working directory;
    concatenation avoids depending on that behavior. Header includes survive.
    """
    filename.parent.mkdir(parents=True, exist_ok=True)
    sources = list(dict.fromkeys(e["src"] for e in sorted(entries, key=lambda e: e["addr"])))
    lines = ["/* E2 generated TU: original address order; no OMF rewriting. */"]
    for src in sources:
        p = (substitutions or {}).get(src, ROOT / src)
        lines.append("/* BEGIN " + src + " */\n" + p.read_text() + "\n/* END " + src + " */")
    filename.write_text("\n".join(lines) + "\n")
    return filename


def compile_source(src, flags, key, cc="10.0a", overlay=None):
    # The 1994 compiler silently exits on sufficiently long output paths.
    # Flat content-derived names also keep Wine paths below that limit.
    obj = SCRATCH / "obj" / (sha((cc+":"+key).encode())[:16] + ".obj")
    obj.parent.mkdir(parents=True, exist_ok=True)
    # Quiet compiler diagnostics still raise: a broken toolchain never counts
    # as a code mismatch. No cache: every invocation recompiles from source.
    return match.compile_c(str(src), flags, str(obj), cc=cc,
        includes=(() if overlay is None else (str(overlay),)), quiet=True, timeout=180)


def starts(mod):
    ti, _ = mod.seg("_TEXT")
    return sorted((off, n) for n, (si, off) in
                  {**mod.publics, **mod.statics}.items() if si == ti)


def body_evidence(mod, name):
    """Reachable body and relocation-neutral instruction fingerprint.

    Follow direct intrafunction branches; stop at ret/tail transfer. Preserve
    internal loop filler in the contiguous body. Normalize OMF fields and
    independently named intra-TU near transfers only. All other bytes survive.
    Cross-function short branches remain observable instructions. This is a
    diagnostic comparison against same-flags standalone, not extraction.
    """
    ti, seg = mod.seg("_TEXT")
    ss = starts(mod)
    off = next(o for o, n in ss if n == name)
    hi = next((o for o, _ in ss if o > off), len(seg.data))
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    decoded = {i.address: i for i in md.disasm(bytes(seg.data[off:hi]), off)}
    pending, visited, exits = [off], set(), []
    while pending:
        a = pending.pop()
        if a in visited or a not in decoded:
            continue
        visited.add(a)
        i = decoded[a]
        nxt = a + i.size
        is_jump = i.mnemonic.startswith("j") or i.mnemonic.startswith("loop")
        if is_jump:
            try:
                target = int(i.op_str, 16)
            except ValueError:
                target = None
            # A linker's zero displacement is not a CFG edge into padding.
            # In particular, a tail jmp with an external FIXUPP terminates
            # the function even when its placeholder points at the next byte.
            if any(f.self_rel and a <= f.offset < nxt for f in seg.fixups):
                target = None
            if target is not None and off <= target < hi:
                pending.append(target)
            else:
                exits.append(dict(offset=a-off, mnemonic=i.mnemonic,
                                  target_offset=target))
        if not i.mnemonic.startswith("ret") and i.mnemonic != "jmp":
            pending.append(nxt)
    end = max((a + decoded[a].size for a in visited), default=off)
    raw = bytes(seg.data[off:end])
    neutral = bytearray(raw)
    fixups = []
    call_fields = set()
    named = {o: n for o, n in ss}
    calls = []
    for fu in seg.fixups:
        if off <= fu.offset and fu.offset + fu.size <= end:
            neutral[fu.offset-off:fu.offset-off+fu.size] = bytes(fu.size)
            fixups.append(dict(asdict(fu), body_offset=fu.offset-off,
                inline_addend=int.from_bytes(seg.data[fu.offset:fu.offset+fu.size],
                                             "little", signed=True)))
            if fu.self_rel:
                call_fields.add(fu.offset)
                calls.append([fu.offset-off, fu.target_kind, fu.target])
    for a in sorted(visited):
        i = decoded[a]
        b = bytes(i.bytes)
        if len(b) == 5 and b[0] in (0xe8, 0xe9) and a+1 not in call_fields:
            target = a+5+int.from_bytes(b[1:], "little", signed=True)
            if target in named:
                neutral[a+1-off:a+5-off] = bytes(4)
                calls.append([a+1-off, "ext", named[target]])
    return dict(start=off, next_start=hi, extent=hi-off, body_size=end-off,
        body_raw_sha256=sha(raw), instruction_sha256=sha(neutral),
        body_hex=raw.hex(), neutral_hex=neutral.hex(),
        padding_hex=bytes(seg.data[end:hi]).hex(),
        padding_is_filler=(end == hi or match.is_filler(bytes(seg.data[end:hi]))),
        exits=exits, fixups=fixups, calls=sorted(calls),
        instructions=[[a-off, decoded[a].mnemonic, decoded[a].op_str]
                      for a in sorted(visited)])


def compact(result):
    """Keep all non-byte diagnostics, losslessly coalesce byte mismatch runs.

    Omit repeated addressing-obligation listings; checker metrics prove their
    counts. No verdict or diagnostic is changed or removed.
    """
    fs, byte_runs = [], []
    for f in result["findings"]:
        if f["code"] != "byte_mismatch":
            fs.append(f)
            continue
        if (byte_runs and byte_runs[-1]["segment"] == f["evidence"]["segment"] and
                byte_runs[-1]["offset"] + len(byte_runs[-1]["got"]) == f["offset"] and
                byte_runs[-1]["orig_addr"] + len(byte_runs[-1]["got"]) == f["orig_addr"]):
            run = byte_runs[-1]
        else:
            run = dict(segment=f["evidence"]["segment"], offset=f["offset"],
                       orig_addr=f["orig_addr"], got=[], want=[])
            byte_runs.append(run)
        run["got"].append(f["evidence"]["got"])
        run["want"].append(f["evidence"]["want"])
    for run in byte_runs:
        run["got"] = bytes(run["got"]).hex()
        run["want"] = bytes(run["want"]).hex()
    return {**{k: result[k] for k in ("verdict", "orig_start", "orig_end", "metrics")},
            "finding_counts": dict(sorted(Counter(f["code"] for f in result["findings"]).items())),
            "findings": fs, "byte_mismatch_runs": byte_runs}


def evaluate(p, idx, db, mod):
    return match_module(p, mod, db, idx)


def adjacent_runs(entries, p):
    order = {f["start"]: i for i, f in enumerate(sorted(p.functions, key=lambda f: f["start"]))}
    runs = []
    for e in sorted(entries, key=lambda e: e["addr"]):
        if (not runs or order[e["addr"]] != order[runs[-1][-1]["addr"]] + 1 or
                e["flags"] != runs[-1][-1]["flags"]):
            runs.append([])
        runs[-1].append(e)
    return [r for r in runs if len(r) >= 2]


def wilson(k, n):
    if not n:
        return None
    z = 1.959963984540054
    center = (k/n + z*z/(2*n))/(1+z*z/n)
    half = z*math.sqrt(k/n*(1-k/n)/n + z*z/(4*n*n))/(1+z*z/n)
    return [round(center-half, 6), round(center+half, 6)]


def summary(rows):
    n = len(rows)
    retained = sum(r["baseline_function"] == r["function"] == "MATCH" for r in rows)
    return dict(n_tested=n, n_retained_match=retained,
        n_lost_match=sum(r["baseline_function"] == "MATCH" and r["function"] != "MATCH" for r in rows),
        n_gained_match=sum(r["baseline_function"] != "MATCH" and r["function"] == "MATCH" for r in rows),
        n_genuine_context_body_changes=sum(r["context_body_changed"] for r in rows),
        n_flag_body_changes=sum(r["flag_body_changed"] for r in rows),
        reasons=dict(sorted(Counter(x for r in rows for x in r["causes"]).items())),
        verdicts=dict(sorted(Counter(r["function"] for r in rows).items())),
        retention_wilson95=wilson(retained, n))
