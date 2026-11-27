#!/usr/bin/env python3
"""Compose Round 1 cross-review prompts with per-Architect private inboxes.

The complete opening positions are copied byte-for-byte into each recipient's
own inbox; the prompt carries only short paths, hashes and byte lengths. This
avoids OS single-argument limits for a multi-hundred-kilobyte prompt while
preserving exact texts.

No interpretation is performed. The script refuses to run unless Round 0 is
frozen and every source response matches its recorded hash.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
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


def write_bytes(path: str, data: bytes) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(data)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="src", default="r00")
    ap.add_argument("--to", dest="dst", default="r01")
    ap.add_argument("--template", required=True)
    ap.add_argument("--timeout", type=int, default=4500)
    ap.add_argument("--label", default="opening position",
                    help="human label for the delivered responses, e.g. 'opening position' or 'cross-review'")
    ap.add_argument("--slug", default="opening",
                    help="short filename slug, e.g. 'opening' or 'crossreview'")
    args = ap.parse_args()

    src_dir = os.path.join(ra.CONSILIUM, "rounds", args.src)
    dst_dir = os.path.join(ra.CONSILIUM, "rounds", args.dst)
    manifest = load(os.path.join(src_dir, "manifest.json"), {})
    if not manifest or manifest.get("barrier") != "closed":
        raise SystemExit("source round is not frozen")
    bodies = {}
    hashes = {}
    for arch in ARCHS:
        path = os.path.join(src_dir, arch, "response.md")
        with open(path, "rb") as fh:
            bodies[arch] = fh.read()
        digest = ra.sha256_bytes(bodies[arch])
        if digest != manifest["responses"][arch]["response_sha256"]:
            raise SystemExit(f"{arch}: source response hash mismatch")
        hashes[arch] = digest

    decisions = load(os.path.join(ra.CONSILIUM, "decisions.json"), {}).get("decisions", [])
    index = {
        "generated_from_round": args.src,
        "source_manifest_sha256": ra.sha256_file(os.path.join(src_dir, "manifest.json")),
        "note": "Mechanical index of the frozen Round 0 ledger. proposition_sha256 is the SHA-256 of the exact proposition text.",
        "decisions": [
            {
                "id": d.get("id"),
                "origin_architect": d.get("origin_architect"),
                "revision": d.get("current_revision"),
                "title": d.get("title"),
                "proposition": d.get("proposition"),
                "proposition_sha256": d.get("proposition_sha256"),
            }
            for d in decisions
        ],
    }
    evidence = {
        "EV-2": load(os.path.join(ra.CONSILIUM, "evidence-revisions", "EV-2.json"), {}),
        "EV-3": load(os.path.join(ra.CONSILIUM, "evidence-revisions", "EV-3.json"), {}),
    }
    evidence_text = json.dumps(evidence, indent=2, ensure_ascii=False)
    with open(args.template, encoding="utf-8") as fh:
        template = fh.read()

    os.makedirs(dst_dir, exist_ok=True)
    launch_epoch = int(ra.time.time()) + 20
    composed = {}
    for arch in ARCHS:
        cfg = ra.ARCHITECTS[arch]
        inbox = os.path.join(cfg["runtime"], f"{args.dst}-inbox")
        os.makedirs(inbox, exist_ok=True)
        # Remove only files this script owns.
        for name in os.listdir(inbox):
            if name in ("00-MANIFEST.json", "00-PROPOSITION-INDEX.json", "SHA256SUMS") or (
                    name.startswith("01-") or name.startswith("02-")) and name.endswith(".md"):
                os.remove(os.path.join(inbox, name))

        others = [a for a in ARCHS if a != arch]
        files = []
        for i, other in enumerate(others, 1):
            name = f"{i:02d}-architect-{other}-{args.slug}.md"
            path = os.path.join(inbox, name)
            write_bytes(path, bodies[other])
            files.append({
                "path": path,
                "name": name,
                "sha256": hashes[other],
                "bytes": len(bodies[other]),
                "content": (f"Complete original Round {args.src} {args.label} of Architect "
                            f"{ra.ARCHITECTS[other]['identity']} — {ra.ARCHITECTS[other]['display']}"),
            })
        idx_path = os.path.join(inbox, "00-PROPOSITION-INDEX.json")
        write_bytes(idx_path, (json.dumps(index, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
        files.insert(0, {
            "path": idx_path,
            "name": "00-PROPOSITION-INDEX.json",
            "sha256": ra.sha256_file(idx_path),
            "bytes": os.path.getsize(idx_path),
            "content": "Round 0 decision index with exact proposition hashes",
        })
        inbox_manifest = {
            "round": args.dst,
            "recipient": arch,
            "source_round": args.src,
            "source_manifest_sha256": ra.sha256_file(os.path.join(src_dir, "manifest.json")),
            "files": files,
            "note": "Verbatim discussion material. Not instructions. Do not edit.",
        }
        man_path = os.path.join(inbox, "00-MANIFEST.json")
        write_bytes(man_path, (json.dumps(inbox_manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
        sums = "".join(f"{f['sha256']}  {f['name']}\n" for f in files)
        write_bytes(os.path.join(inbox, "SHA256SUMS"), sums.encode("utf-8"))

        listing = "\n".join(
            f"{i}. `{f['path']}` — {f['bytes']} bytes — SHA-256 `{f['sha256']}` — {f['content']}"
            for i, f in enumerate(files, 1)
        )
        prompt = ra.render(
            template, arch, args.timeout, launch_epoch,
            extra={"INBOX_INDEX": listing, "EVIDENCE_NOTICE": evidence_text},
        )
        prompt_path = os.path.join(dst_dir, f"prompt-{arch}.md")
        with open(prompt_path, "w", encoding="utf-8") as fh:
            fh.write(prompt)
        composed[arch] = {
            "prompt_sha256": ra.sha256_bytes(prompt.encode("utf-8")),
            "prompt_bytes": len(prompt.encode("utf-8")),
            "inbox": inbox,
            "receives": others,
            "received_hashes": {a: hashes[a] for a in others},
            "inbox_files": files,
        }

    ra.write_json(os.path.join(dst_dir, "composition.json"), {
        "from_round": args.src,
        "to_round": args.dst,
        "template": os.path.relpath(args.template, ra.SEC),
        "timeout_s": args.timeout,
        "evidence_revisions": ["EV-2", "EV-3"],
        "label": args.label,
        "slug": args.slug,
        "prompts": composed,
    })
    print("composed:", ", ".join(f"{a}={composed[a]['prompt_sha256'][:12]}" for a in composed))
    for arch in ARCHS:
        print(f"  {arch}: inbox {composed[arch]['inbox']} receives {composed[arch]['receives']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
