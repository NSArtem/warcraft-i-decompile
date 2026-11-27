#!/usr/bin/env python3
"""Compose the per-Architect prior-review material for the revision-3 approval.

Delivers to each Architect only what the protocol allows:

- the pinned evidence manifest and the EV-2/EV-3 notices (all three);
- Architect A's previous required changes (A1–A4) to A and B;
- Architect B's previous required changes (C-1–C-3) to B;
- a short note stating the review boundary (dual role for A, fresh verdict for
  C, independent final review for B).

The current verdicts of the other Architects are never copied here.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(__file__))
import run_architect as ra  # noqa: E402

ARCHS = ["gpt", "claude", "gemini"]

NOTES = {
    "gpt": (
        "## Editor's dual role\n\n"
        "You were the RFC Editor for revision 3. This is your Architect A approval "
        "verdict, not the editorial report. `CHANGELOG-v3.md` is delivered with the "
        "draft but is not an approval and is not counted as one. Review the frozen "
        "candidate independently; if you find a blocking defect, return "
        "`REQUEST_CHANGES` with the exact passage and required correction."),
    "gemini": (
        "## Fresh verdict\n\n"
        "Your revision-2 approval does not carry over. This is a new immutable "
        "candidate; issue a fresh independent verdict against the hashes above. You "
        "have not received the other Architects' current verdicts."),
    "claude": (
        "## Independent final review\n\n"
        "You are Architect B. The RFC Editor role was reassigned to Architect A by "
        "the owner; your remaining resources are reserved for this independent final "
        "review. Your own previous required changes (C-1–C-3) and Architect A's "
        "previous required changes (A1–A4) are included below, with the pinned "
        "evidence manifest and the EV-2/EV-3 notices. You have not received the "
        "other Architects' current verdicts; issue your verdict independently. "
        "Approval of revision 2 does not carry over."),
}

COMMON = [
    ("evidence-manifest.json", "01-EVIDENCE-MANIFEST.json"),
    ("evidence-revisions/EV-2.json", "02-EV-2.json"),
    ("evidence-revisions/EV-3.json", "03-EV-3.json"),
]
EXTRA = {
    "gpt": [("rounds/approval/gpt/response.md", "04-GPT-PREVIOUS-REQUEST-CHANGES.md")],
    "claude": [("rounds/approval/claude/response.md", "04-CLAUDE-PREVIOUS-REQUEST-CHANGES.md"),
               ("rounds/approval/gpt/response.md", "05-GPT-PREVIOUS-REQUEST-CHANGES.md")],
    "gemini": [],
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", default="approval-3")
    args = ap.parse_args()
    C = ra.CONSILIUM
    out = os.path.join(C, "rounds", args.round, "prior")
    if os.path.isdir(out):
        shutil.rmtree(out)
    manifest = {}
    for arch in ARCHS:
        adir = os.path.join(out, arch)
        os.makedirs(adir)
        with open(os.path.join(adir, "00-NOTE.md"), "w", encoding="utf-8") as fh:
            fh.write(NOTES[arch] + "\n")
        for src_rel, name in COMMON + EXTRA[arch]:
            src = os.path.join(C, src_rel)
            dst = os.path.join(adir, name)
            shutil.copyfile(src, dst)
        manifest[arch] = [
            {"name": n, "sha256": ra.sha256_file(os.path.join(adir, n)),
             "bytes": os.path.getsize(os.path.join(adir, n))}
            for n in sorted(os.listdir(adir))]
    ra.write_json(os.path.join(C, "rounds", args.round, "notes.json"), NOTES)
    ra.write_json(os.path.join(C, "rounds", args.round, "prior-manifest.json"), manifest)
    print(f"composed prior material for {args.round}: " +
          ", ".join(f"{a}={len(manifest[a])}" for a in ARCHS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
