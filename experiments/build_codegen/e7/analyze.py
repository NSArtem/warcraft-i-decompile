"""Pure aggregation: full S(f), regression pairs, CU diagnostics, greedy presets."""
from collections import Counter
import csv
from itertools import product
from pathlib import Path

from .common import RESULTS, STATES, digest, dump, flag_key

R6 = [0x13c04, 0x13c84, 0x13dd0, 0x15314, 0x1af20, 0x21df0, 0x22a4c,
      0x22a98, 0x29f40, 0x2ab54, 0x34060, 0x22f48, 0x31fc0, 0x34480]
LEGACY = ["c01", "c02", "c18", "c20", "c21", "c05", "c03", "c04"]


def untested_space(configs):
    """Explicit finite hypothesis universe, not all possible compiler commands."""
    tested = {flag_key(c["flags"]) for c in configs}
    axes = dict(arch=["-3r", "-4r", "-5r"], mode=["-ot", "-os", "-od"],
                loops=["", "-ol", "-ol+"], alias=["", "-oa"],
                secondary=["", "-or", "-oi", "-om", "-oc"], packing=["-zp1", "-zp2", "-zp4"],
                debug=["", "-d1", "-d1+", "-d2"], frame=["", "-of", "-of+"])
    out = []
    for arch, mode, loop, alias, secondary, packing, debug, frame in product(*axes.values()):
        flags = " ".join(t for t in ("-s", mode, alias, loop, secondary, arch, debug, frame, packing) if t)
        if flag_key(flags) not in tested:
            out.append(dict(flags=flags, state="untested"))
    return dict(fixed=["-s", "-q -zl -bt=dos"], axes=axes, combinations=out,
                other_options="Capability-only options -oe/-ou/-ox/-oz/-j/-ri/-zc and interactions between multiple secondary options are untested outside this finite universe.")


def index(matrix):
    return ({u["source"]: u for u in matrix["units"]}, {c["id"]: c for c in matrix["configurations"]})


def att(r, cid, units):
    return units[r["source"]]["attempts"][cid]


def improved(r, cid, baseline=None):
    a, b = r["cells"][cid].get("score"), r["cells"][baseline or r["declared_config"]].get("score")
    return a is not None and b is not None and tuple(a) < tuple(b)


def counts(rows, cids, units):
    return dict(function_matches=sum(any(r["cells"][c]["state"] == "matched" for c in cids) for r in rows),
                whole_object_matches=sum(any(r["cells"][c]["state"] == "matched" and att(r,c,units).get("whole_object_match",False) for c in cids) for r in rows),
                e0_region_matches=sum(any(att(r,c,units).get("region",{}).get("verdict") == "MATCH" for c in cids) for r in rows),
                buildable_t3=sum(any(r["cells"][c]["state"] == "matched" and att(r,c,units).get("buildable",False) for c in cids) for r in rows),
                score_improvements=sum(any(improved(r,c) for c in cids) for r in rows),
                score_improvements_vs_default=sum(any(improved(r,c,"c01") for c in cids) for r in rows),
                residual_mismatch_score_improvements=sum(not r["compatible_configs"] and any(improved(r,c) for c in cids) for r in rows))


def compatibility(rows, configs):
    groups = {k: [] for k in ("only_4r", "only_5r", "both_4r_5r", "only_3r", "neither_4r_nor_5r")}
    for r in rows:
        arches = {a for c in configs if c["id"] in r["compatible_configs"] for a in ("-3r","-4r","-5r") if a in c["flags"].split()}
        if "-4r" in arches and "-5r" in arches:
            key = "both_4r_5r"
        elif "-4r" in arches:
            key = "only_4r"
        elif "-5r" in arches:
            key = "only_5r"
        elif "-3r" in arches:
            key = "only_3r"
        else:
            key = "neither_4r_nor_5r"
        groups[key].append(r["addr"])
    pairs = {}
    for name, cid in (("4r_to_5r","c06"),("remove_ol","c03"),("add_oa","c02"),
                      ("add_or","c11"),("add_oi","c12"),("zp2_to_zp1","c16")):
        baseline = {r["addr"] for r in rows if r["cells"]["c01"]["state"] == "matched"}
        variant = {r["addr"] for r in rows if r["cells"][cid]["state"] == "matched"}
        pairs[name] = dict(baseline="c01", variant=cid, baseline_matches=len(baseline),
                           variant_matches=len(variant), regressions=sorted(baseline-variant),
                           recoveries=sorted(variant-baseline), both=len(baseline&variant))
    return dict(group_counts={k:len(v) for k,v in groups.items()}, group_functions=groups,
                definition="Existence of a tested E0 FunctionMatch under each architecture; only_3r is separated from neither. Unequal search coverage is not proof of original architecture.",
                paired_toggles=pairs,
                declared_configuration_failures=[dict(addr=r["addr"], source=r["source"],
                    declared_compiler=r["declared_compiler"], declared_config=r["declared_config"],
                    state=r["cells"][r["declared_config"]]["state"], function=r["cells"][r["declared_config"]].get("function"))
                    for r in rows if r["cells"][r["declared_config"]]["state"] != "matched"])


