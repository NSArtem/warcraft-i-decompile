#!/usr/bin/env python3
"""Compose per-Architect cross-review prompts from frozen prior-round responses.

This script performs no interpretation. It copies each response verbatim into a
delimited block, records its SHA-256, and renders the round template for each
Architect with the *other two* responses. It refuses to run unless the prior
round manifest is closed and every response hash matches.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import run_architect as ra  # noqa: E402


def load_frozen(round_id: str) -> dict:
    rdir = os.path.join(ra.CONSILIUM, "rounds", round_id)
    manifest_path = os.path.join(rdir, "manifest.json")
    manifest = ra.load_json(manifest_path)
    if not manifest or manifest.get("barrier") != "closed":
        raise SystemExit(f"{manifest_path}: prior round is not frozen/closed")
    for arch in ra.ARCHITECTS:
        path = os.path.join(rdir, arch, "response.md")
        with open(path, "rb") as fh:
            body = fh.read()
        digest = ra.sha256_bytes(body)
        recorded = (manifest.get("responses", {}).get(arch) or {}).get("response_sha256")
        if digest != recorded:
            raise SystemExit(f"{arch}: response hash mismatch ({digest} != {recorded})")
    return manifest


def block(arch: str, text: str, digest: str) -> str:
    cfg = ra.ARCHITECTS[arch]
    label = f"ARCHITECT {cfg['identity']} — {cfg['display'].upper()}"
    head = (
        f"===== BEGIN COMPLETE ORIGINAL POSITION — {label} "
        f"(model {cfg['model_id']}, sha256 {digest}, {len(text.encode('utf-8'))} bytes) =====\n"
    )
    tail = (
        f"\n===== END COMPLETE ORIGINAL POSITION — {label} "
        f"(sha256 {digest}) =====\n"
    )
    return head + text.rstrip("\n") + tail


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="src", required=True)
    ap.add_argument("--to", dest="dst", required=True)
    ap.add_argument("--template", required=True)
    ap.add_argument("--timeout", type=int, default=4500)
    args = ap.parse_args()

    manifest = load_frozen(args.src)
    src_dir = os.path.join(ra.CONSILIUM, "rounds", args.src)
    dst_dir = os.path.join(ra.CONSILIUM, "rounds", args.dst)
    os.makedirs(dst_dir, exist_ok=True)
    with open(args.template, encoding="utf-8") as fh:
        template = fh.read()

    texts = {}
    digests = {}
    for arch in ra.ARCHITECTS:
        with open(os.path.join(src_dir, arch, "response.md"), encoding="utf-8") as fh:
            texts[arch] = fh.read()
        digests[arch] = manifest["responses"][arch]["response_sha256"]

    launch_epoch = int(ra.time.time()) + 20
    composed = {}
    for arch in ra.ARCHITECTS:
        others = [a for a in ra.ARCHITECTS if a != arch]
        payload = "\n\n".join(block(a, texts[a], digests[a]) for a in others)
        prompt = ra.render(template, arch, args.timeout, launch_epoch,
                           extra={"OTHER_POSITIONS": payload})
        with open(os.path.join(dst_dir, f"prompt-{arch}.md"), "w", encoding="utf-8") as fh:
            fh.write(prompt)
        composed[arch] = {
            "sha256": ra.sha256_bytes(prompt.encode("utf-8")),
            "bytes": len(prompt.encode("utf-8")),
            "receives": others,
            "received_hashes": {a: digests[a] for a in others},
        }

    ra.write_json(os.path.join(dst_dir, "composition.json"), {
        "from_round": args.src,
        "to_round": args.dst,
        "source_manifest_sha256": ra.sha256_file(os.path.join(src_dir, "manifest.json")),
        "template": os.path.relpath(args.template, ra.SEC),
        "timeout_s": args.timeout,
        "prompts": composed,
    })
    print(f"composed {args.dst} from {args.src}: " +
          ", ".join(f"{a}={composed[a]['sha256'][:12]}" for a in composed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
