"""Concurrency-safe campaign telemetry recorder and consolidator (Section 12)."""
import argparse
import csv
import datetime
import glob
import json
import os
import subprocess
import sys
import time
import uuid

from . import CAMPAIGN_ID, LEDGER_PATH, MAIN_REPO, MANAGER_SESSION_ID, STATE_ROOT, TELEMETRY_DIR


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def _streams_dir():
    d = os.path.join(STATE_ROOT, "streams")
    os.makedirs(d, exist_ok=True)
    return d


def write_event(event_type, payload):
    rec = {
        "event_id": f"{event_type}-{uuid.uuid4().hex[:12]}",
        "event_type": event_type,
        "timestamp_utc": utc_now(),
        "campaign_id": CAMPAIGN_ID,
    }
    rec.update(payload)
    fname = f"{event_type}_{int(time.time()*1000)}_{os.getpid()}_{uuid.uuid4().hex[:6]}.json"
    fpath = os.path.join(_streams_dir(), fname)
    tmp = fpath + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, indent=2)
    os.replace(tmp, fpath)
    return rec


def log_decision(action, rationale, *, exp_id=None, session_id=None, details=None):
    return write_event("manager_decision", {
        "action": action,
        "exp_id": exp_id,
        "session_id": session_id,
        "rationale": rationale,
        "details": details or {},
    })


def capture_quota_snapshot(trigger, *, exp_id=None, session_id=None, active_sessions=None):
    from wc1 import codex
    rl = codex.get_latest_rate_limits()
    snap = {
        "trigger": trigger,
        "exp_id": exp_id,
        "session_id": session_id,
        "active_sessions": list(active_sessions or []),
        "codex": {
            "provenance": "exact" if (rl and (rl.get("primary") or rl.get("secondary"))) else "unavailable",
            "observed_at": rl.get("observed_at") if rl else None,
            "source": rl.get("source") if rl else None,
            "plan_type": rl.get("plan_type") if rl else None,
            "primary_5h": rl.get("primary") if rl else None,
            "secondary_7d": rl.get("secondary") if rl else None,
        },
        "google_antigravity": {
            "provenance": "unavailable",
            "reason": "Antigravity CLI does not expose subscription quota percentages locally",
            "value": None,
        },
    }
    return write_event("quota_snapshot", snap)


def log_termination(session_id, role, model, exp_id, start_ts, end_ts, task_status,
                    resources, reason, initiator, successor_created=False,
                    successor_session_id=None, checkpoint=None, rationale=""):
    return write_event("session_termination", {
        "session_id": session_id,
        "role": role,
        "model": model,
        "exp_id": exp_id,
        "start_ts_utc": start_ts,
        "end_ts_utc": end_ts,
        "task_status": task_status,
        "resources": resources,
        "reason": reason,
        "initiator": initiator,
        "successor_created": bool(successor_created),
        "successor_session_id": successor_session_id,
        "checkpoint": checkpoint,
        "rationale": rationale,
    })


