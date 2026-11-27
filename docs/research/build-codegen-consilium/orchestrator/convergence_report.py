#!/usr/bin/env python3
"""Mechanical convergence and resource report for the consilium.

Recomputes, from frozen responses and the rebuilt ledger only:

- decision status at the end of each round (replay via ``ledger_lib.build``);
- objection status and how many objections are unanimously upheld, closure
  eligible (every named resolution unanimously resolved) or blocked;
- per-Architect invocation count, wall time, tokens and quota readings;
- failed invocations kept separate from responses of record.

No value is estimated. Missing measurements are reported as unavailable.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ledger_lib  # noqa: E402


def load(path, default=None):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--consilium", required=True)
    ap.add_argument("--write", action="store_true",
                    help="write final/resource-and-convergence-report.md")
    args = ap.parse_args()
    C = args.consilium

    lines = ["# Resource and convergence report", ""]
    lines.append("Mechanically derived from frozen responses, the rebuilt ledger and "
                 "recorded provider telemetry. No value is estimated.")
    lines.append("")

    rounds = ledger_lib.closed_rounds(C)
    lines.append("## Convergence by round")
    lines.append("")
    lines.append("| round | decisions | unanimously accepted | unanimously rejected | "
                 "conditional | disputed | conflict | withdrawn+superseded | open objections |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for r in rounds:
        d, o, _ = ledger_lib.build(C, upto=r)
        dc = Counter(x["status"] for x in d.values())
        oc = Counter(x["status"] for x in o.values())
        lines.append(f"| {r} | {len(d)} | {dc['UNANIMOUS']} | {dc['UNANIMOUS_REJECTED']} | "
                     f"{dc['CONDITIONAL']} | {dc['DISPUTED']} | {dc['CONFLICT']} | "
                     f"{dc['WITHDRAWN_SUPERSEDED'] + dc['WITHDRAWN']} | {oc['OPEN']} |")
    lines.append("")

    d, o, report = ledger_lib.build(C)
    lines.append("## Final ledger state")
    lines.append("")
    lines.append(f"- rounds read: {report['rounds_read']}")
    lines.append(f"- rounds skipped (barrier open or no manifest): {report['rounds_skipped']}")
    lines.append(f"- admitted propositions: {report['admitted_propositions']}")
    lines.append(f"- unverified propositions (hash not anchored): {len(report['unverified_propositions'])}")
    lines.append(f"- revision-identity conflicts: {len(report['conflicts'])}")
    for c in report["conflicts"]:
        lines.append(f"  - `{c['decision_id']}` revision {c['revision']} "
                     f"(rounds {', '.join(c['rounds'])})")
    lines.append("")
    lines.append("- decision status: " + json.dumps(dict(sorted(Counter(
        x["status"] for x in d.values()).items()))))
    lines.append("- objection status: " + json.dumps(dict(sorted(Counter(
        x["status"] for x in o.values()).items()))))
    lines.append(f"- objections unanimously upheld: "
                 f"{sum(1 for x in o.values() if x.get('unanimous_uphold'))}")
    lines.append(f"- objections closure eligible: "
                 f"{sum(1 for x in o.values() if x.get('closure_eligible'))}")
    lines.append(f"- objections blocked by an unresolved decision: "
                 f"{sum(1 for x in o.values() if x.get('unresolved_decision_ids'))}")
    lines.append("")

    lines.append("## Resource usage (recorded invocations)")
    lines.append("")
    lines.append("| round | architect | model | effort | wall_s | input | cached input | output | 5h % | 7d % |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    import csv
    with open(os.path.join(C, "telemetry/resource-usage.csv"), newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            lines.append("| {round} | {architect} | {model} | {effort} | {wall_s} | {input_tokens} | "
                         "{cached_input_tokens} | {output_tokens} | {five_hour_used_percent} | "
                         "{seven_day_used_percent} |".format(**row))
    lines.append("")
    fail_path = os.path.join(C, "telemetry/failed-invocations.csv")
    if os.path.isfile(fail_path):
        lines.append("### Failed invocations (consumed quota, produced no response)")
        lines.append("")
        lines.append("| round | architect | attempt | wall_s | api_error | input | output | cost (API-equivalent) |")
        lines.append("|---|---|---|---|---|---|---|---|")
        with open(fail_path, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                lines.append("| {round} | {architect} | {attempt} | {wall_s} | {api_error} | "
                             "{input_tokens} | {output_tokens} | {api_equivalent_cost_usd} |".format(**row))
        lines.append("")
    lines.append("Quota percentages are provider-reported utilisation of the shared "
                 "subscription window after the invocation; they are not attributable to "
                 "the consilium alone and are never summed across rows.")
    lines.append("")

    lines.append("## Sessions")
    lines.append("")
    for arch in ("gpt", "claude", "gemini"):
        sess = load(os.path.join("/mnt/data/projects/warcraft-1-decompile-consilium",
                                 "sessions", f"{arch}.json"), {}) or {}
        lines.append(f"- {arch}: native session `{sess.get('native_session_id')}`, "
                     f"invocations {sess.get('invocations')}")
    lines.append("")

    text = "\n".join(lines) + "\n"
    if args.write:
        out = os.path.join(C, "final", "resource-and-convergence-report.md")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"[report] wrote {out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
