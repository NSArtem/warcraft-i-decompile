#!/usr/bin/env python3
"""Strict, deterministic validation of an Architect's machine-readable decision delta.

From Round 4 on, every Architect submits ``rounds/<round>/<architect>/delta.json``
next to its unrestricted prose. The delta is the authoritative structured record;
the prose stays the response of record. Rules:

- A delta is accepted or rejected *as a whole*. Invalid records are never
  partially applied and are never "repaired" by the Secretary.
- ``proposition_sha256`` is recomputed from the exact proposition text; a
  mismatch is an error, never a warning.
- Only the Architect that authored a proposition may withdraw or supersede it.
- A conditional position must state its condition.
- Unknown fields are errors, so a typo cannot silently change meaning.
- ``source_response_sha256`` must equal the hash of the frozen response in the
  same round directory, binding the delta to the prose it accompanies.
"""

from __future__ import annotations

import hashlib
import json
import os
import re

ARCHS = ("gpt", "claude", "gemini")
ID_ARCH = {"A": "gpt", "B": "claude", "C": "gemini"}
POSITIONS = ("PROPOSE", "ACCEPT", "REJECT", "CONDITIONAL", "NEEDS_EVIDENCE")
OBJECTION_DISPOSITIONS = (
    "UPHOLD", "UPHOLD_PARTIAL", "REBUT", "RESOLVED", "WITHDRAWN",
    "WITHDRAWN_PARTIAL", "DEFERRED", "SUPERSEDED", "OPEN",
)
DEC_RE = re.compile(r"^DEC-[A-C][0-9]{2}$")
OBJ_RE = re.compile(r"^OBJ-[A-C][0-9]{2}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
EVIDENCE_RE = re.compile(r"^\S+@[0-9a-f]{7,64}$")

TOP_KEYS = {"kind", "schema_version", "round", "architect",
            "source_response_sha256", "decisions", "objections"}
TOP_REQUIRED = TOP_KEYS - {"objections"}
DEC_KEYS = {"decision_id", "revision", "proposition", "proposition_sha256",
            "position", "conditions", "withdraws", "supersedes",
            "objection_dispositions", "evidence", "note"}
DEC_REQUIRED = {"decision_id", "revision", "position"}
OBJ_KEYS = {"objection_id", "disposition", "basis", "related_decision_ids"}
WITHDRAW_KEYS = {"decision_id", "revision", "replacement_decision_ids", "note"}


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _is_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def validate(delta, *, consilium: str | None, round_id: str, architect: str,
             source_response: str | None = None) -> list[str]:
    """Return a list of errors. An empty list means the delta is valid."""
    errs: list[str] = []
    if not isinstance(delta, dict):
        return ["delta is not a JSON object"]
    extra = set(delta) - TOP_KEYS
    missing = TOP_REQUIRED - set(delta)
    if extra:
        errs.append(f"unknown top-level fields: {sorted(extra)}")
    if missing:
        errs.append(f"missing top-level fields: {sorted(missing)}")
    if delta.get("kind") != "consilium_decision_delta":
        errs.append("kind must be 'consilium_decision_delta'")
    if delta.get("schema_version") != 1 or not _is_int(delta.get("schema_version")):
        errs.append("schema_version must be the integer 1")
    if delta.get("round") != round_id:
        errs.append(f"round {delta.get('round')!r} does not match directory round {round_id!r}")
    if delta.get("architect") != architect:
        errs.append(f"architect {delta.get('architect')!r} does not match {architect!r}")

    resp_path = source_response
    if resp_path is None and consilium is not None:
        resp_path = os.path.join(consilium, "rounds", round_id, architect, "response.md")
    if resp_path is None or not os.path.isfile(resp_path):
        errs.append(f"no source response to bind against (rounds/{round_id}/{architect}/response.md)")
    else:
        with open(resp_path, "rb") as fh:
            actual = sha256_text(fh.read().decode("utf-8", "replace"))
        if delta.get("source_response_sha256") != actual:
            errs.append("source_response_sha256 does not match the frozen response")

    decisions = delta.get("decisions")
    if not isinstance(decisions, list) or not decisions:
        errs.append("decisions must be a non-empty list")
        decisions = []

    seen: dict[tuple[str, int], dict] = {}
    for n, rec in enumerate(decisions):
        where = f"decisions[{n}]"
        if not isinstance(rec, dict):
            errs.append(f"{where}: not an object")
            continue
        extra = set(rec) - DEC_KEYS
        missing = DEC_REQUIRED - set(rec)
        if extra:
            errs.append(f"{where}: unknown fields {sorted(extra)}")
        if missing:
            errs.append(f"{where}: missing fields {sorted(missing)}")
        did = rec.get("decision_id")
        if not isinstance(did, str) or not DEC_RE.match(did):
            errs.append(f"{where}: bad decision_id {did!r}")
            continue
        rev = rec.get("revision")
        if not _is_int(rev) or rev < 1:
            errs.append(f"{where}: revision must be an integer >= 1")
        pos = rec.get("position")
        if pos not in POSITIONS:
            errs.append(f"{where}: position {pos!r} not in {POSITIONS}")

        prop = rec.get("proposition")
        prop_sha = rec.get("proposition_sha256")
        if pos == "PROPOSE" and not prop:
            errs.append(f"{where}: PROPOSE requires the exact proposition text")
        if prop:
            if not isinstance(prop, str) or not prop.strip():
                errs.append(f"{where}: proposition must be non-empty text")
            elif not isinstance(prop_sha, str) or not HEX64.match(prop_sha):
                errs.append(f"{where}: proposition_sha256 must be 64 lowercase hex")
            elif sha256_text(prop) != prop_sha:
                errs.append(f"{where}: proposition_sha256 does not match the proposition text")
        elif prop_sha:
            errs.append(f"{where}: proposition_sha256 given without proposition text")

        cond = rec.get("conditions")
        if pos == "CONDITIONAL":
            if not isinstance(cond, str) or cond.strip().lower() in ("", "none", "n/a"):
                errs.append(f"{where}: CONDITIONAL requires a stated condition")

        key = (did, rev if _is_int(rev) else -1)
        if key in seen:
            prev = seen[key]
            if prev.get("proposition") != prop or prev.get("position") != pos:
                errs.append(f"{where}: duplicate {did} revision {rev} with different content")
        else:
            seen[key] = rec

        for field in ("withdraws", "supersedes"):
            entries = rec.get(field, [])
            if not isinstance(entries, list):
                errs.append(f"{where}.{field}: must be a list")
                continue
            for m, w in enumerate(entries):
                wwhere = f"{where}.{field}[{m}]"
                if not isinstance(w, dict):
                    errs.append(f"{wwhere}: not an object")
                    continue
                extra = set(w) - WITHDRAW_KEYS
                if extra:
                    errs.append(f"{wwhere}: unknown fields {sorted(extra)}")
                target = w.get("decision_id")
                if not isinstance(target, str) or not DEC_RE.match(target):
                    errs.append(f"{wwhere}: bad decision_id {target!r}")
                    continue
                if ID_ARCH.get(target[4]) != architect:
                    errs.append(f"{wwhere}: only the authoring Architect may withdraw {target}")
                trev = w.get("revision")
                if not _is_int(trev) or trev < 1:
                    errs.append(f"{wwhere}: revision must be an integer >= 1")
                reps = w.get("replacement_decision_ids", [])
                if not isinstance(reps, list) or any(
                        not isinstance(r, str) or not DEC_RE.match(r) for r in reps):
                    errs.append(f"{wwhere}: replacement_decision_ids must be decision ids")

        disps = rec.get("objection_dispositions", [])
        if not isinstance(disps, list):
            errs.append(f"{where}.objection_dispositions: must be a list")
            disps = []
        for m, d in enumerate(disps):
            dwhere = f"{where}.objection_dispositions[{m}]"
            if not isinstance(d, dict):
                errs.append(f"{dwhere}: not an object")
                continue
            extra = set(d) - OBJ_KEYS
            if extra:
                errs.append(f"{dwhere}: unknown fields {sorted(extra)}")
            oid = d.get("objection_id")
            if not isinstance(oid, str) or not OBJ_RE.match(oid):
                errs.append(f"{dwhere}: bad objection_id {oid!r}")
            if d.get("disposition") not in OBJECTION_DISPOSITIONS:
                errs.append(f"{dwhere}: bad disposition {d.get('disposition')!r}")
            if d.get("disposition") == "WITHDRAWN" and ID_ARCH.get(str(oid)[4:5]) != architect:
                errs.append(f"{dwhere}: only the originating Architect may withdraw {oid}")
            if not isinstance(d.get("basis", ""), str):
                errs.append(f"{dwhere}: basis must be text")

        ev = rec.get("evidence", [])
        if not isinstance(ev, list) or any(
                not isinstance(e, str) or not EVIDENCE_RE.match(e) for e in ev):
            errs.append(f"{where}: evidence entries must look like 'path@sha'")

    objections = delta.get("objections", [])
    if not isinstance(objections, list):
        errs.append("objections must be a list")
    return errs


def load_and_validate(path: str, *, consilium: str | None, round_id: str,
                      architect: str, source_response: str | None = None):
    try:
        with open(path, encoding="utf-8") as fh:
            delta = json.load(fh)
    except (OSError, ValueError) as exc:
        return None, [f"cannot read delta: {exc}"]
    errs = validate(delta, consilium=consilium, round_id=round_id, architect=architect,
                    source_response=source_response)
    return delta, errs


def to_records(delta: dict) -> dict:
    """Convert a validated delta into the ledger's internal record shapes."""
    rid, arch = delta["round"], delta["architect"]
    proposals, positions, withdrawals, disps = [], [], [], []
    for rec in delta["decisions"]:
        did, rev = rec["decision_id"], rec["revision"]
        if rec.get("proposition"):
            proposals.append({
                "round": rid, "architect": arch, "decision_id": did, "revision": rev,
                "title": "", "proposition": rec["proposition"],
                "proposition_sha256": rec["proposition_sha256"],
                "declared_sha256": rec["proposition_sha256"],
                "hash_anchored": True, "kind": "structured_delta",
                "raw_span_sha256": sha256_text(json.dumps(rec, sort_keys=True)),
            })
        positions.append({
            "round": rid, "architect": arch, "decision_id": did, "revision": rev,
            "position": rec["position"],
            "position_as_printed": rec["position"],
            "declared_sha256": rec.get("proposition_sha256"),
            "proposition_sha256": rec.get("proposition_sha256"),
            "reason": rec.get("note", ""),
            "conditions": rec.get("conditions", ""),
            "related_objections": "",
            "raw_span_sha256": sha256_text(json.dumps(rec, sort_keys=True)),
        })
        for field in ("withdraws", "supersedes"):
            for w in rec.get(field, []):
                withdrawals.append({
                    "round": rid, "architect": arch, "decision_id": w["decision_id"],
                    "authoritative": ID_ARCH.get(w["decision_id"][4]) == arch,
                    "revision_hint": w.get("revision"),
                    "replacement_decision_ids": sorted(w.get("replacement_decision_ids", [])),
                    "kind": f"delta_{field}",
                    "as_printed": w.get("note", ""),
                    "raw_span_sha256": sha256_text(json.dumps(w, sort_keys=True)),
                })
        for d in rec.get("objection_dispositions", []):
            disps.append({
                "round": rid, "architect": arch, "objection_id": d["objection_id"],
                "disposition": d["disposition"],
                "as_printed": d.get("basis", ""),
                "referenced_decision_ids": sorted(d.get("related_decision_ids", [])),
                "raw_span_sha256": sha256_text(json.dumps(d, sort_keys=True)),
            })
    for o in delta.get("objections", []):
        if isinstance(o, dict) and o.get("objection_id"):
            disps.append({
                "round": rid, "architect": arch, "objection_id": o["objection_id"],
                "disposition": o.get("disposition", "OPEN"),
                "as_printed": o.get("basis", ""),
                "referenced_decision_ids": sorted(o.get("related_decision_ids", [])),
                "raw_span_sha256": sha256_text(json.dumps(o, sort_keys=True)),
            })
    return {"proposals": proposals, "positions": positions,
            "withdrawals": withdrawals, "objection_dispositions": disps}


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--consilium", default=None)
    ap.add_argument("--round", required=True)
    ap.add_argument("--architect", required=True, choices=ARCHS)
    ap.add_argument("--source-response", default=None,
                    help="response file the delta must bind to (overrides the round slot)")
    args = ap.parse_args(argv)
    delta, errs = load_and_validate(args.path, consilium=args.consilium,
                                    round_id=args.round, architect=args.architect,
                                    source_response=args.source_response)
    if errs:
        for e in errs:
            print(f"[delta] ERROR {e}")
        return 1
    print(f"[delta] valid: {len(delta['decisions'])} decision records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
