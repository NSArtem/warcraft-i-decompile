"""Run E8 end to end and write the committed artifacts deterministically.

    python3 -m experiments.build_codegen.e8.run_e8

Artifacts (all path-free, JSON with sorted keys, CSV with LF):

    docs/research/build-codegen/results/e8/synthetic_manifest.json
    docs/research/build-codegen/results/e8/metrics.json
    docs/research/build-codegen/results/e8/signal_metrics.csv
    docs/research/build-codegen/results/e8/game_exploratory.json

Corpus A is rebuilt from source when `build/e8/` is missing or the recipe
changed; the libsig sweep is cached on the digests of `war.exe` and the 10.0a
libraries; `setup.exe` sharing is cached on both executables' digests.
"""
import argparse
import json
import tomllib
from collections import Counter, defaultdict

from wc1 import path

from . import EXPERIMENT, RESULTS, SCHEMA, SCRATCH, dump_json, sha256_file, write_csv
from . import evaluate_signals as ev
from . import real_corpus, synthetic_corpus

E7_MATRIX = path("docs", "research", "build-codegen", "results", "e7", "calibration_matrix.json")


# ---------------------------------------------------------------------------
# E7 S(f) for the exploratory game reading
# ---------------------------------------------------------------------------
def e7_sf(refresh=False):
    """{addr: [config ids]} from E7's measured matrix (exploratory input only)."""
    import os
    key = sha256_file(E7_MATRIX)
    cache = SCRATCH / "e7_sf.json"
    if not refresh and cache.exists():
        rec = json.loads(cache.read_text(encoding="utf-8"))
        if rec.get("matrix_sha256") == key:
            return rec["sf"], rec["caveat"]
    mat = json.loads(open(E7_MATRIX, encoding="utf-8").read())
    sf = {}
    for f in mat["functions"]:
        cfgs = f.get("compatible_configs") or []
        if cfgs:
            sf[str(f["addr"])] = sorted(cfgs)
    caveat = mat.get("explored_space", {}).get("policy", "")
    caveat = ("S(f) is E7's observed compatible-configuration set in the function's current "
              "reconstructed TU context, not a property of the original compilation unit. "
              + (caveat or ""))
    dump_json(cache, {"matrix_sha256": key, "sf": sf, "caveat": caveat})
    return sf, caveat


def module_table():
    mods = tomllib.load(open(path("analysis", "modules.toml"), "rb"))["module"]
    return {m["start"]: {"name": m["name"], "kind": m["kind"]} for m in mods}


# ---------------------------------------------------------------------------
# metrics assembly
# ---------------------------------------------------------------------------
def corpus_block(corpus, result, extra=None):
    rows = result["rows"]
    ex = ev.examples(result)
    block = {
        "id": corpus["id"], "kind": corpus["kind"], "caveat": corpus.get("caveat", ""),
        "provenance": corpus.get("provenance", {}),
        "sample": {
            "pairs": len(rows),
            "boundaries": sum(1 for r in rows if r["truth"] == "boundary"),
            "same_cu": sum(1 for r in rows if r["truth"] == "same_cu"),
            "functions": len(corpus["functions"]),
            "cus_or_extents": len(corpus["cus"]),
            "gap_rules": dict(sorted(Counter(r["facts"]["rule"] or "none"
                                             for r in rows).items())),
        },
        "signals": [],
    }
    if extra:
        block["sample"].update(extra)
    for metric in ev.metrics(result):
        name = metric["signal"]
        entry = dict(metric)
        entry["classification"] = ev.classify(metric)
        entry["assumption"] = ev.PROVEN.get(name)
        entry["examples"] = _compact_examples(ex[name])
        block["signals"].append(entry)
    return block


def _compact_examples(entry):
    def one(x):
        out = {k: x.get(k) for k in ("prev", "cur", "gap", "gap_len", "rule",
                                     "style_prev", "style_cur", "prev_cu", "cur_cu",
                                     "prev_name", "cur_name", "evidence",
                                     "const_refs_prev", "const_refs_cur",
                                     "data_refs_prev", "data_refs_cur",
                                     "call_prev_to_cur", "call_cur_to_prev")}
        out["S_prev"] = x.get("S_prev", [])
        out["S_cur"] = x.get("S_cur", [])
        return out
    return {"false_positives": [one(x) for x in entry["false_positives"]],
            "false_negatives": [one(x) for x in entry["false_negatives"]]}