def summarize(matrix):
    units, configs = index(matrix)
    cids = list(configs)
    t3 = [r for r in matrix["functions"] if r["tier"] == "T3"]
    t4 = [r for r in matrix["functions"] if r["tier"] == "T4"]
    clean = [r for r in t4 if r["dependency_clean"]]
    t4units = {r["source"] for r in t4}
    return dict(cohorts=dict(t3=len(t3),t3_files=len({r['source'] for r in t3}),
                            t4=len(t4),t4_files=len(t4units),
                            t4_dependency_clean=len(clean),
                            t4_dependency_clean_files=sum(units[s]["dependency_clean"] for s in t4units),
                            t4_unresolved_relocations=sum(not r["dependency_clean"] and units[r["source"]]["baseline_dependencies"] is not None for r in t4),
                            t4_unresolved_files=sum(not units[s]["dependency_clean"] and units[s]["baseline_dependencies"] is not None for s in t4units),
                            t4_baseline_compile_errors=sum(units[s]["baseline_dependencies"] is None for s in t4units)),
                states={s:sum(cell["state"]==s for r in matrix["functions"] for cell in r["cells"].values()) for s in STATES},
                all_tested_t4=counts(clean,cids,units), legacy_eight_t4=counts(clean,LEGACY,units),
                per_config_t4={cid:counts(clean,[cid],units) for cid in cids},
                t3_compatibility=compatibility(t3,list(configs.values())),
                r6=dict(historical_expected_addresses=R6,
                    evidence=[dict(addr=r["addr"], name=r["name"], source=r["source"],
                        declared_config=r["declared_config"], baseline_score=r["cells"][r["declared_config"]].get("score"),
                        default_score=r["cells"]["c01"].get("score"),
                        five_r=r["cells"]["c06"], object=att(r,"c06",units)) for r in clean if r["addr"] in R6],
                    five_r_score_improvements=[r["addr"] for r in clean if improved(r,"c06")],
                    five_r_score_improvements_vs_default=[r["addr"] for r in clean if improved(r,"c06","c01")]))


def cu_hypotheses(matrix):
    from wc1 import progress
    groups = {}
    for r in matrix["functions"]:
        groups.setdefault(r["module"], []).append(r)
    modules = {m["name"]:m for m in progress.load_modules()}
    rows = []
    for name, rs in sorted(groups.items()):
        intersection = sorted(set.intersection(*(set(r["compatible_configs"]) for r in rs)))
        # Also show the already recovered T3 subset: unsolved T4s trivially
        # empty many mixed-module intersections and cannot establish a boundary.
        t3 = [r for r in rs if r["tier"] == "T3"]
        t3_intersection = sorted(set.intersection(*(set(r["compatible_configs"]) for r in t3))) if t3 else None
        diagnostics = dict(incomplete_flag_space="Possible: finite orthogonal grid, most interactions explicitly untested.",
                           reconstructed_c_error="Possible, unproven: T4 equivalence does not recover original source spelling.",
                           local_pragma="Possible, unproven: source pragmas and per-function backend choices were not recovered.",
                           source_specificity="Possible: different reconstructed TUs, local data, inlining, register allocation and alignment.",
                           hidden_none16_boundary="Unproven; requires independent boundary evidence. No CU boundary is inferred here.")
        rows.append(dict(module=name,start=modules[name]["start"],end=modules[name]["end"],
                         audited_functions=[r["addr"] for r in rs], recovered_t3_functions=len(t3),
                         intersection=intersection,t3_only_intersection=t3_intersection,
                         functions_with_empty_s=[r["addr"] for r in rs if not r["compatible_configs"]],
                         incomplete_functions=[r["addr"] for r in rs if any(c["state"]=="untested" for c in r["cells"].values())],
                         status="consistent_tested_flags" if intersection else "contradictory_evidence",
                         competing_causes=diagnostics if not intersection else None,
                         boundary_inferred=False))
    return dict(schema=1,matrix_sha256=digest(matrix),modules=rows,
                summary=dict(modules=len(rows),nonempty_intersection=sum(bool(r["intersection"]) for r in rows),
                             empty_intersection=sum(not r["intersection"] for r in rows),
                             t3_only_nonempty=sum(bool(r["t3_only_intersection"]) for r in rows),
                             t3_only_empty=sum(r["t3_only_intersection"]==[] for r in rows)),
                caveat="modules.toml ranges are hypotheses, not proven original compilation units; S(f) belongs to its current reconstructed TU context.")


