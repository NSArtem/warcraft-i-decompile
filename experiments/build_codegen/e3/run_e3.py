"""Compile the real cases and reproduce E3's deterministic evidence report."""
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from wc1 import analysis, match, oldcc, symbols

from ..e0.matcher_proto import OriginalIndex
from .fixtures import synthetic
from .partial_matcher import VerifiedRegion, evaluate_module

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / "docs/research/build-codegen/results/e3/results.json"
SCORE = "src/save_score/score_reference.c"
SCORE_FIXTURE = "experiments/build_codegen/e3/fixtures/score_reference.c"
REAL = (
    ("dialog", "src/mod_16390/dialog_hit_test_reference.c", "-os"),
    ("farm", "src/status/panel_state_reference.c", "-ot -oa"),
    ("score_baseline", SCORE, "-ot"),
    ("score_swapped", SCORE_FIXTURE, "-ot"),
)
POOLS = ("shifted_const", "mutable_shift", "proven_mutable_shift", "corrupted_const",
         "aliased_const", "aliased_original")
BRANCHES = ("outgoing_rel8", "wrong_sibling", "unresolved_sibling", "direct_rel32")


def digest(data):
    return sha256(data).hexdigest()


def serialize_region(value):
    proof = value.proof
    rewrites = [ref for ref in value.outgoing_refs if "rewrite" in ref]
    if isinstance(proof, VerifiedRegion):
        details = asdict(proof)
        for field in ("obligations", "data_deps", "outgoing_refs"):
            details[field] = [dict(record) for record in details[field]]
        classification = "requires_rel32_extraction" if rewrites else "proven_standalone_region"
        verdict = ("REGION_MATCH_WITH_REL32_REWRITE_NEEDED" if rewrites else "REGION_MATCH")
    else:
        details = None
        blocked = any("reason" in ref for ref in value.outgoing_refs)
        classification = "blocked_by_sibling_dependency" if blocked else "unverified"
        verdict = type(proof).__name__.upper()
    return dict(candidate=asdict(value.candidate), function_verdicts=value.functions,
                region_verdict=verdict, dependency_classification=classification,
                proof=details, segment_bases=value.segment_bases,
                findings=value.result.findings, metrics=value.result.metrics,
                outgoing_refs=value.outgoing_refs, incoming_refs=value.incoming_refs)


def summarize(p, m, db, index=None, boundaries=()):
    by_entry, whole, bases = evaluate_module(p, m, db, index=index, boundaries=boundaries)
    all_findings = whole["region"]["findings"]
    return dict(
        segment_names={i: s.name for i, s in enumerate(m.segments, 1)},
        object_wide=dict(verdict=whole["region"]["verdict"], segment_bases=bases,
                         finding_codes=sorted({f["code"] for f in all_findings}),
                         anchor_conflicts=[f for f in all_findings
                                           if f["code"] == "inconsistent_segment_anchor"]),
        regions={name: serialize_region(value) for name, value in by_entry.items()},
    )


def real_cases():
    p = analysis.run(cache=False)
    funcs, data, _ = symbols.load()
    by_link = {e["link_name"]: e for table in (funcs, data) for e in table.values()}
    index = OriginalIndex(p)
    real = {}
    with TemporaryDirectory(prefix=".compile-", dir=HERE) as directory:
        directory = Path(directory)
        for key, name, opts in REAL:
            src = ROOT / name
            flags = f"-s {opts} -ol -4r -zp2"
            obj = match.compile_c(str(src), flags, str(directory / f"{key}.obj"),
                                  cc="10.0a", timeout=60, quiet=True)
            real[key] = dict(source=name, source_sha256=digest(src.read_bytes()), cflags=flags,
                             compiler="Watcom 10.0a", **summarize(p, obj, by_link, index))
    return real


def synthetic_cases():
    cases = {}
    for name in POOLS:
        p, m, db, boundaries = synthetic.string_pool(name)
        cases[name] = summarize(p, m, db, boundaries=boundaries)
    for name in BRANCHES:
        cases[name] = summarize(*synthetic.branch(name))
    return cases


def collect():
    cc = Path(oldcc.require()) / "binnt/wcc386.exe"
    return dict(experiment="E3", baseline="1abb053c112332ec901a8961dc918bdcc25d73c4",
                inputs=dict(compiler_sha256=digest(cc.read_bytes()),
                            original_exe_sha256=digest((ROOT / "original/install/war.exe").read_bytes())),
                real=real_cases(), synthetic=synthetic_cases())


def main():
    results = collect()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, sort_keys=True, indent=2) + "\n")
    print(OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
