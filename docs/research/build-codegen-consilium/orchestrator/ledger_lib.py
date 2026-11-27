#!/usr/bin/env python3
"""Mechanical decision/objection ledger extraction for the consilium.

Design rules (charter §3, protocol §5, §11):

- The Secretary never merges two propositions by semantic similarity, never
  rewrites a proposition, and never infers a position from prose tone.
- A proposition revision is *admitted* only when its exact text is
  hash-anchored: ``sha256(text)`` must appear as a declared SHA-256 token in the
  corpus (an Architect-printed proposition hash) or be declared next to the
  text in the same structured block. Formats differ between Architects, so the
  extractor accepts the observed formats and rejects everything else instead of
  guessing.
- Two different hash-anchored texts for the same ``(decision, revision)`` are a
  CONFLICT; the decision fails closed and is never reported as accepted.
- An acceptance counts only for the *current* revision. Positions on an
  obsolete revision are preserved as stale and never carry over.
- All three explicit rejections of the same revision and hash are a resolved
  decision (``UNANIMOUS_REJECTED``), not an ongoing disagreement.
- Withdrawals are authoritative only for the Architect that authored the
  proposition; a peer's report of a withdrawal is preserved but not applied.
- An objection is closed only by an explicit disposition from its author, or by
  an explicit closing disposition from all three Architects. Silence never
  closes anything.
"""

from __future__ import annotations

import glob
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import decision_delta  # noqa: E402

ARCHS = ["gpt", "claude", "gemini"]
ID_ARCH = {"A": "gpt", "B": "claude", "C": "gemini"}
POSITIONS = ["PROPOSE", "ACCEPT", "REJECT", "CONDITIONAL", "NEEDS_EVIDENCE"]
STATUS_VALUES = [
    "PROPOSED", "UNANIMOUS", "UNANIMOUS_REJECTED", "CONDITIONAL", "DISPUTED",
    "NEEDS_EXPERIMENT", "WITHDRAWN", "WITHDRAWN_SUPERSEDED", "SUPERSEDED",
    "CONFLICT", "DEFERRED",
]
OBJ_STATUS_VALUES = ["OPEN", "RESOLVED", "WITHDRAWN", "DEFERRED", "SUPERSEDED"]

HEX64 = re.compile(r"\b[0-9a-f]{64}\b")
DEC_ID = re.compile(r"DEC-[A-C][0-9]{2}")
OBJ_ID = re.compile(r"OBJ-[A-C][0-9]{2}")

STRUCT_DEC = re.compile(
    r"^[ \t>*#`-]*Decision(?:\*\*)?[ \t]*:[ \t*`]*(DEC-[A-C][0-9]{2})", re.M)
PROSE_DEC = re.compile(r"^\*\*(DEC-[A-C][0-9]{2}) r(\d+)\.\*\*[ \t]+(.+)$", re.M)
REV_CONTEXT = re.compile(
    r"(DEC-[A-C][0-9]{2})`?[^\n]{0,60}?\((?:Rev|rev|Revision)[^\n]*?->\s*"
    r"(?:Rev|rev|Revision)\s*(\d+)\s*`([0-9a-f]{64})`")
NEW_REVISION = re.compile(r"\*New \([Rr]ev (\d+)\):\*\s*`(.+)`")
OBJ_RAISE_BOLD = re.compile(r"^[ \t>*#`-]*\*\*(OBJ-[A-C][0-9]{2})\b", re.M)
OBJ_RAISE_HEADING = re.compile(r"^[ \t#]+`?(OBJ-[A-C][0-9]{2})`?[ \t]*$", re.M)
OBJ_TABLE = re.compile(r"^\|\s*(OBJ-[A-C][0-9]{2})\s*·\s*([^|]+)\|")
OBJ_ISSUE = re.compile(r"^[ \t>*#`-]*Issue[ \t]*:[ \t*`]*(OBJ-[A-C][0-9]{2})", re.M)
OBJ_DISP_FIELD = re.compile(
    r"^[ \t>*#`-]*(?:Your position|Disposition|Decision on objection)[ \t]*:[ \t*`]*(.+)$", re.M)

