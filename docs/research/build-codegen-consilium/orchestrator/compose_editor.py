#!/usr/bin/env python3
"""Compose the RFC Editor's drafting package and prompt.

Only the nominated Architect runs this round. The package contains the rebuilt
ledger, the frozen convergence responses, the evidence manifest and the RFC
baseline exactly as committed; nothing is summarised or reworded by the
Secretary.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
import run_architect as ra  # noqa: E402

ARCHS = ["gpt", "claude", "gemini"]
RFC_BASELINE_COMMIT = "6f319ac8ff780bb45ff028d006216016fc932a13"
RFC_BASELINE_PATH = "docs/architecture/rfc-build-codegen-infrastructure.md"


def load(path, default=None):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def write_bytes(path: str, data: bytes) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(data)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--editor", required=True, choices=ARCHS)
    ap.add_argument("--round", required=True)
    ap.add_argument("--timeout", type=int, default=5400)
    ap.add_argument("--responses", default="r05,r04",
                    help="comma-separated rounds whose responses are part of the package")
    args = ap.parse_args()

    C = ra.CONSILIUM
    decisions = load(os.path.join(C, "decisions.json"), {}) or {}
    objections = load(os.path.join(C, "objections.json"), {}) or {}
    if decisions.get("schema_version") != 2:
        raise SystemExit("rebuilt ledger (schema 2) is required")
    conflicts = [d["id"] for d in decisions["decisions"] if d.get("status") == "CONFLICT"]
    if conflicts:
        raise SystemExit(f"ledger still has CONFLICT decisions: {conflicts}; the Editor "
                         "must not be asked to resolve them")

    rdir = os.path.join(C, "rounds", args.round)
    os.makedirs(rdir, exist_ok=True)
    cfg = ra.ARCHITECTS[args.editor]
    inbox = os.path.join(cfg["runtime"], f"{args.round}-inbox")
    os.makedirs(inbox, exist_ok=True)
    for name in os.listdir(inbox):
        p = os.path.join(inbox, name)
        if os.path.isfile(p):
            os.remove(p)

    files = []

    def add(name: str, data: bytes, content: str) -> None:
        path = os.path.join(inbox, name)
        write_bytes(path, data)
        files.append({"path": path, "name": name, "sha256": ra.sha256_bytes(data),
                      "bytes": len(data), "content": content})

    # A compact canonical view (one entry per decision and objection) so the
    # Editor can read the whole contract without paging through every historic
    # position; the full ledgers are delivered alongside for traceability.
    canonical = {
        "schema": "consilium-canonical-ledger/1",
        "decisions": [
            {
                "id": d["id"],
                "origin_architect": d.get("origin_architect"),
                "status": d.get("status"),
                "revision": d.get("current_revision"),
                "title": d.get("title"),
                "proposition": d.get("proposition"),
                "proposition_sha256": d.get("proposition_sha256"),
                "positions": {a: ({"position": p["position"], "round": p["round"],
                                   "conditions": p.get("conditions", "")}
                                  if p else None)
                              for a, p in (d.get("live_positions") or {}).items()},
                "withdrawals": [
                    {"architect": w["architect"], "revision": w.get("applies_to_revision"),
                     "replacement_decision_ids": w.get("replacement_decision_ids", [])}
                    for w in d.get("authoritative_withdrawals", [])],
                "status_basis": d.get("status_basis"),
            }
            for d in decisions["decisions"]
        ],
        "objections": [
            {
                "id": o["id"],
                "origin_architect": o.get("origin_architect"),
                "status": o.get("status"),
                "status_basis": o.get("status_basis"),
                "dispositions": {a: d["disposition"]
                                 for a, d in (o.get("live_dispositions") or {}).items()},
                "referenced_decision_ids": o.get("referenced_decision_ids", []),
                "closure_note": o.get("closure_note"),
            }
            for o in objections["objections"]
        ],
    }
    add("00-CANONICAL-LEDGER.json",
        (json.dumps(canonical, indent=2, ensure_ascii=False) + "\n").encode("utf-8"),
        "Canonical contract: one entry per decision and objection with status, exact proposition, hash and conditions")
    add("00a-DECISION-LEDGER-FULL.json",
        (json.dumps(decisions, indent=2, ensure_ascii=False) + "\n").encode("utf-8"),
        "Full rebuilt decision ledger (schema 2) with every admitted proposition, revision, position and stale record")
    add("01-OBJECTION-LEDGER.json",
        (json.dumps(objections, indent=2, ensure_ascii=False) + "\n").encode("utf-8"),
        "Objection ledger with explicit dispositions and closure eligibility")
    add("02-EVIDENCE-MANIFEST.json",
        open(ra.MANIFEST, "rb").read(),
        "Evidence manifest pinned by the campaign")

    n = 3
    for rid in [r.strip() for r in args.responses.split(",") if r.strip()]:
        src = os.path.join(C, "rounds", rid)
        manifest = load(os.path.join(src, "manifest.json"), {}) or {}
        if manifest.get("barrier") != "closed":
            raise SystemExit(f"{rid} is not frozen")
        for arch in ARCHS:
            p = os.path.join(src, arch, "response.md")
            if not os.path.isfile(p):
                continue
            digest = ra.sha256_file(p)
            if digest != manifest["responses"][arch]["response_sha256"]:
                raise SystemExit(f"{rid}/{arch}: response hash mismatch")
            add(f"{n:02d}-{rid}-{arch}-response.md", open(p, "rb").read(),
                f"Frozen {rid} response of Architect {ra.ARCHITECTS[arch]['identity']} — "
                f"{ra.ARCHITECTS[arch]['display']}")
            n += 1

    # RFC baseline exactly as committed on the experimental branch.
    try:
        baseline = subprocess.run(
            ["git", "-C", ra.ARCHITECTS["gpt"]["worktree"], "show",
             f"{RFC_BASELINE_COMMIT}:{RFC_BASELINE_PATH}"],
            check=True, capture_output=True).stdout
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"cannot read RFC baseline: {exc}")
    add(f"{n:02d}-RFC-BASELINE.md", baseline,
        f"Existing RFC at {RFC_BASELINE_COMMIT}:{RFC_BASELINE_PATH} (unmodified baseline)")
    n += 1

    with open(os.path.join(C, "final", "editor-nomination-template.md"), encoding="utf-8"):
        pass  # template existence check only

    template_path = os.path.join(C, "rounds", "editor", "prompt-template.md")
    template = open(template_path, encoding="utf-8").read()
    listing = "\n".join(
        f"{i}. `{f['path']}` — {f['bytes']} bytes — SHA-256 `{f['sha256']}` — {f['content']}"
        for i, f in enumerate(files, 1))
    launch_epoch = int(ra.time.time()) + 20
    prompt = ra.render(template, args.editor, args.timeout, launch_epoch,
                       extra={"PACKAGE_INDEX": listing})
    prompt_path = os.path.join(rdir, f"prompt-{args.editor}.md")
    with open(prompt_path, "w", encoding="utf-8") as fh:
        fh.write(prompt)

    ra.write_json(os.path.join(rdir, "composition.json"), {
        "round": args.round, "editor": args.editor,
        "editor_model": cfg["model_id"], "editor_effort": cfg["effort"],
        "template": os.path.relpath(template_path, ra.SEC),
        "timeout_s": args.timeout,
        "prompt_sha256": ra.sha256_bytes(prompt.encode("utf-8")),
        "prompt_bytes": len(prompt.encode("utf-8")),
        "inbox": inbox, "package": files,
        "ledger": {"decisions_sha256": ra.sha256_file(os.path.join(C, "decisions.json")),
                   "objections_sha256": ra.sha256_file(os.path.join(C, "objections.json"))},
    })
    print(f"composed editor package for {args.editor}: {len(files)} files, "
          f"prompt {ra.sha256_bytes(prompt.encode('utf-8'))[:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