def presets(matrix):
    units, configs = index(matrix)
    rows = [r for r in matrix["functions"] if r["tier"]=="T4" and r["dependency_clean"]]
    t3 = [r for r in matrix["functions"] if r["tier"]=="T3"]
    def events(cid):
        found = set()
        for r in rows:
            if r["cells"][cid]["state"]=="matched":
                found.add(("function",r["addr"]))
                if att(r,cid,units).get("buildable"):
                    found.add(("buildable",r["addr"]))
            if improved(r,cid):
                found.add(("improvement",r["addr"]))
        found.update(("existing_t3",r["addr"]) for r in t3 if r["cells"][cid]["state"]=="matched")
        return found
    sets = {c:events(c) for c in configs}
    covered, remaining, ranking = set(), list(configs), []
    while remaining:
        def gain(cid):
            ctr=Counter(k for k,a in sets[cid]-covered)
            return tuple(ctr[k] for k in ("buildable","function","improvement","existing_t3"))
        cid = "c01" if not ranking else max(remaining,key=gain)
        fresh = sets[cid]-covered
        marginal = Counter(k for k,a in fresh)
        ranking.append(dict(config=cid,flags=configs[cid]["flags"],
                            marginal_t3_gain=marginal["function"],marginal_buildable_t3_gain=marginal["buildable"],
                            marginal_score_improvements=marginal["improvement"],marginal_existing_t3_coverage=marginal["existing_t3"],
                            cumulative_function_matches=sum(k=="function" for k,a in covered|fresh),
                            cumulative_buildable_t3=sum(k=="buildable" for k,a in covered|fresh)))
        covered |= sets[cid]
        remaining.remove(cid)
    useful = [r for r in ranking if any(r[k] for k in ("marginal_t3_gain","marginal_buildable_t3_gain","marginal_score_improvements","marginal_existing_t3_coverage"))]
    return dict(schema=1,matrix_sha256=digest(matrix),
                method="Seed current default, then greedy lexicographic marginal (buildable T4, function T4, strict score improvement, existing T3 coverage), ties by config order. Events are functions, not compiler timing estimates.",
                tier1=useful[:5],tier2=useful[5:],ranking=ranking,
                tier1_policy="First five useful configs: bounded fast search; Tier 2 retains every remaining nonzero-yield configuration.",
                default_change_recommended=False,
                default_caveat="Add search presets; a -5r default switch regresses existing -4r matches. Presets are not recovered original CU options.")


def write_derived(matrix, output=RESULTS):
    output=Path(output)
    dump(output/"cu_hypotheses.json",cu_hypotheses(matrix))
    dump(output/"proposed_presets.json",presets(matrix))
    units, configs=index(matrix)
    columns=["addr","name","source","config","flags","whole_object_match","e0_region_match","check_t3_buildable","buildable_t3","baseline_score","score"]
    with (output/"t4_new_matches.csv").open("w",newline="") as fh:
        writer=csv.DictWriter(fh,fieldnames=columns)
        writer.writeheader()
        for r in matrix["functions"]:
            if r["tier"]!="T4":continue
            for cid in r["compatible_configs"]:
                a=att(r,cid,units)
                writer.writerow(dict(addr=hex(r["addr"]),name=r["name"],source=r["source"],config=cid,
                    flags=configs[cid]["flags"],whole_object_match=a["whole_object_match"],
                    e0_region_match=a["region"]["verdict"]=="MATCH",
                    check_t3_buildable=a.get("placement_check",{}).get("ok",False),buildable_t3=a["buildable"],
                    baseline_score=r["cells"][r["declared_config"]].get("score"),score=r["cells"][cid].get("score")))