WITHDRAW_VERB = re.compile(r"\bwithdr(?:aw|aws|ew|awn)\b", re.I)
FIRST_PERSON = re.compile(r"\b(I|my|me)\b")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_json(path: str, default=None):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


# --------------------------------------------------------------------------- #
# Corpus
# --------------------------------------------------------------------------- #

def closed_rounds(consilium: str) -> list[str]:
    """Rounds whose barrier is closed. A partial/interrupted round is never read."""
    out = []
    for path in glob.glob(os.path.join(consilium, "rounds", "r[0-9][0-9]")):
        manifest = os.path.join(path, "manifest.json")
        m = load_json(manifest) or {}
        if m.get("barrier") == "closed":
            out.append(os.path.basename(path))
    return sorted(out)


def skipped_rounds(consilium: str) -> list[dict]:
    out = []
    for path in glob.glob(os.path.join(consilium, "rounds", "r[0-9][0-9]")):
        rid = os.path.basename(path)
        manifest = os.path.join(path, "manifest.json")
        if not os.path.isfile(manifest):
            out.append({"round": rid, "reason": "no manifest.json (interrupted or partial round)"})
            continue
        m = load_json(manifest) or {}
        if m.get("barrier") != "closed":
            out.append({"round": rid, "reason": f"barrier={m.get('barrier')!r}"})
    return out


def load_corpus(consilium: str) -> list[dict]:
    corpus = []
    for rid in closed_rounds(consilium):
        for arch in ARCHS:
            path = os.path.join(consilium, "rounds", rid, arch, "response.md")
            if not os.path.isfile(path):
                continue
            with open(path, "rb") as fh:
                raw = fh.read()
            corpus.append({
                "round": rid,
                "architect": arch,
                "text": raw.decode("utf-8", "replace"),
                "response_sha256": sha256_text(raw.decode("utf-8", "replace")),
                "path": os.path.relpath(path, consilium),
            })
    return corpus


def declared_hash_tokens(corpus: list[dict]) -> set[str]:
    toks: set[str] = set()
    for rec in corpus:
        toks.update(HEX64.findall(rec["text"]))
    return toks


# --------------------------------------------------------------------------- #
# Response parsing
# --------------------------------------------------------------------------- #

def _fields(span: str) -> dict:
    fields: dict[str, str] = {}
    for line in span.splitlines():
        fm = re.match(
            r"^[ \t>*#`-]*([A-Za-z][A-Za-z0-9 /_-]{1,40})(?:\*\*)?[ \t]*:[ \t]*"
            r"(?:\*\*[ \t]*)?(.*)$", line)
        if not fm:
            continue
        key = fm.group(1).strip().lower().replace(" ", "_")
        fields.setdefault(key, fm.group(2).strip())
    return fields


def _blocks(text: str, start_re: re.Pattern) -> list[tuple[str, str]]:
    starts = list(start_re.finditer(text))
    out = []
    for i, m in enumerate(starts):
        end = starts[i + 1].start() if i + 1 < len(starts) else len(text)
        out.append((m.group(1), text[m.start():end]))
    return out


def _rev_int(value) -> int | None:
    m = re.search(r"\d+", str(value or ""))
    return int(m.group(0)) if m else None


def _position(value: str) -> str | None:
    m = re.match(r"^[`*\s]*(PROPOSE|ACCEPT|REJECT|CONDITIONAL|NEEDS_EVIDENCE)\b",
                 value or "", re.I)
    return m.group(1).upper() if m else None