def extract_manager_antigravity_usage():
    """Extract exact Manager token usage and API timings from Antigravity transcript.jsonl."""
    tpath = (
        f"/home/artem/.gemini/antigravity-cli/brain/{MANAGER_SESSION_ID}"
        "/.system_generated/logs/transcript.jsonl"
    )
    if not os.path.isfile(tpath):
        return {"provenance": "unavailable", "reason": f"transcript not found at {tpath}"}
    in_tok = cached_tok = out_tok = reason_tok = 0
    reqs = tool_calls = 0
    first_ts = last_ts = None
    with open(tpath, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            ts = rec.get("timestamp") or rec.get("createdAt")
            if ts:
                if first_ts is None:
                    first_ts = ts
                last_ts = ts
            # Inspect common Antigravity usage fields without fabricating anything
            usage = rec.get("usage") or rec.get("tokenUsage") or {}
            if isinstance(usage, dict) and any(k in usage for k in ("inputTokens", "input_tokens", "promptTokenCount")):
                reqs += 1
                in_tok += int(usage.get("inputTokens") or usage.get("input_tokens") or usage.get("promptTokenCount") or 0)
                cached_tok += int(usage.get("cacheReadTokens") or usage.get("cachedContentTokenCount") or usage.get("cached_input_tokens") or 0)
                out_tok += int(usage.get("outputTokens") or usage.get("output_tokens") or usage.get("candidatesTokenCount") or 0)
                reason_tok += int(usage.get("thoughtsTokenCount") or usage.get("reasoningTokens") or usage.get("reasoning_tokens") or 0)
            if rec.get("type") in ("tool_call", "toolCall") or rec.get("toolCalls"):
                tcs = rec.get("toolCalls")
                tool_calls += len(tcs) if isinstance(tcs, list) else 1
    return {
        "session_id": MANAGER_SESSION_ID,
        "role": "manager",
        "provider": "google",
        "harness": "antigravity-cli",
        "model": "Gemini 4 Neon",
        "reasoning_effort": "high",
        "first_ts": first_ts,
        "last_ts": last_ts,
        "requests": reqs if reqs > 0 else None,
        "tool_calls": tool_calls if tool_calls > 0 else None,
        "input_tokens": in_tok if reqs > 0 else None,
        "cached_input_tokens": cached_tok if reqs > 0 else None,
        "output_tokens": out_tok if reqs > 0 else None,
        "reasoning_tokens": reason_tok if reqs > 0 else None,
        "provenance": "exact" if reqs > 0 else "unavailable",
        "note": "Extracted from Antigravity transcript.jsonl" if reqs > 0 else "Usage metadata not present in transcript.jsonl lines",
    }


def consolidate():
    os.makedirs(TELEMETRY_DIR, exist_ok=True)
    sdir = _streams_dir()
    files = sorted(glob.glob(os.path.join(sdir, "*.json")))
    sessions = []
    events = []
    quotas = []
    verifies = []
    terminations = []

    for fp in files:
        try:
            with open(fp, encoding="utf-8") as fh:
                rec = json.load(fh)
        except Exception:
            continue
        et = rec.get("event_type")
        if et == "agent_session":
            sessions.append(rec)
        elif et == "quota_snapshot":
            quotas.append(rec)
        elif et == "serialized_verify":
            verifies.append(rec)
            events.append(rec)
        elif et == "session_termination":
            terminations.append(rec)
            events.append(rec)
        else:
            events.append(rec)

    sessions.sort(key=lambda r: r.get("start_ts_utc") or "")
    events.sort(key=lambda r: r.get("timestamp_utc") or r.get("request_ts_utc") or "")
    quotas.sort(key=lambda r: r.get("timestamp_utc") or "")

    with open(os.path.join(TELEMETRY_DIR, "sessions.jsonl"), "w", encoding="utf-8") as fh:
        for s in sessions:
            fh.write(json.dumps(s, sort_keys=True) + "\n")
    with open(os.path.join(TELEMETRY_DIR, "events.jsonl"), "w", encoding="utf-8") as fh:
        for e in events:
            fh.write(json.dumps(e, sort_keys=True) + "\n")
    with open(os.path.join(TELEMETRY_DIR, "quota_snapshots.jsonl"), "w", encoding="utf-8") as fh:
        for q in quotas:
            fh.write(json.dumps(q, sort_keys=True) + "\n")

    # Reviews CSV
    rev_fields = [
        "session_id", "exp_id", "task_id", "model", "effort", "start_ts_utc", "end_ts_utc",
        "wall_s", "input_tokens", "cached_input_tokens", "output_tokens", "reasoning_tokens",
        "turns", "tool_calls", "verdict", "exit_code", "target_commits",
    ]
    with open(os.path.join(TELEMETRY_DIR, "reviews.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=rev_fields)
        w.writeheader()
        for s in sessions:
            if s.get("role") == "reviewer":
                w.writerow({
                    "session_id": s.get("session_id"),
                    "exp_id": s.get("exp_id"),
                    "task_id": s.get("task_id"),
                    "model": s.get("model"),
                    "effort": s.get("reasoning_effort"),
                    "start_ts_utc": s.get("start_ts_utc"),
                    "end_ts_utc": s.get("end_ts_utc"),
                    "wall_s": s.get("wall_s"),
                    "input_tokens": s.get("input_tokens"),
                    "cached_input_tokens": s.get("cached_input_tokens"),
                    "output_tokens": s.get("output_tokens"),
                    "reasoning_tokens": s.get("reasoning_tokens"),
                    "turns": s.get("turns"),
                    "tool_calls": s.get("tool_calls"),
                    "verdict": s.get("review_verdict"),
                    "exit_code": s.get("exit_code"),
                    "target_commits": ";".join(s.get("reviewed_commits") or []),
                })

    # Experiments CSV from ledger if present
    ledger = {}
    if os.path.isfile(LEDGER_PATH):
        with open(LEDGER_PATH, encoding="utf-8") as fh:
            ledger = json.load(fh)
    exp_fields = [
        "exp_id", "status", "scientific_outcome", "branch", "baseline_commit",
        "current_commit", "review_verdict", "integration_status",
        "dev_sessions", "rev_sessions", "total_wall_s", "total_input_tokens",
        "total_cached_tokens", "total_output_tokens", "total_reasoning_tokens",
    ]
    with open(os.path.join(TELEMETRY_DIR, "experiments.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=exp_fields)
        w.writeheader()
        for eid, edata in sorted((ledger.get("experiments") or {}).items()):
            esess = [s for s in sessions if s.get("exp_id") == eid]
            w.writerow({
                "exp_id": eid,
                "status": edata.get("status"),
                "scientific_outcome": edata.get("scientific_outcome"),
                "branch": edata.get("branch"),
                "baseline_commit": edata.get("baseline_commit"),
                "current_commit": edata.get("current_commit"),
                "review_verdict": edata.get("review_verdict"),
                "integration_status": edata.get("integration_status"),
                "dev_sessions": sum(1 for s in esess if s.get("role") == "developer"),
                "rev_sessions": sum(1 for s in esess if s.get("role") == "reviewer"),
                "total_wall_s": round(sum(float(s.get("wall_s") or 0) for s in esess), 2),
                "total_input_tokens": sum(int(s.get("input_tokens") or 0) for s in esess),
                "total_cached_tokens": sum(int(s.get("cached_input_tokens") or 0) for s in esess),
                "total_output_tokens": sum(int(s.get("output_tokens") or 0) for s in esess),
                "total_reasoning_tokens": sum(int(s.get("reasoning_tokens") or 0) for s in esess),
            })

    # Campaign summary JSON
    head_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=MAIN_REPO, capture_output=True, text=True).stdout.strip()
    mgr_usage = extract_manager_antigravity_usage()
    campaign = {
        "campaign_id": CAMPAIGN_ID,
        "generated_at_utc": utc_now(),
        "rfc_commit": "6f319ac8ff780bb45ff028d006216016fc932a13",
        "main_baseline_commit": "e14d5c0a5d37d2f85ffcfcc311008004bb5c40da",
        "campaign_branch": "research/build-codegen-experiments",
        "current_head_commit": head_sha,
        "model_configuration": {
            "manager": {"provider": "google", "harness": "antigravity-cli", "model": "Gemini 4 Neon", "effort": "high"},
            "developer": {"provider": "openai", "harness": "codex-cli 0.172.0", "model": "gpt-6.1-sol", "effort": "high"},
            "reviewer": {"provider": "openai", "harness": "codex-cli 0.172.0", "model": "gpt-6.1-sol", "effort": "high"},
        },
        "manager_telemetry": mgr_usage,
        "counts": {
            "agent_sessions": len(sessions),
            "developer_sessions": sum(1 for s in sessions if s.get("role") == "developer"),
            "reviewer_sessions": sum(1 for s in sessions if s.get("role") == "reviewer"),
            "forced_terminations": sum(1 for t in terminations if t.get("initiator") == "manager"),
            "session_replacements": sum(1 for t in terminations if t.get("successor_created")),
            "verify_runs": len(verifies),
            "quota_snapshots": len(quotas),
        },
        "totals_subagents": {
            "sum_wall_s": round(sum(float(s.get("wall_s") or 0) for s in sessions), 2),
            "sum_tool_exec_s": round(sum(float(s.get("tool_exec_s") or 0) for s in sessions), 2),
            "sum_verify_s": round(sum(float(v.get("duration_s") or 0) for v in verifies), 2),
            "sum_verify_wait_s": round(sum(float(v.get("wait_s") or 0) for v in verifies), 2),
            "input_tokens": sum(int(s.get("input_tokens") or 0) for s in sessions),
            "cached_input_tokens": sum(int(s.get("cached_input_tokens") or 0) for s in sessions),
            "output_tokens": sum(int(s.get("output_tokens") or 0) for s in sessions),
            "reasoning_tokens": sum(int(s.get("reasoning_tokens") or 0) for s in sessions),
            "turns": sum(int(s.get("turns") or 0) for s in sessions),
            "tool_calls": sum(int(s.get("tool_calls") or 0) for s in sessions),
        },
        "initial_quota": quotas[0] if quotas else None,
        "latest_quota": quotas[-1] if quotas else None,
        "ledger": ledger,
    }
    with open(os.path.join(TELEMETRY_DIR, "campaign.json"), "w", encoding="utf-8") as fh:
        json.dump(campaign, fh, indent=2)
    return campaign


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("consolidate")
    q = sub.add_parser("quota")
    q.add_argument("--trigger", required=True)
    q.add_argument("--exp", default=None)
    q.add_argument("--session-id", default=None)
    d = sub.add_parser("decision")
    d.add_argument("--action", required=True)
    d.add_argument("--rationale", required=True)
    d.add_argument("--exp", default=None)
    d.add_argument("--session-id", default=None)
    args = ap.parse_args()
    if args.cmd == "consolidate":
        c = consolidate()
        print(json.dumps(c["counts"]))
    elif args.cmd == "quota":
        s = capture_quota_snapshot(args.trigger, exp_id=args.exp, session_id=args.session_id)
        print(json.dumps(s))
    elif args.cmd == "decision":
        r = log_decision(args.action, args.rationale, exp_id=args.exp, session_id=args.session_id)
        print(json.dumps(r))


if __name__ == "__main__":
    main()
