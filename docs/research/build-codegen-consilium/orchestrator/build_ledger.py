#!/usr/bin/env python3
"""Build the decision and objection ledgers mechanically from frozen responses.

Rules:
- A decision keeps its Architect-prefixed identifier (DEC-A01, DEC-B01, ...).
  The Secretary never merges two proposals by semantic similarity.
- The current proposition is the latest *explicit* proposal or revision found in
  a frozen response, in round order. Every earlier version stays in `history`.
- An Architect's position is taken only from an explicit `Position:` field in a
  `Decision:` block; silence is never treated as agreement.
- Status is computed from explicit positions on the current revision:
  UNANIMOUS only if all three ACCEPT the same current revision.
- Objections are never closed by the Secretary. A resolution is recorded only
  when an Architect explicitly states it.
"""

from __future__ import annotations

import glob
import json
import os
import re
import sys

SEC = "/mnt/data/projects/warcraft-1-decompile-wt/cons-sec"
CONSILIUM = os.path.join(SEC, "docs/research/build-codegen-consilium")
ARCHS = ["gpt", "claude", "gemini"]

DEC_LINE = re.compile(r"^[ \t>*#`-]*Decision(?:\*\*)?[ \t]*:[ \t*`]*(DEC-[A-Za-z0-9._-]+)", re.M)
OBJ_LINE = re.compile(r"^[ \t>*#`-]*(?:(?:Objection|OBJ)[ \t]*:[ \t*`]*)?(OBJ-[A-C][0-9]+)\b", re.M)