def parse_response(rec: dict, declared: set[str]) -> dict:
    """Extract proposals, positions, withdrawals and objection records.

    Every extracted item keeps the round, architect and a hash of the raw span
    it came from, so the ledger can always be audited against the frozen text.
    """
    text = rec["text"]
    rid, arch = rec["round"], rec["architect"]
    out = {"proposals": [], "positions": [], "withdrawals": [],
           "objection_raises": [], "objection_dispositions": [],
           "unverified": []}

    # --- structured blocks (Decision:/Title:/Proposition:/Revision:/...) ---- #
    for did, span in _blocks(text, STRUCT_DEC):
        f = _fields(span)
        rev = _rev_int(f.get("revision"))
        prop = (f.get("proposition") or "").strip()
        declared_sha = (f.get("proposition_sha-256") or "").strip("`* ").lower() or None
        if prop:
            calc = sha256_text(prop)
            anchored = calc in declared or (declared_sha is not None and declared_sha == calc)
            entry = {
                "round": rid, "architect": arch, "decision_id": did, "revision": rev,
                "title": f.get("title", ""), "proposition": prop,
                "proposition_sha256": calc, "declared_sha256": declared_sha,
                "hash_anchored": anchored, "kind": "structured_block",
                "raw_span_sha256": sha256_text(span),
            }
            if not anchored:
                out["unverified"].append({**entry, "reason": "declared hash does not match text"})
            elif declared_sha is not None and declared_sha != calc:
                out["unverified"].append({**entry, "reason": "declared hash differs from text hash"})
            else:
                out["proposals"].append(entry)
        pos = _position(f.get("position"))
        if pos and rev is not None:
            out["positions"].append({
                "round": rid, "architect": arch, "decision_id": did, "revision": rev,
                "position": pos,
                "position_as_printed": f.get("position", ""),
                "declared_sha256": declared_sha,
                "proposition_sha256": calc if prop else declared_sha,
                "reason": f.get("reason", ""),
                "conditions": f.get("conditions", ""),
                "related_objections": f.get("related_objections", ""),
                "raw_span_sha256": sha256_text(span),
            })

    # --- prose revision texts: "**DEC-A02 r2.** exact proposition text" ----- #
    for m in PROSE_DEC.finditer(text):
        did, rev, prop = m.group(1), int(m.group(2)), m.group(3).strip()
        calc = sha256_text(prop)
        if calc in declared:
            out["proposals"].append({
                "round": rid, "architect": arch, "decision_id": did, "revision": rev,
                "title": "", "proposition": prop, "proposition_sha256": calc,
                "declared_sha256": calc, "hash_anchored": True,
                "kind": "prose_revision", "raw_span_sha256": sha256_text(m.group(0)),
            })

    # --- inline author revision: "(Rev 1 `...` -> Rev 2 `hash`):" + New ----- #
    context: tuple[str, int, str] | None = None
    for line in text.splitlines():
        cm = REV_CONTEXT.search(line)
        if cm:
            context = (cm.group(1), int(cm.group(2)), cm.group(3))
            continue
        nm = NEW_REVISION.search(line)
        if nm and context:
            rev = int(nm.group(1))
            prop = nm.group(2).strip()
            calc = sha256_text(prop)
            if rev == context[1] and calc == context[2]:
                out["proposals"].append({
                    "round": rid, "architect": arch, "decision_id": context[0],
                    "revision": rev, "title": "", "proposition": prop,
                    "proposition_sha256": calc, "declared_sha256": context[2],
                    "hash_anchored": True, "kind": "inline_revision",
                    "raw_span_sha256": sha256_text(line),
                })
            context = None

    # --- withdrawals (author's own voice only) ------------------------------ #
    for sentence in re.split(r"(?<=\.)\s+|\n\n+", text):
        if not (WITHDRAW_VERB.search(sentence) and FIRST_PERSON.search(sentence)):
            continue
        verb = WITHDRAW_VERB.search(sentence)
        head, tail = sentence[:verb.end()], sentence[verb.end():]
        matches = []
        for m in DEC_ID.finditer(tail):
            before = tail[max(0, m.start() - 8):m.start()]
            if re.search(r"(?:->|/)\s*`?\s*$", before):
                matches.append((m, True))     # replacement target, not withdrawn
            else:
                matches.append((m, False))
        withdrawn = [(m, rep) for m, rep in matches if not rep]
        lead = tail[:withdrawn[0][0].start()] if withdrawn else tail
        for n, (m, _) in enumerate(withdrawn):
            end_pos = (withdrawn[n + 1][0].start() if n + 1 < len(withdrawn) else len(tail))
            window = tail[m.end():end_pos]
            did = m.group(0)
            hint = (re.search(r"\brev(?:ision)?\s*(\d+)", head + lead, re.I)
                    or re.search(r"\brev(?:ision)?\s*(\d+)", window, re.I))
            reps = set()
            for m2 in DEC_ID.finditer(window):
                reps.add(m2.group(0))
            if "->" in window:
                # "(-> `DEC-B02`/`A02` rev 2)": the second id lacks the prefix
                for m2 in re.finditer(r"(?<![A-Za-z0-9])([ABC])(\d{2})(?![0-9])", window):
                    reps.add(f"DEC-{m2.group(1)}{m2.group(2)}")
            reps.discard(did)
            out["withdrawals"].append({
                "round": rid, "architect": arch, "decision_id": did,
                "authoritative": ID_ARCH.get(did[4]) == arch,
                "revision_hint": int(hint.group(1)) if hint else None,
                "replacement_decision_ids": sorted(reps),
                "as_printed": sentence.strip()[:600],
                "raw_span_sha256": sha256_text(sentence),
            })

    # --- objections: raises ------------------------------------------------- #
    for m in list(OBJ_RAISE_BOLD.finditer(text)) + list(OBJ_RAISE_HEADING.finditer(text)):
        oid = m.group(1)
        if ID_ARCH.get(oid[4]) != arch:
            continue
        out["objection_raises"].append({
            "round": rid, "architect": arch, "objection_id": oid,
            "raw_span_sha256": sha256_text(m.group(0)),
            "excerpt": _line_at(text, m.start())[:400],
        })

    # --- objections: dispositions ------------------------------------------ #
    for m in OBJ_TABLE.finditer(text):
        oid, disp = m.group(1), m.group(2).strip()
        out["objection_dispositions"].append(_disp_entry(rid, arch, oid, disp, m.group(0)))
    for oid, span in _blocks(text, OBJ_ISSUE):
        field = OBJ_DISP_FIELD.search(span)
        if not field:
            continue
        out["objection_dispositions"].append(
            _disp_entry(rid, arch, oid, field.group(1).strip(), field.group(0)))
    return out


