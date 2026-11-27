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
    with open(os.path.join(rdir, "manifest.json"), encoding="utf-8") as fh:
        barrier = json.load(fh)
    if barrier.get("barrier") != "closed":
        raise SystemExit("Final review round is not frozen")
    verdicts = {}
    for arch in ARCHS:
        path = os.path.join(rdir, arch, "response.md")
        if sha(path) != barrier["responses"][arch]["response_sha256"]:
            raise SystemExit(f"{arch}: final review hash differs from frozen response")
        text = open(path, encoding="utf-8").read()
        # Accept explicit labelled fields, in any order.
        fields = {}
        for line in text.splitlines():
            m = re.match(r"^[ \t>*#`-]*([A-Za-z_]+)[ \t]*:[ \t]*`?([A-Za-z0-9_./-]+)`?\s*$", line)
            if m:
                key = m.group(1).lower()
                if key in fields and fields[key] != m.group(2):
                    raise SystemExit(f"{arch}: conflicting final-review field: {key}")
                fields[key] = m.group(2)
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
    required = {"rfc_sha256": "revised-rfc.md", "roadmap_sha256": "implementation-roadmap.md"}
    hashes_ok = (
        all(path in expected for path in required.values())
        and all(sha(os.path.join(draft_dir, path)) == digest for path, digest in expected.items())
        and all(v[key] == expected[path] for v in verdicts.values() for key, path in required.items())
    )
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
