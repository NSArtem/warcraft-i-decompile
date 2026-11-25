"""Read-only dynamic audit of every in-scope T3; compile each source once."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import csv
import hashlib
import json
from pathlib import Path
import subprocess

from wc1 import analysis, match, path, progress, symbols
from .matcher_proto import OriginalIndex, match_module


VERDICTS = ("MATCH", "MISMATCH", "UNSUPPORTED", "ERROR")
CATEGORIES = ("unaffected", "code_reloc_defect", "data_pointer_defect",
              "boundary_extent_defect", "matcher_unsupported", "other_mismatch")
RESULTS = Path(path("docs", "research", "build-codegen", "results", "e0"))


def dump_json(filename, payload):
    filename = Path(filename)
    filename.parent.mkdir(parents=True, exist_ok=True)
    filename.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def discover(p, funcs):
    rows = progress.classify([f["start"] for f in p.functions], funcs,
                             progress.load_modules())
    return [funcs[r["addr"]] for r in rows if r["scope"] == "in" and r["c"] == "T3"]


def scoped_findings(function, region):
    """Union with explicit scopes; never drop an independent finding."""
    out = []
    for scope, rr in (("function", function), ("region", region)):
        for f in rr["findings"]:
            existing = next((x for x in out if
                             {k: v for k, v in x.items() if k != "verification_scopes"} == f), None)
            if existing is not None:
                existing["verification_scopes"].append(scope)
            else:
                out.append(dict(deepcopy(f), verification_scopes=[scope]))
    return out


def classify_row(row):
    """One primary category, all secondary defects retained in findings.

    Priority: unsupported, code relocation, data pointer, boundary, residual.
    ERROR is residual other_mismatch and is separately counted by verdict.
    """
    if row["e0_region_verdict"] == row["e0_function_verdict"] == "MATCH":
        return "unaffected"
    if "UNSUPPORTED" in (row["e0_region_verdict"], row["e0_function_verdict"]):
        return "matcher_unsupported"
    fs = row["findings"]
    cats = {f["category"] for f in fs}
    if cats & {"code_reloc_forward", "code_reloc_reverse"}:
        return "code_reloc_defect"
    if cats & {"data_reloc_forward", "data_reloc_reverse"}:
        return "data_pointer_defect"
    if cats & {"leading_bytes", "extent_retry"} or any(f["evidence"].get("leading_bytes") for f in fs):
        return "boundary_extent_defect"
    return "other_mismatch"


def _error(message):
    return dict(verdict="ERROR", findings=[dict(code="audit_error", category="error",
                offset=None, orig_addr=None, message=message, evidence={})], obligations=[], metrics={})


def audit_has_errors(result):
    return any(result["summary"][scope]["ERROR"] > 0
               for scope in ("function_verdicts", "region_verdicts"))


def audit(jobs=4, output=RESULTS):
    p = analysis.run()
    funcs, datas, _ = symbols.load()
    entries = discover(p, funcs)
    by_link = {e["link_name"]: e for t in (funcs, datas) for e in t.values()}
    grouped = {}
    for e in entries:
        grouped.setdefault(e["src"], []).append(e)
    idx = OriginalIndex(p)
    objdir = Path(path("build", "e0", "obj", "reaudit"))
    objdir.mkdir(parents=True, exist_ok=True)

    def compile_one(src):
        # No reuse/cache: every invocation performs a fresh compile exactly once.
        obj = objdir / (src.removeprefix("src/").replace("/", "__").removesuffix(".c") + ".obj")
        try:
            m = match.compile_c(path(src), None, str(obj), timeout=180, quiet=True)
            return m, hashlib.sha256(obj.read_bytes()).hexdigest(), None
        except (Exception, SystemExit) as exc:
            return None, None, f"{type(exc).__name__}: {exc}"

    rows = []
    sources = sorted(grouped)
    # Only compiles are parallel. Capstone-backed legacy comparisons are serial.
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        for count, (src, (mod, digest, err)) in enumerate(zip(sources, pool.map(compile_one, sources)), 1):
            if err:
                result, region, legacy = None, _error(err), []
            else:
                try:
                    result = match_module(p, mod, by_link, idx)
                    region = result["region"]
                except Exception as exc:
                    result, region = None, _error(f"{type(exc).__name__}: {exc}")
                try:
                    legacy = match.match_module(p, mod, by_link)
                except Exception as exc:
                    legacy = [["audit", "ERROR", [f"{type(exc).__name__}: {exc}"]]]
            legacy_map = {n: verdict for n, verdict, _ in legacy}
            legacy_region = "ERROR" if not legacy or any(x[1] == "ERROR" for x in legacy) else (
                "MATCH" if all(x[1] == "MATCH" for x in legacy) else "MISMATCH")
            for e in sorted(grouped[src], key=lambda x: x["addr"]):
                fr = (result or {}).get("functions", {}).get(e["link_name"],
                            _error("Expected T3 public missing from object") if result else region)
                row = dict(addr=hex(e["addr"]), name=e["name"], link_name=e["link_name"],
                           src=src, compiler=match.file_cc(path(src)), cflags=match.file_cflags(path(src)),
                           obj_sha256=digest, legacy_verdict=legacy_map.get(e["link_name"], "ERROR"),
                           legacy_region_verdict=legacy_region, legacy_results=legacy,
                           e0_function_verdict=fr["verdict"], e0_region_verdict=region["verdict"],
                           findings=scoped_findings(fr, region),
                           function_orig_range=[fr.get("orig_start"), fr.get("orig_end")],
                           region_orig_range=[region.get("orig_start"), region.get("orig_end")],
                           excluded_metadata=(result or {}).get("excluded_metadata", []),
                           normalized_obligations=region.get("obligations", []))
                row.update({k: region["metrics"].get(k, 0) for k in (
                    "leading_bytes_len", "data_segments_checked", "data_fixups_checked",
                    "code_fixups_checked", "reverse_le_fixups_checked")})
                row["rfc15_category"] = classify_row(row)
                rows.append(row)
            if count % 50 == 0 or count == len(sources):
                print(f"E0 audit: {count}/{len(sources)} C files, {len(rows)} T3 functions", flush=True)
    rows.sort(key=lambda r: int(r["addr"], 16))
    summary = dict(functions_discovered=len(entries), c_files=len(sources),
                   expected_functions=519, expected_c_files=514,
                   count_matches_expectation=len(entries) == 519 and len(sources) == 514,
                   function_verdicts={v: sum(r["e0_function_verdict"] == v for r in rows) for v in VERDICTS},
                   region_verdicts={v: sum(r["e0_region_verdict"] == v for r in rows) for v in VERDICTS},
                   legacy_verdicts=dict(Counter(r["legacy_verdict"] for r in rows)),
                   rfc15_categories={c: sum(r["rfc15_category"] == c for r in rows) for c in CATEGORIES},
                   nonmatch_functions=sum(r["e0_function_verdict"] != "MATCH" or
                                          r["e0_region_verdict"] != "MATCH" for r in rows),
                   legacy_false_match_candidates=sum(r["legacy_region_verdict"] == "MATCH" and
                       r["e0_region_verdict"] == "MISMATCH" for r in rows))
    baseline = "3ee53aa5d4e7911e7f8d1bb0097de17223c8a559"
    payload = dict(experiment="E0", baseline=baseline, summary=summary, functions=rows,
                   provenance=dict(jobs=jobs, fresh_compile=True, compiler_timeout_seconds=180,
                     discovery="symbols.load + progress.classify(analysis.run().functions)",
                     original_exe_sha256=hashlib.sha256(Path(path("original", "install", "war.exe")).read_bytes()).hexdigest(),
                     prototype_sha256=hashlib.sha256(Path(__file__).with_name("matcher_proto.py").read_bytes()).hexdigest(),
                     production_diff=subprocess.check_output(["git", "diff", baseline, "--", "tools/", "src/", "analysis/", "tests/", "asm/", "Makefile", "flake.nix", "AGENTS.md"], text=True)))
    output = Path(output)
    dump_json(output / "t3_reaudit.json", payload)
    columns = ["addr", "name", "link_name", "src", "compiler", "cflags", "obj_sha256",
               "legacy_verdict", "legacy_region_verdict", "e0_function_verdict", "e0_region_verdict",
               "rfc15_category", "findings", "leading_bytes_len", "data_segments_checked",
               "data_fixups_checked", "code_fixups_checked", "reverse_le_fixups_checked"]
    with (output / "t3_reaudit.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row, findings=json.dumps(row["findings"], sort_keys=True)))
    print(json.dumps(summary, sort_keys=True), flush=True)
    return payload


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--output", type=Path, default=RESULTS)
    args = ap.parse_args()
    if args.jobs < 1:
        ap.error("jobs must be positive")
    result = audit(args.jobs, args.output)
    return int(audit_has_errors(result))


if __name__ == "__main__":
    raise SystemExit(main())
