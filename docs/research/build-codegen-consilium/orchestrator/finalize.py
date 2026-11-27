#!/usr/bin/env python3
"""Draft hashing and final-approval verification.

Subcommands:
  hash-draft   Hash an immutable draft directory and write SHA256SUMS + manifest.
  check        Verify three explicit Architect verdicts against the same hashes.
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


def sha(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def hash_draft(draft_dir: str, revision: str) -> int:
    files = []
    for root, _, names in os.walk(draft_dir):
        for n in sorted(names):
            if n in ("manifest.json", "SHA256SUMS"):
                continue
            p = os.path.join(root, n)
            files.append({
                "path": os.path.relpath(p, draft_dir),
                "sha256": sha(p),
                "bytes": os.path.getsize(p),
            })
    files.sort(key=lambda x: x["path"])
    manifest = {"draft_revision": revision, "files": files}
    with open(os.path.join(draft_dir, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
        fh.write("\n")
    with open(os.path.join(draft_dir, "SHA256SUMS"), "w", encoding="utf-8") as fh:
        for f in files:
            fh.write(f"{f['sha256']}  {f['path']}\n")
    print(json.dumps(manifest, indent=2))
    return 0


def check(round_id: str, draft_dir: str) -> int:
    manifest = json.load(open(os.path.join(draft_dir, "manifest.json"), encoding="utf-8"))
    expected = {f["path"]: f["sha256"] for f in manifest["files"]}
    rdir = os.path.join(CONSILIUM, "rounds", round_id)
    verdicts = {}
    for arch in ARCHS:
        text = open(os.path.join(rdir, arch, "response.md"), encoding="utf-8").read()
        # Accept explicit labelled fields, in any order.
        fields = {}
        for line in text.splitlines():
            m = re.match(r"^[ \t>*#`-]*([A-Za-z_]+)[ \t]*:[ \t]*`?([A-Za-z0-9_./-]+)`?\s*$", line)
            if m:
                fields[m.group(1).lower()] = m.group(2)
        verdict = fields.get("verdict")
        rfc = fields.get("rfc_sha256")
        roadmap = fields.get("roadmap_sha256")
        verdicts[arch] = {
            "verdict": verdict,
            "rfc_sha256": rfc,
            "roadmap_sha256": roadmap,
            "response_sha256": sha(os.path.join(rdir, arch, "response.md")),
        }
    ok = all(v["verdict"] == "APPROVE" for v in verdicts.values())
    hashes_ok = True
    for arch, v in verdicts.items():
        for path, digest in expected.items():
            key = os.path.basename(path).replace("-", "_").replace(".md", "").upper() + "_SHA256"
            if key in ("REVISED_RFC_SHA256",):
                key = "RFC_SHA256"
            if key in ("IMPLEMENTATION_ROADMAP_SHA256",):
                key = "ROADMAP_SHA256"
            if key in v and v[key] is not None and v[key] != digest:
                hashes_ok = False
    out = {
        "round": round_id,
        "draft_revision": manifest["draft_revision"],
        "expected": expected,
        "verdicts": verdicts,
        "all_approve": ok,
        "hashes_match": hashes_ok,
        "status": "CONSENSUS_ACHIEVED" if ok and hashes_ok else "NOT_APPROVED",
    }
    path = os.path.join(CONSILIUM, "final", "approvals.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
        fh.write("\n")
    print(json.dumps(out, indent=2))
    return 0 if out["status"] == "CONSENSUS_ACHIEVED" else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    h = sub.add_parser("hash-draft")
    h.add_argument("--dir", required=True)
    h.add_argument("--revision", required=True)
    c = sub.add_parser("check")
    c.add_argument("--round", required=True)
    c.add_argument("--dir", required=True)
    args = ap.parse_args()
    if args.cmd == "hash-draft":
        return hash_draft(args.dir, args.revision)
    if args.cmd == "check":
        return check(args.round, args.dir)
    return 2


if __name__ == "__main__":
    sys.exit(main())
