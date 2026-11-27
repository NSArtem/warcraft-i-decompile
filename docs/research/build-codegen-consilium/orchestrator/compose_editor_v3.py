#!/usr/bin/env python3
"""Compose the reassigned RFC Editor package for draft revision 3 (Architect A).

The owner reassigned the RFC Editor role from Architect B to Architect A after B
exhausted its subscription window mid-draft. This script assembles a private,
fully hashed inbox for Architect A containing:

- frozen revision 2 (all seven files);
- Architect B's preserved partial revision 3 (all seven files, read-only copy);
- the three exact revision-2 approval responses;
- the canonical decision ledger and the relevant manifests;
- the original revision 3 assignment prompt and the failed invocation record.

Nothing is summarised or rewritten. The prompt is rendered from
``rounds/editor-v3/prompt-gpt-template.md`` and the package is indexed in
``MANIFEST.json`` + ``SHA256SUMS``.

Usage: compose_editor_v3.py [--round editor-v3]
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(__file__))
import run_architect as ra  # noqa: E402

ARCH = "gpt"
V2 = "final/drafts/v2"
PARTIAL = "rounds/editor-v3/claude/partial-draft"
APPROVAL = "rounds/approval"
FAILED = "rounds/editor-v3/claude/attempts/01-provider-rate-limit"
ORIGINAL_PROMPT = "rounds/editor/prompt-claude-v3.md"
LEDGER_SHA = "dc6bda93ea7f3cf2b1506f481600b12af6a357c3fa9a84beb8208bbb39b4e97a"
DRAFT_FILES = ["revised-rfc.md", "implementation-roadmap.md",
               "experimental-interpretation.md", "decision-rationale.md",
               "decision-ledger.json", "deferred-questions.md",
               "editorial-notes.md"]


def load(path, default=None):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", default="editor-v3")
    ap.add_argument("--timeout", type=int, default=5400)
    args = ap.parse_args()

    C = ra.CONSILIUM
    cfg = ra.ARCHITECTS[ARCH]
    inbox = os.path.join(cfg["runtime"], f"{args.round}-inbox")

    # --- Validate sources before copying -----------------------------------
    v2_manifest = load(os.path.join(C, V2, "manifest.json"), {}) or {}
    if v2_manifest.get("draft_revision") != "2":
        raise SystemExit("revision 2 manifest missing or wrong revision")
    expected_v2 = {f["path"]: f["sha256"] for f in v2_manifest.get("files", [])}
    for name in DRAFT_FILES:
        p = os.path.join(C, V2, name)
        if ra.sha256_file(p) != expected_v2.get(name):
            raise SystemExit(f"revision 2 file hash mismatch: {name}")
    if ra.sha256_file(os.path.join(C, V2, "decision-ledger.json")) != LEDGER_SHA:
        raise SystemExit("revision 2 canonical ledger identity mismatch")
    if ra.sha256_file(os.path.join(C, PARTIAL, "decision-ledger.json")) != LEDGER_SHA:
        raise SystemExit("partial revision 3 ledger is not byte-identical to the canonical ledger")

    approval_manifest = load(os.path.join(C, APPROVAL, "manifest.json"), {}) or {}
    if approval_manifest.get("barrier") != "closed":
        raise SystemExit("approval round is not frozen")
    for arch in ("gpt", "claude", "gemini"):
        p = os.path.join(C, APPROVAL, arch, "response.md")
        if ra.sha256_file(p) != approval_manifest["responses"][arch]["response_sha256"]:
            raise SystemExit(f"approval/{arch} response hash mismatch")

    # --- Rebuild the inbox from scratch ------------------------------------
    if os.path.isdir(inbox):
        shutil.rmtree(inbox)
    os.makedirs(inbox)
    entries = []

    def add(relpath: str, data: bytes, content: str) -> None:
        dst = os.path.join(inbox, relpath)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "wb") as fh:
            fh.write(data)
        entries.append({"path": relpath, "sha256": ra.sha256_bytes(data),
                        "bytes": len(data), "content": content})

    def copy(relpath: str, src: str, content: str) -> None:
        with open(src, "rb") as fh:
            add(relpath, fh.read(), content)

    # Canonical ledger and revision 2 package.
    add("00-CANONICAL-LEDGER-v2.json",
        open(os.path.join(C, V2, "decision-ledger.json"), "rb").read(),
        "Canonical decision ledger, byte-identical to revision 2; the Editor must preserve it byte-for-byte")
    copy("01-DRAFT-V2-MANIFEST.json", os.path.join(C, V2, "manifest.json"),
         "Frozen revision 2 manifest with per-file SHA-256")
    copy("02-DRAFT-V2-SHA256SUMS.txt", os.path.join(C, V2, "SHA256SUMS"),
         "Frozen revision 2 SHA256SUMS")
    for name in DRAFT_FILES:
        copy(f"v2/{name}", os.path.join(C, V2, name),
             f"Frozen revision 2 file: {name}")
    for name in DRAFT_FILES:
        copy(f"partial-v3/{name}", os.path.join(C, PARTIAL, name),
             f"Architect B's preserved partial revision 3 file: {name} (read-only)")

    # Partial-draft manifest computed from the preserved files.
    partial_files = [{"path": n, "sha256": ra.sha256_file(os.path.join(C, PARTIAL, n)),
                      "bytes": os.path.getsize(os.path.join(C, PARTIAL, n))}
                     for n in DRAFT_FILES]
    add("05-PARTIAL-DRAFT-MANIFEST.json",
        (json.dumps({"source": PARTIAL, "files": partial_files}, indent=2) + "\n").encode("utf-8"),
        "Hashes of Architect B's preserved partial revision 3 (seven files)")

    # Exact approval responses.
    for arch in ("gpt", "claude", "gemini"):
        copy(f"approval/{arch}-response.md", os.path.join(C, APPROVAL, arch, "response.md"),
             f"Exact revision-2 approval response of Architect {ra.ARCHITECTS[arch]['identity']} — {ra.ARCHITECTS[arch]['display']}")

    # Original assignment and failed invocation record.
    copy("03-ORIGINAL-ASSIGNMENT-prompt-claude-v3.md", os.path.join(C, ORIGINAL_PROMPT),
         "The original revision 3 editor assignment given to Architect B")
    copy("04-FAILED-ATTEMPT-01/meta.json", os.path.join(C, FAILED, "meta.json"),
         "Metadata of Architect B's failed revision 3 invocation (provider rate limit)")
    copy("04-FAILED-ATTEMPT-01/response.md", os.path.join(C, FAILED, "response.md"),
         "Provider error text recorded for the failed invocation")

    # --- Manifest and checksums --------------------------------------------
    entries.sort(key=lambda e: e["path"])
    manifest = {
        "round": args.round,
        "reassigned_editor": ARCH,
        "previous_editor": "claude",
        "draft_revision": "3",
        "canonical_ledger_sha256": LEDGER_SHA,
        "v2_manifest_sha256": ra.sha256_file(os.path.join(C, V2, "manifest.json")),
        "files": entries,
    }
    ra.write_json(os.path.join(inbox, "MANIFEST.json"), manifest)
    with open(os.path.join(inbox, "SHA256SUMS"), "w", encoding="utf-8") as fh:
        for e in entries:
            fh.write(f"{e['sha256']}  {e['path']}\n")

    # --- Render the prompt --------------------------------------------------
    template_path = os.path.join(C, "rounds", args.round, "prompt-gpt-template.md")
    template = open(template_path, encoding="utf-8").read()
    index = "\n".join(
        f"{i}. `{e['path']}` — {e['bytes']} bytes — SHA-256 `{e['sha256']}` — {e['content']}"
        for i, e in enumerate(entries, 1))
    launch_epoch = int(ra.time.time()) + 20
    prompt = ra.render(template, ARCH, args.timeout, launch_epoch, extra={
        "PACKAGE_INDEX": index,
        "LEDGER_SHA256": LEDGER_SHA,
        "V2_MANIFEST_SHA256": manifest["v2_manifest_sha256"],
    })
    round_dir = os.path.join(C, "rounds", args.round)
    prompt_path = os.path.join(round_dir, f"prompt-{ARCH}.md")
    with open(prompt_path, "w", encoding="utf-8") as fh:
        fh.write(prompt)

    ra.write_json(os.path.join(round_dir, "composition-gpt.json"), {
        "round": args.round, "editor": ARCH, "previous_editor": "claude",
        "editor_model": cfg["model_id"], "editor_effort": cfg["effort"],
        "template": os.path.relpath(template_path, ra.SEC),
        "timeout_s": args.timeout,
        "prompt_sha256": ra.sha256_bytes(prompt.encode("utf-8")),
        "prompt_bytes": len(prompt.encode("utf-8")),
        "inbox": inbox,
        "package_manifest_sha256": ra.sha256_file(os.path.join(inbox, "MANIFEST.json")),
        "canonical_ledger_sha256": LEDGER_SHA,
        "package": entries,
    })
    print(f"composed reassigned editor package: {len(entries)} files, "
          f"prompt {ra.sha256_bytes(prompt.encode('utf-8'))[:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
