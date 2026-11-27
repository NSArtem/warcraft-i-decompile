#!/usr/bin/env python3
"""Compact administrative status report for the consilium (no interpretation)."""

from __future__ import annotations

import glob
import json
import os
import sys

SEC = "/mnt/data/projects/warcraft-1-decompile-wt/cons-sec"
CONSILIUM = os.path.join(SEC, "docs/research/build-codegen-consilium")


def load(path, default=None):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def main() -> int:
    state = load(os.path.join(CONSILIUM, "state.json"), {}) or {}
    dec = load(os.path.join(CONSILIUM, "decisions.json"), {}) or {}
    obj = load(os.path.join(CONSILIUM, "objections.json"), {}) or {}
    print(f"phase: {state.get('phase')}")
    print(f"baseline: {state.get('baseline', {}).get('sha')}")
    print(f"evidence: {state.get('current_evidence_revision')}")
    print(f"next round: {state.get('next_round')}")
    print()
    print("rounds:")
    for rid in sorted((state.get("rounds") or {})):
        r = state["rounds"][rid]
        hashes = {a: (r.get("responses", {}).get(a, {}) or {}).get("sha256") for a in ("gpt", "claude", "gemini")}
        print(f"  {rid}: status={r.get('status')} barrier={r.get('barrier')} "
              f"hashes={ {a: (h or '-')[:10] for a, h in hashes.items()} }")
    print()
    ds = dec.get("decisions", [])
    by = {}
    for d in ds:
        by[d.get("status")] = by.get(d.get("status"), 0) + 1
    print(f"decisions: {len(ds)} {by}")
    print(f"objections: {len(obj.get('objections', []))}")
    print()
    print("sessions:")
    for a in ("gpt", "claude", "gemini"):
        s = load(os.path.join("/mnt/data/projects/warcraft-1-decompile-consilium/sessions", f"{a}.json"), {}) or {}
        print(f"  {a}: id={s.get('native_session_id')} invocations={s.get('invocations')}")
    print()
    qpath = os.path.join(CONSILIUM, "telemetry", "quota-snapshots.jsonl")
    if os.path.isfile(qpath):
        lines = open(qpath, encoding="utf-8").read().strip().splitlines()
        if lines:
            print("last quota snapshots:")
            for line in lines[-3:]:
                q = json.loads(line)
                print(f"  {q.get('round')}/{q.get('architect')}: {q.get('quota')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
