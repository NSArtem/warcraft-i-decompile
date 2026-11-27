#!/usr/bin/env python3
"""Mechanical validation of a frozen draft candidate (Secretary only).

This does not judge prose. It checks the properties the Secretary can verify
mechanically before freezing:

1. every required draft file exists;
2. the draft's decision ledger is byte-identical to the canonical ledger;
3. every recorded proposition hashes to its ``proposition_sha256``;
4. the ledger's decision/objection status counts match the campaign's settled
   counts (38/4/12 and 64/2);
5. the gate and authority phrases carried by the previous revision still appear
   in the candidate (a phrase that disappears entirely is an error; a lower
   count is reported as a note, not a failure).

Usage:
    python3 validate_frozen_draft.py --draft-dir final/drafts/v3 \
        --ledger final/drafts/v2/decision-ledger.json \
        --previous final/drafts/v2 [--expect 38,4,12,64,2]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

REQUIRED = ["revised-rfc.md", "implementation-roadmap.md",
            "experimental-interpretation.md", "decision-rationale.md",
            "decision-ledger.json", "deferred-questions.md", "editorial-notes.md",
            "CHANGELOG-v3.md"]
GATE_PHRASES = ["make verify", "make goal", "T3", "T4", "wc1.progress",
                "Build A", "IDENTICAL", "OW2", "10.0a", "owner", "unanimous"]


def sha_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--draft-dir", required=True)
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--previous", default=None)
    ap.add_argument("--expect", default="38,4,12,64,2",
                    help="UNANIMOUS,UNANIMOUS_REJECTED,WITHDRAWN_SUPERSEDED,RESOLVED,WITHDRAWN")
    args = ap.parse_args()

    errors: list[str] = []
    notes: list[str] = []

    for name in REQUIRED:
        if not os.path.isfile(os.path.join(args.draft_dir, name)):
            errors.append(f"missing required file: {name}")

    draft_ledger = os.path.join(args.draft_dir, "decision-ledger.json")
    if os.path.isfile(draft_ledger):
        if sha_file(draft_ledger) != sha_file(args.ledger):
            errors.append("decision-ledger.json is not byte-identical to the canonical ledger")
    ledger = load(args.ledger)
    decisions = ledger.get("decisions", [])
    objections = ledger.get("objections", [])

    # Proposition hashes.
    bad_hashes = 0
    for d in decisions:
        prop = d.get("proposition")
        rec = d.get("proposition_sha256")
        if prop is None or rec is None:
            continue
        if hashlib.sha256(prop.encode("utf-8")).hexdigest() != rec:
            bad_hashes += 1
            errors.append(f"{d.get('id')}: proposition hash mismatch")
    if not bad_hashes:
        notes.append(f"all {sum(1 for d in decisions if d.get('proposition_sha256'))} proposition hashes verified")

    # Status counts.
    def count(rows, status):
        return sum(1 for r in rows if r.get("status") == status)

    expected = [int(x) for x in args.expect.split(",")]
    got = [count(decisions, "UNANIMOUS"), count(decisions, "UNANIMOUS_REJECTED"),
           count(decisions, "WITHDRAWN_SUPERSEDED"), count(objections, "RESOLVED"),
           count(objections, "WITHDRAWN")]
    if got != expected:
        errors.append(f"ledger status counts {got} != expected {expected}")
    else:
        notes.append(f"ledger status counts match: {got}")

    # Gate phrases.
    cand = ""
    for name in ("revised-rfc.md", "implementation-roadmap.md", "decision-rationale.md"):
        p = os.path.join(args.draft_dir, name)
        if os.path.isfile(p):
            cand += open(p, encoding="utf-8").read()
    prev_text = ""
    if args.previous:
        for name in ("revised-rfc.md", "implementation-roadmap.md", "decision-rationale.md"):
            p = os.path.join(args.previous, name)
            if os.path.isfile(p):
                prev_text += open(p, encoding="utf-8").read()
    for phrase in GATE_PHRASES:
        c = cand.lower().count(phrase.lower())
        if c == 0:
            errors.append(f"gate/authority phrase disappeared: {phrase!r}")
            continue
        if prev_text:
            pc = prev_text.lower().count(phrase.lower())
            if c < pc:
                notes.append(f"phrase {phrase!r} appears {c}x (was {pc}x)")

    for n in notes:
        print(f"[draft] note: {n}")
    for e in errors:
        print(f"[draft] ERROR {e}")
    if errors:
        print(f"[draft] {len(errors)} mechanical defect(s)")
        return 1
    print("[draft] mechanical validation: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
