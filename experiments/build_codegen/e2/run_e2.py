"""Reproduce E2 from fresh compiler output; writes only E2-owned paths.

Run: python3 -m experiments.build_codegen.e2.run_e2
No make targets, production edits, linker placeholder repairs, or OMF rewriting.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
import json
from pathlib import Path
import subprocess

from wc1 import analysis, oldcc
from experiments.build_codegen.e0.matcher_proto import OriginalIndex
from .harness import (AREAS, BASELINE, FLAGS, HERE, RESULTS, ROOT, SCRATCH,
    VARIANTS, adjacent_runs, body_evidence, compact, compile_source, consolidate,
    dump, evaluate, header_overlay, inventory, sha, starts, summary)
from .synthetic import run_synthetic


def first_difference(a, b):
    aa, bb = bytes.fromhex(a["neutral_hex"]), bytes.fromhex(b["neutral_hex"])
    off = next((i for i, (x, y) in enumerate(zip(aa, bb)) if x != y), min(len(aa), len(bb)))
    if aa == bb:
        return None
    def nearest(body):
        return next((i for i in reversed(body["instructions"]) if i[0] <= off), None)
    return dict(body_offset=off, standalone_instruction=nearest(a),
                consolidated_instruction=nearest(b), standalone_size=len(aa),
                consolidated_size=len(bb))


def diagnose(fr, body, standalone, primary, region, original_end):
    context_changed = body["instruction_sha256"] != standalone["instruction_sha256"]
    flag_changed = standalone["instruction_sha256"] != primary["instruction_sha256"]
    causes = []
    ff = fr["findings"]
    codes = {f["code"] for f in ff}
    if context_changed:
        causes.append("genuine_context_body_change")
        # A cross-function short epilogue jump is emitted by the optimizer;
        # the unchanged function source did not ask for this transfer.
        if any(e["mnemonic"].startswith("j") and e["target_offset"] is not None
               for e in body["exits"]):
            causes.append("cross_function_epilogue_or_tail_transfer")
    if flag_changed:
        causes.append("standalone_flag_body_change")
    if fr["verdict"] != "MATCH":
        if any(f["code"] in ("relocation_target_mismatch", "local_definition_mismatch") and
               (f["evidence"].get("target_kind") == "seg" and
                f["evidence"].get("symbolic_target") != 1 or
                f["evidence"].get("segment") not in (None, 1)) for f in ff):
            causes.append("data_anchor_shift")
        if any(f["code"] in ("relocation_target_mismatch", "local_definition_mismatch") and
               (f["evidence"].get("target_kind") == "seg" and
                f["evidence"].get("symbolic_target") == 1 or
                f["evidence"].get("segment") == 1) for f in ff):
            causes.append("intra_tu_code_anchor_shift")
        if "relative_target_mismatch" in codes:
            causes.append("intra_tu_relative_displacement")
        if "external_rel8" in codes:
            external = [f for f in ff if f["code"] == "external_rel8"]
            if any(fr["orig_start"] <= f["evidence"]["original_target"] < original_end for f in external):
                causes.append("e0_noncontiguous_region_bounds")
            if any(not fr["orig_start"] <= f["evidence"]["original_target"] < original_end for f in external):
                causes.append("e0_cross_function_rel8_unsupported")
        if "byte_mismatch" in codes and not context_changed and not flag_changed:
            causes.append("inter_function_filler_extent")
        if not causes:
            causes.append("e0_obligation_or_extent_failure")
    # A region data collision does not automatically fail FunctionMatch.
    # Record separately, without attributing every function to that collision.
    return context_changed, flag_changed, sorted(set(causes))


def light_body(body):
    return {k: v for k, v in body.items() if k not in ("body_hex", "neutral_hex", "instructions")}


def study(p, idx, db, entries, overlay, jobs):
    controls, objects, signatures = {}, {}, {}
    tasks = []
    for e in entries:
        variants = dict(VARIANTS)
        variants["declared"] = e["flags"]
        # Compile each unique flags context once; declared aliases native or
        # alias for this inventory, but all mappings remain explicit.
        for flags in dict.fromkeys(variants.values()):
            tasks.append((e, flags, "control/"+e["name"]+"_"+sha(flags.encode())[:10]))
    def compile_control(task):
        e, flags, key = task
        return e, flags, compile_source(ROOT / e["src"], flags, key)
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        for i, (e, flags, mod) in enumerate(pool.map(compile_control, tasks), 1):
            r = evaluate(p, idx, db, mod)
            name = e["link_name"]
            controls[e["name"], flags] = dict(function=compact(r["functions"][name]),
                                             region=compact(r["region"]))
            objects[e["name"], flags] = mod
            signatures[e["name"], flags] = body_evidence(mod, name)
            if i % 96 == 0 or i == len(tasks):
                print(f"standalone controls: {i}/{len(tasks)}", flush=True)
    baseline = []
    for e in entries:
        cr = controls[e["name"], e["flags"]]
        baseline.append(dict(name=e["name"], src=e["src"], flags=e["flags"],
                             **cr, body=light_body(signatures[e["name"], e["flags"]])))
    failed = [b["name"] for b in baseline if b["function"]["verdict"] != "MATCH"]
    if failed:
        dump(RESULTS / "failed_controls.json", baseline)
        raise RuntimeError(f"Declared standalone E0 FunctionMatch controls failed: {failed}")

    # Check that declaration-only reconciliation has no baseline body/verdict
    # effect on any STATUS standalone, including those not using status.h.
    overlay_checks = []
    for e in entries:
        if e["area"] != "status":
            continue
        mod = compile_source(ROOT / e["src"], e["flags"], "overlay/"+e["name"], overlay=overlay)
        r = evaluate(p, idx, db, mod)
        body = body_evidence(mod, e["link_name"])
        control = signatures[e["name"], e["flags"]]
        ok = body["instruction_sha256"] == control["instruction_sha256"]
        assert ok and r["functions"][e["link_name"]]["verdict"] == "MATCH", e["name"]
        overlay_checks.append(dict(name=e["name"], identical_body=ok, function="MATCH"))

    groups = []
    for area in AREAS:
        ee = [e for e in entries if e["area"] == area]
        # Full area always measured under a single flag set. Native STATUS is
        # explicitly forced: only StatusPanelDraw originally requires -oa.
        groups.append(dict(id=area+"_all", area=area, kind="whole_area", entries=ee))
        if len({e["flags"] for e in ee}) > 1:
            for k, flags in enumerate(dict.fromkeys(e["flags"] for e in ee)):
                groups.append(dict(id=area+f"_compatible_{k}", area=area,
                                   kind="compatible", entries=[e for e in ee if e["flags"] == flags],
                                   declared_flags=flags))
        for k, run in enumerate(adjacent_runs(ee, p)):
            groups.append(dict(id=area+f"_run_{k}", area=area, kind="adjacent_run", entries=run,
                               declared_flags=run[0]["flags"]))
            # Also test contiguous subsets whose original starts share a
            # mod16 value. This supplies real RegionMatched TUs for Part C
            # even when a maximal contiguous T3 run mixes 4-byte spacings.
            blocks = []
            for e in run:
                if not blocks or e["addr"] % 16 != blocks[-1][-1]["addr"] % 16:
                    blocks.append([])
                blocks[-1].append(e)
            for j, block in enumerate(blocks):
                if 2 <= len(block) < len(run):
                    groups.append(dict(id=area+f"_run_{k}_aligned_{j}", area=area,
                        kind="adjacent_subset", entries=block, declared_flags=block[0]["flags"]))

    rows, results, native_runs = [], [], []
    for group in groups:
        ee = group["entries"]
        src = consolidate(ee, SCRATCH / "tu" / (group["id"]+".c"))
        variants = dict(VARIANTS)
        if group.get("declared_flags") not in (None, FLAGS):
            variants["declared"] = group["declared_flags"]
        for variant, flags in variants.items():
            mod = compile_source(src, flags, f"tu/{group['id']}/{variant}", overlay=overlay)
            r = evaluate(p, idx, db, mod)
            ss = dict((n, off) for off, n in starts(mod))
            rb = ee[0]["addr"] - ss[ee[0]["link_name"]]
            gr = []
            for e in ee:
                name = e["link_name"]
                body = body_evidence(mod, name)
                same = signatures[e["name"], flags]
                primary = signatures[e["name"], e["flags"]]
                fr = r["functions"][name]
                changed, flag_changed, causes = diagnose(fr, body, same, primary, r["region"],
                                                         idx.functions[e["addr"]]["end"])
                row = dict(group=group["id"], group_kind=group["kind"], area=group["area"],
                    variant=variant, flags=flags, name=e["name"], addr=e["addr"], src=e["src"],
                    baseline_function=controls[e["name"], e["flags"]]["function"]["verdict"],
                    same_flags_standalone_function=controls[e["name"], flags]["function"]["verdict"],
                    function=fr["verdict"], region=r["region"]["verdict"],
                    original_relative_offset=e["addr"]-ee[0]["addr"],
                    compiled_relative_offset=ss[name]-ss[ee[0]["link_name"]],
                    relative_offset_error=ss[name]+rb-e["addr"],
                    context_body_changed=changed, flag_body_changed=flag_changed, causes=causes,
                    context_first_difference=first_difference(same, body),
                    flag_first_difference=first_difference(primary, same),
                    body=light_body(body), standalone_body=light_body(same),
                    e0_function=compact(fr))
                rows.append(row)
                gr.append(row)
            sg = summary(gr)
            sg["n_gained_vs_same_flags_standalone"] = sum(
                x["same_flags_standalone_function"] != "MATCH" and x["function"] == "MATCH" for x in gr)
            # Test every original-adjacent run's relative offsets inside each
            # full group too. RegionMatch itself is the untouched E0 whole-
            # module verdict; separate run TUs supply complete run verdicts.
            adjacent = []
            for run in adjacent_runs(ee, p):
                first = run[0]
                adjacent.append(dict(names=[x["name"] for x in run],
                    relative_offsets_match=all(ss[x["link_name"]]-ss[first["link_name"]] ==
                        x["addr"]-first["addr"] for x in run),
                    offsets=[[x["name"], x["addr"]-first["addr"],
                              ss[x["link_name"]]-ss[first["link_name"]]] for x in run]))
            results.append(dict(id=group["id"], kind=group["kind"], area=group["area"],
                variant=variant, flags=flags, names=[e["name"] for e in ee],
                summary=sg, e0_region=compact(r["region"]), adjacent_offsets=adjacent,
                segments=[dict(name=s.name, cls=s.cls, size=s.length, align=s.align,
                               sha256=sha(bytes(s.data))) for s in mod.segments],
                tu_sha256=sha(src.read_bytes())))
            if group["kind"] in ("adjacent_run", "adjacent_subset") and variant == "native" and r["region"]["verdict"] == "MATCH":
                native_runs.append((group, mod, r))
        print(f"consolidation: {group['id']} ({len(ee)} functions)", flush=True)
    return dict(baseline=baseline, overlay_controls=overlay_checks,
        groups=results, rows=rows, standalone_variant_controls=[dict(name=e["name"], variant=v,
            flags=f, **controls[e["name"], f]) for e in entries for v, f in VARIANTS.items()]), native_runs


def perturbations(p, idx, db, native_runs, overlay):
    """Perturb first/middle/last neighbor in two genuinely RegionMatched TUs."""
    chosen = []
    for area in ("playflic", "status", "gamedlg"):
        candidates = [g for g in native_runs if g[0]["area"] == area]
        if not candidates:
            raise RuntimeError(f"No consolidated RegionMatch control for {area}")
        chosen.append(max(candidates, key=lambda x: len(x[0]["entries"])))
    out = []
    additions = {f"bytes_{n}": f"E2Bytes{n}();" for n in (1, 2, 3, 7)}
    additions.update(string='E2UseString("E2-neighbor-literal");',
        pressure="E2Pressure(E2Gate, E2Gate+1, E2Gate+2, E2Gate+3, E2Gate+4, E2Gate+5, E2Gate+6, E2Gate+7);",
        epilogue="if (E2Gate) return E2Gate;")
    # Epilogue injection uses a void-compatible gate/return at the end of a
    # void function; for nonvoid functions inject early return 0 instead.
    preamble = "extern void E2UseString(const char *);\nextern volatile int E2Gate;\n" + \
               "extern void E2Pressure(unsigned,unsigned,unsigned,unsigned,unsigned,unsigned,unsigned,unsigned);\n"
    for n in (1, 2, 3, 7):
        preamble += f"void E2Bytes{n}(void);\n#pragma aux E2Bytes{n} = " + \
                    " ".join(["0x90"]*n) + " modify exact [];\n"
    for group, control_mod, control_r in chosen:
        ee = group["entries"]
        # Three positions make propagation before/after the edit observable.
        for target_index in sorted({0, len(ee)//2, len(ee)-1}):
            target = ee[target_index]
            original = (ROOT / target["src"]).read_text()
            # All selected files have exactly one top-level function body.
            import re
            clean = re.sub(r"/\*.*?\*/", "", original, flags=re.S)
            # C89 requires statements after the initial declaration block.
            positioned = re.sub(r"/\*.*?\*/", lambda m: " "*len(m[0]), original, flags=re.S)
            definition = re.search(r"\b"+re.escape(target["name"])+r"\s*\([^;{}]*\)\s*\{", positioned)
            assert definition is not None, target["name"]
            insertion = definition.end()
            while True:
                decl = re.match(r"\s*(?:const\s+|volatile\s+)*(?:void|unsigned|short|int|char|long)\b", positioned[insertion:])
                if decl is None:
                    break
                insertion = positioned.index(";", insertion) + 1
            is_void = bool(re.search(r"\bvoid\s+"+target["name"]+r"\s*\(", clean))
            for kind, statement in additions.items():
                if kind == "epilogue":
                    statement = "if (E2Gate) return;" if is_void else "if (E2Gate) return 0;"
                changed_src = SCRATCH / "perturb" / (sha(group["id"].encode())[:8]+f"_{target_index}_{kind}.c")
                changed_src.parent.mkdir(parents=True, exist_ok=True)
                changed_src.write_text(preamble + original[:insertion]+"\n"+statement+"\n"+original[insertion:])
                tu = consolidate(ee, changed_src.with_name(changed_src.stem+"_tu.c"),
                                 {target["src"]: changed_src})
                mod = compile_source(tu, FLAGS, f"perturb/{group['id']}_{target_index}_{kind}", overlay=overlay)
                result = evaluate(p, idx, db, mod)
                neighbors = []
                for e in ee:
                    if e == target:
                        continue
                    before = body_evidence(control_mod, e["link_name"])
                    after = body_evidence(mod, e["link_name"])
                    neighbors.append(dict(name=e["name"],
                        start_shift=after["start"]-before["start"],
                        body_raw_changed=after["body_raw_sha256"] != before["body_raw_sha256"],
                        instruction_changed=after["instruction_sha256"] != before["instruction_sha256"],
                        before_function=control_r["functions"][e["link_name"]]["verdict"],
                        after_function=result["functions"][e["link_name"]]["verdict"],
                        first_difference=first_difference(before, after),
                        before=light_body(before), after=light_body(after),
                        e0_function=compact(result["functions"][e["link_name"]])))
                before = body_evidence(control_mod, target["link_name"])
                after = body_evidence(mod, target["link_name"])
                # These byte emitters must actually add the requested number
                # of machine body bytes, independently of padded start shifts.
                delta = after["body_size"]-before["body_size"]
                if kind.startswith("bytes_"):
                    assert delta == int(kind.split("_")[1]), (kind, delta)
                out.append(dict(group=group["id"], names=[e["name"] for e in ee],
                    control_region=control_r["region"]["verdict"],
                    edited_name=target["name"], edited_index=target_index, kind=kind,
                    edited_body_size_delta=delta, neighbors=neighbors,
                    e0_region=compact(result["region"])))
        print(f"neighbor perturbations: {group['id']}", flush=True)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--jobs", type=int, default=4)
    args = ap.parse_args()
    if args.jobs < 1:
        ap.error("--jobs must be positive")
    SCRATCH.mkdir(parents=True, exist_ok=True)
    entries, excluded, db = inventory()
    p = analysis.run(cache=False)
    idx = OriginalIndex(p)
    overlay, overlay_info = header_overlay()
    # Capture the actual unmodified-source compiler failure as a negative
    # control. Diagnostics paths are normalized for reproduction elsewhere.
    src = consolidate([e for e in entries if e["area"] == "status"], SCRATCH / "status_unmodified.c")
    try:
        compile_source(src, FLAGS, "status_unmodified")
    except SystemExit as exc:
        # A crash/timeout must not masquerade as the expected declaration
        # negative control. Keep deterministic diagnostics, without timings.
        if "E1151" not in str(exc):
            raise
        overlay_info["unmodified_compile_errors"] = [line.replace(str(ROOT), "<ROOT>").replace(
            str(ROOT).replace("/", "\\"), "<ROOT>") for line in str(exc).splitlines() if "Error!" in line]
    else:
        raise RuntimeError("Expected stale STATUS header declarations no longer fail; review overlay")
    real, matching_runs = study(p, idx, db, entries, overlay, args.jobs)
    dump(SCRATCH / "real.json", real)
    synthetic = run_synthetic()
    dump(SCRATCH / "synthetic.json", synthetic)
    perturb = perturbations(p, idx, db, matching_runs, overlay)
    primary = [r for r in real["rows"] if r["group_kind"] == "whole_area" and r["variant"] == "native"]
    by_name = {r["name"]: r for r in primary}
    variant_transitions = {}
    for variant in VARIANTS:
        rr = [r for r in real["rows"] if r["group_kind"] == "whole_area" and r["variant"] == variant]
        variant_transitions[variant] = dict(summary(rr),
            gained_vs_native_names=[r["name"] for r in rr if by_name[r["name"]]["function"] != "MATCH" and r["function"] == "MATCH"],
            lost_vs_native_names=[r["name"] for r in rr if by_name[r["name"]]["function"] == "MATCH" and r["function"] != "MATCH"])
    compatible = [r for r in real["rows"] if (r["group"] in ("gamedlg_all", "playflic_all", "status_compatible_0")
        and r["variant"] == "native") or (r["group"] == "status_compatible_1" and r["variant"] == "alias")]
    production = subprocess.check_output(["git", "diff", BASELINE, "--", "tools/", "src/", "analysis/",
        "tests/", "Makefile", "flake.nix", "AGENTS.md"], cwd=ROOT, text=True)
    if production:
        raise RuntimeError("Production changes violate E2 scope")
    payload = dict(experiment="E2", baseline_commit=BASELINE, selection=entries, excluded=excluded,
        provenance=dict(original_exe_sha256=sha((ROOT / "original/install/war.exe").read_bytes()),
            e0_matcher_sha256=sha((HERE.parent / "e0/matcher_proto.py").read_bytes()),
            watcom10a_wcc_sha256=sha((Path(oldcc.root()) / "binnt/wcc386.exe").read_bytes()),
            ow2_wcc_sha256=sha(Path(subprocess.check_output(["which", "wcc386"], text=True).strip()).read_bytes()),
            fresh_compilation=True, compiler_timeout=180, production_diff=production),
        header_reconciliation=overlay_info, synthetic=synthetic, consolidation=real,
        perturbations=perturb, summary=dict(forced_primary=summary(primary), compatible_primary=summary(compatible),
            whole_area_variants=variant_transitions,
            baseline_function_matches=sum(b["function"]["verdict"] == "MATCH" for b in real["baseline"]),
            selected_functions=len(entries), groups=len(real["groups"]), observations=len(real["rows"])))
    dump(RESULTS / "results.json", payload)
    columns = ["group", "group_kind", "area", "variant", "flags", "name", "addr", "src",
        "baseline_function", "same_flags_standalone_function", "function", "region",
        "original_relative_offset", "compiled_relative_offset", "relative_offset_error",
        "context_body_changed", "flag_body_changed", "causes", "context_first_difference", "flag_first_difference"]
    with (RESULTS / "consolidation_rows.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for r in real["rows"]:
            writer.writerow({k: json.dumps(r[k], sort_keys=True) if isinstance(r[k], (list, dict)) else r[k]
                             for k in columns})
    print(json.dumps(payload["summary"], sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
