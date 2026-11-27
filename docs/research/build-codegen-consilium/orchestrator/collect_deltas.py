#!/usr/bin/env python3
"""Collect and validate the Architects' structured decision deltas for a round.

Each Architect writes ``CONSILIUM-<ROUND>-DELTA.json`` in its own worktree. This
script copies it into the campaign tree unchanged, validates it against the
frozen response of the same round, and records the outcome. An invalid delta is
kept but never applied; the ledger builder rejects it independently.

The copy is byte-identical: the Secretary never edits an Architect's delta.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import decision_delta  # noqa: E402
import run_architect as ra  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", required=True)
    args = ap.parse_args()
    rid = args.round
    rdir = os.path.join(ra.CONSILIUM, "rounds", rid)
    manifest = ra.load_json(os.path.join(rdir, "manifest.json"), {}) or {}
    if manifest.get("barrier") != "closed":
        raise SystemExit("round is not frozen; collect deltas after the barrier closes")

    record = {"round": rid, "deltas": {}}
    for arch in ("gpt", "claude", "gemini"):
        src = os.path.join(ra.ARCHITECTS[arch]["worktree"],
                           f"CONSILIUM-{rid.upper()}-DELTA.json")
        dst = os.path.join(rdir, arch, "delta.json")
        entry = {"source": src, "present": os.path.isfile(src)}
        if not entry["present"]:
            record["deltas"][arch] = entry
            print(f"[deltas] {arch}: no delta submitted")
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)
        entry["stored"] = os.path.relpath(dst, ra.CONSILIUM)
        entry["sha256"] = ra.sha256_file(dst)
        entry["bytes"] = os.path.getsize(dst)
        _delta, errs = decision_delta.load_and_validate(
            dst, consilium=ra.CONSILIUM, round_id=rid, architect=arch)
        entry["valid"] = not errs
        entry["errors"] = errs
        record["deltas"][arch] = entry
        print(f"[deltas] {arch}: {'valid' if not errs else 'INVALID'} ({len(errs)} errors)")
        for e in errs[:8]:
            print(f"    - {e}")
    ra.write_json(os.path.join(rdir, "deltas.json"), record)
    return 0 if all(v.get("valid") or not v.get("present")
                    for v in record["deltas"].values()) else 1


if __name__ == "__main__":
    sys.exit(main())