def _csv_rows(blocks):
    rows = []
    for corpus_id in ("synthetic", "libsig", "setup"):
        blk = blocks[corpus_id]
        for s in blk["signals"]:
            rows.append([corpus_id, s["signal"], s["role"], s["TP"], s["FP"], s["TN"],
                         s["FN"], _num(s["precision"]), _num(s["recall"]), _num(s["F1"]),
                         s["sample_size"], s["unavailable"], s["classification"]])
    return rows


def _num(v):
    return "" if v is None else f"{v:.6f}"


CSV_HEADER = ["corpus", "signal", "role", "TP", "FP", "TN", "FN", "precision", "recall",
              "F1", "sample_size", "unavailable", "classification"]


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def run(refresh_synthetic=False, refresh_libsig=False, refresh_setup=False, verbose=True):
    if verbose:
        print("E8: building corpus A (Watcom 10.0a + 10.0a wlink) ...", flush=True)
    synth = synthetic_corpus.build(force=refresh_synthetic)
    sf = synthetic_corpus.sf_table(synth, force=refresh_synthetic)
    synth["sf"] = sf
    prog_a = synthetic_corpus.program(synth)
    res_a = ev.evaluate(prog_a, synth)
    cases = synth.get("designed_cases") or synthetic_corpus._designed_cases(synth)
    if verbose:
        print("E8: corpus A: %d CUs, %d functions, %d labelled pairs"
              % (len(synth["cus"]), len(synth["functions"]), len(synth["labels"])), flush=True)

    if verbose:
        print("E8: corpus B1 (libsig object identity) ...", flush=True)
    prog = real_corpus.war_program()
    lib = real_corpus.libsig_corpus(prog, refresh=refresh_libsig)
    res_lib = ev.evaluate(prog, lib)
    # One assembly stub table (`clib3r:intxa386`) holds 259 of B1's same-CU
    # pairs.  The sensitivity corpus drops it so the compiler-generated C
    # runtime objects are not swamped by a single hand-written object.  It
    # reuses the cache the main B1 call has just refreshed or validated.
    lib_no_intx = real_corpus.libsig_corpus(prog, refresh=False,
                                            exclude_modules={"intxa386"})
    res_lib_no_intx = ev.evaluate(prog, lib_no_intx)
    if verbose:
        print("E8: corpus B2 (setup.exe provenance) ...", flush=True)
    setup = real_corpus.setup_corpus(prog, refresh=refresh_setup)
    res_setup = ev.evaluate(prog, setup)

    if verbose:
        print("E8: exploratory game analysis ...", flush=True)
    sf_e7, caveat = e7_sf()
    game = ev.game_analysis(prog, real_corpus.war_functions(prog), module_table(), sf=sf_e7)
    game["S_f_provenance"] = {"matrix": "results/e7/calibration_matrix.json",
                              "matrix_sha256": sha256_file(E7_MATRIX), "caveat": caveat}

    blocks = {
        "synthetic": corpus_block(synth, res_a, {"designed_cases": cases["checks"]}),
        "libsig": corpus_block(lib, res_lib, lib["diagnostics"]),
        "setup": corpus_block(setup, res_setup,
                              {k: v for k, v in setup["diagnostics"].items() if k != "runs"}),
    }
    sens_extra = dict(lib_no_intx["diagnostics"])
    sens_extra.update({
        "excluded_modules": ["intxa386"],
        "note": ("Sensitivity run: the verified `clib3r:intxa386` object is removed so one "
                 "hand-written assembly stub table cannot dominate the same-CU population. "
                 "All other admitted, non-overlapping extents are unchanged."),
    })
    sensitivity = {
        "libsig_without_intxa386": corpus_block(lib_no_intx, res_lib_no_intx, sens_extra),
    }
    full_sample = blocks["libsig"]["sample"]
    sens_sample = sensitivity["libsig_without_intxa386"]["sample"]
    sens_sample.update({
        "excluded_pairs": full_sample["pairs"] - sens_sample["pairs"],
        "excluded_same_cu_pairs": full_sample["same_cu"] - sens_sample["same_cu"],
        "excluded_boundary_pairs": full_sample["boundaries"] - sens_sample["boundaries"],
    })
    metrics = {
        "schema": SCHEMA, "experiment": EXPERIMENT, "artifact": "metrics",
        "ground_truth_rule": {
            "synthetic": ("Corpus A: CU membership from the build recipe, verified against the "
                          "10.0a wlink map; every adjacent function pair is labelled."),
            "libsig": ("Corpus B1: a 10.0a clib3r.lib / cstrtx3r.obj object's contiguous _TEXT "
                       "contribution, admitted only after the whole CODE segment is verified "
                       "byte-for-byte against war.exe with its relocation fields masked. "
                       "Overlapping candidate extents are removed, and pairs are labelled only "
                       "when both functions lie in admitted extents and no non-padding bytes sit "
                       "between them. The `libsig_without_intxa386` sensitivity block repeats "
                       "every metric without the clib3r:intxa386 stub table."),
            "setup": ("Corpus B2: setup.exe provenance; adjacent (identical, not identical) pairs "
                      "are boundaries under the whole-object-link premise. Pairs in which either "
                      "side is shorter than the setup identity matcher's minimum are excluded "
                      "(it cannot call such a function identical). Boundary labels only, so "
                      "precision is not measurable on this corpus."),
            "exploratory": ("The war.exe game range is NEVER ground truth and is not part of any "
                            "precision/recall number here."),
        },
        "rubric": {
            "strong_evidence": "precision >= 0.95 and TP >= 5",
            "weak_ambiguous": "0.60 <= precision < 0.95",
            "unreliable_noisy": "precision < 0.60",
            "unknown": "sample_size < 5 or precision undefined",
            "note": ("The rubric summarises measured precision only. `proven constraint` is not a "
                     "metric label: it names a logical constraint whose premise is stated in the "
                     "signal's `assumption` field, and the corpus reports how often the premise "
                     "fails in practice."),
        },
        "corpora": blocks,
        "sensitivity": sensitivity,
    }
    det = _determinism_checks(synth, lib, setup, res_a)
    metrics["determinism"] = det

    dump_json(RESULTS / "synthetic_manifest.json",
              synthetic_corpus.manifest(synth, sf=sf))
    dump_json(RESULTS / "metrics.json", metrics)
    write_csv(RESULTS / "signal_metrics.csv", CSV_HEADER, _csv_rows(blocks))
    dump_json(RESULTS / "game_exploratory.json", game)
    if verbose:
        _print_summary(blocks)
    return metrics, game