def _line_at(text: str, index: int) -> str:
    start = text.rfind("\n", 0, index) + 1
    end = text.find("\n", index)
    return text[start:end if end != -1 else len(text)]


def _canonical_disposition(value: str) -> str:
    head = re.split(r"[.(—:]", value, maxsplit=1)[0].strip().upper()
    if "REBUT" in head:
        return "REBUT"
    if "WITHDRAW" in head and re.search(r"\bretain|in part|partly", value, re.I):
        return "WITHDRAWN_PARTIAL"
    if "UPHOLD IN PART" in head or "PART" in head and "UPHOLD" in head:
        return "UPHOLD_PARTIAL"
    if "UPHOLD" in head:
        return "UPHOLD"
    for key, val in (("WITHDRAW", "WITHDRAWN"), ("RESOLV", "RESOLVED"),
                     ("CLOSE", "RESOLVED"), ("CLOSED", "RESOLVED"),
                     ("SATISFI", "RESOLVED"), ("DEFER", "DEFERRED"),
                     ("SUPERSED", "SUPERSEDED"), ("OPEN", "OPEN")):
        if key in head:
            return val
    return "UNCLASSIFIED"


def _disp_entry(rid: str, arch: str, oid: str, disp: str, span: str) -> dict:
    return {
        "round": rid, "architect": arch, "objection_id": oid,
        "disposition": _canonical_disposition(disp),
        "as_printed": disp.strip()[:300],
        "raw_span_sha256": sha256_text(span),
    }



# --------------------------------------------------------------------------- #
# Merge and status
# --------------------------------------------------------------------------- #

def _norm_conditions(value: str) -> str:
    return (value or "").strip().strip("`* .").lower()


def _round_index(rid: str) -> int:
    return int(rid[1:])


