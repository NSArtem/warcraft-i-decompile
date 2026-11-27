#!/usr/bin/env python3
"""Mechanically extract structured Decision/Objection blocks from frozen responses.

This is an additive extraction. It never edits a response and never infers
agreement. Every extracted record keeps the exact source span and a hash so the
Secretary can verify it against the original.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

SEC = "/mnt/data/projects/warcraft-1-decompile-wt/cons-sec"
CONSILIUM = os.path.join(SEC, "docs/research/build-codegen-consilium")
ARCHS = ["gpt", "claude", "gemini"]

DEC_START = re.compile(r"^[ \t>*#`-]*Decision[ \t]*:[ \t]*`?(DEC-[A-Za-z0-9._-]+)`?", re.M)
OBJ_ID = re.compile(r"\bOBJ-[A-Za-z][0-9]{1,3}\b")
FIELD = re.compile(r"^[ \t>*#`-]*([A-Za-z][A-Za-z /_-]{1,40})[ \t]*:[ \t]*(.*)$", re.M)


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_decisions(text: str) -> list[dict]:
    starts = list(DEC_START.finditer(text))
    out = []
    for i, m in enumerate(starts):
        end = starts[i + 1].start() if i + 1 < len(starts) else len(text)
        span = text[m.start():end]
        # Stop at a major heading that clearly starts a new section only if the
        # span is implausibly long; otherwise keep the full block.
        fields = {}
        for fm in FIELD.finditer(span):
            key = fm.group(1).strip().lower().replace(" ", "_")
            val = fm.group(2).strip()
            if key in ("decision", "title", "proposition", "revision", "position",
                       "reason", "evidence", "assumptions", "dependencies",
                       "conditions", "related_objections", "confidence"):
                fields.setdefault(key, val)
        out.append({
            "decision_id": m.group(1),
            "architect": None,
            "fields": fields,
            "source_span_sha256": sha(span),
            "source_chars": len(span),
            "raw": span,
        })
    return out


def parse_objections(text: str) -> list[dict]:
    out = []
    seen = set()
    for m in OBJ_ID.finditer(text):
        oid = m.group(0)
        if oid in seen:
            continue
        seen.add(oid)
        # Take a bounded window around the identifier for review; the full
        # response remains the authoritative text.
        start = max(0, m.start() - 200)
        end = min(len(text), m.end() + 2500)
        span = text[start:end]
        out.append({
            "objection_id": oid,
            "architect": None,
            "source_span_sha256": sha(span),
            "window_chars": len(span),
            "raw_window": span,
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", required=True)
    args = ap.parse_args()
    rdir = os.path.join(CONSILIUM, "rounds", args.round)
    result = {"round": args.round, "architects": {}, "counts": {}}
    for arch in ARCHS:
        path = os.path.join(rdir, arch, "response.md")
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        decs = parse_decisions(text)
        objs = parse_objections(text)
        for rec in decs + objs:
            rec["architect"] = arch
        result["architects"][arch] = {
            "response_sha256": sha(text),
            "response_chars": len(text),
            "decisions": decs,
            "objections": objs,
        }
    result["counts"] = {
        "decisions": sum(len(v["decisions"]) for v in result["architects"].values()),
        "unique_decision_ids": len({
            d["decision_id"]
            for v in result["architects"].values() for d in v["decisions"]
        }),
        "objections": sum(len(v["objections"]) for v in result["architects"].values()),
        "unique_objection_ids": len({
            o["objection_id"]
            for v in result["architects"].values() for o in v["objections"]
        }),
    }
    out = os.path.join(rdir, "extracted.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print(json.dumps(result["counts"], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
