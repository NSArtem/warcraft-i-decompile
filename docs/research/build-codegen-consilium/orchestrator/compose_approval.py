#!/usr/bin/env python3
"""Deliver one immutable RFC/roadmap draft to all three Architects for final approval.

Copies the exact draft files into each Architect's private inbox and renders a
short review prompt with hashes and paths. No draft content is paraphrased.
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--draft-dir", required=True)
    ap.add_argument("--revision", required=True)
    ap.add_argument("--round", required=True)
    ap.add_argument("--timeout", type=int, default=2400)
    ap.add_argument("--prior-dir", default=None,
                    help="optional dir of per-Architect prior review material: <prior-dir>/<arch>/...")
    ap.add_argument("--notes", default=None,
                    help="optional JSON file mapping architect -> a short note for the prompt")
    ap.add_argument("--only", action="append", choices=ARCHS,
                    help="compose only for these Architects (repeatable)")
    args = ap.parse_args()

    manifest_path = os.path.join(args.draft_dir, "manifest.json")
    manifest = load(manifest_path, {})
    if not manifest or manifest.get("draft_revision") != args.revision:
        raise SystemExit("draft manifest missing or revision mismatch; run finalize.py hash-draft first")
    files = []
    for f in manifest["files"]:
        p = os.path.join(args.draft_dir, f["path"])
        with open(p, "rb") as fh:
            data = fh.read()
        if ra.sha256_bytes(data) != f["sha256"]:
            raise SystemExit(f"draft file hash mismatch: {p}")
        files.append(f)
    by_name = {os.path.basename(f["path"]): f for f in files}
    if "revised-rfc.md" not in by_name or "implementation-roadmap.md" not in by_name:
        raise SystemExit("draft must contain revised-rfc.md and implementation-roadmap.md")

    template_path = os.path.join(ra.CONSILIUM, "final", "approval-template.md")
    with open(template_path, encoding="utf-8") as fh:
        template = fh.read()

    dst_dir = os.path.join(ra.CONSILIUM, "rounds", args.round)
    os.makedirs(dst_dir, exist_ok=True)
    notes = {}
    if args.notes and os.path.isfile(args.notes):
        notes = load(args.notes, {}) or {}
    launch_epoch = int(ra.time.time()) + 20
    composed = {}
    archs = [a for a in ARCHS if not args.only or a in args.only]
    for arch in archs:
        cfg = ra.ARCHITECTS[arch]
        inbox = os.path.join(cfg["runtime"], f"{args.round}-inbox")
        os.makedirs(inbox, exist_ok=True)
        for name in os.listdir(inbox):
            if name == "00-MANIFEST.json" or name == "SHA256SUMS" or name.startswith("draft-"):
                p = os.path.join(inbox, name)
                shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
            elif name == "prior":
                shutil.rmtree(os.path.join(inbox, name), ignore_errors=True)
        entries = []
        for f in files:
            name = "draft-" + os.path.basename(f["path"])
            dst = os.path.join(inbox, name)
            shutil.copyfile(os.path.join(args.draft_dir, f["path"]), dst)
            entries.append({"path": dst, "name": name, "sha256": f["sha256"],
                            "bytes": f["bytes"], "content": "Immutable draft file"})
        prior_entries = []
        if args.prior_dir:
            pdir = os.path.join(args.prior_dir, arch)
            if os.path.isdir(pdir):
                for root, _dirs, names in os.walk(pdir):
                    for n in sorted(names):
                        src = os.path.join(root, n)
                        rel = os.path.relpath(src, pdir)
                        dst = os.path.join(inbox, "prior", rel)
                        os.makedirs(os.path.dirname(dst), exist_ok=True)
                        shutil.copyfile(src, dst)
                        prior_entries.append({
                            "path": dst, "name": os.path.join("prior", rel),
                            "sha256": ra.sha256_file(src), "bytes": os.path.getsize(src),
                            "content": "Prior review material"})
        note = (notes.get(arch) or "").strip()
        prior_material = ""
        if note or prior_entries:
            prior_material = "## 1b. Prior review material\n\n"
            if note:
                prior_material += note + "\n\n"
            for e in prior_entries:
                prior_material += (f"- `{e['path']}` — {e['bytes']} bytes — "
                                   f"SHA-256 `{e['sha256']}` — {e['content']}\n")
        idx = "\n".join(
            f"{i}. `{e['path']}` — {e['bytes']} bytes — SHA-256 `{e['sha256']}` — {e['content']}"
            for i, e in enumerate(entries, 1)
        )
        changelogs = [e for e in entries if "CHANGELOG" in e["name"].upper()]
        if changelogs:
            idx += ("\n\nThis revision carries a change log listing every change against the "
                    "previous revision:\n" + "\n".join(
                        f"- `{e['path']}` — SHA-256 `{e['sha256']}`" for e in changelogs))
        prompt = ra.render(template, arch, args.timeout, launch_epoch, extra={
            "DRAFT_REVISION": args.revision,
            "RFC_SHA256": by_name["revised-rfc.md"]["sha256"],
            "ROADMAP_SHA256": by_name["implementation-roadmap.md"]["sha256"],
            "MANIFEST_SHA256": ra.sha256_file(manifest_path),
            "DRAFT_TEXT": idx,
            "PRIOR_MATERIAL": prior_material,
        })
        prompt_path = os.path.join(dst_dir, f"prompt-{arch}.md")
        with open(prompt_path, "w", encoding="utf-8") as fh:
            fh.write(prompt)
        composed[arch] = {"prompt_sha256": ra.sha256_bytes(prompt.encode("utf-8")),
                          "prompt_bytes": len(prompt.encode("utf-8")),
                          "inbox": inbox, "files": entries, "prior": prior_entries}
    ra.write_json(os.path.join(dst_dir, "composition.json"), {
        "round": args.round, "draft_revision": args.revision,
        "draft_manifest_sha256": ra.sha256_file(manifest_path),
        "prior_dir": os.path.relpath(args.prior_dir, ra.SEC) if args.prior_dir else None,
        "notes": os.path.relpath(args.notes, ra.SEC) if args.notes else None,
        "timeout_s": args.timeout, "prompts": composed,
    })
    print(f"composed final approval {args.round} for draft {args.revision}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