def build(consilium: str) -> tuple[dict, dict, dict]:
    """Build both ledgers from frozen responses. Never merges or rewrites."""
    corpus = load_corpus(consilium)
    declared = declared_hash_tokens(corpus)
    parsed = [parse_response(rec, declared) for rec in corpus]

    # Structured decision deltas (Round 4+) are authoritative; an invalid delta
    # is rejected as a whole and never partially applied.
    delta_report = {"applied": [], "rejected": []}
    for rec, p in zip(corpus, parsed):
        path = os.path.join(consilium, "rounds", rec["round"],
                            rec["architect"], "delta.json")
        if not os.path.isfile(path):
            continue
        delta, errs = decision_delta.load_and_validate(
            path, consilium=consilium, round_id=rec["round"],
            architect=rec["architect"])
        if errs:
            delta_report["rejected"].append({
                "round": rec["round"], "architect": rec["architect"],
                "delta_sha256": sha256_text(open(path, encoding="utf-8").read()),
                "errors": errs})
            continue
        converted = decision_delta.to_records(delta)
        p["proposals"].extend(converted["proposals"])
        p["positions"].extend(converted["positions"])
        p["withdrawals"].extend(converted["withdrawals"])
        p["objection_dispositions"].extend(converted["objection_dispositions"])
        delta_report["applied"].append({
            "round": rec["round"], "architect": rec["architect"],
            "decisions": len(delta["decisions"])})

    decisions: dict[str, dict] = {}
    objections: dict[str, dict] = {}
    report = {
        "rounds_read": sorted({r["round"] for r in corpus}),
        "rounds_skipped": skipped_rounds(consilium),
        "unverified_propositions": [],
        "withdrawal_reports": [],
        "admitted_propositions": 0,
        "conflicts": [],
        "deltas": delta_report,
    }

    for rec, p in zip(corpus, parsed):
        rid, arch = rec["round"], rec["architect"]
        report["unverified_propositions"].extend(p["unverified"])
        report["withdrawal_reports"].extend(p["withdrawals"])
        report["admitted_propositions"] += len(p["proposals"])

        for prop in p["proposals"]:
            did = prop["decision_id"]
            row = decisions.setdefault(did, {
                "id": did,
                "origin_architect": ID_ARCH.get(did[4]),
                "first_seen_round": rid,
                "history": [],
                "positions": {a: [] for a in ARCHS},
                "withdrawals": [],
                "objections": [],
                "revision_owner": {},
            })
            row["history"].append(prop)
            row["revision_owner"].setdefault(str(prop["revision"]), prop["architect"])

        for pos in p["positions"]:
            did = pos["decision_id"]
            row = decisions.setdefault(did, {
                "id": did,
                "origin_architect": ID_ARCH.get(did[4]),
                "first_seen_round": rid,
                "history": [], "positions": {a: [] for a in ARCHS},
                "withdrawals": [], "objections": [], "revision_owner": {},
            })
            row["positions"][arch].append(pos)
            for oid in OBJ_ID.findall(pos.get("related_objections", "")):
                if oid not in row["objections"]:
                    row["objections"].append(oid)

        for w in p["withdrawals"]:
            row = decisions.setdefault(w["decision_id"], {
                "id": w["decision_id"],
                "origin_architect": ID_ARCH.get(w["decision_id"][4]),
                "first_seen_round": rid,
                "history": [], "positions": {a: [] for a in ARCHS},
                "withdrawals": [], "objections": [], "revision_owner": {},
            })
            row["withdrawals"].append(w)

        for raise_ in p["objection_raises"]:
            oid = raise_["objection_id"]
            row = objections.setdefault(oid, {
                "id": oid,
                "origin_architect": arch,
                "first_seen_round": rid,
                "raised": [],
                "dispositions": [],
            })
            if not row["raised"] or row["raised"][-1]["raw_span_sha256"] != raise_["raw_span_sha256"]:
                row["raised"].append(raise_)

        for disp in p["objection_dispositions"]:
            oid = disp["objection_id"]
            row = objections.setdefault(oid, {
                "id": oid,
                "origin_architect": ID_ARCH.get(oid[4]),
                "first_seen_round": rid,
                "raised": [], "dispositions": [],
            })
            row["dispositions"].append(disp)

    # ---- decision status ---------------------------------------------------- #
    for did, row in decisions.items():
        by_rev: dict[int, list[dict]] = {}
        for prop in row["history"]:
            by_rev.setdefault(prop["revision"], []).append(prop)

        revisions = {}
        conflicted = set()
        for rev, props in sorted(by_rev.items()):
            texts = {p["proposition"] for p in props}
            hashes = {p["proposition_sha256"] for p in props}
            conflict = len(texts) > 1
            if conflict:
                conflicted.add(rev)
                report["conflicts"].append({
                    "decision_id": did, "revision": rev,
                    "texts": sorted(texts),
                    "text_sha256": sorted(hashes),
                    "rounds": sorted({p["round"] for p in props}),
                })
            revisions[str(rev)] = {
                "revision": rev,
                "proposition": props[0]["proposition"],
                "proposition_sha256": props[0]["proposition_sha256"],
                "texts": sorted(texts),
                "contested": conflict,
                "admitted_by": sorted({p["architect"] for p in props}),
                "stated_in": [{"round": p["round"], "architect": p["architect"],
                               "kind": p["kind"]} for p in props],
                "hash_anchored": all(p["hash_anchored"] for p in props),
            }
        row["revisions"] = revisions
        highest = max(by_rev) if by_rev else None
        if highest is not None and highest in conflicted:
            # The newest revision cannot be identified by exact text: fail closed
            # rather than silently falling back to an older proposition.
            current_rev = None
        else:
            current_rev = max((r for r in by_rev if r not in conflicted), default=None)
        row["current_revision"] = current_rev
        if current_rev is None:
            row["proposition"] = None
            row["proposition_sha256"] = None
            row["title"] = None
        else:
            cur = revisions[str(current_rev)]
            row["proposition"] = cur["proposition"]
            row["proposition_sha256"] = cur["proposition_sha256"]
            row["title"] = next(
                (p["title"] for p in by_rev[current_rev] if p.get("title")), "")

        # live vs stale positions: acceptance never carries across revisions
        live, stale, mismatched = {}, {}, []
        for arch in ARCHS:
            entries = row["positions"].get(arch, [])
            if not entries:
                live[arch] = None
                stale[arch] = []
                continue
            stale[arch] = [e for e in entries if e["revision"] != current_rev]
            current = [e for e in entries if e["revision"] == current_rev]
            if not current:
                live[arch] = None
                continue
            last = current[-1]
            declared = (last.get("declared_sha256") or "").lower()
            if declared and row["proposition_sha256"] and declared != row["proposition_sha256"]:
                mismatched.append({"architect": arch, "revision": current_rev,
                                   "declared_sha256": declared,
                                   "proposition_sha256": row["proposition_sha256"]})
                live[arch] = None
            else:
                live[arch] = last
        row["live_positions"] = live
        row["stale_positions"] = stale
        row["stale_position_count"] = sum(len(v) for v in stale.values())
        row["position_hash_mismatches"] = mismatched

        # withdrawals that target the current revision
        authoritative = [w for w in row["withdrawals"] if w["authoritative"]]
        peer_reported = [w for w in row["withdrawals"] if not w["authoritative"]]
        row["authoritative_withdrawals"] = authoritative
        row["peer_reported_withdrawals"] = peer_reported
        withdrawn_current = []
        for w in authoritative:
            target = w["revision_hint"] if w.get("revision_hint") else current_rev
            w["applies_to_revision"] = target
            if target == current_rev:
                withdrawn_current.append(w)
            else:
                w["applies_to_superseded_revisions"] = True
        row["withdrawn_current_revisions"] = sorted(
            {w["applies_to_revision"] for w in withdrawn_current})

        vals = {a: (live[a] or {}).get("position") for a in ARCHS}
        # A conditional acceptance is not unconditional consensus.
        effective = {
            a: ("CONDITIONAL" if (vals[a] == "ACCEPT"
                                  and _norm_conditions(live[a].get("conditions", ""))
                                  not in ("", "none", "n/a")) else vals[a])
            for a in ARCHS}
        row["effective_positions"] = effective
        all_present = all(vals[a] for a in ARCHS)
        unanimous_accept = (
            all_present and all(vals[a] == "ACCEPT" for a in ARCHS)
            and all(_norm_conditions(live[a].get("conditions", "")) in ("", "none", "n/a")
                    for a in ARCHS)
            and not any(declared_mismatch(row, a, current_rev) for a in ARCHS))
        unanimous_reject = (
            all_present and all(vals[a] == "REJECT" for a in ARCHS)
            and not any(declared_mismatch(row, a, current_rev) for a in ARCHS))

        if current_rev is None and conflicted:
            status = "CONFLICT"
            basis = "two different hash-anchored texts share this revision"
        elif unanimous_reject:
            status = "UNANIMOUS_REJECTED"
            basis = "all three explicitly reject the same revision and proposition hash"
        elif withdrawn_current and not unanimous_accept:
            replacements = sorted({d for w in withdrawn_current
                                   for d in w.get("replacement_decision_ids", [])})
            row["replacement_decision_ids"] = replacements
            status = "WITHDRAWN_SUPERSEDED" if replacements else "WITHDRAWN"
            basis = ("author withdrew this revision in favour of other decisions; "
                     "withdrawal does not approve the replacement propositions")
        elif unanimous_accept:
            status = "UNANIMOUS"
            basis = "all three explicitly accept the same current revision and hash with no conditions"
        elif any(v == "REJECT" for v in effective.values()):
            status = "DISPUTED"
            basis = "at least one explicit rejection of the current revision"
        elif any(v == "CONDITIONAL" for v in effective.values()):
            status = "CONDITIONAL"
            basis = "at least one conditional acceptance"
        elif any(v == "NEEDS_EVIDENCE" for v in effective.values()):
            status = "NEEDS_EXPERIMENT"
            basis = "at least one position requires further evidence"
        else:
            status = "PROPOSED"
            basis = "fewer than three live positions on the current revision"
        row["status"] = status
        row["status_basis"] = basis

    # ---- replacement acceptance (second pass) ------------------------------ #
    for did, row in decisions.items():
        reps = row.get("replacement_decision_ids") or []
        row["replacement_status"] = {
            r: (decisions[r]["status"] if r in decisions else "UNKNOWN") for r in reps}
        row["replacement_accepted"] = sorted(
            r for r, st in row["replacement_status"].items() if st == "UNANIMOUS")

    # ---- objection status --------------------------------------------------- #
    for oid, row in objections.items():
        latest = {}
        for d in row["dispositions"]:
            latest[d["architect"]] = d
        row["live_dispositions"] = latest
        kinds = {a: d["disposition"] for a, d in latest.items()}
        row["unanimous_uphold"] = (
            len(kinds) == 3 and all(k in ("UPHOLD", "UPHOLD_PARTIAL", "REBUT")
                                    for k in kinds.values()))
        author = row["origin_architect"]
        if kinds.get(author) == "WITHDRAWN":
            status, basis = "WITHDRAWN", "the originating Architect explicitly withdrew the objection"
        elif len(kinds) == 3 and set(kinds.values()) == {"RESOLVED"}:
            status, basis = "RESOLVED", ("all three explicitly recorded a closing disposition; the "
                                        "agreed acceptance test remains a roadmap obligation, not an "
                                        "open architectural dispute")
        elif len(kinds) == 3 and set(kinds.values()) == {"SUPERSEDED"}:
            status, basis = "SUPERSEDED", "all three explicitly recorded supersession"
        elif len(kinds) == 3 and set(kinds.values()) == {"DEFERRED"}:
            status, basis = "DEFERRED", "all three explicitly deferred the objection"
        else:
            status = "OPEN"
            basis = ("no closing disposition agreed by all three"
                     if kinds else "no explicit disposition recorded")
        row["status"] = status
        row["status_basis"] = basis

    return decisions, objections, report


def declared_mismatch(row: dict, arch: str, current_rev) -> bool:
    return any(m["architect"] == arch and m["revision"] == current_rev
               for m in row.get("position_hash_mismatches", []))
