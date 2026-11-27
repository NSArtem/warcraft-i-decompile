#!/usr/bin/env python3
"""Build the decision and objection ledgers mechanically from frozen responses.

Rules (see ``ledger_lib.py`` for the extraction contract):

- A decision keeps its Architect-prefixed identifier (DEC-A01, DEC-B01, ...).
  The Secretary never merges two proposals by semantic similarity.
- A proposition revision is admitted only when its exact text is hash-anchored;
  two hash-anchored texts for one revision are a CONFLICT and fail closed.
- A position counts only for the current revision; positions on obsolete
  revisions are preserved as stale and never carry over.
- Unanimous acceptance and unanimous rejection are both resolved decisions.
- Withdrawals are authoritative for their author only and never approve the
  replacement proposition.
- Objections close only via an explicit disposition from the author or from all
  three Architects.

Usage:
  build_ledger.py [--consilium DIR] [--print-summary]
  build_ledger.py --check        rebuild and compare with the committed ledgers
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ledger_lib  # noqa: E402

DEFAULT = os.path.join(
    "/mnt/data/projects/warcraft-1-decompile-wt/cons-sec",
    "docs/research/build-codegen-consilium")


def decision_document(decisions: dict, report: dict) -> dict:
    docs = []
    for did in sorted(decisions):
        row = decisions[did]
        row = dict(row)
        row["live_position_summary"] = {
            a: ({"position": p["position"], "round": p["round"],
                 "revision": p["revision"]} if p else None)
            for a, p in row["live_positions"].items()}
        docs.append(row)
    return {
        "schema_version": 2,
        "schema_note": (
            "Mechanically built from frozen responses. Architect-prefixed identifiers are "
            "never merged. A revision is admitted only when its exact text is hash-anchored "
            "against a declared SHA-256; conflicting texts for one revision fail closed. "
            "Positions count only for the current revision; silence is not agreement."),
        "status_values": ledger_lib.STATUS_VALUES,
        "rounds_read": report["rounds_read"],
        "rounds_skipped": report["rounds_skipped"],
        "admitted_propositions": report["admitted_propositions"],
        "conflicts": report["conflicts"],
        "unverified_propositions": report["unverified_propositions"],
        "withdrawal_reports": report["withdrawal_reports"],
        "decisions": docs,
    }


def objection_document(objections: dict) -> dict:
    return {
        "schema_version": 2,
        "schema_note": (
            "Mechanically extracted objection identifiers, raises and explicit dispositions. "
            "An objection is never closed by the Secretary: closure requires an explicit "
            "author withdrawal or an explicit closing disposition from all three Architects. "
            "A closing disposition records architectural agreement; execution of the agreed "
            "acceptance test remains a roadmap obligation."),
        "status_values": ledger_lib.OBJ_STATUS_VALUES,
        "objections": [objections[k] for k in sorted(objections)],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--consilium", default=os.environ.get("WC1_CONSILIUM_DIR", DEFAULT))
    ap.add_argument("--check", action="store_true",
                    help="rebuild in memory and fail if the committed ledgers differ")
    ap.add_argument("--print-summary", action="store_true")
    args = ap.parse_args()

    decisions, objections, report = ledger_lib.build(args.consilium)
    dec_doc = decision_document(decisions, report)
    obj_doc = objection_document(objections)

    dec_path = os.path.join(args.consilium, "decisions.json")
    obj_path = os.path.join(args.consilium, "objections.json")

    if args.check:
        stale = []
        for path, doc in ((dec_path, dec_doc), (obj_path, obj_doc)):
            current = ledger_lib.load_json(path) or {}
            if json.dumps(current, sort_keys=True) != json.dumps(doc, sort_keys=True):
                stale.append(os.path.basename(path))
        if stale:
            print(f"[ledger] committed ledgers out of date: {', '.join(stale)}", file=sys.stderr)
            return 1
        print("[ledger] committed ledgers match a fresh rebuild")
        return 0

    for path, doc in ((dec_path, dec_doc), (obj_path, obj_doc)):
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        os.replace(tmp, path)

    from collections import Counter
    dec_counts = Counter(d["status"] for d in dec_doc["decisions"])
    obj_counts = Counter(o["status"] for o in obj_doc["objections"])
    print(f"[ledger] rounds read: {report['rounds_read']}")
    if report["rounds_skipped"]:
        print(f"[ledger] rounds skipped: {report['rounds_skipped']}")
    print(f"[ledger] decisions: {len(dec_doc['decisions'])} {dict(sorted(dec_counts.items()))}")
    print(f"[ledger] objections: {len(obj_doc['objections'])} {dict(sorted(obj_counts.items()))}")
    print(f"[ledger] admitted propositions: {report['admitted_propositions']}")
    print(f"[ledger] unverified propositions: {len(report['unverified_propositions'])}")
    print(f"[ledger] conflicts: {len(report['conflicts'])}")
    if args.print_summary:
        for d in dec_doc["decisions"]:
            live = {a: (p["position"] if p else None)
                    for a, p in d["live_position_summary"].items()}
            print(f"  {d['id']}: rev {d['current_revision']} {d['status']:18} {live}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
