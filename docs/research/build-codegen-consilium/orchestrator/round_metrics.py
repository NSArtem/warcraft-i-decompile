#!/usr/bin/env python3
"""Mechanical round metrics and resource accounting for the consilium.

Counts only what is directly observable: response sizes, decision/objection
identifiers, structured position values, changed positions for the same
decision id across rounds, token/time fields from per-session metadata, and
quota snapshots. No judgment about argument quality.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys

SEC = "/mnt/data/projects/warcraft-1-decompile-wt/cons-sec"
CONSILIUM = os.path.join(SEC, "docs/research/build-codegen-consilium")
ARCHS = ["gpt", "claude", "gemini"]
DEC = re.compile(r"\bDEC-[ABC][0-9]{2}\b")
OBJ = re.compile(r"\bOBJ-[ABC][0-9]{2}\b")
POS = re.compile(r"^[ \t>*#`-]*Position[ \t]*:[ \t]*`?([A-Z_]+)`?", re.M)


def load(path, default=None):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def positions_by_decision(text: str) -> dict:
    """Best-effort mapping decision id -> last Position value in its block."""
    lines = text.splitlines()
    out = {}
    cur = None
    for ln in lines:
        m = re.match(r"^[ \t>*#`-]*Decision[ \t]*:[ \t]*`?(DEC-[A-Za-z0-9._-]+)`?", ln)
        if m:
            cur = m.group(1)
            continue
        if cur:
            pm = re.match(r"^[ \t>*#`-]*Position[ \t]*:[ \t]*`?([A-Z_]+)`?", ln)
            if pm:
                out[cur] = pm.group(1)
    return out


def round_metrics(round_id: str, prev_id: str | None) -> dict:
    rdir = os.path.join(CONSILIUM, "rounds", round_id)
    manifest = load(os.path.join(rdir, "manifest.json"), {}) or {}
    per = {}
    all_dec, all_obj = set(), set()
    prev_positions = {}
    prev_decisions = set()
    if prev_id:
        pdir = os.path.join(CONSILIUM, "rounds", prev_id)
        for arch in ARCHS:
            p = os.path.join(pdir, arch, "response.md")
            if os.path.isfile(p):
                text = open(p, encoding="utf-8").read()
                prev_positions.update(positions_by_decision(text))
                prev_decisions |= set(DEC.findall(text))
    changed = []
    for arch in ARCHS:
        p = os.path.join(rdir, arch, "response.md")
        text = open(p, encoding="utf-8").read() if os.path.isfile(p) else ""
        decs = set(DEC.findall(text))
        objs = set(OBJ.findall(text))
        pos = positions_by_decision(text)
        for d, v in pos.items():
            if d in prev_positions and prev_positions[d] != v:
                changed.append({"decision": d, "from": prev_positions[d], "to": v, "architect": arch})
        all_dec |= decs
        all_obj |= objs
        meta = load(os.path.join(rdir, arch, "meta.json"), {}) or {}
        per[arch] = {
            "response_chars": len(text),
            "decisions_mentioned": len(decs),
            "objections_mentioned": len(objs),
            "structured_positions": pos,
            "wall_s": meta.get("wall_s"),
            "timed_out": meta.get("timed_out"),
            "usage": meta.get("usage"),
            "quota_after": meta.get("quota_after"),
        }
    return {
        "round": round_id,
        "barrier": manifest.get("barrier"),
        "new_decision_proposals": sorted(d for d in all_dec if d not in prev_decisions),
        "newly_accepted_decisions": sorted(
            d["id"] for d in (load(os.path.join(CONSILIUM, "decisions.json"), {}).get("decisions", []))
            if d.get("status") == "UNANIMOUS"
        ),
        "unanimous_decisions": sorted(
            d["id"] for d in (load(os.path.join(CONSILIUM, "decisions.json"), {}).get("decisions", []))
            if d.get("status") == "UNANIMOUS"
        ),
        "revised_propositions": sorted({c["decision"] for c in changed}),
        "explicit_position_changes": changed,
        "newly_opened_objections": sorted(all_obj),
        "previously_discussed_issues_reopened": [],
        "new_experimental_evidence": [],
        "outstanding_disputed_decisions": sorted(
            {d for arch in per for d, v in per[arch]["structured_positions"].items()
             if v in ("REJECT", "CONDITIONAL", "NEEDS_EVIDENCE")}
        ),
        "architects": per,
    }


def consolidate_telemetry(round_id: str) -> None:
    rdir = os.path.join(CONSILIUM, "rounds", round_id)
    tel = os.path.join(CONSILIUM, "telemetry")
    os.makedirs(tel, exist_ok=True)
    quota_path = os.path.join(tel, "quota-snapshots.jsonl")
    resource_path = os.path.join(tel, "resource-usage.csv")
    rows = []
    with open(quota_path, "a", encoding="utf-8") as qf:
        for arch in ARCHS:
            meta = load(os.path.join(rdir, arch, "meta.json"), {}) or {}
            q = meta.get("quota_after") or {}
            qf.write(json.dumps({
                "round": round_id, "architect": arch, "captured_at_utc": meta.get("end_utc"),
                "provider": {"gpt": "codex", "claude": "claude", "gemini": "agy"}[arch],
                "quota": q,
            }, ensure_ascii=False) + "\n")
            rows.append({
                "round": round_id,
                "architect": arch,
                "model": meta.get("model_observed") or meta.get("model_requested"),
                "effort": meta.get("effort_observed") or meta.get("effort_requested"),
                "wall_s": meta.get("wall_s"),
                "input_tokens": (meta.get("usage") or {}).get("input_tokens"),
                "cached_input_tokens": (meta.get("usage") or {}).get("cached_input_tokens"),
                "output_tokens": (meta.get("usage") or {}).get("output_tokens"),
                "reasoning_tokens": (meta.get("usage") or {}).get("reasoning_tokens"),
                "token_provenance": (meta.get("usage") or {}).get("provenance"),
                "five_hour_used_percent": ((meta.get("quota_after") or {}).get("five_hour_used_percent")),
                "seven_day_used_percent": ((meta.get("quota_after") or {}).get("seven_day_used_percent")),
            })
    exists = os.path.isfile(resource_path)
    with open(resource_path, "a", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        if not exists:
            w.writeheader()
        w.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", required=True)
    ap.add_argument("--prev", default=None)
    ap.add_argument("--metrics-only", action="store_true",
                    help="write round metrics without appending resource telemetry again")
    args = ap.parse_args()
    m = round_metrics(args.round, args.prev)
    out = os.path.join(CONSILIUM, "rounds", args.round, "metrics.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(m, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    if not args.metrics_only:
        consolidate_telemetry(args.round)
    print(json.dumps({k: v for k, v in m.items() if k != "architects"}, indent=2)[:4000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
