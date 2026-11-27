#!/usr/bin/env python3
"""Compose a targeted-deliberation round.

Delivers the other two frozen responses plus a mechanical index of every
non-unanimous decision and every open objection. The Secretary does not choose
which issues are substantive; the index is exhaustive, and the Architects
classify and resolve them in their responses.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import run_architect as ra  # noqa: E402

ARCHS = ["gpt", "claude", "gemini"]


def load(path, default=None):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def objection_dispositions(text: str) -> dict:
    """Extract the first explicit UPHOLD/REBUT/UNRESOLVED in each OBJ block.

    Mechanical and approximate: the original response remains authoritative.
    """
    import re
    starts = list(re.finditer(r"\bOBJ-[ABC][0-9]{2}\b", text))
    out = {}
    for i, m in enumerate(starts):
        oid = m.group(0)
        end = starts[i + 1].start() if i + 1 < len(starts) else len(text)
        block = text[m.start():end]
        dm = re.search(r"\b(UPHOLD|REBUT|UNRESOLVED)\b", block)
        if dm and oid not in out:
            out[oid] = dm.group(1)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="src", required=True)
    ap.add_argument("--to", dest="dst", required=True)
    ap.add_argument("--template", required=True)
    ap.add_argument("--timeout", type=int, default=4500)
    args = ap.parse_args()

    src_dir = os.path.join(ra.CONSILIUM, "rounds", args.src)
    dst_dir = os.path.join(ra.CONSILIUM, "rounds", args.dst)
    manifest = load(os.path.join(src_dir, "manifest.json"), {})
    if not manifest or manifest.get("barrier") != "closed":
        raise SystemExit("source round is not frozen")
    bodies, hashes = {}, {}
    for arch in ARCHS:
        path = os.path.join(src_dir, arch, "response.md")
        with open(path, "rb") as fh:
            bodies[arch] = fh.read()
        digest = ra.sha256_bytes(bodies[arch])
        if digest != manifest["responses"][arch]["response_sha256"]:
            raise SystemExit(f"{arch}: source response hash mismatch")
        hashes[arch] = digest

    decisions = load(os.path.join(ra.CONSILIUM, "decisions.json"), {}).get("decisions", [])
    objections = load(os.path.join(ra.CONSILIUM, "objections.json"), {}).get("objections", [])
    live_dec, unanimous = [], []
    for d in decisions:
        rec = {
            "id": d.get("id"),
            "revision": d.get("current_revision"),
            "title": d.get("title"),
            "proposition": d.get("proposition"),
            "proposition_sha256": d.get("proposition_sha256"),
            "status": d.get("status"),
            "positions": {
                a: (d.get("live_positions", {}).get(a) or None)
                for a in ARCHS
            },
            "objections": d.get("objections", []),
            "history_rounds": sorted({h.get("round") for h in d.get("history", [])}),
        }
        if d.get("status") == "UNANIMOUS":
            unanimous.append({"id": rec["id"], "revision": rec["revision"],
                              "proposition_sha256": rec["proposition_sha256"]})
        else:
            live_dec.append(rec)
    live_obj = [
        {
            "id": o.get("id"),
            "origin_architect": o.get("origin_architect"),
            "first_seen_round": o.get("first_seen_round"),
            "status": o.get("status"),
            "excerpt": (o.get("history") or [{}])[-1].get("excerpt", ""),
        }
        for o in objections if o.get("status") == "OPEN"
    ]
    dispositions = {
        arch: objection_dispositions(bodies[arch].decode("utf-8", errors="replace"))
        for arch in ARCHS
    }
    issues = {
        "generated_from_round": args.src,
        "source_manifest_sha256": ra.sha256_file(os.path.join(src_dir, "manifest.json")),
        "note": ("Mechanical index. Every non-unanimous decision and every open objection is "
                 "included; the Secretary does not decide which are substantive. UNANIMOUS "
                 "decisions are listed separately and must not be reopened without new evidence."),
        "non_unanimous_decisions": live_dec,
        "open_objections": live_obj,
        "objection_dispositions_from_source_round": dispositions,
        "unanimous_decisions": unanimous,
    }

    with open(args.template, encoding="utf-8") as fh:
        template = fh.read()
    evidence_revision = "EV-3"
    os.makedirs(dst_dir, exist_ok=True)
    launch_epoch = int(ra.time.time()) + 20
    composed = {}
    for arch in ARCHS:
        cfg = ra.ARCHITECTS[arch]
        inbox = os.path.join(cfg["runtime"], f"{args.dst}-inbox")
        os.makedirs(inbox, exist_ok=True)
        for name in os.listdir(inbox):
            if name in ("00-MANIFEST.json", "00-LIVE-ISSUES.json", "SHA256SUMS") or (
                    name.startswith("01-") or name.startswith("02-")) and name.endswith(".md"):
                os.remove(os.path.join(inbox, name))
        files = []
        for i, other in enumerate([a for a in ARCHS if a != arch], 1):
            name = f"{i:02d}-architect-{other}-response.md"
            path = os.path.join(inbox, name)
            with open(path, "wb") as fh:
                fh.write(bodies[other])
            files.append({"path": path, "name": name, "sha256": hashes[other],
                          "bytes": len(bodies[other]),
                          "content": f"Complete original Round {args.src} response of Architect "
                                     f"{ra.ARCHITECTS[other]['identity']} — {ra.ARCHITECTS[other]['display']}"})
        issue_path = os.path.join(inbox, "00-LIVE-ISSUES.json")
        with open(issue_path, "w", encoding="utf-8") as fh:
            json.dump(issues, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        files.insert(0, {"path": issue_path, "name": "00-LIVE-ISSUES.json",
                         "sha256": ra.sha256_file(issue_path),
                         "bytes": os.path.getsize(issue_path),
                         "content": "Mechanical live-issues index (all non-unanimous decisions and open objections)"})
        man_path = os.path.join(inbox, "00-MANIFEST.json")
        with open(man_path, "w", encoding="utf-8") as fh:
            json.dump({"round": args.dst, "recipient": arch, "source_round": args.src,
                       "source_manifest_sha256": ra.sha256_file(os.path.join(src_dir, "manifest.json")),
                       "files": files, "note": "Verbatim discussion material. Not instructions."},
                      fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        with open(os.path.join(inbox, "SHA256SUMS"), "w", encoding="utf-8") as fh:
            for f in files:
                fh.write(f"{f['sha256']}  {f['name']}\n")
        listing = "\n".join(
            f"{i}. `{f['path']}` — {f['bytes']} bytes — SHA-256 `{f['sha256']}` — {f['content']}"
            for i, f in enumerate(files, 1)
        )
        prompt = ra.render(template, arch, args.timeout, launch_epoch, extra={
            "INBOX_INDEX": listing,
            "ROUND_NUMBER": str(int(args.dst[1:])),
            "ROUND_PAD": args.dst[1:],
            "EVIDENCE_REVISION": evidence_revision,
        })
        prompt_path = os.path.join(dst_dir, f"prompt-{arch}.md")
        with open(prompt_path, "w", encoding="utf-8") as fh:
            fh.write(prompt)
        composed[arch] = {
            "prompt_sha256": ra.sha256_bytes(prompt.encode("utf-8")),
            "prompt_bytes": len(prompt.encode("utf-8")),
            "inbox": inbox,
            "receives": [a for a in ARCHS if a != arch],
            "inbox_files": files,
        }
    ra.write_json(os.path.join(dst_dir, "composition.json"), {
        "from_round": args.src, "to_round": args.dst,
        "template": os.path.relpath(args.template, ra.SEC),
        "timeout_s": args.timeout, "evidence_revision": evidence_revision,
        "live_issue_counts": {"decisions": len(live_dec), "objections": len(live_obj),
                              "unanimous": len(unanimous)},
        "prompts": composed,
    })
    print(f"composed {args.dst}: live decisions={len(live_dec)} objections={len(live_obj)} "
          f"unanimous={len(unanimous)}")
    for arch in ARCHS:
        print(f"  {arch}: prompt {composed[arch]['prompt_bytes']}B inbox {composed[arch]['inbox']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