def _determinism_checks(synth, lib, setup, res_a):
    return {
        "artifact_serialization": "JSON sort_keys=True, CSV lineterminator='\\n'",
        "paths_recorded": False,
        "corpus_a_image_sha256": synth["image"]["text_sha256"],
        "corpus_a_labels_from_recipe_membership": _labels_from_membership(synth) == [
            (l["i"], l["truth"]) for l in synth["labels"]],
        "corpus_b1_labels_from_object_identity": all(
            "library object" in l["evidence"] or "->" in l["evidence"] for l in lib["labels"]),
        "corpus_b1_extents_non_overlapping": _non_overlapping(lib),
        "corpus_b2_labels_from_setup_provenance": all(
            "identical" in l["evidence"] for l in setup["labels"]),
        "corpus_a_evaluated_pairs": len(res_a["rows"]),
    }


def _labels_from_membership(corpus):
    funcs = corpus["functions"]
    return [(i, "boundary" if funcs[i - 1]["cu"] != funcs[i]["cu"] else "same_cu")
            for i in range(1, len(funcs))]


def _non_overlapping(corpus):
    cus = sorted(corpus["cus"], key=lambda c: (c["start"], c["end"]))
    return all(a["end"] <= b["start"] for a, b in zip(cus, cus[1:]))


def _print_summary(blocks):
    print()
    print("%-10s %-32s %-5s %5s %4s %4s %4s %8s %7s %6s" % (
        "corpus", "signal", "role", "TP", "FP", "TN", "FN", "precision", "recall", "class"))
    for cid in ("synthetic", "libsig", "setup"):
        for s in blocks[cid]["signals"]:
            print("%-10s %-32s %-5s %5d %4d %4d %4d %8s %7s %6s" % (
                cid, s["signal"], s["role"], s["TP"], s["FP"], s["TN"], s["FN"],
                "-" if s["precision"] is None else "%.3f" % s["precision"],
                "-" if s["recall"] is None else "%.3f" % s["recall"],
                s["classification"]))
    print()
    print("artifacts written to", RESULTS.relative_to(path()))


def main():
    ap = argparse.ArgumentParser(description="E8: CU boundary evidence validation")
    ap.add_argument("--refresh", action="store_true", help="rebuild every cache")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    run(refresh_synthetic=a.refresh, refresh_libsig=a.refresh, refresh_setup=a.refresh,
        verbose=not a.quiet)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