def sha(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def blocks(text: str, start_re: re.Pattern) -> list[tuple[str, str]]:
    starts = list(start_re.finditer(text))
    out = []
    for i, m in enumerate(starts):
        end = starts[i + 1].start() if i + 1 < len(starts) else len(text)
        out.append((m.group(1), text[m.start():end]))
    return out


def fields_of(span: str) -> dict:
    fields = {}
    for line in span.splitlines():
        fm = re.match(r"^[ \t>*#`-]*([A-Za-z][A-Za-z /_-]{1,40})(?:\*\*)?[ \t]*:[ \t]*(?:\*\*[ \t]*)?(.*)$", line)
        if not fm:
            continue
        key = fm.group(1).strip().lower().replace(" ", "_")
        if key in ("decision", "title", "proposition", "revision", "position",
                   "reason", "evidence", "assumptions", "dependencies",
                   "conditions", "related_objections", "confidence", "status"):
            fields.setdefault(key, fm.group(2).strip())
    return fields


def rounds() -> list[str]:
    rs = []
    for p in glob.glob(os.path.join(CONSILIUM, "rounds", "r[0-9][0-9]")):
        manifest = os.path.join(p, "manifest.json")
        if os.path.isfile(manifest):
            with open(manifest, encoding="utf-8") as fh:
                if json.load(fh).get("barrier") == "closed":
                    rs.append(os.path.basename(p))
    return sorted(rs)


def main() -> int:
    decisions: dict[str, dict] = {}
    objections: dict[str, dict] = {}

    for rid in rounds():
        for arch in ARCHS:
            path = os.path.join(CONSILIUM, "rounds", rid, arch, "response.md")
            if not os.path.isfile(path):
                continue
            text = open(path, encoding="utf-8").read()
            for did, span in blocks(text, DEC_LINE):
                f = fields_of(span)
                rec = decisions.setdefault(did, {
                    "id": did,
                    "origin": did.split("-")[1].split("0")[0] if "-" in did else None,
                    "origin_architect": {"A": "gpt", "B": "claude", "C": "gemini"}.get(
                        did[4:5].upper()) if did.startswith("DEC-") else None,
                    "first_seen_round": rid,
                    "history": [],
                    "positions": {a: [] for a in ARCHS},
                    "objections": [],
                    "status": "PROPOSED",
                })
                revision = f.get("revision", "").strip("`*")
                prop = f.get("proposition", "")
                entry = {
                    "round": rid,
                    "architect": arch,
                    "revision": revision,
                    "title": f.get("title", ""),
                    "proposition": prop,
                    "proposition_sha256": sha(prop) if prop else None,
                    "evidence": f.get("evidence", ""),
                    "assumptions": f.get("assumptions", ""),
                    "dependencies": f.get("dependencies", ""),
                    "raw_span_sha256": sha(span),
                }
                rec["history"].append(entry)
                pos = f.get("position", "").strip("`*")
                if pos:
                    rec["positions"][arch].append({
                        "round": rid,
                        "revision": revision,
                        "position": pos,
                        "reason": f.get("reason", ""),
                        "conditions": f.get("conditions", ""),
                        "related_objections": f.get("related_objections", ""),
                    })
                for oid in re.findall(r"\bOBJ-[A-Za-z][0-9]{1,3}\b", f.get("related_objections", "")):
                    if oid not in rec["objections"]:
                        rec["objections"].append(oid)
            for oid, span in blocks(text, OBJ_LINE):
                if {"A": "gpt", "B": "claude", "C": "gemini"}.get(oid[4]) != arch:
                    continue
                rec = objections.setdefault(oid, {
                    "id": oid,
                    "origin_architect": arch,
                    "first_seen_round": rid,
                    "history": [],
                    "mentions": [],
                    "status": "OPEN",
                })
                rec["history"].append({
                    "round": rid,
                    "architect": arch,
                    "raw_span_sha256": sha(span),
                    "excerpt": span.split("\n\n## ", 1)[0].rstrip(),
                })

    # Compute per-decision status from explicit positions on the current revision.
    for did, rec in decisions.items():
        proposals = [entry for entry in rec["history"] if
                     entry["architect"] == rec["origin_architect"] and
                     entry["revision"] and entry["proposition"]]
        latest = proposals[-1] if proposals else {}
        cur_rev = latest.get("revision")
        rec["current_revision"] = cur_rev
        rec["proposition"] = latest.get("proposition")
        rec["title"] = latest.get("title")
        rec["proposition_sha256"] = latest.get("proposition_sha256")
        conflicting_revision = len({p["proposition_sha256"] for p in proposals
                                    if p["revision"] == cur_rev}) > 1
        live = {}
        for arch in ARCHS:
            ps = [p for p in rec["positions"].get(arch, []) if p.get("revision") == cur_rev]
            live[arch] = ps[-1] if ps else None
        rec["live_positions"] = live
        vals = [live[a]["position"].upper() for a in ARCHS if live[a]]
        if conflicting_revision:
            status = "DISPUTED"
        elif cur_rev and len(vals) == 3 and all(v == "ACCEPT" for v in vals):
            status = "UNANIMOUS"
        elif any(v == "REJECT" for v in vals):
            status = "DISPUTED"
        elif any(v == "CONDITIONAL" for v in vals):
            status = "CONDITIONAL"
        elif any(v == "NEEDS_EVIDENCE" for v in vals):
            status = "NEEDS_EXPERIMENT"
        else:
            status = "PROPOSED"
        rec["status"] = status

    out = {
        "schema_note": (
            "Mechanically built from frozen responses. Architect-prefixed identifiers are "
            "never merged by the Secretary. Status is computed only from explicit positions "
            "on the current revision; silence is not agreement."
        ),
        "status_values": ["PROPOSED", "UNANIMOUS", "CONDITIONAL", "DISPUTED",
                          "NEEDS_EXPERIMENT", "SUPERSEDED"],
        "rounds_read": rounds(),
        "decisions": sorted(decisions.values(), key=lambda r: r["id"]),
    }
    with open(os.path.join(CONSILIUM, "decisions.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    outo = {
        "schema_note": (
            "Mechanically extracted objection identifiers and verbatim excerpts. The "
            "Secretary never closes an objection; resolution requires an explicit Architect "
            "statement in a later frozen response."
        ),
        "objections": sorted(objections.values(), key=lambda r: r["id"]),
    }
    with open(os.path.join(CONSILIUM, "objections.json"), "w", encoding="utf-8") as fh:
        json.dump(outo, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print(f"rounds: {out['rounds_read']}")
    print(f"decisions: {len(decisions)}  objections: {len(objections)}")
    for did, rec in sorted(decisions.items()):
        print(f"  {did}: rev {rec['current_revision']} status {rec['status']} "
              f"live={ {a: (rec['live_positions'][a] or {}).get('position') for a in ARCHS} }")
    return 0


if __name__ == "__main__":
    sys.exit(main())
