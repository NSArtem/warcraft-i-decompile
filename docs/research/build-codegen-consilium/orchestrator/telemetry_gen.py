#!/usr/bin/env python3
"""Deterministic telemetry generator for the Build & Codegen Consilium.

The campaign's earlier resource accounting was partly hand-edited, which let
cumulative provider counters be differenced in the wrong order (alphabetical by
round instead of chronological by start time) and let one failed invocation be
counted twice. This module rebuilds every derived telemetry file from the
authoritative per-attempt invocation records under ``rounds/`` only:

- one record per actual invocation, including failures;
- records deduplicated when a round slot copies an attempt record;
- records sorted by real ``start_utc`` before any cumulative delta;
- cumulative counters differenced only inside one native session;
- negative cost deltas rejected unless a documented provider reset says so;
- per-invocation and per-session token counters kept in separate columns.

Outputs (all derived, none hand-edited):

- ``telemetry/invocations.jsonl``      one authoritative record per attempt
- ``telemetry/resource-usage.csv``     completed invocations (responses of record)
- ``telemetry/failed-invocations.csv`` failed invocations (quota consumed, no response)
- ``telemetry/summary.json``           per-Architect totals and the delta ledger

Usage:
    python3 telemetry_gen.py --consilium DIR [--check]

``--check`` regenerates into memory and fails if the files on disk differ.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import sys

ARCHS = ["gpt", "claude", "gemini"]
COMPLETED = {"COMPLETED"}
# Cumulative token counters by provider, in the order they are differenced.
CUMULATIVE_TOKENS = {
    "gpt": ["input_tokens", "cached_input_tokens", "output_tokens", "reasoning_tokens"],
    "gemini": ["input_tokens", "uncached_input_tokens", "cached_input_tokens",
               "output_tokens", "thinking_tokens"],
    "claude": [],  # Claude reports per-invocation token usage; only cost is cumulative
}


def load(path, default=None):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def _iter_meta(consilium: str):
    rounds = os.path.join(consilium, "rounds")
    for root, _dirs, names in os.walk(rounds):
        if "meta.json" in names:
            yield os.path.join(root, "meta.json")


def collect(consilium: str) -> list[dict]:
    """Return one record per actual invocation, deduplicated and annotated."""
    by_key: dict[tuple, dict] = {}
    for path in _iter_meta(consilium):
        meta = load(path, {}) or {}
        arch = meta.get("architect")
        start = meta.get("start_utc")
        if arch not in ARCHS or not start:
            continue
        rec = dict(meta)
        rel = os.path.relpath(path, consilium)
        rec["_path"] = rel
        rec["_from_attempts"] = "/attempts/" in rel.replace(os.sep, "/")
        # The attempt tag is the directory name even when the meta left it null.
        if not rec.get("attempt") and rec["_from_attempts"]:
            rec["attempt"] = rel.replace(os.sep, "/").split("/attempts/", 1)[1].split("/", 1)[0]
        key = (arch, start)
        prev = by_key.get(key)
        # Prefer the attempt-scoped copy over a round-slot duplicate.
        if prev is None or (rec["_from_attempts"] and not prev["_from_attempts"]):
            by_key[key] = rec
    records = list(by_key.values())
    annotate(records)
    return records


def _num(v):
    return v if isinstance(v, (int, float)) else None


def annotate(records: list[dict]) -> None:
    """Add per-invocation deltas, differencing cumulative counters per session."""
    records.sort(key=lambda r: (r["start_utc"], r["architect"]))
    prev_cum: dict[tuple, dict] = {}
    for rec in records:
        arch = rec["architect"]
        sess = rec.get("session_id")
        usage = rec.get("usage") or {}
        bucket = (arch, sess)
        prev = prev_cum.setdefault(bucket, {})
        rec["usage_per_invocation"] = dict(usage)
        rec["cumulative"] = {}
        # Token counters.
        for field in CUMULATIVE_TOKENS.get(arch, []):
            cur = _num(usage.get(field))
            if cur is None:
                continue
            before = prev.get(field, 0)
            if cur < before:
                if rec.get("provider_counter_reset"):
                    delta = cur
                else:
                    raise ValueError(
                        f"negative delta for {arch} {field} at {rec.get('start_utc')} "
                        f"({rec.get('round')}/{rec.get('attempt')}): {cur} < {before}")
            else:
                delta = cur - before
            rec["usage_per_invocation"][field] = delta
            rec["cumulative"][field] = cur
            prev[field] = cur
        # Cumulative API-equivalent cost (Claude). Never a per-invocation charge.
        if "total_cost_usd" in usage and usage.get("total_cost_usd") is not None:
            cur = float(usage["total_cost_usd"])
            before = float(prev.get("total_cost_usd", 0.0))
            if cur < before - 1e-9:
                if rec.get("provider_counter_reset"):
                    delta = cur
                else:
                    raise ValueError(
                        f"negative cumulative-cost delta for {arch} at {rec.get('start_utc')} "
                        f"({rec.get('round')}/{rec.get('attempt')}): {cur} < {before}")
            else:
                delta = cur - before
            rec["cumulative"]["total_cost_usd"] = cur
            rec["usage_per_invocation"]["cost_delta_usd"] = round(delta, 10)
            prev["total_cost_usd"] = cur
        rec["status"] = rec.get("status") or (
            "COMPLETED" if rec.get("exit_code") == 0 and not rec.get("timed_out") else "FAILED")


def _quota(rec, key):
    q = rec.get("quota_after") or {}
    v = q.get(key)
    return "" if v is None else v


def _sorted(records):
    return sorted(records, key=lambda r: (r["start_utc"], r["architect"]))


def render(consilium: str) -> dict[str, str]:
    records = collect(consilium)
    completed = [r for r in _sorted(records) if r["status"] in COMPLETED]
    failed = [r for r in _sorted(records) if r["status"] not in COMPLETED]

    # invocations.jsonl: authoritative, one line per attempt.
    inv_lines = []
    for r in _sorted(records):
        row = {
            "round": r.get("round"), "architect": r["architect"], "attempt": r.get("attempt"),
            "status": r["status"], "start_utc": r["start_utc"], "end_utc": r.get("end_utc"),
            "wall_s": r.get("wall_s"), "session_id": r.get("session_id"),
            "session_was_resumed": r.get("session_was_resumed"),
            "prompt_sha256": r.get("prompt_sha256"), "response_sha256": r.get("response_sha256"),
            "model_observed": r.get("model_observed"), "effort_observed": r.get("effort_observed"),
            "usage": r.get("usage"), "usage_per_invocation": r.get("usage_per_invocation"),
            "cumulative": r.get("cumulative"), "quota_after": r.get("quota_after"),
            "api_error": r.get("api_error"), "source": r.get("_path"),
        }
        inv_lines.append(json.dumps(row, ensure_ascii=False, sort_keys=True))
    inv = "\n".join(inv_lines) + "\n"

    # resource-usage.csv: completed invocations.
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["round", "architect", "model", "effort", "wall_s", "input_tokens",
                "uncached_input_tokens", "cached_input_tokens", "output_tokens",
                "reasoning_tokens", "counter_scope", "token_provenance",
                "five_hour_used_percent", "seven_day_used_percent",
                "cost_delta_usd", "cumulative_cost_usd", "start_utc"])
    for r in completed:
        u = r["usage_per_invocation"]
        cu = r.get("cumulative") or {}
        scope = ("per_invocation (claude result usage)" if r["architect"] == "claude"
                 else f"per_invocation (delta of {'agy' if r['architect'] == 'gemini' else 'rollout'} cumulative)")
        prov = (r.get("usage") or {}).get("provenance", "")
        w.writerow([
            r.get("round"), r["architect"], r.get("model_observed") or "", r.get("effort_observed") or "",
            r.get("wall_s"), u.get("input_tokens", ""), u.get("uncached_input_tokens", ""),
            u.get("cached_input_tokens", ""), u.get("output_tokens", ""),
            u.get("reasoning_tokens", u.get("thinking_tokens", "")),
            scope, prov, _quota(r, "five_hour_used_percent"), _quota(r, "seven_day_used_percent"),
            ("" if "cost_delta_usd" not in u else f"{u['cost_delta_usd']:.6f}"),
            ("" if "total_cost_usd" not in cu else f"{cu['total_cost_usd']:.6f}"),
            r["start_utc"],
        ])
    usage_csv = buf.getvalue()

    # failed-invocations.csv: failures, cost delta preserved.
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["round", "architect", "attempt", "start_utc", "end_utc", "wall_s", "exit_code",
                "api_error", "input_tokens", "cached_input_tokens", "cache_creation_input_tokens",
                "output_tokens", "thinking_tokens", "api_equivalent_cost_usd",
                "cumulative_cost_usd", "outcome", "provenance"])
    for r in failed:
        u = r["usage_per_invocation"]
        cu = r.get("cumulative") or {}
        w.writerow([
            r.get("round"), r["architect"], r.get("attempt") or "", r["start_utc"], r.get("end_utc"),
            r.get("wall_s"), r.get("exit_code"), r.get("api_error") or "",
            u.get("input_tokens", ""), u.get("cached_input_tokens", ""),
            u.get("cache_creation_input_tokens", ""), u.get("output_tokens", ""),
            u.get("thinking_tokens", ""),
            ("" if "cost_delta_usd" not in u else f"{u['cost_delta_usd']:.6f}"),
            ("" if "total_cost_usd" not in cu else f"{cu['total_cost_usd']:.6f}"),
            "provider_error_no_response" if r.get("api_error") else "no_response",
            (r.get("usage") or {}).get("provenance", ""),
        ])
    failed_csv = buf.getvalue()

    # summary.json: per-Architect totals and the full delta ledger.
    summary = {"architects": {}, "counts": {}}
    for arch in ARCHS:
        rs = [r for r in _sorted(records) if r["architect"] == arch]
        comp = [r for r in rs if r["status"] in COMPLETED]
        fail = [r for r in rs if r["status"] not in COMPLETED]
        def total(rows, field):
            vals = [(r["usage_per_invocation"].get(field)) for r in rows]
            vals = [v for v in vals if isinstance(v, (int, float))]
            return sum(vals)
        sess = sorted({r.get("session_id") for r in rs if r.get("session_id")})
        summary["architects"][arch] = {
            "native_sessions": sess,
            "invocations": len(rs),
            "completed": len(comp),
            "failed": len(fail),
            "wall_s": round(sum((r.get("wall_s") or 0) for r in rs), 3),
            "input_tokens_total": total(rs, "input_tokens"),
            "cached_input_tokens_total": total(rs, "cached_input_tokens"),
            "output_tokens_total": total(rs, "output_tokens"),
            "reasoning_or_thinking_tokens_total": total(rs, "reasoning_tokens") + total(rs, "thinking_tokens"),
            "api_equivalent_cost_delta_usd_total": round(total(rs, "cost_delta_usd"), 6),
            "cost_deltas": [
                {"round": r.get("round"), "attempt": r.get("attempt"), "status": r["status"],
                 "start_utc": r["start_utc"], "cost_delta_usd": r["usage_per_invocation"].get("cost_delta_usd"),
                 "cumulative_cost_usd": (r.get("cumulative") or {}).get("total_cost_usd")}
                for r in rs if "cost_delta_usd" in r["usage_per_invocation"]],
        }
    summary["counts"] = {"invocations": len(records), "completed": len(completed), "failed": len(failed)}
    summary["note"] = ("Cumulative provider counters are differenced only within one native "
                       "session and only after sorting by start_utc. Claude total_cost_usd is a "
                       "cumulative API-equivalent estimate, not a per-invocation charge.")
    summary_text = json.dumps(summary, indent=2, ensure_ascii=False) + "\n"

    return {
        "telemetry/invocations.jsonl": inv,
        "telemetry/resource-usage.csv": usage_csv,
        "telemetry/failed-invocations.csv": failed_csv,
        "telemetry/summary.json": summary_text,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--consilium", required=True)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    outputs = render(args.consilium)
    rc = 0
    for rel, text in outputs.items():
        path = os.path.join(args.consilium, rel)
        if args.check:
            current = open(path, encoding="utf-8").read() if os.path.isfile(path) else None
            if current != text:
                print(f"[telemetry] DRIFT {rel}", file=sys.stderr)
                rc = 1
        else:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)
            print(f"[telemetry] wrote {rel}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
