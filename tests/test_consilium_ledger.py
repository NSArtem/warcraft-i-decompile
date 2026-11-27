"""Regression tests for the consilium decision/objection ledger.

Each test builds a synthetic frozen round set in a temporary directory and
checks one mechanical rule from the ledger contract. No Architect session and
no real campaign artifact is touched.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib

import pytest

ORCH = pathlib.Path(__file__).resolve().parents[1] / (
    "docs/research/build-codegen-consilium/orchestrator/ledger_lib.py")


def load_lib():
    spec = importlib.util.spec_from_file_location("consilium_ledger_lib", ORCH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


LIB = load_lib()


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def make_round(root, rid, responses, barrier="closed"):
    rdir = root / "rounds" / rid
    rdir.mkdir(parents=True, exist_ok=True)
    if barrier is not None:
        (rdir / "manifest.json").write_text(
            json.dumps({"round": rid, "barrier": barrier}), encoding="utf-8")
    for arch, text in responses.items():
        d = rdir / arch
        d.mkdir(parents=True, exist_ok=True)
        (d / "response.md").write_text(text, encoding="utf-8")


def proposal(did, rev, prop, position="PROPOSE", conditions="none", sha_override=None):
    digest = sha_override if sha_override is not None else sha(prop)
    return (
        "```text\n"
        f"Decision: {did}\n"
        f"Title: t\n"
        f"Proposition: {prop}\n"
        f"Revision: {rev}\n"
        f"Position: {position}\n"
        f"Conditions: {conditions}\n"
        f"Proposition SHA-256: {digest}\n"
        "```\n")


def vote(did, rev, position, prop_hash, conditions="none"):
    return (
        "```text\n"
        f"Decision: {did}\n"
        f"Revision: {rev}\n"
        f"Position: {position}\n"
        f"Conditions: {conditions}\n"
        f"Proposition SHA-256: {prop_hash}\n"
        "```\n")


def build(root):
    decisions, objections, report = LIB.build(str(root))
    return decisions, objections, report


def test_prose_revision_requires_hash_anchor(tmp_path):
    prop2 = "Revised proposition text for A02 revision two."
    responses = {
        "gpt": proposal("DEC-A02", 1, "Original text rev one.") +
               f"**DEC-A02 r2.** {prop2}\n" +
               vote("DEC-A02", 2, "ACCEPT", sha(prop2)),
    }
    make_round(tmp_path, "r00", responses)
    decisions, _, report = build(tmp_path)
    row = decisions["DEC-A02"]
    assert row["current_revision"] == 2
    assert row["revisions"]["2"]["proposition"] == prop2
    assert row["revisions"]["2"]["admitted_by"] == ["gpt"]
    assert report["unverified_propositions"] == []


def test_prose_revision_without_any_declared_hash_is_rejected(tmp_path):
    # The bold text is a plausible revision but no SHA-256 token anchors it.
    make_round(tmp_path, "r00", {
        "gpt": proposal("DEC-A02", 1, "Original revision one text.") +
               "**DEC-A02 r2.** Unanchored text, hash never printed.\n",
    })
    decisions, _, report = build(tmp_path)
    assert decisions["DEC-A02"]["current_revision"] == 1
    assert decisions["DEC-A02"]["revisions"].get("2") is None


def test_hash_mismatch_is_not_admitted(tmp_path):
    prop = "A proposition whose declared hash does not match."
    make_round(tmp_path, "r00", {
        "gpt": proposal("DEC-B01", 1, prop, sha_override="0" * 64),
    })
    decisions, _, report = build(tmp_path)
    row = decisions.get("DEC-B01")
    assert row is None or row["proposition"] is None
    assert report["unverified_propositions"]


def test_approval_of_obsolete_revision_does_not_count(tmp_path):
    prop1, prop2 = "Revision one text.", "Revision two text."
    make_round(tmp_path, "r00", {
        "gpt": proposal("DEC-A05", 1, prop1) + proposal("DEC-A05", 2, prop2),
        "claude": vote("DEC-A05", 1, "ACCEPT", sha(prop1)),
        "gemini": vote("DEC-A05", 1, "ACCEPT", sha(prop1)),
    })
    decisions, _, _ = build(tmp_path)
    row = decisions["DEC-A05"]
    assert row["current_revision"] == 2
    assert row["status"] != "UNANIMOUS"
    assert row["live_positions"]["claude"] is None
    assert row["stale_position_count"] >= 2


def test_unanimous_rejection_is_resolved(tmp_path):
    prop = "Selective OMF extraction is the M2 strategy."
    make_round(tmp_path, "r00", {
        "gpt": proposal("DEC-C08", 1, prop) +
               vote("DEC-C08", 1, "REJECT", sha(prop)),
        "claude": vote("DEC-C08", 1, "REJECT", sha(prop)),
        "gemini": vote("DEC-C08", 1, "REJECT", sha(prop)),
    })
    decisions, _, _ = build(tmp_path)
    assert decisions["DEC-C08"]["status"] == "UNANIMOUS_REJECTED"


def test_unanimous_acceptance_with_condition_is_conditional(tmp_path):
    prop = "Adopt one planner."
    make_round(tmp_path, "r00", {
        "gpt": proposal("DEC-B03", 1, prop) + vote("DEC-B03", 1, "ACCEPT", sha(prop)),
        "claude": vote("DEC-B03", 1, "ACCEPT", sha(prop)),
        "gemini": vote("DEC-B03", 1, "ACCEPT", sha(prop), conditions="only after audit"),
    })
    decisions, _, _ = build(tmp_path)
    assert decisions["DEC-B03"]["status"] == "CONDITIONAL"


def test_author_withdrawal_and_replacement_mapping(tmp_path):
    make_round(tmp_path, "r00", {
        "gemini": proposal("DEC-C02", 1, "Superseded C text."),
    })
    make_round(tmp_path, "r01", {
        "gemini": "I formally withdraw (`REJECT` rev 1 as superseded): "
                  "`DEC-C02` (-> `DEC-B02`/`A02` rev 2).\n",
        "gpt": vote("DEC-B02", 1, "ACCEPT", sha("B02 text")),
    }, barrier="closed")
    # Round 1 has no DEC-B02 proposition, so the replacement is not approved.
    decisions, _, _ = build(tmp_path)
    row = decisions["DEC-C02"]
    assert row["status"] == "WITHDRAWN_SUPERSEDED"
    assert row["replacement_decision_ids"] == ["DEC-A02", "DEC-B02"]
    assert row["replacement_status"]["DEC-B02"] != "UNANIMOUS"


def test_peer_reported_withdrawal_is_not_applied(tmp_path):
    make_round(tmp_path, "r00", {
        "claude": proposal("DEC-B07", 1, "B07 text."),
    })
    make_round(tmp_path, "r01", {
        "gpt": "I now reject B07 r1 because B withdrew it in favour of A11.\n",
    })
    decisions, _, _ = build(tmp_path)
    row = decisions["DEC-B07"]
    assert row["status"] != "WITHDRAWN"
    assert not row["authoritative_withdrawals"]


def test_conflicting_texts_sharing_a_revision_fail_closed(tmp_path):
    make_round(tmp_path, "r00", {
        "gemini": proposal("DEC-C01", 2, "First published revision two text."),
    })
    make_round(tmp_path, "r01", {
        "gemini": proposal("DEC-C01", 2, "Second, different revision two text."),
    })
    decisions, _, report = build(tmp_path)
    row = decisions["DEC-C01"]
    assert row["status"] == "CONFLICT"
    assert row["current_revision"] is None
    assert report["conflicts"][0]["decision_id"] == "DEC-C01"


def test_objection_closes_only_with_all_three_dispositions(tmp_path):
    objection_block = (
        "Issue: OBJ-A01\n"
        "Exact proposition under dispute: something.\n"
        "Your position: {disp}.\n")
    make_round(tmp_path, "r00", {
        "gpt": "**OBJ-A01 — Correctness/verification.** The objection text.\n"
               + objection_block.format(disp="UPHOLD"),
        "claude": objection_block.format(disp="UPHOLD"),
        "gemini": objection_block.format(disp="UPHOLD"),
    })
    _, objections, _ = build(tmp_path)
    assert objections["OBJ-A01"]["status"] == "OPEN"
    assert objections["OBJ-A01"]["unanimous_uphold"]


def test_objection_author_withdrawal_closes_it(tmp_path):
    raise_text = "**OBJ-C09 — Correctness/verification.** The objection text.\n"
    make_round(tmp_path, "r00", {"gemini": raise_text})
    make_round(tmp_path, "r01", {
        "gemini": "Issue: OBJ-C09\nYour position: WITHDRAWN (the premise was refuted).\n",
    })
    _, objections, _ = build(tmp_path)
    assert objections["OBJ-C09"]["status"] == "WITHDRAWN"


def test_partial_withdrawal_keeps_objection_open(tmp_path):
    raise_text = "**OBJ-C09 — Correctness/verification.** The objection text.\n"
    make_round(tmp_path, "r00", {"gemini": raise_text})
    make_round(tmp_path, "r01", {
        "gemini": "Issue: OBJ-C09\nYour position: WITHDRAW the remedy; retain the factual part.\n",
    })
    _, objections, _ = build(tmp_path)
    assert objections["OBJ-C09"]["status"] == "OPEN"


def test_unanimous_resolution_requires_all_three(tmp_path):
    raise_text = "**OBJ-A02 — Correctness/verification.** The objection text.\n"
    make_round(tmp_path, "r00", {"gpt": raise_text})
    partial = ("Issue: OBJ-A02\nYour position: RESOLVED by DEC-B03.\n")
    make_round(tmp_path, "r01", {
        "gpt": partial,
        "claude": partial,
    })
    _, objections, _ = build(tmp_path)
    assert objections["OBJ-A02"]["status"] == "OPEN"
    make_round(tmp_path, "r01", {"gemini": partial})
    _, objections, _ = build(tmp_path)
    assert objections["OBJ-A02"]["status"] == "RESOLVED"


def test_missing_positions_leave_decision_proposed(tmp_path):
    prop = "A proposition only one Architect has voted on."
    make_round(tmp_path, "r00", {
        "gpt": proposal("DEC-A12", 1, prop) + vote("DEC-A12", 1, "ACCEPT", sha(prop)),
    })
    decisions, _, _ = build(tmp_path)
    assert decisions["DEC-A12"]["status"] == "PROPOSED"


def test_incomplete_round_is_not_read(tmp_path):
    prop1 = "Round zero proposition text."
    make_round(tmp_path, "r00", {"gpt": proposal("DEC-A01", 1, prop1)})
    make_round(tmp_path, "r01", {
        "gpt": vote("DEC-A01", 1, "ACCEPT", sha(prop1)),
        "claude": vote("DEC-A01", 1, "ACCEPT", sha(prop1)),
        "gemini": vote("DEC-A01", 1, "ACCEPT", sha(prop1)),
    })
    prop2 = "Round two replaces the proposition."
    make_round(tmp_path, "r02", {"gpt": proposal("DEC-A01", 2, prop2)}, barrier="open")
    make_round(tmp_path, "r03", {"gpt": "interrupted"}, barrier=None)
    decisions, _, report = build(tmp_path)
    assert report["rounds_read"] == ["r00", "r01"]
    assert {k["round"] for k in report["rounds_skipped"]} == {"r02", "r03"}
    assert decisions["DEC-A01"]["current_revision"] == 1
    assert decisions["DEC-A01"]["status"] == "UNANIMOUS"


def test_structured_inline_revision_is_admitted(tmp_path):
    prop = "Inline revised proposition for C13."
    text = ("1. **`DEC-C13` (Rev 1 `" + "a" * 64 + "` -> Rev 2 `" + sha(prop) + "`):**\n"
            f"   - *New (Rev 2):* `{prop}`\n")
    make_round(tmp_path, "r00", {"gemini": text + proposal("DEC-C14", 1, "Other.")})
    decisions, _, _ = build(tmp_path)
    assert decisions["DEC-C13"]["current_revision"] == 2
    assert decisions["DEC-C13"]["revisions"]["2"]["proposition"] == prop


# --------------------------------------------------------------------------- #
# Structured decision deltas
# --------------------------------------------------------------------------- #

def load_delta_module():
    path = pathlib.Path(__file__).resolve().parents[1] / (
        "docs/research/build-codegen-consilium/orchestrator/decision_delta.py")
    spec = importlib.util.spec_from_file_location("consilium_decision_delta", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


DELTA = load_delta_module()


def delta_fixture(tmp_path, prop="Adopt one planner.", position="PROPOSE",
                  extra_dec=None, withdraw=None, conditions=None):
    resp = "```text\nDecision: DEC-B03\nRevision: 1\nPosition: ACCEPT\n```\n"
    make_round(tmp_path, "r04", {"claude": resp})
    response_sha = sha(resp)
    rec = {
        "decision_id": "DEC-B03",
        "revision": 1,
        "position": position,
        "evidence": [],
    }
    if prop is not None:
        rec["proposition"] = prop
        rec["proposition_sha256"] = sha(prop)
    if conditions is not None:
        rec["conditions"] = conditions
    if extra_dec:
        rec.update(extra_dec)
    if withdraw:
        rec["withdraws"] = [withdraw]
    doc = {
        "kind": "consilium_decision_delta",
        "schema_version": 1,
        "round": "r04",
        "architect": "claude",
        "source_response_sha256": response_sha,
        "decisions": [rec],
    }
    return doc


def check(tmp_path, doc):
    return DELTA.validate(doc, consilium=str(tmp_path), round_id="r04", architect="claude")


def test_delta_valid_record(tmp_path):
    assert check(tmp_path, delta_fixture(tmp_path)) == []


def test_delta_proposition_hash_mismatch(tmp_path):
    doc = delta_fixture(tmp_path)
    doc["decisions"][0]["proposition_sha256"] = "0" * 64
    errs = check(tmp_path, doc)
    assert any("does not match the proposition text" in e for e in errs)


def test_delta_response_hash_binding(tmp_path):
    doc = delta_fixture(tmp_path)
    doc["source_response_sha256"] = "1" * 64
    assert any("source_response_sha256" in e for e in check(tmp_path, doc))


def test_delta_requires_condition_for_conditional(tmp_path):
    doc = delta_fixture(tmp_path, position="CONDITIONAL")
    assert any("requires a stated condition" in e for e in check(tmp_path, doc))


def test_delta_propose_requires_text(tmp_path):
    doc = delta_fixture(tmp_path, prop=None)
    assert any("PROPOSE requires the exact proposition text" in e
               for e in check(tmp_path, doc))


def test_delta_rejects_unknown_fields(tmp_path):
    doc = delta_fixture(tmp_path, extra_dec={"typo_field": 1})
    assert any("unknown fields" in e for e in check(tmp_path, doc))


def test_delta_only_author_may_withdraw(tmp_path):
    doc = delta_fixture(tmp_path, withdraw={
        "decision_id": "DEC-A11", "revision": 1, "replacement_decision_ids": []})
    assert any("only the authoring Architect" in e for e in check(tmp_path, doc))


def test_delta_duplicate_revision_must_agree(tmp_path):
    doc = delta_fixture(tmp_path)
    second = dict(doc["decisions"][0])
    second["position"] = "REJECT"
    doc["decisions"].append(second)
    assert any("duplicate" in e for e in check(tmp_path, doc))


def test_invalid_delta_is_not_applied(tmp_path):
    prop = "Round four proposition."
    doc = delta_fixture(tmp_path, prop=prop)
    doc["decisions"][0]["position"] = "MAYBE"
    (tmp_path / "rounds/r04/claude/delta.json").write_text(
        json.dumps(doc), encoding="utf-8")
    (tmp_path / "rounds/r04/manifest.json").write_text(
        json.dumps({"barrier": "closed"}), encoding="utf-8")
    decisions, _, report = build(tmp_path)
    assert report["deltas"]["rejected"]
    assert not report["deltas"]["applied"]
    assert decisions.get("DEC-B03") is None or decisions["DEC-B03"]["status"] != "UNANIMOUS"


def test_valid_delta_supplies_structured_records(tmp_path):
    prop = "Round four proposition from the delta."
    doc = delta_fixture(tmp_path, prop=prop, position="PROPOSE")
    (tmp_path / "rounds/r04/claude/delta.json").write_text(
        json.dumps(doc), encoding="utf-8")
    (tmp_path / "rounds/r04/manifest.json").write_text(
        json.dumps({"barrier": "closed"}), encoding="utf-8")
    decisions, _, report = build(tmp_path)
    assert report["deltas"]["applied"]
    row = decisions["DEC-B03"]
    assert row["proposition"] == prop
    assert row["live_positions"]["claude"]["position"] == "PROPOSE"
