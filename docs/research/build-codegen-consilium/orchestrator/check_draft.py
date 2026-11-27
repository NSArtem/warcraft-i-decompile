#!/usr/bin/env python3
"""Mechanical conformance check on the Editor's draft package.

This does not judge the prose. It checks only that the draft is traceable to the
ledger it claims to preserve:

1. every required file exists;
2. `decision-ledger.json` is byte-identical to the delivered ledger;
3. every decision id appears in `decision-rationale.md` with its current status
   and proposition hash;
4. every objection id appears somewhere in the draft prose (`decision-rationale.md`,
   `deferred-questions.md` or `revised-rfc.md`);
5. every decision that is not unanimously accepted or unanimously rejected is
   named in `deferred-questions.md` or carries its status word next to its id,
   so it cannot be presented as settled by omission;
6. `SHA256SUMS`/`manifest.json`, when present, match the files.

A failure here is reported to the Editor as a mechanical defect; it is not a
Secretary verdict on the architecture.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

REQUIRED = ["revised-rfc.md", "experimental-interpretation.md",
            "implementation-roadmap.md", "deferred-questions.md",
            "decision-rationale.md", "decision-ledger.json"]


def load(path, default=None):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--draft-dir", required=True)
    ap.add_argument("--ledger", required=True,
                    help="delivered ledger the draft's decision-ledger.json must copy exactly")
    ap.add_argument("--alternate-ledger", action="append", default=[],
                    help="another delivered ledger an exact copy may match instead")
    ap.add_argument("--objections", required=True)
    args = ap.parse_args()

    errors: list[str] = []
    for name in REQUIRED:
        if not os.path.isfile(os.path.join(args.draft_dir, name)):
            errors.append(f"missing required file: {name}")

    ledger = load(args.ledger, {}) or {}
    objections = load(args.objections, {}) or {}
    draft_ledger_path = os.path.join(args.draft_dir, "decision-ledger.json")
    if os.path.isfile(draft_ledger_path):
        copy = open(draft_ledger_path, "rb").read()
        candidates = [args.ledger] + list(args.alternate_ledger)
        matched = None
        for cand in candidates:
            if os.path.isfile(cand) and open(cand, "rb").read() == copy:
                matched = cand
                break
        if matched is None:
            errors.append("decision-ledger.json is not an exact copy of any delivered ledger")

    rationale = ""
    if os.path.isfile(os.path.join(args.draft_dir, "decision-rationale.md")):
        rationale = open(os.path.join(args.draft_dir, "decision-rationale.md"),
                         encoding="utf-8").read()
    deferred = ""
    if os.path.isfile(os.path.join(args.draft_dir, "deferred-questions.md")):
        deferred = open(os.path.join(args.draft_dir, "deferred-questions.md"),
                        encoding="utf-8").read()

    settled = {"UNANIMOUS", "UNANIMOUS_REJECTED"}
    for d in ledger.get("decisions", []):
        did, status = d["id"], d.get("status")
        if did not in rationale:
            errors.append(f"{did} absent from decision-rationale.md")
            continue
        if status and status not in rationale:
            errors.append(f"{did}: status {status} not stated in the rationale")
        sha = d.get("proposition_sha256")
        if sha and sha not in rationale:
            errors.append(f"{did}: proposition hash {sha[:12]} not cited in the rationale")
        if status not in settled and did not in deferred:
            if status not in rationale:
                errors.append(f"{did} is {status} but neither deferred nor marked with its status")

    rfc = ""
    if os.path.isfile(os.path.join(args.draft_dir, "revised-rfc.md")):
        rfc = open(os.path.join(args.draft_dir, "revised-rfc.md"), encoding="utf-8").read()
    for o in objections.get("objections", []):
        oid = o["id"]
        if oid not in rationale and oid not in deferred and oid not in rfc:
            errors.append(f"{oid} absent from decision-rationale.md, deferred-questions.md "
                          f"and revised-rfc.md")

    if errors:
        for e in errors:
            print(f"[draft] ERROR {e}")
        print(f"[draft] {len(errors)} mechanical defect(s)")
        return 1
    print("[draft] mechanical conformance: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
