"""Zero-supervisor overnight runner for wc1.batch_driver on Claude Pro.

Runs unattended across the ROI-ordered M2 backlog (Wave 2 `c-only`, then Wave 3
`full`) without any long-lived LLM supervisor:

  1. Builds the live queue from `wc1.progress` (chunking large modules).
  2. Enforces a fractional 5-hour rolling window budget `--window-budget` in
     (0.0, 1.0] using live Claude `five_hour` / `seven_day` quota events from
     `build/live/rate_limits.json` with fallback to the rolling ledger.
     (1.0 = use the full Pro window until rate-limited, then sleep until
     recovery and continue).
  3. Invokes stateless `wc1.batch_driver` for each module/chunk and atomically
     publishes live state to `build/live/state.json` for `wc1.tui`.
  4. Runs `make verify`. On failure, optionally invokes ONE bounded, isolated
     `claude -p` streaming repair pass scoped strictly to that module's files,
     then re-runs `make verify`.
  5. If green, commits ONLY the files changed/created by that module atomically.
     If still failing, archives those files into `build/failed/<tag>/`, cleanly
     rolls back only that module's changes (never touching pre-existing
     untracked WIP such as `BULLET.C`), and moves on to the next module.

Usage:
    nix develop -c python3 -m wc1.overnight                # interactive TUI launcher (TTY)
    nix develop -c python3 -m wc1.overnight --tui          # start & attach dashboard
    nix develop -c python3 -m wc1.overnight --headless     # pure CLI backend
    nix develop -c python3 -m wc1.overnight --dry-run      # preview queue & spend
"""
import argparse
from collections import defaultdict
import datetime
import glob
import json
import os
import stat
import posixpath
import re
import select
import shutil
import signal
import subprocess
import sys
import threading
import time
from zoneinfo import ZoneInfo

from . import analysis, batch_driver, codex, live, match, path, progress, symbols

WINDOW_SECONDS = 5 * 3600
SEVEN_DAY_SECONDS = 7 * 24 * 3600
# PLAYFLIC.C: IntroOpPlaySound/IntroOpSyncSound match locally but cannot be
# built from C until 0x231cc/0x231ec match too (shared epilogue; playflic.md).
DEFAULT_SKIP = ("BULLET.C", "STATUS.C", "PLAYFLIC.C")

# Existing project headers mapped by module name (so c-only and full reuse them)
KNOWN_HEADERS = {
    "mod_13f60": "src/include/mod_13f60.h",
    "mod_16390": "src/include/mod_16390.h",
    "mod_2c4e0": "src/include/game_2c4e0.h",
    "mod_20c30": "src/include/mod_20c30.h",
    "PLACEBOX.C": "src/include/mod_20c30.h",
    "SAVE.C": "src/include/save_score.h",
    "SCORE.C": "src/include/save_score.h",
    "SND.C": "src/include/audio.h",
    "PLAYFLIC.C": "src/include/playflic.h",
    "flic_decode": "src/include/playflic.h",
    "mod_2efd0": "src/include/mod_2efd0.h",
    "STATUS.C": "src/include/status.h",
    "GAMEDLG.C": "src/include/gamedlg.h",
    "INIT.C": "src/include/war.h",
    "mod_104b0": "src/include/mod_104b0.h",
    "mod_1b800": "src/include/mod_1b800.h",
    "mod_295d0": "src/include/mod_295d0.h",
    "mod_2b8e0": "src/include/mod_2b8e0.h",
    "CMD.C": "src/include/cmd_123f0.h",
    "NETWORK.C": "src/include/network.h",
    "PACKET.C": "src/include/packet.h",
}

# Modules that need a specific area name to respect AGENTS.md ownership rules
AREA_OVERRIDES = {
    "INIT.C": "startup",
    "mod_20c30": "mod_20c30_ui",
}


class ImmediateKillError(Exception):
    """Raised when an immediate kill control command or SIGTERM is received."""


class StallError(Exception):
    """Raised when a watched child showed no sign of life for `stall_timeout` s."""


DEFAULT_STALL_TIMEOUT = 1200


def _now_str():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _slug(module_name):
    return re.sub(r"[^a-z0-9_]+", "_", module_name.lower().replace(".c", "")).strip("_")


def _parse_ts(val):
    """Parse ledger timestamp (ISO-8601 UTC string or numeric unix timestamp)."""
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str) and val:
        try:
            dt = datetime.datetime.fromisoformat(val.replace("Z", "+00:00"))
            return dt.timestamp()
        except ValueError:
            return 0.0
    return 0.0


def parse_reset_text(text, now=None):
    """Parse textual Claude CLI reset hint like 'resets 5:20am (Asia/Yerevan)' -> unix ts."""
    if not text:
        return None
    m = re.search(
        r"resets\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?(?:\s*\(([^)]+)\))?",
        str(text),
        re.I,
    )
    if not m:
        return None
    hour = int(m.group(1))
    minute = int(m.group(2) or 0)
    ampm = (m.group(3) or "").lower()
    tz_name = (m.group(4) or "").strip()
    if ampm == "pm" and hour < 12:
        hour += 12
    elif ampm == "am" and hour == 12:
        hour = 0
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return None

    now_ts = time.time() if now is None else float(now)
    tz = None
    if tz_name:
        try:
            tz = ZoneInfo(tz_name)
        except Exception:
            tz = None
    if tz is not None:
        base = datetime.datetime.fromtimestamp(now_ts, tz=tz)
    else:
        base = datetime.datetime.fromtimestamp(now_ts).astimezone()
    cand = base.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if cand.timestamp() <= now_ts + 15:
        cand = cand + datetime.timedelta(days=1)
    return cand.timestamp()


def ledger_metrics(ledger_dir=None, now=None, buckets=24):
    """Aggregate rolling 5h & 7d spend, cache hit %, burn rate and sparkline from ledgers."""
    now = time.time() if now is None else float(now)
    cutoff_5h = now - WINDOW_SECONDS
    cutoff_7d = now - SEVEN_DAY_SECONDS
    cutoff_1h = now - 3600.0
    ldir = ledger_dir or path("build", "ledger")

    spend_5h = 0.0
    calls_5h = 0
    oldest_5h = None
    spend_7d = 0.0
    calls_7d = 0
    spend_1h = 0.0
    cr_5h = 0
    cc_5h = 0
    in_5h = 0
    spark = [0.0] * max(1, buckets)
    bucket_w = WINDOW_SECONDS / float(max(1, buckets))

    if os.path.isdir(ldir):
        for fpath in sorted(glob.glob(os.path.join(ldir, "*.jsonl"))):
            try:
                with open(fpath, encoding="utf-8", errors="replace") as fh:
                    for line in fh:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            rec = json.loads(line)
                        except ValueError:
                            continue
                        if rec.get("stage", rec.get("event")) != "claude_call":
                            continue
                        ts = _parse_ts(rec.get("ts"))
                        if ts < cutoff_7d or ts > now + 60:
                            continue
                        cost = float(rec.get("cost_usd") or 0.0)
                        spend_7d += cost
                        calls_7d += 1
                        if ts >= cutoff_5h:
                            spend_5h += cost
                            calls_5h += 1
                            if oldest_5h is None or ts < oldest_5h:
                                oldest_5h = ts
                            u = rec.get("usage") or {}
                            cr_5h += int(u.get("cache_read_input_tokens") or 0)
                            cc_5h += int(u.get("cache_creation_input_tokens") or 0)
                            in_5h += int(u.get("input_tokens") or 0)
                            b = int((ts - cutoff_5h) / bucket_w)
                            b = max(0, min(len(spark) - 1, b))
                            spark[b] += cost
                        if ts >= cutoff_1h:
                            spend_1h += cost
            except OSError:
                continue

    denom = cr_5h + cc_5h + in_5h
    cache_hit_pct = round(100.0 * cr_5h / denom, 1) if denom > 0 else 0.0
    return {
        "spend_5h": round(spend_5h, 4),
        "calls_5h": calls_5h,
        "oldest_5h": oldest_5h,
        "spend_7d": round(spend_7d, 4),
        "calls_7d": calls_7d,
        "burn_rate_usd_per_h": round(spend_1h, 4),
        "cache_hit_pct": cache_hit_pct,
        "sparkline": [round(x, 4) for x in spark],
    }


def rolling_window_spend(ledger_dir=None, now=None, window_seconds=WINDOW_SECONDS):
    """Sum Claude API-equivalent USD spent in the rolling 5-hour window across ledgers.

    Returns (total_usd, call_count, oldest_ts_or_None).
    """
    if window_seconds == WINDOW_SECONDS:
        m = ledger_metrics(ledger_dir=ledger_dir, now=now)
        return m["spend_5h"], m["calls_5h"], m["oldest_5h"]
    now = time.time() if now is None else now
    cutoff = now - window_seconds
    ldir = ledger_dir or path("build", "ledger")
    total = 0.0
    calls = 0
    oldest = None
    if not os.path.isdir(ldir):
        return 0.0, 0, None
    for fpath in sorted(glob.glob(os.path.join(ldir, "*.jsonl"))):
        try:
            with open(fpath) as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if rec.get("stage", rec.get("event")) != "claude_call":
                        continue
                    ts = _parse_ts(rec.get("ts"))
                    if ts >= cutoff:
                        total += float(rec.get("cost_usd") or 0.0)
                        calls += 1
                        if oldest is None or ts < oldest:
                            oldest = ts
        except OSError:
            continue
    return round(total, 4), calls, oldest


def should_wait_for_window(window_budget, rolling_spend, window_capacity):
    """Return True if pre-emptive sleep is required before starting the next module.

    When `window_budget >= 1.0`, never pre-emptively pause — let Claude run until
    it actually returns a rate limit error, then wait for window recovery.
    """
    if window_budget >= 1.0:
        return False
    return rolling_spend >= (window_budget * window_capacity)


def compute_wait_seconds(oldest_ts, now=None, fallback_seconds=900, margin_seconds=90):
    """Seconds until the oldest call in the rolling 5h window ages out."""
    now = time.time() if now is None else now
    if oldest_ts is None:
        return fallback_seconds
    remaining = (oldest_ts + WINDOW_SECONDS + margin_seconds) - now
    if remaining <= 0:
        return 60
    return int(remaining)


def check_window_budget(window_budget, rl_info, rolling_spend, window_capacity,
                        oldest_ts=None, now=None, margin_seconds=60):
    """Decide whether to pause before the next module using live 5h/7d quota + ledger fallback.

    Returns `(should_wait, wait_seconds, reason)`.
    """
    now = time.time() if now is None else float(now)
    rl = rl_info or {}
    five = rl.get("five_hour") if isinstance(rl.get("five_hour"), dict) else None
    seven = rl.get("seven_day") if isinstance(rl.get("seven_day"), dict) else None

    # Check explicit rejection on 7d or 5h if reset timestamp is still in the future
    for label, win in (("7d", seven), ("5h", five)):
        if not win:
            continue
        resets_at = win.get("resets_at")
        fresh = (resets_at is None) or (float(resets_at) > now)
        if fresh and win.get("status") == "rejected":
            wait_s = int(max(60, (float(resets_at) - now + margin_seconds))) if resets_at else 900
            return True, wait_s, f"Claude {label} window rejected"

    # Live 5h utilization check (preferred over USD estimate when fresh)
    if five and five.get("utilization") is not None:
        resets_at = five.get("resets_at")
        fresh = (resets_at is None) or (float(resets_at) > now)
        if fresh:
            util = float(five["utilization"])
            if window_budget < 1.0 and util >= window_budget:
                wait_s = (int(max(60, float(resets_at) - now + margin_seconds))
                          if resets_at else compute_wait_seconds(oldest_ts, now=now))
                return True, wait_s, (
                    f"live 5h quota {util * 100.0:.1f}% >= {window_budget * 100.0:.0f}% budget"
                )
            return False, 0, ""

    # Fallback to rolling 5h ledger USD estimate
    if should_wait_for_window(window_budget, rolling_spend, window_capacity):
        wait_s = compute_wait_seconds(oldest_ts, now=now)
        return True, wait_s, (
            f"rolling 5h spend ${rolling_spend:.2f} >= {int(window_budget * 100)}% of ${window_capacity:.1f}"
        )
    return False, 0, ""


def _ledger_is_resumable(ledger_path, module_budget=None, module_calls=None, provider="claude"):
    """True only when an existing ledger stopped mid-flight on a transient interruption
    (rate_limit / claude_timeout / codex_timeout), was never finished or rolled back, and has budget left."""
    if not os.path.exists(ledger_path):
        return False
    lg = batch_driver.Ledger(ledger_path)
    if not lg.entries:
        return False
    terminal = {"stage4_done", "stage4_fail", "rolled_back", "stage2_early_stop"}
    if any(e.get("stage") in terminal for e in lg.entries):
        return False
    if provider != "codex" and module_budget is not None and lg.total_cost() >= float(module_budget):
        return False
    if module_calls is not None and lg.total_calls(provider=provider) >= int(module_calls):
        return False
    return lg.entries[-1].get("stage") in ("rate_limit", "claude_timeout", "codex_timeout")


DEFAULT_MAX_CHUNK_INSNS = 500


def _pack_chunks(fns, chunk_size, max_chunk_insns=DEFAULT_MAX_CHUNK_INSNS):
    """Greedily pack `(addr, ninsns)` tuples preserving order, capped by both
    `chunk_size` (max functions) and `max_chunk_insns` (max instructions, 0=unlimited).
    A single function with `ninsns > max_chunk_insns` always gets its own 1-fn chunk.
    """
    if not fns:
        return []
    cap_fns = max(1, int(chunk_size or 1))
    cap_insns = int(max_chunk_insns or 0)
    chunks = []
    cur = []
    cur_insns = 0
    for item in fns:
        n = int(item[1])
        if cur and (len(cur) >= cap_fns or (cap_insns > 0 and cur_insns + n > cap_insns)):
            chunks.append(cur)
            cur = []
            cur_insns = 0
        cur.append(item)
        cur_insns += n
    if cur:
        chunks.append(cur)
    return chunks


WAVE4_MODE = "t3-recovery"
WAVE4A_MODE = "t3-reconcile"
WAVE4_MAX_CALLS = 2
WAVE4A_MAX_CALLS = 2
WAVE4_WAVES = ("wave4", "wave4a", "wave4b")
MAX_IN_RUN_WAVE4_ATTEMPTS = 3


def _wave4_is_real_discover(fn):
    from . import wave4
    return getattr(fn, "__module__", "") == wave4.__name__ and getattr(fn, "__name__", "") == "discover"


def _wave4_repo_state_hint(info):
    """Observational global repository state hint (NEVER part of the cache key)."""
    msig = (info or {}).get("matcher_signature")
    return {"matcher_sig": msig} if msig else None


def _wave4_in_run_suppressed(key, rkey, failed_set, failed_fingerprints):
    """Return `(suppressed, requeued_from_fps)` for in-run retry eligibility.

    A Wave 4 item that previously failed under fingerprint `fp_old` becomes
    eligible again during the same run ONLY when its current dependency-scoped
    fingerprint `rkey` is non-None and differs from all prior attempted
    fingerprints (bounded by `MAX_IN_RUN_WAVE4_ATTEMPTS`). Items with uncertain
    dependencies (`rkey is None`), stalls, or legacy `failed_keys` without
    `failed_fingerprints` remain suppressed for the rest of the run.
    """
    if key not in failed_set:
        return False, None
    if not isinstance(failed_fingerprints, dict) or key not in failed_fingerprints:
        return True, None
    rec = failed_fingerprints[key]
    if rec.get("unconditional") or int(rec.get("attempts", 0)) >= MAX_IN_RUN_WAVE4_ATTEMPTS:
        return True, None
    prior_fps = rec.get("fingerprints") or set()
    if not rkey or rkey in prior_fps:
        return True, None
    return False, prior_fps


def _format_cache_diag_summary(label, cache_obj):
    if cache_obj is None or not hasattr(cache_obj, "diagnostics_summary"):
        return None
    s = cache_obj.diagnostics_summary()
    parts = []
    if s.get("hits"):
        h_s = f"{s['hits']} hit(s)"
        if s.get("preserved_unrelated"):
            h_s += f" ({s['preserved_unrelated']} preserved across unrelated repo change)"
        parts.append(h_s)
    if s.get("invalidated_dep_change"):
        parts.append(f"{s['invalidated_dep_change']} dep-invalidated")
    if s.get("invalidated_legacy_schema"):
        parts.append(f"{s['invalidated_legacy_schema']} legacy-schema invalidated")
    if s.get("bypassed_uncertain"):
        parts.append(f"{s['bypassed_uncertain']} bypassed (uncertain deps)")
    if s.get("in_run_requeued"):
        parts.append(f"{s['in_run_requeued']} requeued in-run")
    return f"Cache ({label}): " + ", ".join(parts) if parts else None


def wave4a_items(only=None, skip=None, failed_keys=None, discover=None, reconcile_cache=None,
                 retry_misses=False, refresh_stale=True, failed_fingerprints=None, cache_log=None):
    """Wave 4A queue: auto-promotions and unresolved dependency groups in priority order.

    `only` matches group_id, module name, target/affected hex address (`0x...`), or symbol name.
    Completed misses / ambiguous results with the same dependency-scoped inputs are skipped
    unless `retry_misses`.
    """
    from . import wave4a
    raw_items, info = (discover or (lambda: wave4a.discover(refresh_stale=refresh_stale)))()
    only_set = set(only) if only else None
    skip_set = set(skip or ())
    failed_set = set(failed_keys or ())
    dep_ctx = info.get("dep_ctx")
    msig = info.get("matcher_signature")
    hint = _wave4_repo_state_hint(info)
    if reconcile_cache:
        if hasattr(reconcile_cache, "begin_pass"):
            reconcile_cache.begin_pass()
        else:
            reconcile_cache.skipped = 0
    items, reserved = [], set()
    for g in raw_items:
        gid = g["group_id"]
        mods = set(g.get("affected_modules") or ())
        addrs_hex = {af["addr_hex"] for af in (g.get("affected_functions") or ())}
        if g.get("target_address_hex"):
            addrs_hex.add(g["target_address_hex"])
        syms = set(g.get("symbols") or ())
        selected = bool(only_set and (gid in only_set or (mods & only_set) or (addrs_hex & only_set) or (syms & only_set)))
        if mods and mods <= skip_set and not selected:
            continue
        if only_set is not None and not selected:
            continue
        key = (WAVE4A_MODE, gid)
        is_auto = g.get("task_kind") == "auto_promote"
        fp_res = None
        rkey = None
        if reconcile_cache and not is_auto:
            if hasattr(reconcile_cache, "compute_fingerprint"):
                fp_res = reconcile_cache.compute_fingerprint(g, matcher_sig=msig, dep_ctx=dep_ctx)
                rkey = fp_res.key
            else:
                rkey = reconcile_cache.fingerprint(g, msig)
        suppressed, req_fps = _wave4_in_run_suppressed(key, rkey, failed_set, failed_fingerprints)
        if suppressed:
            continue
        if reconcile_cache and not is_auto:
            if hasattr(reconcile_cache, "lookup"):
                lk = reconcile_cache.lookup(gid, fp_res if fp_res is not None else rkey, repo_state_hint=hint)
                if retry_misses and lk.hit:
                    if cache_log:
                        cache_log(f"[cache:wave4a] RETRY OVERRIDE (--wave4-retry): {gid}")
                else:
                    if hasattr(reconcile_cache, "diag"):
                        msg = reconcile_cache.diag.record(gid, lk)
                        if msg and cache_log:
                            cache_log(msg)
                    if lk.hit:
                        reconcile_cache.skipped += 1
                        continue
            elif not retry_misses and rkey and reconcile_cache.contains(gid, rkey):
                reconcile_cache.skipped += 1
                continue
        if req_fps is not None and reconcile_cache and hasattr(reconcile_cache, "diag"):
            msg = reconcile_cache.diag.record_in_run_requeue(gid, req_fps, rkey)
            if msg and cache_log:
                cache_log(msg)
        base, k = f"w4a_{gid}", 0
        while True:
            tag = base if k == 0 else f"{base}_{k + 1}"
            k += 1
            lp = path("build", "ledger", f"{tag}.jsonl")
            if tag not in reserved and not os.path.exists(lp):
                reserved.add(tag)
                break
        addrs = [af["addr"] for af in (g.get("affected_functions") or ())]
        mod_label = ",".join(sorted(mods)[:2]) + ("+" if len(mods) > 2 else "") if mods else "reconcile"
        items.append({
            "key": key, "mode": WAVE4A_MODE, "module": mod_label, "area": tag,
            "src_subdir": None, "header": None, "limit": None,
            "count": max(1, len(addrs)), "addrs": addrs, "module_total": max(1, len(addrs)),
            "chunk_insns": 0, "total_insns": 0, "avg_insns": 0.0,
            "group_id": gid, "task_kind": g.get("task_kind", "reconcile"),
            "classification": g.get("classification"), "mechanical": bool(g.get("mechanical")),
            "symbols": list(g.get("symbols") or ()),
            "affected_refs": list(g.get("affected_refs") or ()),
            "zero_score_blocked_count": int(g.get("zero_score_blocked_count") or 0),
            "target_address": g.get("target_address"),
            "target_address_hex": g.get("target_address_hex"),
            "retry_key": rkey,
            "retry_fp": fp_res,
            "repo_state_hint": hint,
        })
    return items


def wave4_items(only=None, skip=None, failed_keys=None, discover=None, retry_cache=None,
                retry_misses=False, exclude_unresolved=False, refresh_stale=True,
                failed_fingerprints=None, cache_log=None):
    """Wave 4B queue: one item per eligible T4 function, in wave4.discover order
    (fresh/incremental audit report when available, else deterministic fallback).
    A function whose key is in failed_keys is suppressed unless its dependency-scoped
    fingerprint genuinely changed (bounded by MAX_IN_RUN_WAVE4_ATTEMPTS). Completed
    misses with the same dependency-scoped inputs are skipped unless retry_misses is
    set. When `exclude_unresolved=True`, functions whose best audit attempt has
    unresolved relocations are routed to Wave 4A unless explicitly targeted by hex
    address in `only`."""
    from . import t3_audit, wave4
    only_set = set(only) if only else None
    only_hex = {str(x).lower() for x in (only_set or ()) if str(x).lower().startswith("0x")}
    # Only bypass unresolved routing globally if `only` contains exclusively hex addresses;
    # for mixed `--only 0x10040,MOD_A`, keep unresolved filtering on non-hex-selected functions.
    eff_exclude = bool(exclude_unresolved and not (only_set and only_hex and len(only_hex) == len(only_set)))
    if discover is not None:
        queue, info = discover()
    elif _wave4_is_real_discover(wave4.discover):
        from . import wave4a
        try:
            rep = wave4a.load_audit_report_incremental(refresh_stale=refresh_stale)
            queue, info = wave4.discover(report=rep, report_state="fresh", exclude_unresolved=False)
        except t3_audit.ToolchainAbort:
            raise
        except Exception as ex:
            print(f"[{_now_str()}] WARNING: incremental Wave 4 audit failed ({ex}); falling back to wave4.discover",
                  file=sys.stderr, flush=True)
            queue, info = wave4.discover(exclude_unresolved=False)
    else:
        queue, info = wave4.discover()
    skip_set = set(skip or ())
    failed_set = set(failed_keys or ())
    dep_ctx = info.get("dep_ctx")
    msig = info.get("matcher_signature")
    hint = _wave4_repo_state_hint(info)
    siblings = defaultdict(list)
    if retry_cache:
        if hasattr(retry_cache, "begin_pass"):
            retry_cache.begin_pass()
        else:
            retry_cache.skipped = 0
        for c in queue:
            siblings[c["ref"]].append(c)
    items, reserved = [], set()
    for c in queue:
        hex_selected = bool(only_hex and c["addr_hex"].lower() in only_hex)
        selected = only_set and (c["module"] in only_set or hex_selected)
        if c["module"] in skip_set and not selected:
            continue
        if only_set is not None and not selected:
            continue
        if exclude_unresolved and c.get("unresolved_count", 0) > 0 and not hex_selected:
            continue
        key = (WAVE4_MODE, c["module"], (c["addr"],))
        fp_res = None
        retry_key = None
        if retry_cache:
            if hasattr(retry_cache, "compute_fingerprint"):
                fp_res = retry_cache.compute_fingerprint(c, siblings[c["ref"]], matcher=msig, dep_ctx=dep_ctx)
                retry_key = fp_res.key
            else:
                retry_key = retry_cache.fingerprint(c, siblings[c["ref"]], msig)
        suppressed, req_fps = _wave4_in_run_suppressed(key, retry_key, failed_set, failed_fingerprints)
        if suppressed:
            continue
        if retry_cache:
            if hasattr(retry_cache, "lookup"):
                lk = retry_cache.lookup(c["addr"], fp_res if fp_res is not None else retry_key, repo_state_hint=hint)
                if retry_misses and lk.hit:
                    if cache_log:
                        cache_log(f"[cache:wave4b] RETRY OVERRIDE (--wave4-retry): {c['addr']:#x}")
                else:
                    if hasattr(retry_cache, "diag"):
                        msg = retry_cache.diag.record(f"{c['addr']:#x}", lk)
                        if msg and cache_log:
                            cache_log(msg)
                    if lk.hit:
                        retry_cache.skipped += 1
                        continue
            elif not retry_misses and retry_cache.contains(c["addr"], retry_key):
                retry_cache.skipped += 1
                continue
        if req_fps is not None and retry_cache and hasattr(retry_cache, "diag"):
            msg = retry_cache.diag.record_in_run_requeue(f"{c['addr']:#x}", req_fps, retry_key)
            if msg and cache_log:
                cache_log(msg)
        base, k = f"w4_{c['addr']:x}", 0
        while True:
            tag = base if k == 0 else f"{base}_{k + 1}"
            k += 1
            lp = path("build", "ledger", f"{tag}.jsonl")
            # A fresh invocation gets a fresh budget; in-run quota resumes
            # retain this item (and its ledger) through resume_item.
            if tag not in reserved and not os.path.exists(lp):
                reserved.add(tag)
                break
        items.append({"key": key, "mode": WAVE4_MODE, "module": c["module"], "area": tag,
                      "src_subdir": None, "header": None, "limit": None, "count": 1,
                      "addrs": [c["addr"]], "module_total": 1, "chunk_insns": c.get("ninsns", 0),
                      "total_insns": c.get("ninsns", 0), "avg_insns": float(c.get("ninsns", 0)),
                      "name": c["name"], "ref": c["ref"], "wave4_group": c["group"],
                      "audit_status": c.get("audit_status"), "report_state": info["report"],
                      "unresolved_count": c.get("unresolved_count", 0), "retry_key": retry_key,
                      "retry_fp": fp_res, "repo_state_hint": hint})
    return items


def build_queue_with_needs_human(wave="all", chunk_size=12, skip=DEFAULT_SKIP, only=None,
                                 failed_keys=None, module_budget=None, module_calls=None,
                                 max_chunk_insns=DEFAULT_MAX_CHUNK_INSNS, provider="claude",
                                 retry_cache=None, retry_misses=False, reconcile_cache=None,
                                 wave4_include_unresolved=False, refresh_stale=True,
                                 failed_fingerprints=None, cache_log=None):
    """Build the ROI-ordered queue of overnight work items plus a `needs_human` list.

    Partitions undone in-scope functions into:
      - Wave 2 (`c-only`): named, missing C, not blocked.
      - Wave 3 (`full`): unnamed, missing C, no pre-existing DB entry in another TOML, not blocked.
      - Wave 4A (`t3-reconcile`): auto-promotions and unresolved dependency groups.
      - Wave 4B (`t3-recovery`): dependency-clean T4 -> T3 codegen recovery.
      - Wave 4 (`wave4`): combined Wave 4A followed by Wave 4B.
      - `needs_human`: data-in-code (`datas_db`), `codegen_promo.toml`, untracked WIP TOMLs,
        already-matched unbuildable T3s (`verified_by = "match: ..."` without `src`),
        name-only entries (already have T3/T4 C), and pre-existing placeholder/low entries
        in other TOMLs (require supervised rename/confidence upgrade).
    """
    if wave == "wave4a":
        return wave4a_items(only=only, skip=skip, failed_keys=failed_keys,
                            reconcile_cache=reconcile_cache, retry_misses=retry_misses,
                            refresh_stale=refresh_stale, failed_fingerprints=failed_fingerprints,
                            cache_log=cache_log), []
    if wave == "wave4b":
        return wave4_items(only=only, skip=skip, failed_keys=failed_keys,
                           retry_cache=retry_cache, retry_misses=retry_misses,
                           exclude_unresolved=not wave4_include_unresolved,
                           refresh_stale=refresh_stale, failed_fingerprints=failed_fingerprints,
                           cache_log=cache_log), []
    if wave == "wave4":
        from . import t3_audit, wave4
        if _wave4_is_real_discover(wave4.discover):
            try:
                w4a = wave4a_items(only=only, skip=skip, failed_keys=failed_keys,
                                   reconcile_cache=reconcile_cache, retry_misses=retry_misses,
                                   refresh_stale=refresh_stale, failed_fingerprints=failed_fingerprints,
                                   cache_log=cache_log)
            except t3_audit.ToolchainAbort:
                raise
            except Exception as ex:
                print(f"[{_now_str()}] WARNING: Wave 4A discovery failed ({ex}); falling back to Wave 4B",
                      file=sys.stderr, flush=True)
                w4a = []
            if w4a:
                return w4a, []
        return wave4_items(only=only, skip=skip, failed_keys=failed_keys,
                           retry_cache=retry_cache, retry_misses=retry_misses,
                           exclude_unresolved=not wave4_include_unresolved,
                           refresh_stale=refresh_stale, failed_fingerprints=failed_fingerprints,
                           cache_log=cache_log), []
    p = analysis.run()
    funcs_db, datas_db, _ = symbols.load(strict=False)
    mods = progress.load_modules()
    rows = progress.classify([f["start"] for f in p.functions], funcs_db, mods)
    by_addr = {f["start"]: f for f in p.functions}
    tracked = batch_driver._git_tracked_files()

    skip_set = set(skip or ())
    only_set = set(only) if only else None
    failed_set = set(failed_keys or ())

    w2 = defaultdict(list)
    w3 = defaultdict(list)
    needs_human = []
    for r in rows:
        if r["scope"] != "in" or r["done"]:
            continue
        m = r["module"]
        if m in skip_set:
            continue
        if only_set is not None and m not in only_set:
            continue
        a = r["addr"]
        e = funcs_db.get(a)
        ninsns = by_addr[a]["ninsns"]

        reason = None
        if a in datas_db:
            reason = f"data-in-code ({datas_db[a]['name']} in {datas_db[a]['_file']})"
        elif e is not None:
            ef = e["_file"].replace("\\", "/")
            if ef in batch_driver.LOCKED_TOMLS:
                reason = f"locked TOML ({ef})"
            elif tracked is not None and ef not in tracked:
                reason = f"untracked WIP TOML ({ef})"
            elif r["c"] == "none" and str(e.get("verified_by", "")).startswith("match:"):
                reason = "unbuildable T3 (already matched; blocked on interior refs)"
            elif not r["named"] and r["c"] in ("T3", "T4"):
                reason = f"name-only (already {r['c']} in {ef}; needs supervised rename/upgrade)"
            elif not r["named"]:
                reason = f"existing cross-TOML entry ({e['name']}, {e['confidence']} in {ef}; needs supervised rename/upgrade)"

        if reason is not None:
            needs_human.append({
                "addr": a, "module": m, "name": e["name"] if e else None,
                "reason": reason,
            })
            continue

        if r["named"] and r["c"] == "none":
            w2[m].append((a, ninsns))
        elif not r["named"] and r["c"] == "none":
            w3[m].append((a, ninsns))
        elif r["named"] and r["c"] in ("ref", "T4"):
            needs_human.append({
                "addr": a, "module": m, "name": e["name"] if e else None,
                "reason": f"T4 incomplete ({r['c']}; missing {', '.join(r['missing'])})",
            })

    items = []
    reserved_areas = set()

    def _next_free_area(base, mode, idx_hint=0):
        """Pick a fresh monotonic area tag, or resume only a genuinely interrupted in-flight ledger."""
        suffix = "c" if mode == "c-only" else "f"
        if idx_hint == 0:
            first = f"{base}_{suffix}" if mode == "c-only" else base
            if first not in reserved_areas:
                lp = path("build", "ledger", f"{first}.jsonl")
                if not os.path.exists(lp) or _ledger_is_resumable(
                    lp, module_budget=module_budget, module_calls=module_calls, provider=provider,
                ):
                    reserved_areas.add(first)
                    return first
        k = max(1, idx_hint + 1)
        while True:
            cand = f"{base}_{suffix}{k}"
            k += 1
            if cand in reserved_areas:
                continue
            lp = path("build", "ledger", f"{cand}.jsonl")
            if not os.path.exists(lp) or _ledger_is_resumable(
                lp, module_budget=module_budget, module_calls=module_calls, provider=provider,
            ):
                reserved_areas.add(cand)
                return cand

    def _add_module_items(mode, m, fns):
        base = AREA_OVERRIDES.get(m, _slug(m))
        hdr = KNOWN_HEADERS.get(m)
        if hdr and not os.path.exists(path(hdr)):
            hdr = None
        count = len(fns)
        total_insns = sum(x[1] for x in fns)
        avg = total_insns / max(1, count)
        chunks = _pack_chunks(fns, chunk_size=chunk_size, max_chunk_insns=max_chunk_insns)
        n_chunks = len(chunks)
        for ci, chunk_fns in enumerate(chunks):
            chunk_addrs = [x[0] for x in chunk_fns]
            key = (mode, m, tuple(chunk_addrs))
            if key in failed_set or (mode, m) in failed_set or (mode, m, ci) in failed_set:
                continue
            tag = _next_free_area(base, mode, idx_hint=ci if n_chunks > 1 else 0)
            lim = len(chunk_fns) if n_chunks > 1 else None
            chunk_insns = sum(x[1] for x in chunk_fns)
            chunk_avg = chunk_insns / max(1, len(chunk_fns))
            src_sub = _slug(m)
            items.append({
                "key": key,
                "mode": mode,
                "module": m,
                "area": tag,
                "src_subdir": src_sub,
                "header": hdr,
                "limit": lim,
                "count": len(chunk_fns),
                "addrs": chunk_addrs,
                "module_total": count,
                "chunk_insns": chunk_insns,
                "total_insns": total_insns,
                "avg_insns": round(chunk_avg, 1),
            })

    if wave in ("all", "wave2"):
        for m, fns in sorted(w2.items(), key=lambda kv: (len(kv[1]) < 3, sum(x[1] for x in kv[1]) / len(kv[1]), -len(kv[1]))):
            _add_module_items("c-only", m, fns)

    if wave in ("all", "wave3"):
        for m, fns in sorted(w3.items(), key=lambda kv: (sum(x[1] for x in kv[1]) / len(kv[1]), len(kv[1]))):
            _add_module_items("full", m, fns)

    return items, needs_human


def build_queue(wave="all", chunk_size=12, skip=DEFAULT_SKIP, only=None,
                failed_keys=None, module_budget=None, module_calls=None,
                max_chunk_insns=DEFAULT_MAX_CHUNK_INSNS, provider="claude", retry_cache=None,
                retry_misses=False, reconcile_cache=None, wave4_include_unresolved=False,
                failed_fingerprints=None, cache_log=None):
    """Build the ROI-ordered queue of overnight work items from live progress."""
    items, _ = build_queue_with_needs_human(
        wave=wave, chunk_size=chunk_size, skip=skip, only=only,
        failed_keys=failed_keys, module_budget=module_budget, module_calls=module_calls,
        max_chunk_insns=max_chunk_insns, provider=provider, retry_cache=retry_cache,
        retry_misses=retry_misses, reconcile_cache=reconcile_cache,
        wave4_include_unresolved=wave4_include_unresolved,
        failed_fingerprints=failed_fingerprints, cache_log=cache_log,
    )
    return items


def parse_git_porcelain(output):
    """Parse `git status --porcelain -uall` output into (tracked_mods, untracked)."""
    tracked = set()
    untracked = set()
    for line in (output or "").splitlines():
        if len(line) < 4:
            continue
        xy = line[:2]
        rel = line[3:].strip()
        if " -> " in rel:
            rel = rel.split(" -> ", 1)[1]
        if rel.startswith('"') and rel.endswith('"'):
            rel = rel[1:-1]
        if rel.startswith("build/") or rel.startswith("original/"):
            continue
        if xy == "??":
            untracked.add(rel)
        else:
            tracked.add(rel)
    return tracked, untracked


def git_status(cwd=None):
    r = subprocess.run(["git", "status", "--porcelain", "-uall"],
                       capture_output=True, text=True, cwd=cwd or path(), check=True)
    return parse_git_porcelain(r.stdout)


def _wave4_status():
    """Capture both sides of Git status, including both paths of a rename.

    Paths newly added to the index (`A` in column 0, absent from HEAD) are recorded in
    BOTH `untracked` and `staged` (not `tracked`) so rollback unstages and removes them
    cleanly instead of failing `git restore --source=HEAD`.
    """
    raw = subprocess.check_output(["git", "status", "--porcelain=v1", "-z", "-uall", "--no-renames"], cwd=path())
    tracked, untracked, staged = set(), set(), set()
    for entry in os.fsdecode(raw).rstrip("\0").split("\0"):
        if not entry:
            continue
        rel = entry[3:]
        if entry[:2] == "??":
            if not rel.startswith(("build/", "original/")):
                untracked.add(rel)
        elif entry[0] == "A":
            if not rel.startswith(("build/", "original/")):
                untracked.add(rel)
            staged.add(rel)
        else:
            tracked.add(rel)
            if entry[0] != " ":
                staged.add(rel)
    return tracked, untracked, staged


def _wave4_head():
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=path(), text=True).strip()


def progress_done_count():
    p = analysis.run()
    funcs_db, _, _ = symbols.load(strict=False)
    rows = progress.classify([f["start"] for f in p.functions], funcs_db, progress.load_modules())
    in_scope = [r for r in rows if r["scope"] == "in"]
    done = sum(1 for r in in_scope if r["done"])
    t3 = sum(1 for r in in_scope if r["c"] == "T3")
    t4 = sum(1 for r in in_scope if r["c"] == "T4")
    return done, len(in_scope), t3, t4


def _rollback_tree(tracked_mods, new_untracked, cwd=None, restore_from=None):
    """Restore modified tracked files and remove newly created untracked/staged files."""
    root = cwd or path()
    tracked_set = set(tracked_mods or ())
    untracked_set = set(new_untracked or ())
    if restore_from is not None and tracked_set:
        # Defense-in-depth: any path absent from `restore_from` (e.g. newly staged `A`)
        # must be unstaged + unlinked, never passed to `git restore --source=<restore_from>`.
        r_ls = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", restore_from],
            cwd=root, capture_output=True, text=True,
        )
        if r_ls.returncode == 0:
            in_base = set(r_ls.stdout.splitlines())
            absent = tracked_set - in_base
            if absent:
                tracked_set -= absent
                untracked_set |= absent
    if restore_from is not None and untracked_set:
        # Unstage any newly created files if a failed commit attempt staged them.
        subprocess.run(
            ["git", "--literal-pathspecs", "rm", "--cached", "--ignore-unmatch", "-f", "--", *sorted(untracked_set)],
            cwd=root, capture_output=True,
        )
    if tracked_set:
        if restore_from is not None:
            # Wave 4 starts from a clean index. Restore deleted and staged
            # paths as well as ordinary worktree edits, without moving HEAD.
            cmd = ["git", "--literal-pathspecs", "restore", f"--source={restore_from}", "--staged", "--worktree"]
        else:
            cmd = ["git", "checkout"]
        subprocess.run([*cmd, "--", *sorted(tracked_set)], cwd=root, check=True)
    dirs_to_prune = set()
    for rel in sorted(untracked_set):
        full = os.path.join(root, rel)
        if os.path.isfile(full) or os.path.islink(full):
            os.unlink(full)
            dirs_to_prune.add(os.path.dirname(full))
    root_abs = os.path.abspath(root)
    keep_top = {os.path.join(root_abs, d) for d in ("src", "tests", "docs", "analysis", "tools")}
    for d in sorted(dirs_to_prune, key=len, reverse=True):
        cur = os.path.abspath(d)
        while cur.startswith(root_abs + os.sep) and cur not in keep_top:
            try:
                if os.path.isdir(cur) and not os.listdir(cur):
                    os.rmdir(cur)
                    cur = os.path.dirname(cur)
                else:
                    break
            except OSError:
                break


def archive_and_rollback(area, tracked_mods, new_untracked, log_text="", cwd=None, restore_from=None):
    """Save failed/killed module changes to build/failed/ and cleanly restore git tree."""
    root = cwd or path()
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(root, "build", "failed", f"{stamp}_{area}")
    os.makedirs(dest, exist_ok=True)
    if log_text:
        with open(os.path.join(dest, "failure.log"), "w") as fh:
            fh.write(log_text)
    for rel in sorted(tracked_mods | new_untracked):
        src = os.path.join(root, rel)
        if os.path.isfile(src):
            out = os.path.join(dest, rel)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            shutil.copy2(src, out)
    _rollback_tree(tracked_mods, new_untracked, cwd=root, restore_from=restore_from)
    return dest


def _has_forbidden_test_cheat(paths_list, cwd=None):
    root = cwd or path()
    for rel in paths_list:
        if rel.startswith("tests/") and rel.endswith(".py"):
            full = os.path.join(root, rel)
            if os.path.isfile(full):
                txt = open(full, errors="replace").read()
                reason = batch_driver.find_forbidden_test_cheat(txt)
                if reason:
                    return f"{rel} ({reason})"
    return None


def _snapshot_symbol_state(cwd=None):
    """Capture per-address `(done, c, src, ref, ref_verified_by)` across all discovered functions."""
    root = cwd or path()
    if not os.path.exists(os.path.join(root, "original", "install", "war.exe")):
        return {}
    p = analysis.run()
    funcs_db, _, _ = symbols.load(
        root=os.path.join(root, "analysis", "symbols"), strict=False, repo_root=root,
    )
    rows = progress.classify([f["start"] for f in p.functions], funcs_db, progress.load_modules())
    snap = {}
    for r in rows:
        a = r["addr"]
        e = funcs_db.get(a) or {}
        snap[a] = {
            "done": bool(r["done"]),
            "c": r["c"],
            "src": e.get("src"),
            "ref": e.get("ref"),
            "ref_verified_by": e.get("ref_verified_by"),
            "name": e.get("name"),
            "file": e.get("_file"),
        }
    return snap


def _check_no_regression(before_snap, after_snap):
    """Verify no previously done function, T3 `src =`, or T4 `ref_verified_by` regressed."""
    if not before_snap or not after_snap:
        return []
    regressions = []
    for a, prev in sorted(before_snap.items()):
        cur = after_snap.get(a)
        if cur is None:
            if prev["done"] or prev["src"] or prev["ref_verified_by"]:
                regressions.append(f"{a:#x}: disappeared from snapshot")
            continue
        if prev["done"] and not cur["done"]:
            regressions.append(f"{a:#x} ({prev['name']}): done -> not done")
        if prev["src"] and not cur["src"]:
            regressions.append(f"{a:#x} ({prev['name']}): lost src={prev['src']}")
        if prev["ref_verified_by"] and not cur["ref_verified_by"] and not cur["src"]:
            regressions.append(f"{a:#x} ({prev['name']}): lost ref_verified_by without T3 promotion")
    return regressions


_FORBIDDEN_EXACT = {
    "Makefile", "flake.nix", "flake.lock", "AGENTS.md", "CLAUDE.md", "README.md",
    "src/include/war.h", "analysis/symbols/codegen_promo.toml", "analysis/symbols/clib.toml",
}
_FORBIDDEN_PREFIXES = ("tools/", "asm/", ".claude/", ".opencode/")


def _path_contained(rel, root):
    """True when repo-relative `rel` is a plain relative path whose realpath (symlinks in
    any existing component resolved) stays inside realpath(`root`), not on a symlink."""
    rel = str(rel).replace("\\", "/")
    if not rel or rel.startswith("/") or os.path.isabs(rel) or "\x00" in rel:
        return False
    norm = posixpath.normpath(rel)
    if norm != rel.rstrip("/") or norm == ".." or norm.startswith("../") or norm == ".":
        return False
    root_real = os.path.realpath(root)
    full = os.path.join(root, *norm.split("/"))
    if os.path.islink(full):
        return False
    real = os.path.realpath(full)
    return real == root_real or real.startswith(root_real + os.sep)


def _wave4_outcome(item):
    """The outcome record wave4.run_recovery or wave4a.run_reconciliation wrote ({} if none)."""
    if item["mode"] == WAVE4A_MODE:
        from . import wave4a
        try:
            return wave4a.read_outcome(item["group_id"]) or {}
        except Exception:
            return {}
    from . import wave4
    try:
        return wave4.read_outcome(item["addrs"][0]) or {}
    except Exception:
        return {}


def _check_wave4_paths(changed_paths, outcome, cwd=None):
    """Wave 4B may touch exactly the recovered C file and the TOMLs of the promoted entries."""
    root = cwd or path()
    ok = {str(outcome.get("ref") or "")}
    ok |= {str(t) for t in (outcome.get("tomls") or ())}
    ok.discard("")
    bad = []
    for raw in sorted(changed_paths):
        rel = str(raw).replace("\\", "/")
        if rel not in ok or not _path_contained(rel, root):
            bad.append(rel)
    return bad


def _is_valid_wave4a_category(rel):
    """Allow only C sources, area headers, symbol TOMLs, and pytest files for Wave 4A."""
    if rel.startswith("src/include/") and re.fullmatch(r"src/include/[a-z0-9_]+\.h", rel):
        return rel != "src/include/war.h"
    if rel.startswith("src/") and rel.endswith(".c"):
        return True
    if re.fullmatch(r"analysis/symbols/[a-z0-9_]+\.toml", rel):
        return rel not in _FORBIDDEN_EXACT
    if rel.startswith("tests/") and re.fullmatch(r"tests/test_[a-zA-Z0-9_]+\.py", rel):
        return True
    return False


def _check_wave4a_paths(changed_paths, outcome, cwd=None):
    """Wave 4A may touch only valid C/header/TOML/test paths declared in the receipt, never protected files."""
    root = cwd or path()
    ok = set()
    for key in ("changed_files", "ref_files", "tomls", "headers", "tests"):
        for p in (outcome.get(key) or ()):
            if p:
                ok.add(str(p).replace("\\", "/"))
    bad = []
    for raw in sorted(changed_paths):
        rel = str(raw).replace("\\", "/")
        if (rel not in ok or not _path_contained(rel, root)
                or not _is_valid_wave4a_category(rel)
                or rel in _FORBIDDEN_EXACT or any(rel.startswith(px) for px in _FORBIDDEN_PREFIXES)):
            bad.append(rel)
    return bad


def _check_wave4a_test_anti_weakening(changed_paths, base_rev, cwd=None):
    """Verify any modified test file in a Wave 4A transaction did not weaken behavioral coverage."""
    root = cwd or path()
    for raw in sorted(changed_paths):
        rel = str(raw).replace("\\", "/")
        if not (rel.startswith("tests/") and rel.endswith(".py")):
            continue
        full = os.path.join(root, rel)
        if not os.path.isfile(full):
            return f"{rel}: test file deleted"
        new_src = open(full, encoding="utf-8", errors="replace").read()
        r = subprocess.run(["git", "show", f"{base_rev}:{rel}"], cwd=root, capture_output=True, text=True)
        if r.returncode != 0:
            return f"{rel}: Wave 4A may not create arbitrary untracked test files"
        reason = batch_driver.check_test_patch_not_weakening(r.stdout, new_src, allow_case_edits=False)
        if reason:
            return f"{rel}: {reason}"
    return None


def _wave4a_progress_ok(item, outcome, before, after, changed, delta_done, delta_t3, delta_t4):
    """Accept either genuine T4->T3 promotions (`PROMOTED`) or verified intermediate
    reconciliation progress (`RECONCILED` with strictly fewer unresolved relocations and
    zero tier regressions)."""
    if len(after) < len(before):
        return False
    out_kind = outcome.get("outcome")
    if out_kind == "PROMOTED":
        reported = outcome.get("promoted")
        if not isinstance(reported, list) or not reported or not all(isinstance(a, str) for a in reported):
            return False
        actual = {
            addr for addr, row in after.items()
            if row["c"] == "T3" and before.get(addr, {}).get("c") == "T4"
            and row["src"] == before[addr]["ref"]
        }
        if not actual or len(actual) != len(reported) or {f"{a:#x}" for a in actual} != set(reported):
            return False
        if not all(after[a]["file"] == before[a]["file"] for a in actual):
            return False
        owners = {before[a]["file"] for a in actual if before[a].get("file")}
        refs = {after[a]["src"] for a in actual if after[a].get("src")}
        return (owners <= changed and all(os.path.isfile(path(r)) for r in refs)
                and delta_t3 == len(actual) == -delta_t4 and delta_done == 0)
    if out_kind == "RECONCILED":
        ub = outcome.get("unresolved_before")
        ua = outcome.get("unresolved_after")
        return (bool(changed) and delta_t3 == 0 and delta_t4 == 0 and delta_done == 0
                and type(ub) is int and type(ua) is int and 0 <= ua < ub)
    return False


def _wave4a_inputs(item, before):
    """Verify every affected ref file and owning TOML for a Wave 4A item is tracked and regular."""
    refs = set(item.get("affected_refs") or ())
    if not refs:
        return None
    owners = {
        row.get("file") for row in before.values()
        if row.get("c") == "T4" and row.get("ref") in refs
    }
    if not owners or not all(owners):
        return None
    inputs = refs | owners
    tracked = batch_driver._git_tracked_files(cwd=path()) or set()
    return inputs if inputs <= tracked and _wave4_worktree(inputs) is not None else None


def _wave4_worktree(paths):
    """Raw worktree bytes and modes, independent of Git clean filters."""
    result = {}
    for rel in paths:
        if not _path_contained(rel, path()):
            return None
        fn = path(rel)
        try:
            mode = os.lstat(fn).st_mode
            if not stat.S_ISREG(mode):
                return None
            with open(fn, "rb") as fh:
                result[rel] = (mode, fh.read())
        except OSError:
            return None
    return result


def _wave4_inputs(item, before):
    ref = item["ref"]
    owners = {a: row.get("file") for a, row in before.items() if row["c"] == "T4" and row["ref"] == ref}
    if item["addrs"][0] not in owners or not all(owners.values()):
        return None
    inputs = {ref, *owners.values()}
    tracked = batch_driver._git_tracked_files(cwd=path()) or set()
    return inputs if inputs <= tracked and _wave4_worktree(inputs) is not None else None


def _wave4_progress_ok(item, outcome, before, after, changed, delta_done, delta_t3, delta_t4):
    """Match the receipt to actual T4 -> T3 transitions for this object."""
    reported = outcome.get("promoted")
    tomls = outcome.get("tomls")
    if (not isinstance(reported, list) or not all(isinstance(a, str) for a in reported)
            or not isinstance(tomls, list) or not all(isinstance(fn, str) for fn in tomls)):
        return False
    ref = item["ref"]
    actual = {addr for addr, row in after.items()
              if row["c"] == "T3" and row["src"] == ref
              and before.get(addr, {}).get("c") == "T4" and before[addr]["ref"] == ref}
    owners = {before[a]["file"] for a in actual}
    return (outcome.get("ref") == ref and item["addrs"][0] in actual
            and {f"{a:#x}" for a in actual} == set(reported)
            and len(tomls) == len(owners) and set(tomls) == owners <= changed
            and all(after[a]["file"] == before[a]["file"] for a in actual) and delta_done == 0
            and delta_t3 == len(actual) == len(reported) == -delta_t4)


def _check_allowed_paths(changed_paths, item, owned_tomls=(), cwd=None):
    """Enforce strict per-module path allowlist before committing.

    Prevents bounded repair (or stray edits) from modifying Makefile, tools/,
    war.h, codegen_promo.toml, pre-existing tracked tests, or unrelated modules.
    Returns list of disallowed relative paths.
    """
    root = cwd or path()
    area = item["area"]
    src_sub = item.get("src_subdir") or area
    hdr = item.get("header")
    tracked = batch_driver._git_tracked_files(cwd=root)
    tracked_set = tracked if tracked is not None else set()
    real_repo = os.path.isdir(os.path.join(root, "analysis", "symbols"))

    allowed_tomls = {f"analysis/symbols/{area}.toml"}
    for t in (owned_tomls or ()):
        nt = str(t).replace("\\", "/")
        if nt not in batch_driver.LOCKED_TOMLS and (tracked is None or nt in tracked_set):
            allowed_tomls.add(nt)

    allowed_headers = {f"src/include/{area}.h", f"src/include/{src_sub}.h"}
    if hdr:
        allowed_headers.add(str(hdr).replace("\\", "/"))
    allowed_headers.discard("src/include/war.h")

    test_re = re.compile(rf"tests/test_{re.escape(area)}(?:_[A-Za-z0-9_]+)?\.py")
    disallowed = []
    for raw_rel in sorted(changed_paths):
        rel = str(raw_rel).replace("\\", "/")
        if not _path_contained(rel, root):
            # `..`, absolute paths, or a symlink (in any component) escaping the repo
            disallowed.append(rel)
            continue
        if rel in _FORBIDDEN_EXACT or any(rel.startswith(p) for p in _FORBIDDEN_PREFIXES):
            disallowed.append(rel)
            continue
        if rel.startswith("tests/"):
            # Existing tracked tests must NEVER be modified by unattended runs
            if rel in tracked_set:
                disallowed.append(rel)
                continue
            # only this area's own test files: tests/test_<area>.py, tests/test_<area>_<tag>.py
            if not test_re.fullmatch(rel):
                disallowed.append(rel)
                continue
            continue
        if rel.startswith("analysis/symbols/"):
            if rel not in allowed_tomls:
                disallowed.append(rel)
            continue
        if rel.startswith("src/include/"):
            if rel not in allowed_headers:
                disallowed.append(rel)
            continue
        if rel.startswith("src/"):
            if not rel.startswith(f"src/{src_sub}/"):
                disallowed.append(rel)
            continue
        if rel.startswith("docs/"):
            if rel != f"docs/subsystems/{area}.md":
                disallowed.append(rel)
            continue
        if real_repo:
            disallowed.append(rel)
    return disallowed


def _verify_new_ref_verified_by(before_snap, changed_paths, cwd=None):
    """Verify every newly added/changed `ref_verified_by` in modified TOMLs AND every
    existing `ref_verified_by` whose cited test file was modified in `changed_paths`.
    Checks AST cheat prefilter, ref mention, standalone pytest pass, and runtime oracle audit."""
    import glob as _glob
    import tomllib
    root = cwd or path()
    changed_set = {str(r).replace("\\", "/") for r in changed_paths}
    toml_rels = {r for r in changed_set if r.startswith("analysis/symbols/") and r.endswith(".toml")}
    changed_tests = {r for r in changed_set if r.startswith("tests/") and r.endswith(".py")}
    if not toml_rels and not changed_tests:
        return []
    tracked = batch_driver._git_tracked_files(cwd=root)
    known = (tracked or set()) | changed_set
    # Scan modified TOMLs plus (when any test file changed) all tracked TOMLs referencing them
    scan_tomls = set(toml_rels)
    if changed_tests:
        sym_dir = os.path.join(root, "analysis", "symbols")
        if os.path.isdir(sym_dir):
            for p_abs in _glob.glob(os.path.join(sym_dir, "*.toml")):
                rel_t = os.path.relpath(p_abs, root).replace("\\", "/")
                if tracked is None or rel_t in known:
                    scan_tomls.add(rel_t)

    failures = []
    seen_checks = set()
    for rel in sorted(scan_tomls):
        full = os.path.join(root, rel)
        if not os.path.isfile(full):
            continue
        try:
            data = tomllib.loads(open(full, encoding="utf-8").read())
        except Exception as ex:
            if rel in toml_rels:
                failures.append(f"{rel}: TOML parse error: {ex}")
            continue
        for fn in data.get("func", []):
            a = fn.get("addr")
            rv = fn.get("ref_verified_by")
            if not isinstance(a, int) or not rv:
                continue
            prev_rv = (before_snap.get(a) or {}).get("ref_verified_by") if before_snap else None
            nodes, _perr = symbols.parse_ref_verified_by_nodes(rv)
            cites_changed_test = any(fp.replace("\\", "/") in changed_tests for fp, _ in nodes)
            if prev_rv == rv and not cites_changed_test:
                continue
            if (a, rv) in seen_checks:
                continue
            seen_checks.add((a, rv))
            node = str(rv).strip()
            if node.startswith("difftest:"):
                node = node[len("difftest:"):].strip()
            file_rel = node.split("::", 1)[0].strip() if "::" in node else ""
            if file_rel and file_rel not in known:
                failures.append(f"{a:#x}: test file {file_rel} not tracked or staged")
                continue
            fn_link = None
            if fn.get("name"):
                try:
                    fn_link = symbols.link_name("func", fn)
                except KeyError:
                    fn_link = None
            ok, reason = batch_driver.verify_t4_node(
                rv, ref_rel=fn.get("ref"), orig_addr=a, func_name=fn_link, cwd=root,
            )
            if not ok:
                failures.append(f"{a:#x}: {reason}")
    return failures


def _wire_verified_t4_after_repair(area, owned_tomls=(), cwd=None):
    """Mechanically wire `ref_verified_by` for pending Stage 4 T4 tests that now pass after repair."""
    root = cwd or path()
    lp = os.path.join(root, "build", "ledger", f"{area}.jsonl")
    if not os.path.isfile(lp):
        return {}
    lg = batch_driver.Ledger(lp)
    # Only consider pending_ref_verified_by from the latest run (after the last target_addrs / rolled_back)
    start_idx = 0
    for idx, e in enumerate(lg.entries):
        if e.get("stage") in ("target_addrs", "rolled_back"):
            start_idx = idx
    pending_rv = {}
    for e in lg.entries[start_idx:]:
        prv = e.get("pending_ref_verified_by")
        if isinstance(prv, dict):
            for a_hex, node in prv.items():
                try:
                    pending_rv[int(a_hex, 16)] = node
                except (TypeError, ValueError):
                    pass
    if not pending_rv:
        return {}

    sym_dir = os.path.join(root, "analysis", "symbols")
    if not os.path.isdir(sym_dir):
        return {}
    funcs_db, _, _ = symbols.load(root=sym_dir, strict=False, repo_root=root)
    created_rel = f"analysis/symbols/{area}.toml"
    allowed_tomls = {created_rel} | {str(t).replace("\\", "/") for t in (owned_tomls or ())}
    to_wire = {}
    for a, node in sorted(pending_rv.items()):
        e = funcs_db.get(a)
        if not e:
            continue
        ef = os.path.relpath(os.path.join(path(), e["_file"]), root).replace("\\", "/")
        if ef not in allowed_tomls or batch_driver._is_protected_toml(ef, created_rel=created_rel, cwd=root):
            continue
        if not e.get("ref") or not e.get("t3_blocker") or e.get("ref_verified_by"):
            continue
        ok, _reason = batch_driver.verify_t4_node(
            node, ref_rel=e.get("ref"), orig_addr=a, func_name=e.get("link_name"), cwd=root,
        )
        if ok:
            to_wire[a] = node
    if to_wire:
        batch_driver._update_existing_toml_entries({}, {}, ref_verified=to_wire,
                                                   created_toml=created_rel, cwd=root)
    return to_wire


def _verify_staged_toml_refs(changed_paths, cwd=None):
    """Ensure every src=/ref= path in modified TOMLs is tracked in git or in changed_paths."""
    import tomllib
    root = cwd or path()
    changed_set = set(changed_paths)
    toml_rels = [r for r in sorted(changed_set)
                 if r.startswith("analysis/symbols/") and r.endswith(".toml")]
    if not toml_rels:
        return []
    r = subprocess.run(["git", "ls-files"], capture_output=True, text=True, cwd=root, check=True)
    tracked_set = set(r.stdout.splitlines())
    known = tracked_set | changed_set
    missing = []
    for rel in toml_rels:
        full = os.path.join(root, rel)
        if not os.path.isfile(full):
            continue
        try:
            data = tomllib.loads(open(full, encoding="utf-8").read())
        except Exception:
            continue
        for fn in data.get("func", []):
            for key in ("src", "ref"):
                p = fn.get(key)
                if p and p not in known:
                    missing.append(p)
            vb = str(fn.get("verified_by") or "")
            if not fn.get("src") and vb.startswith("match:"):
                m_src = re.search(r"\b(src/[^\s)]+\.c)\b", vb)
                if m_src:
                    ms = m_src.group(1)
                    if ms not in known:
                        missing.append(ms)
                    elif os.path.exists(os.path.join(root, "original", "install", "war.exe")) and os.environ.get("WATCOM"):
                        # Unbuildable T3 (no src=): re-check wc1.match directly
                        r_m = subprocess.run(
                            [sys.executable, "-m", "wc1.match", ms],
                            capture_output=True, text=True, cwd=root,
                        )
                        if r_m.returncode != 0 or "MATCH" not in r_m.stdout:
                            missing.append(f"unmatched:{ms}")
    return sorted(set(missing))


def build_cli_args(cfg):
    """Build deterministic `python3 -m wc1.overnight --headless ...` args from a config dict."""
    args = ["--headless"]
    args += ["--window-budget", f"{float(cfg.get('window_budget', 0.8)):.2f}"]
    args += ["--window-capacity", f"{float(cfg.get('window_capacity', 35.0)):.1f}"]
    args += ["--max-modules", str(int(cfg.get("max_modules", 0)))]
    args += ["--wave", str(cfg.get("wave", "all"))]
    args += ["--chunk-size", str(int(cfg.get("chunk_size", 12)))]
    args += ["--max-chunk-insns", str(int(cfg.get("max_chunk_insns", DEFAULT_MAX_CHUNK_INSNS)))]
    args += ["--module-budget", f"{float(cfg.get('module_budget', 1.10)):.2f}"]
    args += ["--module-calls", str(int(cfg.get("module_calls", 10)))]
    args += ["--repair-budget", f"{float(cfg.get('repair_budget', 0.45)):.2f}"]
    skip = cfg.get("skip", DEFAULT_SKIP)
    if isinstance(skip, (list, tuple, set)):
        skip_str = ",".join(str(s).strip() for s in skip if str(s).strip())
    else:
        skip_str = str(skip or "").strip()
    args += ["--skip", skip_str]
    only = cfg.get("only") or ""
    if isinstance(only, (list, tuple, set)):
        only_str = ",".join(str(s).strip() for s in only if str(s).strip())
    else:
        only_str = str(only).strip()
    if only_str:
        args += ["--only", only_str]
    if not cfg.get("sleep_on_limit", True):
        args.append("--no-sleep")
    args += ["--rate-limit-sleep", str(int(cfg.get("rate_limit_sleep", 900)))]
    args += ["--stall-timeout", str(int(cfg.get("stall_timeout", DEFAULT_STALL_TIMEOUT)))]
    if str(cfg.get("wave", "all")) in WAVE4_WAVES:
        args += ["--wave4-max-calls", str(int(cfg.get("wave4_max_calls") or WAVE4_MAX_CALLS))]
        if cfg.get("wave4a_max_calls") is not None:
            args += ["--wave4a-max-calls", str(int(cfg["wave4a_max_calls"]))]
        if cfg.get("wave4_retry"):
            args.append("--wave4-retry")
        if cfg.get("wave4_include_unresolved"):
            args.append("--wave4-include-unresolved")
    if cfg.get("provider") == "codex":
        args += ["--provider", "codex"]
        if cfg.get("codex_model"):
            args += ["--codex-model", str(cfg["codex_model"])]
        if cfg.get("codex_effort"):
            args += ["--codex-effort", str(cfg["codex_effort"])]
        for st in codex.STAGES:
            val = cfg.get(f"codex_{st}")
            if val:
                args += [f"--codex-{st}", str(val)]
        args += ["--codex-repair-calls", str(int(cfg.get("codex_repair_calls", 1)))]
        if cfg.get("codex_bin"):
            args += ["--codex-bin", str(cfg["codex_bin"])]
        if cfg.get("codex_home"):
            args += ["--codex-home", str(cfg["codex_home"])]
        if cfg.get("codex_max_5h_pct") is not None:
            args += ["--codex-max-5h-pct", f"{float(cfg['codex_max_5h_pct']):g}"]
        if cfg.get("codex_max_7d_pct") is not None:
            args += ["--codex-max-7d-pct", f"{float(cfg['codex_max_7d_pct']):g}"]
        if cfg.get("codex_max_7d_delta_pp") is not None:
            args += ["--codex-max-7d-delta-pp", f"{float(cfg['codex_max_7d_delta_pp']):g}"]
        if cfg.get("codex_max_total_calls") is not None:
            args += ["--codex-max-total-calls", str(int(cfg["codex_max_total_calls"]))]
        if cfg.get("codex_telemetry_max_age") is not None:
            args += ["--codex-telemetry-max-age", str(int(cfg["codex_telemetry_max_age"]))]
        if cfg.get("codex_early_stop_stage2"):
            args.append("--codex-early-stop-stage2")
    return args


class _RunController:
    """Manages live state publishing, IPC control polling, and signal handling."""

    def __init__(self, config, start_prog, root=None):
        self.root = root
        self.config = dict(config)
        self.run_id = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.getpid()}"
        self.started_at = time.time()
        self.start_prog = start_prog
        self.cur_prog = start_prog
        self.status = "RUNNING"
        self.status_detail = "Starting run"
        self.build_status = "UNKNOWN"
        self.pause_requested = False
        self.stop_requested = False
        self.kill_requested = False
        self.wake_requested = False
        self.sleep_until = None
        self.sleep_reason = ""
        self.active_workers = []
        self.completed = []
        self.commits = []
        self.failed_modules = []
        self.failed_addrs = []
        self.queue = []
        self.active_proc = None
        self._last_publish = 0.0

    def install_signals(self):
        self._prev_usr1 = signal.getsignal(signal.SIGUSR1)
        self._prev_term = signal.getsignal(signal.SIGTERM)
        signal.signal(signal.SIGUSR1, self._on_sigusr1)
        signal.signal(signal.SIGTERM, self._on_sigterm)

    def restore_signals(self):
        if hasattr(self, "_prev_usr1"):
            signal.signal(signal.SIGUSR1, self._prev_usr1)
        if hasattr(self, "_prev_term"):
            signal.signal(signal.SIGTERM, self._prev_term)

    def _on_sigusr1(self, _signum, _frame):
        self.stop_requested = True

    def _on_sigterm(self, _signum, _frame):
        self.kill_requested = True

    def poll_control(self):
        cmd = live.consume_control(root=self.root)
        if not cmd:
            return None
        action = str(cmd.get("action") or "").lower()
        if action == "pause":
            self.pause_requested = True
            self.publish(force=True)
        elif action == "resume":
            self.pause_requested = False
            self.publish(force=True)
        elif action == "wake":
            self.wake_requested = True
            self.pause_requested = False
            self.publish(force=True)
        elif action in ("graceful_stop", "stop"):
            self.stop_requested = True
            self.wake_requested = True
            self.pause_requested = False
            if self.status not in ("DONE", "FAILED", "KILLED"):
                self.status_detail = "Graceful stop requested (finishing current module)"
            self.publish(force=True)
        elif action == "kill":
            self.kill_requested = True
            self.wake_requested = True
            self.pause_requested = False
            if self.active_proc is not None:
                live.terminate_process_tree(self.active_proc)
            self.status = "KILLED"
            self.status_detail = "Immediate kill requested — terminating active worker"
            self.publish(force=True)
        return action

    def sync_active_worker_phase(self, default_phase=None):
        """Propagate live sub-phase (THINKING / PERMUTING / VERIFYING) from worker meta."""
        if not self.active_workers:
            return
        w = self.active_workers[0]
        meta = live.read_worker_meta(w["id"], root=self.root)
        if meta:
            if meta.get("phase"):
                w["phase"] = meta["phase"]
            if meta.get("stage"):
                w["stage"] = meta["stage"]
            if meta.get("model"):
                w["model"] = meta["model"]
            if meta.get("effort"):
                w["effort"] = meta["effort"]
        if default_phase:
            w["phase"] = default_phase
        # Mirror active worker sub-phase to runner status when in active run
        if self.stop_requested and self.status not in ("DONE", "FAILED", "KILLED"):
            self.status = "STOPPING"
        elif w.get("phase") in ("THINKING", "PERMUTING", "VERIFYING", "REPAIRING", "COMMITTING"):
            self.status = w["phase"]

    def _compute_metrics(self):
        m = ledger_metrics()
        run_fns = sum(max(0, int(r.get("delta") or 0)) for r in self.completed)
        run_cost = sum(float(r.get("cost") or 0.0) for r in self.completed)
        cost_per_fn = round(run_cost / run_fns, 4) if run_fns > 0 else (
            round(m["spend_5h"] / max(1, m["calls_5h"]), 4) if m["calls_5h"] > 0 else 0.06
        )
        rl = live.load_rate_limits(root=self.root)
        five = rl.get("five_hour") if isinstance(rl.get("five_hour"), dict) else None
        cap = float(self.config.get("window_capacity", 35.0))
        budget = float(self.config.get("window_budget", 0.8))
        if five and five.get("utilization") is not None:
            rem_frac = max(0.0, budget - float(five["utilization"]))
            rem_usd = rem_frac * cap
        else:
            rem_usd = max(0.0, budget * cap - m["spend_5h"])
        est_fns = int(rem_usd / cost_per_fn) if cost_per_fn > 0.001 else 0
        m["cost_per_fn"] = cost_per_fn
        m["est_fns_left"] = est_fns
        m["run_cost"] = round(run_cost, 4)
        return m

    def publish(self, force=False):
        now = time.time()
        if not force and (now - self._last_publish) < 0.4:
            return
        self._last_publish = now
        done, total, t3, t4 = self.cur_prog
        sp_done, _, sp_t3, sp_t4 = self.start_prog
        payload = {
            "schema_version": 2,
            "pid": os.getpid(),
            "run_id": self.run_id,
            "started_at": self.started_at,
            "updated_at": now,
            "status": self.status,
            "status_detail": self.status_detail,
            "build_status": self.build_status,
            "pause_requested": self.pause_requested,
            "stop_requested": self.stop_requested,
            "sleep_until": self.sleep_until,
            "sleep_reason": self.sleep_reason,
            "config": self.config,
            "progress": {
                "start_done": sp_done,
                "done": done,
                "total": total,
                "start_t3": sp_t3,
                "t3": t3,
                "start_t4": sp_t4,
                "t4": t4,
                "delta_done": done - sp_done,
            },
            "metrics": self._compute_metrics(),
            "active_workers": list(self.active_workers),
            "active_worker": self.active_workers[0] if self.active_workers else None,
            "completed": list(self.completed[-80:]),
            "commits": list(self.commits[-50:]),
            "failed_modules": sorted(set(self.failed_modules)),
            "failed_addrs": sorted(set(self.failed_addrs)),
            "queue": [
                {
                    "module": q["module"],
                    "mode": q["mode"],
                    "area": q["area"],
                    "count": q["count"],
                    "module_total": q["module_total"],
                    "avg_insns": q["avg_insns"],
                }
                for q in self.queue[:30]
            ],
        }
        try:
            live.write_json_atomic(live.state_path(root=self.root), payload)
        except OSError:
            pass


def _kill_stalled(proc, fd, partial, buf, log_fh, stall_worker_id, msg):
    """SIGUSR1 (stack dump), collect up to 2 s of output, kill the tree, raise StallError."""
    try:
        os.kill(proc.pid, signal.SIGUSR1)
    except OSError:
        pass
    dump_end = time.monotonic() + 2.0
    while time.monotonic() < dump_end:
        ready, _, _ = select.select([fd], [], [], 0.2)
        if not ready:
            continue
        try:
            chunk = os.read(fd, 65536)
        except OSError:
            break
        if not chunk:
            break
        partial += chunk
    tail = partial.decode("utf-8", errors="replace")
    out = tail + ("\n" if tail and not tail.endswith("\n") else "") + msg + "\n"
    sys.stdout.write(out)
    sys.stdout.flush()
    log_fh.write(out)
    log_fh.flush()
    buf.append(out)
    if stall_worker_id:
        live.append_event(stall_worker_id, "error", msg)
    live.terminate_process_tree(proc)
    # A leader without a SIGUSR1 handler died of the signal already, which makes
    # terminate_process_tree a no-op: kill what is left of its group directly
    # (the stuck grandchild, e.g. wine wcc386, is the point of the watchdog).
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(proc.pid, sig)
        except OSError:
            break
        time.sleep(0.5)
    err = StallError(msg)
    err.output = "".join(buf)
    raise err


def _reset_wine():
    """Best effort `wineserver -k` on the 10.0a prefix after a stall: killing
    the stuck process group leaves a wineserver that daemonized into its own
    session, and a wedged one would hang the next item's compile too."""
    try:
        from . import oldcc
        oldcc.kill_wineserver(oldcc.wine_env())
    except Exception:
        pass


def _idle_seconds(stall_worker_id, last_output):
    """Seconds since the latest sign of life: child output (last_output, a
    time.monotonic() stamp, immune to wall-clock jumps), or its live event
    stream / meta heartbeat (wall-clock stamps written by the child)."""
    idle = time.monotonic() - last_output
    if stall_worker_id:
        t = 0.0
        try:
            t = os.path.getmtime(live.worker_stream_path(stall_worker_id))
        except OSError:
            pass
        try:
            t = max(t, float(live.read_worker_meta(stall_worker_id).get("updated_at") or 0.0))
        except (TypeError, ValueError):
            pass
        if t:
            idle = min(idle, max(0.0, time.time() - t))
    return idle


def _run_subprocess_logged(cmd, log_fh, cwd=None, controller=None, worker_id=None,
                           event_kind="info", stall_timeout=None, stall_worker_id=None):
    """Run command in its own process group, streaming output + polling IPC/kill.

    With `stall_timeout` (seconds), the child is killed and StallError raised
    once it printed nothing and `stall_worker_id`'s live stream/meta was not
    touched for that long (SIGUSR1 first, so a faulthandler-enabled child
    dumps its stacks into the log)."""
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=cwd or path(),
        start_new_session=True,
    )
    if controller is not None:
        controller.active_proc = proc

    buf = []
    assert proc.stdout is not None
    fd = proc.stdout.fileno()
    partial = b""
    last_poll = 0.0
    last_output = time.monotonic()
    last_stall_check = last_output

    try:
        while True:
            if stall_timeout and stall_timeout > 0:
                now = time.monotonic()
                if now - last_stall_check >= 1.0:
                    last_stall_check = now
                    idle = _idle_seconds(stall_worker_id, last_output)
                    # output already waiting in the pipe is a sign of life: read it first
                    if (idle > stall_timeout and proc.poll() is None
                            and not select.select([fd], [], [], 0)[0]):
                        _kill_stalled(proc, fd, partial, buf, log_fh, stall_worker_id,
                                      f"[STALL] no output or heartbeat for {idle:.0f}s "
                                      f"(> {stall_timeout}s); killing {' '.join(map(str, cmd[1:4]))}")
            if controller is not None:
                now = time.time()
                if now - last_poll >= 0.25:
                    last_poll = now
                    controller.poll_control()
                    if controller.kill_requested:
                        live.terminate_process_tree(proc)
                        raise ImmediateKillError("immediate kill requested")
                    controller.sync_active_worker_phase()
                    controller.publish()

            ready, _, _ = select.select([fd], [], [], 0.25)
            if ready:
                chunk = os.read(fd, 4096)
                if not chunk:
                    break
                partial += chunk
                last_output = time.monotonic()
                while b"\n" in partial:
                    raw_line, partial = partial.split(b"\n", 1)
                    line = raw_line.decode("utf-8", errors="replace") + "\n"
                    sys.stdout.write(line)
                    sys.stdout.flush()
                    log_fh.write(line)
                    log_fh.flush()
                    buf.append(line)
                    if worker_id and event_kind:
                        s = line.strip()
                        if s:
                            live.append_event(worker_id, event_kind, s)
            elif proc.poll() is not None:
                # Drain any final buffered bytes
                try:
                    rest = os.read(fd, 65536)
                    if rest:
                        partial += rest
                except OSError:
                    pass
                break

        if partial:
            line = partial.decode("utf-8", errors="replace")
            sys.stdout.write(line)
            sys.stdout.flush()
            log_fh.write(line)
            log_fh.flush()
            buf.append(line)
            if worker_id and event_kind and line.strip():
                live.append_event(worker_id, event_kind, line.strip())

        rc = proc.wait()
        return rc, "".join(buf)
    finally:
        if proc.poll() is None:
            live.terminate_process_tree(proc)
        if controller is not None and controller.active_proc is proc:
            controller.active_proc = None


_RATE_LIMIT_RES = (
    re.compile(r"\brate[\s_-]?limit", re.I),
    re.compile(r"\busage\s+limit", re.I),
    re.compile(r"\b(?:5-hour|7-day)\s+limit", re.I),
    re.compile(r"\btoo\s+many\s+requests\b", re.I),
    re.compile(r"\boverloaded_error\b", re.I),
    re.compile(r"\b429\b"),
    re.compile(r"\bcredit\s+balance\b", re.I),
)


def _rate_limit_event_rejected(rl):
    if not isinstance(rl, dict):
        return False
    if rl.get("status") == "rejected":
        return True
    info = rl.get("rate_limit_info")
    if isinstance(info, dict) and info.get("status") == "rejected":
        return True
    for key in ("five_hour", "seven_day"):
        win = rl.get(key)
        if isinstance(win, dict) and win.get("status") == "rejected":
            return True
    return False


def _is_repair_rate_limited(rc, result_obj, stderr_txt, rl_rejected=False):
    """Detect a genuine Claude rate limit during stream-json bounded repair.

    Never substring-matches 'rate_limit' against raw stream-json lines, and
    never rejects a clean rc==0 non-error repair result even if one quota
    window reported rejected while another/overage served the request.
    """
    res_is_error = bool((result_obj or {}).get("is_error"))
    if rc == 0 and result_obj is not None and not res_is_error:
        return False
    if rl_rejected:
        return True
    err_parts = []
    if isinstance(result_obj, dict) and result_obj.get("result"):
        err_parts.append(str(result_obj.get("result")))
    if stderr_txt:
        err_parts.append(str(stderr_txt))
    err_txt = "\n".join(err_parts)
    return any(rx.search(err_txt) for rx in _RATE_LIMIT_RES)


def _collect_extra_verify_failures(changed_paths, v_out, cwd=None, timeout=900):
    """When `make verify` short-circuited before `pytest` (e.g. at `compile-check`
    or `symbols`), run this module's new test file(s) and `wc1.symbols` so the
    first repair pass sees ALL failures up front.
    """
    root = cwd or path()
    out_text = v_out or ""
    # If pytest already ran in `make verify`, no extra probe needed.
    if "python3 -m pytest" in out_text or "short test summary info" in out_text:
        return ""
    extras = []
    if "python3 -m wc1.symbols" not in out_text:
        try:
            r_sym = subprocess.run(
                [sys.executable, "-m", "wc1.symbols"],
                capture_output=True, text=True, cwd=root, timeout=min(120, timeout),
            )
            if r_sym.returncode != 0:
                extras.append("=== wc1.symbols ===\n" + (r_sym.stdout + r_sym.stderr).strip()[-1500:])
        except subprocess.TimeoutExpired:
            extras.append("=== wc1.symbols ===\nTimed out running wc1.symbols")
    test_files = sorted(
        p for p in changed_paths
        if p.startswith("tests/") and os.path.basename(p).startswith("test_") and p.endswith(".py")
        and os.path.isfile(os.path.join(root, p))
    )
    if test_files:
        try:
            r_pt = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", "--tb=short", *test_files],
                capture_output=True, text=True, cwd=root, timeout=timeout,
            )
            if r_pt.returncode != 0:
                extras.append("=== pytest (module tests) ===\n" + (r_pt.stdout + r_pt.stderr).strip()[-2500:])
        except subprocess.TimeoutExpired:
            extras.append(f"=== pytest (module tests) ===\nTimed out after {timeout}s running {test_files}")
    return "\n\n".join(extras)


def run_bounded_repair(item, changed_paths, failure_tail, repair_budget, log_fh,
                       controller=None, claude_bin="claude", timeout=600):
    """Run ONE isolated streaming `claude -p` repair pass scoped strictly to this module."""
    if repair_budget <= 0:
        return False, 0.0, False, ""
    area = item["area"]
    ledger = batch_driver.Ledger(path("build", "ledger", f"{area}.jsonl"))
    editable_paths = set(changed_paths)
    item_hdr = item.get("header")
    if item_hdr and str(item_hdr).replace("\\", "/") != "src/include/war.h":
        if os.path.isfile(path(item_hdr)):
            editable_paths.add(str(item_hdr).replace("\\", "/"))
    files_str = "\n".join(f"  - {p}" for p in sorted(editable_paths))
    dossier_rel = f"build/driver/{area}_dossier.md"
    dossier_hint = (
        f"- Disassembly & xrefs dossier is already on disk at `{dossier_rel}` — Read it instead of guessing!\n"
        if os.path.isfile(path(dossier_rel)) else ""
    )
    test_files = [
        p for p in sorted(changed_paths)
        if p.startswith("tests/") and os.path.basename(p).startswith("test_") and p.endswith(".py")
    ]
    c_files = [p for p in sorted(changed_paths) if p.startswith("src/") and p.endswith(".c")]
    test_cmd = f"python3 -m pytest -q {' '.join(test_files)}" if test_files else "python3 -m pytest -q <test_file>"
    cc_hint = (
        f"python3 -m wc1.match --compile-check {' '.join(c_files[:12])}"
        if c_files else "python3 -m wc1.match --compile-check"
    )
    prompt = (
        f"Fix the failing verification/tests for module `{item['module']}` (area `{area}`).\n"
        f"ONLY edit files belonging to this module:\n{files_str}\n\n"
        f"HARD RULES:\n"
        f"{dossier_hint}"
        f"- NEVER add `@pytest.mark.xfail`, `@pytest.mark.skip`, `@pytest.mark.skipif`, or inline `pytest.skip(...)`.\n"
        f"- NEVER wrap `t4spec.run_spec` or `cemu.run_pair` in `pytest.raises`, `contextlib.suppress`, `try/except`, or `finally: return`.\n"
        f"- NEVER weaken, delete, or alter failing test inputs to hide a bug in `*_reference.c` — compare against the disassembly and fix the C code instead.\n"
        f"- NEVER pass empty `watch` + empty `out_regs` + empty `stubs`, and NEVER stub or overwrite `orig_addr`.\n"
        f"- If a module header prototype disagrees with disassembly (`ret N` / call-site registers), only fix it if it does not break other callers in `make verify`.\n"
        f"- NEVER edit Makefile, tools/, war.h, analysis/symbols/codegen_promo.toml, existing tracked tests, or unrelated modules.\n"
        f"- NEVER run `git commit` or `git add`.\n"
        f"- NEVER delete existing `src =` or `ref_verified_by =` entries to silence a build/test failure.\n"
        f"- NEVER edit `ref_verified_by` in TOML files — the runner verifies each passing T4 test and wires `ref_verified_by` mechanically.\n"
        f"- Keep every `extern` declaration in `*_reference.c` on ONE single line.\n"
        f"- Allocate test buffers ONLY inside `init_emu(emu)` so they never overlap C code at 0x800000.\n"
        f"- After editing, verify ALL THREE before finishing (even if the initial failure stopped at compile-check or symbols):\n"
        f"  1) `{cc_hint}`\n"
        f"  2) `{test_cmd}` (0 failed, 0 skipped)\n"
        f"  3) `python3 -m wc1.symbols`\n\n"
        f"Failure output:\n```\n{failure_tail[-5500:]}\n```\n"
    )
    cmd = [
        claude_bin, "-p",
        "--model", "sonnet",
        "--effort", "medium",
        "--allowedTools", "Read,Edit,Bash",
        "--max-turns", "16",
        "--max-budget-usd", f"{repair_budget:.2f}",
        "--no-session-persistence",
        "--output-format", "stream-json",
        "--verbose",
        "--include-partial-messages",
    ]
    live.update_worker_meta(area, phase="REPAIRING", stage="overnight_repair",
                            model="sonnet", effort="medium")
    live.append_event(area, "info", f"Starting bounded repair (${repair_budget:.2f} cap)")

    t0 = time.time()
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=path(),
        start_new_session=True,
    )
    if controller is not None:
        controller.active_proc = proc

    def _feed_stdin():
        try:
            assert proc.stdin is not None
            proc.stdin.write(prompt.encode("utf-8"))
            proc.stdin.flush()
        except OSError:
            pass
        finally:
            try:
                if proc.stdin is not None:
                    proc.stdin.close()
            except OSError:
                pass

    stderr_chunks = []

    def _drain_stderr():
        try:
            assert proc.stderr is not None
            while True:
                chunk = proc.stderr.read(4096)
                if not chunk:
                    break
                stderr_chunks.append(chunk)
        except OSError:
            pass

    t_in = threading.Thread(target=_feed_stdin, daemon=True)
    t_err = threading.Thread(target=_drain_stderr, daemon=True)
    t_in.start()
    t_err.start()

    result_obj = None
    rl_rejected = False
    raw_lines = []
    think_buf = []
    text_buf = []

    def _flush_buf(buf, kind):
        if not buf:
            return
        joined = "".join(buf)
        buf.clear()
        for ln in joined.splitlines():
            if ln.strip():
                live.append_event(area, kind, ln)

    assert proc.stdout is not None
    fd = proc.stdout.fileno()
    partial = b""
    deadline = t0 + max(30, timeout)

    try:
        while True:
            if controller is not None:
                controller.poll_control()
                if controller.kill_requested:
                    live.terminate_process_tree(proc)
                    raise ImmediateKillError("immediate kill requested during repair")
                controller.publish()
            if time.time() > deadline:
                live.terminate_process_tree(proc)
                cost_to = float((result_obj or {}).get("total_cost_usd") or 0.0)
                if cost_to > 0:
                    ledger.record("claude_call", label=f"{area}:overnight_repair_timeout",
                                  model="sonnet", effort="medium", cost_usd=cost_to,
                                  duration_s=round(time.time() - t0, 2),
                                  usage=(result_obj or {}).get("usage") or {})
                live.append_event(area, "error", f"Bounded repair timed out after {timeout}s")
                return False, cost_to, False, "repair timeout"

            ready, _, _ = select.select([fd], [], [], 0.25)
            if ready:
                chunk = os.read(fd, 4096)
                if not chunk:
                    break
                partial += chunk
                while b"\n" in partial:
                    raw_b, partial = partial.split(b"\n", 1)
                    line = raw_b.decode("utf-8", errors="replace")
                    raw_lines.append(line)
                    ev = live.parse_stream_json_line(line)
                    if not ev:
                        continue
                    k = ev["kind"]
                    if k == "thinking_delta":
                        think_buf.append(ev["text"])
                        if "\n" in ev["text"] or sum(len(x) for x in think_buf) >= 120:
                            _flush_buf(think_buf, "think")
                    elif k == "text_delta":
                        text_buf.append(ev["text"])
                        if "\n" in ev["text"] or sum(len(x) for x in text_buf) >= 160:
                            _flush_buf(text_buf, "out")
                    elif k == "tool_use":
                        _flush_buf(think_buf, "think")
                        live.append_event(area, "tool", f"tool_use: {ev.get('name', '')}")
                    elif k == "rate_limit":
                        live.save_rate_limits(ev["rate_limit"])
                        if _rate_limit_event_rejected(ev["rate_limit"]):
                            rl_rejected = True
                    elif k == "result":
                        result_obj = ev["result"]
            elif proc.poll() is not None:
                break

        _flush_buf(think_buf, "think")
        _flush_buf(text_buf, "out")
        rc = proc.wait()
        t_in.join(timeout=2.0)
        t_err.join(timeout=2.0)
    finally:
        if proc.poll() is None:
            live.terminate_process_tree(proc)
        if controller is not None and controller.active_proc is proc:
            controller.active_proc = None

    dt = round(time.time() - t0, 2)
    stderr_txt = b"".join(stderr_chunks).decode("utf-8", errors="replace")
    combined = "\n".join(raw_lines) + "\n" + stderr_txt
    cost = float((result_obj or {}).get("total_cost_usd") or 0.0)
    usage = (result_obj or {}).get("usage") or {}
    if _is_repair_rate_limited(rc, result_obj, stderr_txt, rl_rejected=rl_rejected):
        if cost > 0:
            ledger.record("claude_call", label=f"{area}:overnight_repair_rl", model="sonnet",
                          effort="medium", cost_usd=cost, duration_s=dt, usage=usage)
        log_fh.write(f"[{_now_str()}] [RATE_LIMIT during repair {area}]\n")
        log_fh.flush()
        live.append_event(area, "error", "Rate limit hit during bounded repair")
        rl_hint = str((result_obj or {}).get("result") or "") + "\n" + stderr_txt
        return False, cost, True, rl_hint

    res_subtype = str((result_obj or {}).get("subtype") or "")
    res_text = str((result_obj or {}).get("result") or "")
    turn_cap_hit = (
        res_subtype == "error_max_turns"
        or bool(re.search(r"\breached\s+max\s+turns\b", res_text + "\n" + stderr_txt, re.I))
    )
    ledger.record("claude_call", label=f"{area}:overnight_repair", model="sonnet",
                  effort="medium", cost_usd=cost, duration_s=dt, usage=usage,
                  turn_cap_hit=turn_cap_hit)
    tc_note = " [turn_cap_hit]" if turn_cap_hit else ""
    msg = f"  [repair {area}] rc={rc} {dt}s cost=${cost:.4f}{tc_note}\n"
    sys.stdout.write(msg)
    sys.stdout.flush()
    log_fh.write(msg)
    log_fh.flush()
    live.append_event(area, "info", msg.strip())
    return rc == 0, cost, False, combined


CODEX_VERIFY_PATCH_SCHEMA = {
    "type": "object",
    "properties": {
        "diagnosis": {"type": "string", "description": "Root cause citing exact disassembly/verify error"},
        "file_patches": {
            "type": "array",
            "description": "Search-and-replace patches strictly for this module's allowed files",
            "items": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Repo-relative path"},
                    "old": {"type": "string", "description": "Exact existing substring"},
                    "new": {"type": "string", "description": "Replacement substring"},
                },
                "required": ["path", "old", "new"],
            },
        },
    },
    "required": ["diagnosis", "file_patches"],
}


def _toml_ref_verified_by_map(txt):
    """Parsed `ref_verified_by` values of a symbols TOML, keyed by (table path, addr/name/index)."""
    import tomllib
    data = tomllib.loads(txt)
    out = {}

    def walk(node, where):
        if isinstance(node, dict):
            if "ref_verified_by" in node:
                key = node.get("addr", node.get("name", where))
                out[(where, repr(key))] = node.get("ref_verified_by")
            for k, v in node.items():
                if isinstance(v, (dict, list)):
                    walk(v, f"{where}.{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{where}[{i}]" if not isinstance(v, dict) or "addr" not in v else where)

    walk(data, "")
    return out


def _apply_codex_verify_patches(item, owned_tomls, patch_res, *, cwd=None, compile_check_fn=None):
    """Validate and apply structured Codex post-verify patches atomically.

    Every patch is validated in memory first:
      - strict `_check_allowed_paths` allowlist (no traversal, realpath/symlink containment);
      - TOML files must parse (`tomllib`) and keep every parsed `ref_verified_by`
        (runner-only mechanical wiring);
      - `tests/*.py`: AST cheat prefilter + anti-weakening (`allow_case_edits=False`);
      - changed `src/*.c` files (plus every `.c` in `src/<src_subdir>/` when a header
        changed) must pass `compile_check` with the new texts staged on disk.
    If ANY patch is rejected, every touched file is restored and nothing is applied
    (`applied == 0`).  A compile timeout restores everything and raises `ToolchainError`.
    """
    root = cwd or path()
    by_path = {}
    rejected = []
    for p in (patch_res.get("file_patches") or []) if isinstance(patch_res, dict) else []:
        if not isinstance(p, dict):
            rejected.append(f"malformed patch: {p!r}"[:200])
            continue
        raw_p = str(p.get("path") or "").replace("\\", "/")
        rel = posixpath.normpath(raw_p) if raw_p else ""
        if not raw_p or posixpath.isabs(rel) or rel == ".." or rel.startswith("../") or "/../" in rel:
            rejected.append(f"disallowed path traversal: {raw_p!r}")
            continue
        bad_paths = _check_allowed_paths([rel], item, owned_tomls=owned_tomls, cwd=root)
        if bad_paths:
            rejected.append(f"disallowed path: {rel}")
            continue
        by_path.setdefault(rel, []).append(p)

    # 1. In-memory validation (nothing written yet)
    staged = {}  # rel -> (full, old_txt, new_txt, cnt)
    for rel, plist in by_path.items():
        full = os.path.join(root, rel)
        if not os.path.isfile(full):
            rejected.append(f"missing file: {rel}")
            continue
        try:
            with open(full, encoding="utf-8") as fh:
                old_txt = fh.read()
        except (OSError, UnicodeDecodeError) as ex:
            rejected.append(f"unreadable file {rel}: {ex}")
            continue
        new_txt, cnt = batch_driver._apply_patches_text(old_txt, plist)
        if not cnt or new_txt == old_txt:
            rejected.append(f"no matching hunk in {rel}")
            continue
        if rel.endswith(".toml"):
            old_rv = re.findall(r"^\s*ref_verified_by\s*=.*$", old_txt, re.M)
            new_rv = re.findall(r"^\s*ref_verified_by\s*=.*$", new_txt, re.M)
            if old_rv != new_rv:
                rejected.append(f"rejected ref_verified_by edit in {rel} (runner wires it mechanically)")
                continue
            try:
                new_map = _toml_ref_verified_by_map(new_txt)
            except Exception as ex:
                rejected.append(f"rejected {rel}: patched TOML does not parse ({ex})")
                continue
            try:
                old_map = _toml_ref_verified_by_map(old_txt)
            except Exception:
                old_map = None
            if old_map is not None and old_map != new_map:
                rejected.append(f"rejected ref_verified_by edit in {rel} (parsed values changed)")
                continue
            if old_map is None and new_map:
                rejected.append(f"rejected {rel}: original TOML unparsable, cannot prove ref_verified_by unchanged")
                continue
        if rel.startswith("tests/") and rel.endswith(".py"):
            cheat = batch_driver.find_forbidden_test_cheat(new_txt)
            if cheat:
                rejected.append(f"test patch rejected for {rel} (forbidden test cheat: {cheat})")
                continue
            weak = batch_driver.check_test_patch_not_weakening(old_txt, new_txt, allow_case_edits=False)
            if weak:
                rejected.append(f"test patch rejected for {rel} ({weak})")
                continue
        staged[rel] = (full, old_txt, new_txt, cnt)

    # 2. Stage the validated texts on disk and compile-check; any failure restores all.
    def _restore_all():
        for _rel, (f, old, _new, _c) in staged.items():
            try:
                with open(f, "w", encoding="utf-8") as fh:
                    fh.write(old)
            except OSError:
                pass

    cc_fn = compile_check_fn or (lambda files: match.compile_check(files, jobs=1))
    cc_files = sorted(f for r, (f, _o, _n, _c) in staged.items() if r.startswith("src/") and r.endswith(".c"))
    if any(r.endswith(".h") for r in staged):
        sub = item.get("src_subdir") or item["area"]
        sub_dir = os.path.join(root, "src", *str(sub).split("/"))
        dep = sorted(glob.glob(os.path.join(sub_dir, "**", "*.c"), recursive=True))
        cc_files = sorted(set(cc_files) | set(dep))
    try:
        for _rel, (f, _old, new, _c) in staged.items():
            with open(f, "w", encoding="utf-8") as fh:
                fh.write(new)
        if cc_files:
            try:
                bad_cc = cc_fn(cc_files)
            except match.CompileTimeout as ex:
                _restore_all()
                raise batch_driver.ToolchainError(
                    f"codex repair compile-check timed out ({', '.join(sorted(staged))}): {ex}") from ex
            except (Exception, SystemExit) as ex:
                bad_cc = [(cc_files[0], str(ex))]
            if bad_cc:
                failed = sorted({os.path.relpath(str(b[0]), root) if isinstance(b, (tuple, list)) and b else str(b)
                                 for b in bad_cc})
                rejected.append(f"compile-check failed ({', '.join(failed)}: {bad_cc[:1]}); reverted all patches")
    except batch_driver.ToolchainError:
        raise
    except BaseException:
        _restore_all()
        raise

    if rejected:
        _restore_all()
        applied = 0
    else:
        applied = sum(c for (_f, _o, _n, c) in staged.values())
    return {"applied": applied, "rejected": rejected, "diagnosis": str((patch_res or {}).get("diagnosis") or "")}


def run_codex_structured_repair(item, changed_paths, owned_tomls, failure_tail, log_fh, *,
                                codex_matrix=None, codex_bin=None, codex_home=None,
                                codex_quota_guard=None, timeout=300, cwd=None,
                                max_calls=None):
    """Run ONE stateless structured-patch Codex repair call (no shell/FS access by model).

    Returns `(applied_any: bool, rl_hit: bool, quota_stop: bool, msg: str, resets_at: float|None)`.
    """
    root = cwd or path()
    area = item["area"]
    ledger = batch_driver.Ledger(os.path.join(root, "build", "ledger", f"{area}.jsonl"))
    editable = sorted(set(changed_paths))
    item_hdr = item.get("header")
    if item_hdr and str(item_hdr).replace("\\", "/") != "src/include/war.h":
        if os.path.isfile(os.path.join(root, item_hdr)):
            editable = sorted(set(editable) | {str(item_hdr).replace("\\", "/")})

    file_blocks = []
    for rel in editable:
        full = os.path.join(root, rel)
        if os.path.isfile(full):
            txt = open(full, encoding="utf-8", errors="replace").read()
            file_blocks.append(f"### {rel}\n```\n{txt[:14000]}\n```\n")

    dossier_path = os.path.join(root, "build", "driver", f"{area}_dossier.md")
    dossier_snippet = ""
    if os.path.isfile(dossier_path):
        dossier_snippet = open(dossier_path, encoding="utf-8", errors="replace").read()[:18000]

    sys_file = os.path.join(root, "build", "driver", f"{area}_sys.txt")
    if not os.path.isfile(sys_file):
        os.makedirs(os.path.dirname(sys_file), exist_ok=True)
        with open(sys_file, "w", encoding="utf-8") as fh:
            fh.write(batch_driver.DEFAULT_RULES)

    prompt = (
        f"Fix the failing verification/tests for module `{item['module']}` (area `{area}`).\n"
        f"Return ONLY structured search-and-replace patches (`file_patches`) for these allowed files:\n"
        + "\n".join(f"  - {p}" for p in editable)
        + "\n\nHARD RULES:\n"
        "- NEVER add `@pytest.mark.xfail`, `@pytest.mark.skip`, `@pytest.mark.skipif`, or `pytest.skip(...)`.\n"
        "- NEVER wrap `run_spec`/`run_pair` in `pytest.raises`, `contextlib.suppress`, or `try/except`.\n"
        "- NEVER weaken, delete, or alter existing `T4Case(...)` inputs to hide a bug in `*_reference.c`.\n"
        "- NEVER edit `ref_verified_by` in TOML files (runner wires it mechanically).\n"
        "- Keep every `extern` declaration in C files on ONE single line.\n\n"
        + (f"Module dossier:\n{dossier_snippet}\n\n" if dossier_snippet else "")
        + "Current module files:\n"
        + "\n".join(file_blocks)
        + f"\nVerification failure output:\n```\n{failure_tail[-5000:]}\n```\n"
    )

    matrix = codex_matrix or codex.DEFAULT_STAGE_MATRIX
    model, effort = matrix.get("repair", (codex.DEFAULT_MODEL, codex.DEFAULT_EFFORT))
    live.update_worker_meta(area, phase="REPAIRING", stage="codex_structured_repair",
                            model=model, effort=effort, provider="codex")
    live.append_event(area, "info", f"Starting Codex structured patch repair [{model}/{effort}]")

    try:
        patch_res, _meta = codex.call_codex(
            prompt, CODEX_VERIFY_PATCH_SCHEMA, sys_file,
            model=model, effort=effort,
            ledger=ledger, label=f"{area}:codex_repair",
            max_calls=max_calls,
            timeout=timeout, worker_id=area,
            codex_bin=codex_bin, codex_home=codex_home,
            quota_guard=codex_quota_guard, root=root,
        )
    except codex.CodexCallLimitError as ex:
        # S9: the item's repair call cap is spent; not a run-wide quota stop.
        log_fh.write(f"[{_now_str()}] [CODEX REPAIR CAP {area}] {ex}\n")
        log_fh.flush()
        return False, False, False, str(ex), None
    except codex.CodexQuotaError as ex:
        if ex.action == "wait":
            log_fh.write(f"[{_now_str()}] [CODEX RATE_LIMIT during repair {area}] {ex}\n")
            log_fh.flush()
            return False, True, False, str(ex), ex.resets_at
        log_fh.write(f"[{_now_str()}] [CODEX QUOTA_STOP during repair {area}] {ex}\n")
        log_fh.flush()
        return False, False, True, str(ex), ex.resets_at
    except (TimeoutError, RuntimeError, ValueError) as ex:
        log_fh.write(f"[{_now_str()}] [CODEX REPAIR ERROR {area}] {ex}\n")
        log_fh.flush()
        return False, False, False, str(ex), None

    pres = _apply_codex_verify_patches(item, owned_tomls, patch_res, cwd=root)
    msg = (f"  [codex repair {area}] applied={pres['applied']} rejected={len(pres['rejected'])} "
           f"diag={pres['diagnosis'][:120]}\n")
    sys.stdout.write(msg)
    sys.stdout.flush()
    log_fh.write(msg)
    for rj in pres["rejected"]:
        log_fh.write(f"    [rejected] {rj}\n")
    log_fh.flush()
    live.append_event(area, "info", msg.strip())
    return pres["applied"] > 0, False, False, msg, None


def _sum_ledger_tokens(areas, root=None):
    """Aggregate observed token counts across ledgers for `areas` (returns None fields if absent)."""
    base = root or path()
    in_tok = cached_tok = out_tok = reason_tok = 0
    seen = False
    for area in set(areas):
        lp = os.path.join(base, "build", "ledger", f"{area}.jsonl")
        if not os.path.isfile(lp):
            continue
        try:
            with open(lp, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                    except ValueError:
                        continue
                    u = rec.get("usage")
                    if not isinstance(u, dict) or not u:
                        continue
                    seen = True
                    in_tok += int(u.get("input_tokens") or 0)
                    cached_tok += int(u.get("cached_input_tokens") or u.get("cache_read_input_tokens") or 0)
                    out_tok += int(u.get("output_tokens") or 0)
                    reason_tok += int(u.get("reasoning_output_tokens") or 0)
        except OSError:
            continue
    if not seen:
        return None
    return {
        "input_tokens": in_tok,
        "cached_input_tokens": cached_tok,
        "output_tokens": out_tok,
        "reasoning_output_tokens": reason_tok,
    }


def write_wave4_metrics(results, start_progress, *, started_at, wave, provider="claude",
                        stop_reason="", reconcile_cache=None, retry_cache=None,
                        start_5h_pct=None, start_7d_pct=None, codex_home=None,
                        metrics_path=None):
    """Persist structured Wave 4A + Wave 4B production metrics strictly from observed telemetry."""
    if wave not in WAVE4_WAVES and not any(r.get("mode") in (WAVE4_MODE, WAVE4A_MODE) for r in results):
        return None
    done, total, t3, t4 = progress_done_count()
    sp_done, _, sp_t3, sp_t4 = start_progress
    w4a_recs = [r for r in results if r.get("mode") == WAVE4A_MODE]
    w4b_recs = [r for r in results if r.get("mode") == WAVE4_MODE]

    def _agg(recs, is_4a):
        committed = [r for r in recs if r.get("status") == "COMMITTED"]
        reconciled_only = [r for r in committed if r.get("w4_outcome") == "RECONCILED"]
        promoted_commits = [r for r in committed if r.get("w4_outcome") == "PROMOTED" or not is_4a]
        t3_proms = sum(max(0, int(r.get("delta_t3", r.get("delta", 0)) or 0)) for r in promoted_commits)
        llm_calls = sum(int(r.get("calls") or 0) for r in recs)
        mech_ok = sum(1 for r in committed if r.get("method") in ("mechanical", "auto_promote"))
        llm_ok = sum(1 for r in committed if r.get("method") == "research" or (not is_4a and int(r.get("calls") or 0) > 0))
        zero_llm_proms = sum(
            max(0, int(r.get("delta_t3", r.get("delta", 0)) or 0))
            for r in promoted_commits if int(r.get("calls") or 0) == 0
        )
        unblocked = sum(len(r.get("addrs") or ()) for r in committed) if is_4a else t3_proms
        unblocked_llm = sum(
            len(r.get("addrs") or ()) for r in committed if r.get("method") == "research"
        ) if is_4a else t3_proms
        p5_deltas = [r["primary_delta_pp"] for r in recs if r.get("primary_delta_pp") is not None]
        s7_deltas = [r["secondary_delta_pp"] for r in recs if r.get("secondary_delta_pp") is not None]
        out = {
            "attempted": len(recs),
            "committed": len(committed),
            "t3_promotions": t3_proms,
            "zero_llm_t3_promotions": zero_llm_proms,
            "reconciled_only_commits": len(reconciled_only),
            "resolved_mechanically": mech_ok,
            "resolved_via_llm": llm_ok,
            "functions_unblocked": unblocked,
            "functions_unblocked_via_llm": unblocked_llm,
            "ambiguous": sum(1 for r in recs if r.get("w4_outcome") == "AMBIGUOUS"),
            "no_improvement": sum(1 for r in recs if r.get("status") == "NOOP" and r.get("w4_outcome") != "AMBIGUOUS"),
            "failed_or_rolled_back": sum(1 for r in recs if r.get("status") in ("FAILED", "STALLED", "TOOLCHAIN_ERROR")),
            "llm_calls": llm_calls,
            "cost_usd": round(sum(float(r.get("cost") or 0.0) for r in recs), 4),
            "tokens": _sum_ledger_tokens([r.get("area") for r in recs if r.get("area")]),
            "primary_quota_delta_pp": round(sum(p5_deltas), 2) if p5_deltas else None,
            "secondary_quota_delta_pp": round(sum(s7_deltas), 2) if s7_deltas else None,
            "worker_seconds": round(sum(float(r.get("worker_s") or 0.0) for r in recs), 2),
            "verify_seconds": round(sum(float(r.get("verify_s") or 0.0) for r in recs), 2),
        }
        def _cache_diag(cache_obj):
            if cache_obj is not None and hasattr(cache_obj, "diagnostics_summary"):
                return cache_obj.diagnostics_summary()
            return {
                "schema_version": 2,
                "hits": 0,
                "preserved_unrelated": 0,
                "invalidated_dep_change": 0,
                "invalidated_legacy_schema": 0,
                "bypassed_uncertain": 0,
                "in_run_requeued": 0,
            }

        if is_4a:
            out["cache_hits_skipped"] = int(getattr(reconcile_cache, "skipped", 0) or 0)
            out["cache"] = _cache_diag(reconcile_cache)
            out["unresolved_relocs_eliminated"] = sum(
                max(0, int(r.get("unresolved_delta") or 0)) for r in committed
            )
        else:
            out["cache_hits_skipped"] = int(getattr(retry_cache, "skipped", 0) or 0)
            out["cache"] = _cache_diag(retry_cache)
        return out

    m4a = _agg(w4a_recs, True)
    m4b = _agg(w4b_recs, False)
    wall_s = max(0.001, time.time() - float(started_at))
    tot_t3 = m4a["t3_promotions"] + m4b["t3_promotions"]
    tot_zero = m4a["zero_llm_t3_promotions"] + m4b["zero_llm_t3_promotions"]
    tot_calls = m4a["llm_calls"] + m4b["llm_calls"]
    rl_end = codex.get_latest_rate_limits(codex_home=codex_home) if provider == "codex" else None
    end_5h = (rl_end.get("primary") or {}).get("used_percent") if isinstance(rl_end, dict) else None
    end_7d = (rl_end.get("secondary") or {}).get("used_percent") if isinstance(rl_end, dict) else None
    net_7d_pp = round(end_7d - start_7d_pct, 2) if (end_7d is not None and start_7d_pct is not None) else None
    net_5h_pp = round(end_5h - start_5h_pct, 2) if (end_5h is not None and start_5h_pct is not None) else None

    eff = {
        "t3_promotions_per_llm_call": round(tot_t3 / tot_calls, 3) if tot_calls > 0 else None,
        "t3_promotions_per_7d_pp": round(tot_t3 / net_7d_pp, 3) if (net_7d_pp is not None and net_7d_pp > 0) else None,
        "functions_unblocked_per_4a_llm_task": (
            round(m4a["functions_unblocked_via_llm"] / m4a["resolved_via_llm"], 3)
            if m4a["resolved_via_llm"] > 0 else None
        ),
        "zero_llm_t3_proportion": round(tot_zero / tot_t3, 3) if tot_t3 > 0 else None,
        "useful_commits_per_hour": round((m4a["committed"] + m4b["committed"]) / (wall_s / 3600.0), 2),
    }

    payload = {
        "updated_at": _now_str(),
        "wave": wave,
        "provider": provider,
        "stop_reason": stop_reason,
        "wall_seconds": round(wall_s, 2),
        "progress": {
            "start_done": sp_done, "done": done, "total": total,
            "start_t3": sp_t3, "t3": t3, "delta_t3": t3 - sp_t3,
            "start_t4": sp_t4, "t4": t4, "delta_t4": t4 - sp_t4,
        },
        "quota": {
            "start_5h_pct": start_5h_pct, "end_5h_pct": end_5h, "delta_5h_pp": net_5h_pp,
            "start_7d_pct": start_7d_pct, "end_7d_pct": end_7d, "delta_7d_pp": net_7d_pp,
        },
        "wave4a": m4a,
        "wave4b": m4b,
        "efficiency": eff,
    }
    out_fn = metrics_path or path("build", "wave4", "metrics.json")
    os.makedirs(os.path.dirname(out_fn), exist_ok=True)
    tmp = out_fn + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
    os.replace(tmp, out_fn)
    return payload


def write_summary(results, start_progress, summary_path=None, needs_human=None, provider="claude",
                  codex_home=None):
    done, total, t3, t4 = progress_done_count()
    sp_done, _, sp_t3, sp_t4 = start_progress
    if provider == "codex":
        total_calls = sum(int(r.get("calls") or 0) for r in results)
        rl = codex.get_latest_rate_limits(codex_home=codex_home)
        p5 = (rl.get("primary") or {}).get("used_percent")
        s7 = (rl.get("secondary") or {}).get("used_percent")
        q_desc = f"5h={p5}% 7d={s7}%" if (p5 is not None or s7 is not None) else "unobserved"
        lines = [
            "# wc1.overnight run summary (Codex Plus)",
            "",
            f"- Updated: `{_now_str()}`",
            f"- Progress: **{sp_done} -> {done} / {total} DONE ({100.0 * done / max(1, total):.1f}%)** "
            f"(T3: {sp_t3} -> {t3}, T4: {sp_t4} -> {t4}, delta: **+{done - sp_done}**)",
            f"- Codex run calls: **{total_calls}** | latest quota: `{q_desc}`",
            "",
            "| Time | Module | Mode | Area | Status | Delta DONE | Calls | 5h / 7d Delta | Commit / Note |",
            "|---|---|---|---|---|---:|---:|---|---|",
        ]
        for r in results:
            pd = r.get("primary_delta_pp")
            sd = r.get("secondary_delta_pp")
            qcol = f"{pd:+.1f}pp / {sd:+.1f}pp" if (pd is not None and sd is not None) else (f"{pd:+.1f}pp / n/a" if pd is not None else "n/a")
            lines.append(
                f"| {r['time']} | `{r['module']}` | `{r['mode']}` | `{r['area']}` | "
                f"**{r['status']}** | {r['delta']:+d} | {int(r.get('calls') or 0)} | {qcol} | {r['note']} |"
            )
    else:
        w_spend, w_calls, _ = rolling_window_spend()
        lines = [
            "# wc1.overnight run summary",
            "",
            f"- Updated: `{_now_str()}`",
            f"- Progress: **{sp_done} -> {done} / {total} DONE ({100.0 * done / max(1, total):.1f}%)** "
            f"(T3: {sp_t3} -> {t3}, T4: {sp_t4} -> {t4}, delta: **+{done - sp_done}**)",
            f"- Rolling 5h window spend: **${w_spend:.4f}** ({w_calls} Claude calls)",
            "",
            "| Time | Module | Mode | Area | Status | Delta DONE | Cost USD | Commit / Note |",
            "|---|---|---|---|---|---:|---:|---|",
        ]
        for r in results:
            lines.append(
                f"| {r['time']} | `{r['module']}` | `{r['mode']}` | `{r['area']}` | "
                f"**{r['status']}** | {r['delta']:+d} | ${r['cost']:.4f} | {r['note']} |"
            )
    if needs_human:
        lines += [
            "",
            f"## Skipped (needs human review: {len(needs_human)} functions)",
            "",
            "| Addr | Module | Name | Reason |",
            "|---|---|---|---|",
        ]
        for nh in needs_human[:60]:
            lines.append(
                f"| `{nh['addr']:#x}` | `{nh['module']}` | `{nh['name'] or '-'}` | {nh['reason']} |"
            )
        if len(needs_human) > 60:
            lines.append(f"\n_...and {len(needs_human) - 60} more._")
    out = summary_path or path("build", "overnight_summary.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as fh:
        fh.write("\n".join(lines) + "\n")


def _sleep_with_heartbeat(seconds, reason, log_fh, controller=None):
    end = time.time() + max(1, seconds)
    wake_str = datetime.datetime.fromtimestamp(end).strftime("%H:%M:%S")
    msg = f"[{_now_str()}] [SLEEP] {reason} — sleeping {int(seconds // 60)}m{int(seconds % 60)}s (until ~{wake_str})\n"
    sys.stdout.write(msg)
    sys.stdout.flush()
    log_fh.write(msg)
    log_fh.flush()
    if controller is not None:
        controller.status = "SLEEPING"
        controller.sleep_until = end
        controller.sleep_reason = reason
        controller.status_detail = f"{reason} (until ~{wake_str})"
        controller.publish(force=True)

    last_hb = time.time()
    try:
        while True:
            if controller is not None:
                controller.poll_control()
                if controller.kill_requested:
                    raise ImmediateKillError("immediate kill requested during sleep")
                if controller.stop_requested or controller.wake_requested:
                    controller.wake_requested = False
                    note = "stop requested" if controller.stop_requested else "early wake requested"
                    wmsg = f"[{_now_str()}] [SLEEP] waking early ({note})\n"
                    sys.stdout.write(wmsg)
                    sys.stdout.flush()
                    log_fh.write(wmsg)
                    log_fh.flush()
                    break
                controller.publish()
            rem = end - time.time()
            if rem <= 0:
                break
            time.sleep(min(rem, 0.5))
            if time.time() - last_hb >= 600 and (end - time.time()) > 30:
                last_hb = time.time()
                rem2 = end - time.time()
                hb = f"[{_now_str()}] [SLEEP] still waiting ({int(rem2 // 60)}m remaining)...\n"
                sys.stdout.write(hb)
                sys.stdout.flush()
                log_fh.write(hb)
                log_fh.flush()
    finally:
        if controller is not None:
            controller.sleep_until = None
            controller.sleep_reason = ""
            if not controller.stop_requested and not controller.kill_requested:
                controller.status = "RUNNING"
            controller.publish(force=True)


def _wait_while_paused(log_fh, controller):
    if not controller.pause_requested or controller.stop_requested or controller.kill_requested:
        return
    pmsg = f"[{_now_str()}] [PAUSED] paused at safe module boundary (waiting for resume)\n"
    sys.stdout.write(pmsg)
    sys.stdout.flush()
    log_fh.write(pmsg)
    log_fh.flush()
    controller.status = "PAUSED"
    controller.status_detail = "Paused at module boundary — press p to resume"
    controller.publish(force=True)
    while controller.pause_requested and not controller.stop_requested and not controller.kill_requested:
        controller.poll_control()
        if controller.kill_requested:
            raise ImmediateKillError("immediate kill requested while paused")
        controller.publish()
        time.sleep(0.25)
    if not controller.stop_requested and not controller.kill_requested:
        controller.status = "RUNNING"
        controller.status_detail = "Resumed"
        controller.publish(force=True)


def _compute_rate_limit_wait(out_txt, rate_limit_sleep, oldest_ts, rl_info=None, now=None):
    """Best available wait duration on a real rate limit: live resets_at > parsed text > oldest_ts."""
    now = time.time() if now is None else float(now)
    rl = rl_info or live.load_rate_limits()
    for key in ("five_hour", "seven_day"):
        win = rl.get(key) if isinstance(rl.get(key), dict) else None
        if win and win.get("status") == "rejected" and win.get("resets_at"):
            rem = float(win["resets_at"]) - now + 60
            if rem > 30:
                return int(rem)
    parsed_ts = parse_reset_text(out_txt, now=now)
    if parsed_ts and parsed_ts > now + 30:
        return int(parsed_ts - now + 60)
    return max(300, min(rate_limit_sleep, compute_wait_seconds(oldest_ts, now=now, fallback_seconds=rate_limit_sleep)))


def _fresh_start_7d(rl, max_age_s=codex.DEFAULT_TELEMETRY_MAX_AGE_S, now=None):
    """`(start_7d_pct, start_7d_resets_at)` from FRESH secondary telemetry only (S4).

    A stale or expired 7d reading is no baseline: it returns `(None, None)` and
    the baseline is taken lazily from the first fresh observation instead."""
    if not isinstance(rl, dict):
        return None, None
    sec = rl.get("secondary")
    fresh, _msg = codex.is_window_fresh(sec, rl.get("observed_at"), now=now, max_age_s=max_age_s)
    if not fresh:
        return None, None
    return float(sec["used_percent"]), float(sec["resets_at"])


def _after_reset_kwargs(slept_resets_at, now=None):
    """Gate kwargs for the one-shot post-reset resume (M1): only once the reset
    the runner slept through has actually passed."""
    if slept_resets_at is None:
        return {}
    now_ts = time.time() if now is None else float(now)
    if now_ts < float(slept_resets_at):
        return {}
    return {"after_reset": True, "slept_resets_at": float(slept_resets_at)}


def run_overnight(window_budget=0.8, window_capacity=35.0, max_modules=0,
                  wave="all", chunk_size=12, max_chunk_insns=DEFAULT_MAX_CHUNK_INSNS,
                  module_budget=1.10, module_calls=10, repair_budget=0.45,
                  skip=DEFAULT_SKIP, only=None, sleep_on_limit=True,
                  rate_limit_sleep=900, dry_run=False, stall_timeout=DEFAULT_STALL_TIMEOUT,
                  provider="claude", codex_model=None, codex_effort=None,
                  codex_stage1=None, codex_stage2=None, codex_stage3=None,
                  codex_stage4=None, codex_repair=None, codex_repair_calls=1,
                  codex_bin=None, codex_home=None, codex_max_5h_pct=None,
                  codex_max_7d_pct=90.0, codex_max_7d_delta_pp=None,
                  codex_max_total_calls=None,
                  codex_telemetry_max_age=codex.DEFAULT_TELEMETRY_MAX_AGE_S,
                  codex_early_stop_stage2=False, wave4_max_calls=WAVE4_MAX_CALLS,
                  wave4a_max_calls=WAVE4A_MAX_CALLS, wave4_retry=False,
                  wave4_include_unresolved=False):
    if not (0.0 < window_budget <= 1.0):
        raise ValueError(f"--window-budget must be in (0.0, 1.0], got {window_budget}")
    if int(max_chunk_insns) < 0:
        raise ValueError(f"--max-chunk-insns must be >= 0, got {max_chunk_insns}")
    if provider not in ("claude", "codex"):
        raise ValueError(f"--provider must be 'claude' or 'codex', got {provider!r}")
    if wave not in ("all", "wave2", "wave3", "wave4", "wave4a", "wave4b"):
        raise ValueError(f"--wave must be all, wave2, wave3, wave4, wave4a or wave4b, got {wave!r}")
    if int(wave4_max_calls) < 1:
        raise ValueError(f"--wave4-max-calls must be >= 1, got {wave4_max_calls}")
    if int(wave4a_max_calls) < 0:
        raise ValueError(f"--wave4a-max-calls must be >= 0, got {wave4a_max_calls}")

    codex_matrix = None
    start_5h_pct = None
    start_7d_pct = None
    start_7d_resets_at = None
    if provider == "codex":
        codex_matrix = codex.build_stage_matrix(
            default_model=codex_model,
            default_effort=codex_effort,
            overrides={
                "stage1": codex_stage1,
                "stage2": codex_stage2,
                "stage3": codex_stage3,
                "stage4": codex_stage4,
                "repair": codex_repair,
            },
        )
        rl_init = codex.get_latest_rate_limits(codex_home=codex_home)
        if isinstance(rl_init, dict) and isinstance(rl_init.get("primary"), dict):
            start_5h_pct = rl_init["primary"].get("used_percent")
        start_7d_pct, start_7d_resets_at = _fresh_start_7d(
            rl_init, max_age_s=codex_telemetry_max_age,
        )

    retry_cache = None
    reconcile_cache = None
    retry_options = {}
    if wave in WAVE4_WAVES:
        from . import wave4, wave4a
        model_effort_4b = codex_matrix[wave4.CODEX_RECOVERY_STAGE] if codex_matrix else wave4.CLAUDE_RECOVERY
        model_effort_4a = codex_matrix[wave4a.CODEX_RESEARCH_STAGE] if codex_matrix else wave4a.CLAUDE_RESEARCH
        if wave in ("wave4", "wave4b"):
            retry_cache = wave4.RetryCache(provider, model_effort_4b, wave4_max_calls,
                                           max_cost=float(f"{module_budget:.2f}"))
        if wave in ("wave4", "wave4a"):
            reconcile_cache = wave4a.ReconcileCache(provider, model_effort_4a, wave4a_max_calls,
                                                    max_cost=float(f"{module_budget:.2f}"))
        retry_options = {
            "retry_cache": retry_cache,
            "reconcile_cache": reconcile_cache,
            "retry_misses": wave4_retry,
            "wave4_include_unresolved": wave4_include_unresolved,
        }

    if dry_run:
        q, needs_human = build_queue_with_needs_human(
            wave=wave, chunk_size=chunk_size, skip=skip, only=only,
            module_budget=module_budget, module_calls=module_calls,
            max_chunk_insns=max_chunk_insns, provider=provider,
            refresh_stale=False, **retry_options,
        )
        if max_modules > 0:
            q = q[:max_modules]
        if provider == "codex":
            rl_cx = codex.get_latest_rate_limits(codex_home=codex_home)
            fresh_p, fresh_msg = codex.is_window_fresh(
                rl_cx.get("primary") if isinstance(rl_cx, dict) else None,
                rl_cx.get("observed_at") if isinstance(rl_cx, dict) else None,
                max_age_s=codex_telemetry_max_age,
            )
            p5 = (rl_cx.get("primary") or {}).get("used_percent") if isinstance(rl_cx, dict) else None
            s7 = (rl_cx.get("secondary") or {}).get("used_percent") if isinstance(rl_cx, dict) else None
            gate_preview = codex.check_codex_quota_gate(
                rl_cx, window_budget=window_budget, max_age_s=codex_telemetry_max_age,
                max_5h_pct=codex_max_5h_pct, max_7d_pct=codex_max_7d_pct,
                max_7d_delta_pp=codex_max_7d_delta_pp, start_7d_pct=start_7d_pct,
                start_7d_resets_at=start_7d_resets_at,
                total_calls_used=0, max_total_calls=codex_max_total_calls,
            )
            print(
                f"wc1.overnight DRY RUN [codex]: {len(q)} queue items ({len(needs_human)} fn needs-human) | "
                f"window_budget={window_budget:.2f} | module_calls={module_calls} repair_calls={codex_repair_calls} "
                f"(USD flags ignored for Codex)"
            )
            print(f"  Stage matrix: {codex.format_stage_matrix(codex_matrix)}")
            print(
                f"  Telemetry: 5h={p5}% 7d={s7}% ({fresh_msg}) | "
                f"caps: max_7d={codex_max_7d_pct}% max_7d_delta={codex_max_7d_delta_pp}pp "
                f"max_total_calls={codex_max_total_calls} | gate={gate_preview['action']}"
                + (f" ({gate_preview['reason']})" if gate_preview["reason"] else "")
            )
        else:
            w_spend, w_calls, _oldest = rolling_window_spend()
            cap_desc = (
                "FULL (until rate-limit)"
                if window_budget >= 1.0
                else f"${window_budget * window_capacity:.2f} ({int(window_budget * 100)}% of ${window_capacity:.0f})"
            )
            print(f"wc1.overnight DRY RUN: {len(q)} queue items ({len(needs_human)} fn needs-human) | rolling 5h spend=${w_spend:.4f} ({w_calls} calls) | window_budget={cap_desc}")
        for i, it in enumerate(q, 1):
            hdr_s = f" hdr={it['header']}" if it["header"] else ""
            lim_s = f" limit={it['limit']}" if it["limit"] else ""
            ci_s = f" insns={it['chunk_insns']}" if "chunk_insns" in it else ""
            if it["mode"] == WAVE4A_MODE:
                print(f"  {i:2d}. [{it['mode']}] {it['group_id']} class={it.get('classification')} "
                      f"mech={it.get('mechanical')} z0={it.get('zero_score_blocked_count', 0)} "
                      f"fns={it['count']} syms={','.join((it.get('symbols') or ())[:3])}")
                continue
            if it["mode"] == WAVE4_MODE:
                print(f"  {i:2d}. [{it['mode']}] {it['name']} {it['addrs'][0]:#x} {it['module']} ref={it['ref']} "
                      f"group={it['wave4_group']} audit={it.get('audit_status')} report={it.get('report_state')}")
                continue
            print(f"  {i:2d}. [{it['mode']:6s}] {it['module']:16s} area={it['area']:18s} "
                  f"fn={it['count']:2d}/{it['module_total']:2d} avg={it['avg_insns']:5.1f} insns/fn{ci_s}{lim_s}{hdr_s}")
        if reconcile_cache:
            if reconcile_cache.skipped:
                print(f"Skipped {reconcile_cache.skipped} cached Wave 4A misses/ambiguous (use --wave4-retry to reconsider).")
            diag_line = _format_cache_diag_summary("wave4a", reconcile_cache)
            if diag_line:
                print(diag_line)
        if retry_cache:
            if retry_cache.skipped:
                print(f"Skipped {retry_cache.skipped} cached Wave 4B misses (use --wave4-retry to reconsider).")
            diag_line = _format_cache_diag_summary("wave4b", retry_cache)
            if diag_line:
                print(diag_line)
        if needs_human:
            by_reason = defaultdict(int)
            for nh in needs_human:
                key_r = nh["reason"].split("(", 1)[0].strip()
                by_reason[key_r] += 1
            parts = ", ".join(f"{k}={v}" for k, v in sorted(by_reason.items()))
            print(f"Needs human ({len(needs_human)} fn skipped): {parts}")
        return 0

    if wave in WAVE4_WAVES:
        tracked0, baseline_untracked, _ = _wave4_status()
    else:
        tracked0, baseline_untracked = git_status()
    if tracked0:
        print(f"ERROR: dirty tracked files in working tree: {sorted(tracked0)}", file=sys.stderr)
        print("Commit or stash tracked modifications before running wc1.overnight.", file=sys.stderr)
        return 2

    os.makedirs(path("build"), exist_ok=True)
    log_path = path("build", "overnight.log")
    start_prog = progress_done_count()
    last_clean_done = start_prog[0]
    last_clean_snap = _snapshot_symbol_state()
    resume_item = None
    toolchain_failed = False
    fatal_rc = 0
    results = []
    failed_keys = set()
    failed_fingerprints = {}
    module_fail_counts = defaultdict(int)

    def _record_failed_item(it, *, fp_key=None, unconditional=False):
        k = it["key"]
        failed_keys.add(k)
        if it.get("mode") in (WAVE4_MODE, WAVE4A_MODE):
            rec = failed_fingerprints.setdefault(k, {"fingerprints": set(), "attempts": 0, "unconditional": False})
            rec["attempts"] += 1
            if unconditional or not fp_key:
                rec["unconditional"] = True
            else:
                rec["fingerprints"].add(fp_key)

    def _recompute_wave4_fp_after_noop(it, is_w4a):
        """If the pre-run fingerprint was bypassed (e.g. first run before OMF deps were
        captured on disk), recompute it now that `batch_driver` recorded `omf_deps`."""
        cur_fp = it.get("retry_fp")
        if cur_fp is not None and getattr(cur_fp, "key", None):
            return cur_fp, it.get("repo_state_hint")
        if it.get("retry_key"):
            return it.get("retry_key"), it.get("repo_state_hint")
        try:
            if is_w4a and reconcile_cache and it.get("task_kind") != "auto_promote":
                from . import wave4a as _w4a
                raw_items, info = _w4a.discover(refresh_stale=False)
                g = next((x for x in raw_items if x["group_id"] == it["group_id"]), None)
                if g is not None:
                    fp2 = reconcile_cache.compute_fingerprint(
                        g, matcher_sig=info.get("matcher_signature"), dep_ctx=info.get("dep_ctx"),
                    )
                    return fp2, _wave4_repo_state_hint(info)
            elif not is_w4a and retry_cache:
                from . import wave4 as _w4, wave4a as _w4a
                if _wave4_is_real_discover(_w4.discover):
                    rep = _w4a.load_audit_report_incremental(refresh_stale=False)
                    q_now, info = _w4.discover(report=rep, report_state="fresh", exclude_unresolved=False)
                else:
                    q_now, info = _w4.discover()
                addr0 = it["addrs"][0]
                c = next((x for x in q_now if x["addr"] == addr0), None)
                if c is not None:
                    sibs = [x for x in q_now if x["ref"] == c["ref"]]
                    fp2 = retry_cache.compute_fingerprint(
                        c, sibs, matcher=info.get("matcher_signature"), dep_ctx=info.get("dep_ctx"),
                    )
                    return fp2, _wave4_repo_state_hint(info)
        except Exception:
            pass
        return cur_fp, it.get("repo_state_hint")
    completed_runs = 0
    codex_run_calls = 0
    # M1: reset timestamp the runner last slept through (rate limit / quota wait).
    # Once `now >= cx_slept_resets_at` the next gate check may resume on telemetry
    # that still describes the expired window (one-shot; cleared after use).
    cx_slept_resets_at = None
    # S10: per-item ledger call baselines, kept across rate-limit resumes.
    item_call_base = {}
    observed_capacity = float(window_capacity)

    cfg = {
        "provider": provider,
        "window_budget": window_budget,
        "window_capacity": window_capacity,
        "max_modules": max_modules,
        "wave": wave,
        "chunk_size": chunk_size,
        "max_chunk_insns": max_chunk_insns,
        "module_budget": module_budget,
        "module_calls": module_calls,
        "repair_budget": repair_budget,
        "codex_repair_calls": codex_repair_calls,
        "codex_matrix": {k: list(v) for k, v in codex_matrix.items()} if codex_matrix else None,
        "skip": list(skip or ()),
        "only": list(only or ()),
        "sleep_on_limit": sleep_on_limit,
        "rate_limit_sleep": rate_limit_sleep,
        "stall_timeout": stall_timeout,
        "wave4_max_calls": int(wave4_max_calls),
        "wave4a_max_calls": int(wave4a_max_calls),
        "wave4_retry": wave4_retry,
        "wave4_include_unresolved": wave4_include_unresolved,
    }
    ctrl = _RunController(cfg, start_prog)
    # Clear any stale control file left from an earlier dead run
    live.consume_control()
    ctrl.install_signals()
    ctrl.publish(force=True)
    current_area = None
    wave4_base = None

    def _item_status():
        if wave4_base is not None:
            return _wave4_status()
        tr, un = git_status()
        return tr, un, set()

    def _rollback_options():
        if wave4_base is None:
            return {}
        if _wave4_head() != wave4_base:
            raise RuntimeError("HEAD moved during Wave 4; refusing to restore over another commit")
        return {"restore_from": wave4_base}

    def _mark_ledger_rolled_back(area_tag, reason_text):
        lp = path("build", "ledger", f"{area_tag}.jsonl")
        if os.path.exists(lp):
            batch_driver.Ledger(lp).record("rolled_back", reason=reason_text, ok=False)

    def _cleanup_uncommitted(area_tag, reason_text, archive=False, log_text=""):
        nonlocal last_clean_done, last_clean_snap
        tr_now, un_now, _ = _item_status()
        new_un = un_now - baseline_untracked
        arch = None
        if tr_now or new_un:
            if archive:
                arch = archive_and_rollback(
                    area_tag or "aborted", tr_now, new_un,
                    log_text=log_text or f"Rolled back: {reason_text}\n",
                    **_rollback_options(),
                )
            else:
                _rollback_tree(tr_now, new_un, **_rollback_options())
        if area_tag:
            _mark_ledger_rolled_back(area_tag, reason_text)
        ctrl.cur_prog = progress_done_count()
        last_clean_done = ctrl.cur_prog[0]
        last_clean_snap = _snapshot_symbol_state()
        return arch

    def _record_stall(item, area, ex, ledger_before, where, log_prefix=""):
        """A watched child (batch_driver or make verify) went silent for
        --stall-timeout and was killed: reset Wine, archive + roll back the
        item, record it STALLED.  The caller then stops on a pending graceful
        stop or goes on with the next item (the hang may be the item's own,
        e.g. a test that loops; a stuck toolchain hits the next compile's
        timeout and stops the run as TOOLCHAIN_ERROR)."""
        nonlocal current_area, completed_runs
        _reset_wine()
        arch = _cleanup_uncommitted(area, f"stall_timeout:{where}", archive=True,
                                    log_text=log_prefix + (getattr(ex, "output", "") or f"{ex}\n"))
        _record_failed_item(item, unconditional=True)
        ctrl.failed_modules.append(item["module"])
        ctrl.failed_addrs.extend(item.get("addrs") or [])
        rel_arch = os.path.relpath(arch, path()) if arch else "nothing to archive"
        print(f"[{_now_str()}] [STALLED] {item['module']} in {where} ({ex}) -> {rel_arch}", flush=True)
        live.append_event(area, "error", f"[STALLED] {item['module']} in {where} -> {rel_arch}")
        cost_delta = max(0.0, batch_driver.Ledger(path("build", "ledger", f"{area}.jsonl")).summary()["cost_usd"] - ledger_before)
        rec = {
            "id": area, "provider": provider,
            "time": _now_str(), "module": item["module"], "mode": item["mode"],
            "area": area, "status": "STALLED", "delta": 0, "cost": cost_delta,
            "commit": "", "note": f"{where}: {ex}; archived {rel_arch}",
            "addrs": list(item.get("addrs") or []),
        }
        results.append(rec)
        ctrl.completed.append(rec)
        ctrl.active_workers = []
        current_area = None
        write_summary(results, start_prog, provider=provider, codex_home=codex_home)
        ctrl.publish(force=True)
        completed_runs += 1

    def _record_toolchain_error(item, area, rc, log_text, ledger_before, where):
        """A compile timed out (stuck Wine/wcc386): every further item would hit
        it too and pay for LLM repairs on the way.  Archive + roll back the item,
        record it TOOLCHAIN_ERROR and fail the run (the caller breaks; the run
        exits EXIT_TOOLCHAIN)."""
        nonlocal current_area, toolchain_failed
        arch = _cleanup_uncommitted(area, f"toolchain_error:{where}", archive=True, log_text=log_text)
        rel_arch = os.path.relpath(arch, path()) if arch else "nothing to archive"
        msg = f"[TOOLCHAIN ERROR] {item['module']} ({where}): compiler stuck, stopping the run -> {rel_arch}"
        print(f"[{_now_str()}] {msg}", flush=True)
        live.append_event(area, "error", msg)
        cost_delta = max(0.0, batch_driver.Ledger(path("build", "ledger", f"{area}.jsonl")).summary()["cost_usd"] - ledger_before)
        rec = {
            "id": area, "provider": provider,
            "time": _now_str(), "module": item["module"], "mode": item["mode"],
            "area": area, "status": "TOOLCHAIN_ERROR", "delta": 0, "cost": cost_delta,
            "commit": "", "note": f"compile timed out in {where} (rc={rc}); archived {rel_arch}",
            "addrs": list(item.get("addrs") or []),
        }
        results.append(rec)
        ctrl.completed.append(rec)
        ctrl.active_workers = []
        current_area = None
        write_summary(results, start_prog, provider=provider, codex_home=codex_home)
        toolchain_failed = True
        ctrl.status = "FAILED"
        ctrl.status_detail = "Toolchain error (compile timed out): fix Wine/wcc386, then rerun"
        ctrl.publish(force=True)

    def _toolchain_marked(rc, text, exit_codes=(batch_driver.EXIT_TOOLCHAIN,)):
        return rc in exit_codes or any(l.startswith("[TOOLCHAIN ERROR]") for l in text.splitlines())

    with open(log_path, "a") as log_fh:
        if provider == "codex":
            hdr_msg = (
                f"\n==================== wc1.overnight START [codex] {_now_str()} ====================\n"
                f"window_budget={window_budget} max_modules={max_modules or 'unlimited'} wave={wave} "
                f"chunk_size={chunk_size} module_calls={module_calls} codex_repair_calls={codex_repair_calls} "
                f"matrix=[{codex.format_stage_matrix(codex_matrix)}] baseline_untracked={len(baseline_untracked)}\n"
            )
        else:
            hdr_msg = (
                f"\n==================== wc1.overnight START {_now_str()} ====================\n"
                f"window_budget={window_budget} capacity=${observed_capacity:.1f} "
                f"max_modules={max_modules or 'unlimited'} wave={wave} chunk_size={chunk_size} "
                f"module_budget=${module_budget:.2f} repair_budget=${repair_budget:.2f} "
                f"baseline_untracked={len(baseline_untracked)}\n"
            )
        sys.stdout.write(hdr_msg)
        sys.stdout.flush()
        log_fh.write(hdr_msg)
        log_fh.flush()

        try:
            while True:
                ctrl.poll_control()
                if ctrl.kill_requested:
                    raise ImmediateKillError("immediate kill requested")
                if ctrl.stop_requested:
                    if resume_item is not None:
                        _cleanup_uncommitted(resume_item["area"], "graceful_stop_during_resume", archive=True)
                        resume_item = None
                    print(f"[{_now_str()}] Graceful stop complete — exiting cleanly.", flush=True)
                    ctrl.status = "DONE"
                    ctrl.status_detail = "Stopped gracefully at module boundary"
                    break
                _wait_while_paused(log_fh, ctrl)
                if ctrl.stop_requested:
                    if resume_item is not None:
                        _cleanup_uncommitted(resume_item["area"], "graceful_stop_while_paused", archive=True)
                        resume_item = None
                    ctrl.status = "DONE"
                    ctrl.status_detail = "Stopped gracefully"
                    break

                if max_modules > 0 and completed_runs >= max_modules:
                    print(f"[{_now_str()}] Reached --max-modules={max_modules}, stopping cleanly.")
                    ctrl.status = "DONE"
                    ctrl.status_detail = f"Completed --max-modules={max_modules}"
                    break

                was_resuming = resume_item is not None
                if was_resuming:
                    item = resume_item
                    resume_item = None
                    ctrl.cur_prog = progress_done_count()
                else:
                    from . import t3_audit as _t3a
                    def _cache_log(msg):
                        line = f"[{_now_str()}] {msg}\n"
                        sys.stdout.write(line)
                        sys.stdout.flush()
                        log_fh.write(line)
                        log_fh.flush()
                    q_extra = dict(retry_options)
                    if wave in WAVE4_WAVES:
                        q_extra["failed_fingerprints"] = failed_fingerprints
                        q_extra["cache_log"] = _cache_log
                    try:
                        q = build_queue(wave=wave, chunk_size=chunk_size, skip=skip,
                                        only=only, failed_keys=failed_keys,
                                        module_budget=module_budget, module_calls=module_calls,
                                        max_chunk_insns=max_chunk_insns, provider=provider, **q_extra)
                    except _t3a.ToolchainAbort as ex:
                        print(f"[{_now_str()}] [TOOLCHAIN ERROR] discovery: {ex}", flush=True)
                        toolchain_failed = True
                        ctrl.status = "FAILED"
                        ctrl.status_detail = f"Toolchain error during discovery: {ex}"
                        break
                    ctrl.queue = q
                    ctrl.cur_prog = progress_done_count()
                    if not q:
                        detail = "Queue empty — all eligible modules done"
                        skipped_4a = int(getattr(reconcile_cache, "skipped", 0) or 0)
                        skipped_4b = int(getattr(retry_cache, "skipped", 0) or 0)
                        if skipped_4a or skipped_4b:
                            if skipped_4a and skipped_4b:
                                detail = (f"Queue empty — {skipped_4a} cached Wave 4A misses/ambiguous, "
                                          f"{skipped_4b} cached Wave 4B misses (use --wave4-retry to reconsider)")
                            elif skipped_4a:
                                detail = (f"Queue empty — {skipped_4a} cached Wave 4A misses/ambiguous "
                                          "(use --wave4-retry to reconsider)")
                            else:
                                detail = (f"Queue empty — {skipped_4b} cached Wave 4 misses "
                                          "(use --wave4-retry to reconsider)")
                        print(f"[{_now_str()}] {detail}!")
                        ctrl.status = "DONE"
                        ctrl.status_detail = detail
                        break
                    item = q[0]
                    ctrl.queue = q[1:]

                # Check live 5h/7d quota + rolling window budget before starting
                # (skip quota gate for strictly zero-LLM Wave 4A items: auto_promote or max_calls=0)
                w_spend = 0.0
                cx_after_reset_ts = None
                w4a_zero_llm = (
                    item["mode"] == WAVE4A_MODE
                    and (item.get("task_kind") == "auto_promote" or int(wave4a_max_calls) <= 0)
                )
                if w4a_zero_llm:
                    pass
                elif provider == "codex":
                    rl_cx = codex.get_latest_rate_limits(codex_home=codex_home)
                    if start_7d_pct is None:
                        start_7d_pct, start_7d_resets_at = _fresh_start_7d(
                            rl_cx, max_age_s=codex_telemetry_max_age,
                        )
                    gate = codex.check_codex_quota_gate(
                        rl_cx,
                        window_budget=window_budget,
                        max_age_s=codex_telemetry_max_age,
                        max_5h_pct=codex_max_5h_pct,
                        max_7d_pct=codex_max_7d_pct,
                        max_7d_delta_pp=codex_max_7d_delta_pp,
                        start_7d_pct=start_7d_pct,
                        start_7d_resets_at=start_7d_resets_at,
                        total_calls_used=codex_run_calls,
                        max_total_calls=codex_max_total_calls,
                        **_after_reset_kwargs(cx_slept_resets_at),
                    )
                    if gate["action"] == "ok":
                        if gate.get("after_reset"):
                            # Telemetry still shows the slept-through window: let the
                            # child's first call run once and refresh it.
                            cx_after_reset_ts = cx_slept_resets_at
                        cx_slept_resets_at = None
                    if gate["action"] == "error":
                        if was_resuming:
                            _cleanup_uncommitted(
                                item["area"], "codex_telemetry_error",
                                archive=True, log_text=gate["reason"] + "\n",
                            )
                        print(f"[{_now_str()}] ERROR: {gate['reason']}", file=sys.stderr, flush=True)
                        ctrl.status = "FAILED"
                        ctrl.status_detail = gate["reason"]
                        fatal_rc = 2
                        break
                    if gate["action"] == "stop_budget":
                        if was_resuming:
                            _cleanup_uncommitted(
                                item["area"], "codex_quota_cap",
                                archive=True, log_text=gate["reason"] + "\n",
                            )
                        print(f"[{_now_str()}] [QUOTA CAP] {gate['reason']} — stopping cleanly.", flush=True)
                        ctrl.status = "DONE"
                        ctrl.status_detail = gate["reason"]
                        break
                    if gate["action"] == "wait":
                        wait_s = gate["wait_seconds"]
                        wait_reason = gate["reason"]
                        if not sleep_on_limit:
                            if was_resuming:
                                _cleanup_uncommitted(
                                    item["area"], "window_budget_no_sleep",
                                    archive=True, log_text=f"{wait_reason}\n",
                                )
                            print(f"[{_now_str()}] {wait_reason} (--no-sleep set), stopping.")
                            ctrl.status = "DONE"
                            ctrl.status_detail = f"{wait_reason} (--no-sleep)"
                            break
                        if was_resuming:
                            resume_item = item
                        if gate.get("resets_at") is not None:
                            cx_slept_resets_at = float(gate["resets_at"])
                        _sleep_with_heartbeat(wait_s, wait_reason, log_fh, controller=ctrl)
                        continue
                else:
                    w_spend, _w_calls, oldest_ts = rolling_window_spend()
                    rl_info = live.load_rate_limits()
                    must_wait, wait_s, wait_reason = check_window_budget(
                        window_budget, rl_info, w_spend, observed_capacity, oldest_ts=oldest_ts,
                    )
                    if must_wait:
                        if not sleep_on_limit:
                            if was_resuming:
                                _cleanup_uncommitted(
                                    item["area"], "window_budget_no_sleep",
                                    archive=True, log_text=f"{wait_reason}\n",
                                )
                            print(f"[{_now_str()}] {wait_reason} (--no-sleep set), stopping.")
                            ctrl.status = "DONE"
                            ctrl.status_detail = f"{wait_reason} (--no-sleep)"
                            break
                        if was_resuming:
                            resume_item = item
                        _sleep_with_heartbeat(wait_s, wait_reason, log_fh, controller=ctrl)
                        continue

                done_before = last_clean_done
                before_snap = last_clean_snap
                w4_inputs = None
                is_w4a = (item["mode"] == WAVE4A_MODE)
                is_w4b = (item["mode"] == WAVE4_MODE)
                is_w4 = is_w4a or is_w4b
                if is_w4b:
                    w4_inputs = _wave4_inputs(item, before_snap)
                    if w4_inputs is None:
                        print(f"[{_now_str()}] [SKIPPED] {item['addrs'][0]:#x}: Wave 4 needs a tracked, "
                              "regular reference file and all its owning TOMLs", flush=True)
                        _record_failed_item(item, unconditional=True)
                        continue
                    if not was_resuming:
                        wave4_base = _wave4_head()
                elif is_w4a:
                    if _wave4a_inputs(item, before_snap) is None:
                        print(f"[{_now_str()}] [SKIPPED] {item['group_id']}: Wave 4A needs tracked, "
                              "regular affected reference files and owning TOMLs", flush=True)
                        _record_failed_item(item, unconditional=True)
                        continue
                    if not was_resuming:
                        wave4_base = _wave4_head()
                area = item["area"]
                current_area = area
                owned_tomls = sorted({
                    before_snap[a]["file"]
                    for a in (item.get("addrs") or ())
                    if a in before_snap and before_snap[a].get("file")
                })
                lg_start_sum = batch_driver.Ledger(path("build", "ledger", f"{area}.jsonl")).summary()
                ledger_before = lg_start_sum["cost_usd"]
                codex_calls_before = lg_start_sum["codex_calls"]
                if not (was_resuming and item["key"] in item_call_base):
                    item_call_base[item["key"]] = (lg_start_sum["codex_calls"], lg_start_sum["claude_calls"])
                item_codex_base, item_claude_base = item_call_base[item["key"]]

                def _item_calls(lg_sum):
                    if provider == "codex":
                        return max(0, int(lg_sum["codex_calls"]) - int(item_codex_base))
                    return max(0, int(lg_sum["claude_calls"]) - int(item_claude_base))
                codex_rl_item_before = codex.get_latest_rate_limits(codex_home=codex_home) if provider == "codex" else None
                if provider == "codex":
                    p5_b = (codex_rl_item_before.get("primary") or {}).get("used_percent") if isinstance(codex_rl_item_before, dict) else None
                    s7_b = (codex_rl_item_before.get("secondary") or {}).get("used_percent") if isinstance(codex_rl_item_before, dict) else None
                    banner = (
                        f"\n[{_now_str()}] >>> [{completed_runs + 1}] {item['mode']} {item['module']} "
                        f"(area={area}, ~{item['count']} fn, avg={item['avg_insns']} insns/fn) | "
                        f"provider=codex 5h={p5_b}% 7d={s7_b}% run_calls={codex_run_calls}\n"
                    )
                else:
                    banner = (
                        f"\n[{_now_str()}] >>> [{completed_runs + 1}] {item['mode']} {item['module']} "
                        f"(area={area}, ~{item['count']} fn, avg={item['avg_insns']} insns/fn) | "
                        f"5h spend=${w_spend:.2f}\n"
                    )
                sys.stdout.write(banner)
                sys.stdout.flush()
                log_fh.write(banner)
                log_fh.flush()

                init_model = codex_matrix["stage1"][0] if provider == "codex" else "sonnet"
                init_effort = codex_matrix["stage1"][1] if provider == "codex" else "low"
                worker_entry = {
                    "id": area,
                    "provider": provider,
                    "module": item["module"],
                    "mode": item["mode"],
                    "area": area,
                    "stage": "starting",
                    "phase": "RUNNING",
                    "model": init_model,
                    "effort": init_effort,
                    "status": "ACTIVE",
                    "count": item["count"],
                    "addrs": list(item.get("addrs") or []),
                    "started_at": time.time(),
                    "cost": 0.0,
                }
                ctrl.active_workers = [worker_entry]
                ctrl.status = "STOPPING" if ctrl.stop_requested else "RUNNING"
                ctrl.status_detail = f"{item['mode']} {item['module']} ({area})"
                live.update_worker_meta(area, phase="RUNNING", stage="batch_driver",
                                        model=init_model, effort=init_effort, provider=provider)
                live.append_event(area, "info", f"Starting {item['mode']} {item['module']} ({item['count']} fn) [{provider}]")
                ctrl.publish(force=True)

                if is_w4a:
                    # Wave 4A: one dependency group (mechanical 0-LLM first, else bounded research)
                    cmd = [
                        sys.executable, "-m", "wc1.batch_driver",
                        WAVE4A_MODE, item["group_id"],
                        "--area", area,
                        "--max-cost", f"{module_budget:.2f}",
                        "--max-calls", str(max(0, int(wave4a_max_calls) - _item_calls(lg_start_sum))),
                    ]
                elif is_w4b:
                    # Wave 4B: one function, one bounded attempt: wave4_max_calls LLM calls at most
                    cmd = [
                        sys.executable, "-m", "wc1.batch_driver",
                        WAVE4_MODE, f"{item['addrs'][0]:#x}",
                        "--area", area,
                        "--max-cost", f"{module_budget:.2f}",
                        "--max-calls", str(max(0, int(wave4_max_calls) - _item_calls(lg_start_sum))),
                    ]
                else:
                    cmd = [
                        sys.executable, "-m", "wc1.batch_driver",
                        item["mode"], item["module"],
                        "--area", area,
                        "--src-subdir", item["src_subdir"],
                        "--max-cost", f"{module_budget:.2f}",
                        "--max-calls", str(module_calls),
                    ]
                if provider == "codex":
                    cmd += [
                        "--provider", "codex",
                        "--codex-window-budget", f"{window_budget:.2f}",
                        "--codex-telemetry-max-age", str(int(codex_telemetry_max_age)),
                        "--codex-base-total-calls", str(int(codex_run_calls)),
                    ]
                    for st in codex.STAGES:
                        m_st, e_st = codex_matrix[st]
                        cmd += [f"--codex-{st}", f"{m_st}:{e_st}"]
                    if codex_bin:
                        cmd += ["--codex-bin", codex_bin]
                    if codex_home:
                        cmd += ["--codex-home", str(codex_home)]
                    if codex_max_5h_pct is not None:
                        cmd += ["--codex-max-5h-pct", str(codex_max_5h_pct)]
                    if codex_max_7d_pct is not None:
                        cmd += ["--codex-max-7d-pct", str(codex_max_7d_pct)]
                    if codex_max_7d_delta_pp is not None:
                        cmd += ["--codex-max-7d-delta-pp", str(codex_max_7d_delta_pp)]
                    if start_7d_pct is not None:
                        cmd += ["--codex-start-7d-pct", f"{start_7d_pct:.2f}"]
                    if start_7d_resets_at is not None:
                        cmd += ["--codex-start-7d-resets-at", f"{start_7d_resets_at:.0f}"]
                    if cx_after_reset_ts is not None:
                        cmd += ["--codex-after-reset-ts", f"{cx_after_reset_ts:.3f}"]
                    if codex_max_total_calls is not None:
                        cmd += ["--codex-max-total-calls", str(int(codex_max_total_calls))]
                    if codex_early_stop_stage2:
                        cmd.append("--codex-early-stop-stage2")
                if not is_w4:
                    if item["header"]:
                        cmd += ["--header", item["header"]]
                    if item.get("addrs"):
                        cmd += ["--addrs", ",".join(f"{a:#x}" for a in item["addrs"])]
                    elif item["limit"]:
                        cmd += ["--limit", str(item["limit"])]
                t3_before, t4_before = ctrl.cur_prog[2:4]
                if is_w4a:
                    from . import wave4a as _w4a
                    _w4a.clear_outcome(item["group_id"])
                elif is_w4b:
                    from . import wave4 as _w4
                    _w4.clear_outcome(item["addrs"][0])

                t_worker0 = time.monotonic()
                try:
                    rc, out_txt = _run_subprocess_logged(
                        cmd, log_fh, controller=ctrl,
                        stall_timeout=stall_timeout, stall_worker_id=area,
                    )
                except StallError as ex:
                    # A wedged batch_driver (e.g. a stuck Wine compile): kill it,
                    # archive + roll back this item, go on with the next one.
                    _record_stall(item, area, ex, ledger_before, "batch_driver")
                    if ctrl.stop_requested:
                        ctrl.status = "DONE"
                        ctrl.status_detail = f"Gracefully stopped after {item['module']}"
                        break
                    continue
                worker_s = round(time.monotonic() - t_worker0, 2)
                if provider == "codex":
                    cx_after_bd = batch_driver.Ledger(path("build", "ledger", f"{area}.jsonl")).summary()["codex_calls"]
                    codex_run_calls += max(0, cx_after_bd - codex_calls_before)
                    codex_calls_before = cx_after_bd
                if _toolchain_marked(rc, out_txt):
                    _record_toolchain_error(item, area, rc, out_txt, ledger_before, "batch_driver")
                    break
                if rc == batch_driver.EXIT_QUOTA_STOP or "[QUOTA_CAP]" in out_txt:
                    ctrl.active_workers = []
                    current_area = None
                    _cleanup_uncommitted(area, "codex_quota_cap", archive=True, log_text=out_txt)
                    print(f"[{_now_str()}] [QUOTA CAP] Hard quota ceiling reached during {item['module']} — stopping cleanly.", flush=True)
                    ctrl.status = "DONE"
                    ctrl.status_detail = "Hard Codex quota ceiling reached"
                    break
                if rc == batch_driver.EXIT_RATE_LIMIT or "[RATE_LIMIT]" in out_txt:
                    ctrl.active_workers = []
                    current_area = None
                    if provider == "codex":
                        rl_now = codex.get_latest_rate_limits(codex_home=codex_home)
                        res_ts = codex.extract_codex_reset_ts(out_txt, rl_info=rl_now)
                        if not sleep_on_limit:
                            _cleanup_uncommitted(area, "rate_limit_no_sleep", archive=True, log_text=out_txt)
                            print(f"[{_now_str()}] Codex rate limit hit (--no-sleep set), stopping cleanly.")
                            ctrl.status = "DONE"
                            ctrl.status_detail = "Codex rate limit hit (--no-sleep)"
                            break
                        if res_ts is None:
                            _cleanup_uncommitted(area, "codex_rate_limit_unknown_reset", archive=True, log_text=out_txt)
                            msg = "Codex rate limit hit with unknown reset timestamp — stopping instead of retrying blindly."
                            print(f"[{_now_str()}] ERROR: {msg}", file=sys.stderr, flush=True)
                            ctrl.status = "FAILED"
                            ctrl.status_detail = msg
                            fatal_rc = batch_driver.EXIT_RATE_LIMIT
                            break
                        resume_item = item
                        cx_slept_resets_at = float(res_ts)
                        wait_s = int(max(60, res_ts - time.time() + 60))
                        _sleep_with_heartbeat(
                            wait_s, "Codex Plus rate limit hit (resuming same module)",
                            log_fh, controller=ctrl,
                        )
                        continue
                    w_now, _, oldest_now = rolling_window_spend()
                    if w_now > 5.0 and w_now < observed_capacity:
                        observed_capacity = w_now
                    if not sleep_on_limit:
                        _cleanup_uncommitted(area, "rate_limit_no_sleep", archive=True, log_text=out_txt)
                        print(f"[{_now_str()}] Rate limit hit (--no-sleep set), stopping cleanly.")
                        ctrl.status = "DONE"
                        ctrl.status_detail = "Rate limit hit (--no-sleep)"
                        break
                    # Keep drafted files & ledger in place and resume this exact item on wake
                    resume_item = item
                    wait_s = _compute_rate_limit_wait(out_txt, rate_limit_sleep, oldest_now)
                    _sleep_with_heartbeat(
                        wait_s, "Claude Pro rate limit hit (resuming same module)",
                        log_fh, controller=ctrl,
                    )
                    continue

                tracked_now, untracked_now, staged = _item_status()
                new_untracked = untracked_now - baseline_untracked
                changed = tracked_now | new_untracked
                w4_out = _wave4_outcome(item) if is_w4 else None

                if not changed:
                    remembered_key = item.get("retry_key")
                    if is_w4 and w4_out is not None and rc == 0 and (wave4_base is None or _wave4_head() == wave4_base):
                        fp_to_save, hint_to_save = _recompute_wave4_fp_after_noop(item, is_w4a)
                        remembered_key = getattr(fp_to_save, "key", fp_to_save)
                        if is_w4a and reconcile_cache:
                            try:
                                reconcile_cache.remember(item["group_id"], fp_to_save, w4_out, repo_state_hint=hint_to_save)
                            except OSError as ex:
                                print(f"[{_now_str()}] WARNING: could not save Wave 4A outcome: {ex}", flush=True)
                        elif is_w4b and retry_cache:
                            try:
                                retry_cache.remember(item["addrs"][0], fp_to_save, w4_out, repo_state_hint=hint_to_save)
                            except OSError as ex:
                                print(f"[{_now_str()}] WARNING: could not save Wave 4 miss: {ex}", flush=True)
                    _record_failed_item(item, fp_key=remembered_key, unconditional=(not remembered_key))
                    _mark_ledger_rolled_back(area, f"noop_rc={rc}")
                    lg_noop = batch_driver.Ledger(path("build", "ledger", f"{area}.jsonl")).summary()
                    cost_delta = max(0.0, lg_noop["cost_usd"] - ledger_before)
                    calls_delta_noop = _item_calls(lg_noop)
                    codex_rl_noop = codex.get_latest_rate_limits(codex_home=codex_home) if provider == "codex" else None
                    rec = {
                        "id": area, "provider": provider,
                        "time": _now_str(), "module": item["module"], "mode": item["mode"],
                        "area": area, "status": "NOOP", "delta": 0, "delta_t3": 0,
                        "cost": cost_delta if provider == "claude" else 0.0,
                        "calls": calls_delta_noop,
                        "worker_s": worker_s, "verify_s": 0.0,
                        "w4_outcome": (w4_out or {}).get("outcome") if w4_out is not None else None,
                        "method": (w4_out or {}).get("method") if w4_out is not None else None,
                        "primary_delta_pp": codex.compute_window_delta(codex_rl_item_before, codex_rl_noop, "primary") if provider == "codex" else None,
                        "secondary_delta_pp": codex.compute_window_delta(codex_rl_item_before, codex_rl_noop, "secondary") if provider == "codex" else None,
                        "commit": "", "note": (
                            f"{'wave4a' if is_w4a else 'wave4'} {w4_out.get('outcome', 'NO_OUTCOME')}: "
                            f"{w4_out.get('reason') or ''} (rc={rc})"
                            if w4_out is not None else
                            f"batch_driver produced no file changes (rc={rc})"),
                        "addrs": list(item.get("addrs") or []),
                    }
                    results.append(rec)
                    ctrl.completed.append(rec)
                    ctrl.active_workers = []
                    current_area = None
                    wave4_base = None
                    ctrl.cur_prog = progress_done_count()
                    last_clean_done = ctrl.cur_prog[0]
                    last_clean_snap = _snapshot_symbol_state()
                    write_summary(results, start_prog, provider=provider, codex_home=codex_home)
                    write_wave4_metrics(results, start_prog, started_at=ctrl.started_at, wave=wave,
                                        provider=provider, reconcile_cache=reconcile_cache,
                                        retry_cache=retry_cache, start_5h_pct=start_5h_pct,
                                        start_7d_pct=start_7d_pct, codex_home=codex_home)
                    ctrl.publish(force=True)
                    completed_runs += 1
                    continue

                w4_issue = None
                w4_verified_input = None
                w4_pin_paths = None
                if is_w4b and w4_out is not None:
                    if rc != 0 or w4_out.get("outcome") != "PROMOTED":
                        w4_issue = ("wave4 worker did not finish a clean promotion: "
                                    f"{w4_out.get('outcome', 'NO_OUTCOME')} (rc={rc})")
                    elif staged:
                        w4_issue = "Wave 4 worker changed the Git index"
                    elif changed - w4_inputs:
                        w4_issue = f"disallowed paths: {', '.join(sorted(changed - w4_inputs)[:3])}"
                    else:
                        raw = _wave4_worktree(w4_inputs)
                        if raw is None:
                            w4_issue = "Wave 4 worker replaced or removed a promotion input"
                        else:
                            w4_pin_paths = w4_inputs
                            w4_verified_input = (changed, raw)
                elif is_w4a and w4_out is not None:
                    if rc != 0 or w4_out.get("outcome") not in ("PROMOTED", "RECONCILED"):
                        w4_issue = ("wave4a worker did not finish a clean reconciliation: "
                                    f"{w4_out.get('outcome', 'NO_OUTCOME')} (rc={rc})")
                    elif staged:
                        w4_issue = "Wave 4A worker changed the Git index"
                    else:
                        bad_4a = _check_wave4a_paths(changed, w4_out)
                        if bad_4a:
                            w4_issue = f"disallowed paths: {', '.join(bad_4a[:3])}"
                        else:
                            aw_err = _check_wave4a_test_anti_weakening(changed, wave4_base)
                            if aw_err:
                                w4_issue = f"test weakening: {aw_err}"
                            else:
                                raw = _wave4_worktree(changed)
                                if raw is None:
                                    w4_issue = "Wave 4A worker left a missing or non-regular changed file"
                                else:
                                    w4_pin_paths = set(changed)
                                    w4_verified_input = (set(changed), raw)
                if w4_issue is not None:
                    reason = w4_issue
                    arch = archive_and_rollback(area, tracked_now, new_untracked, log_text=out_txt,
                                                **_rollback_options())
                    _mark_ledger_rolled_back(area, reason)
                    _record_failed_item(item, fp_key=item.get("retry_key"), unconditional=(not item.get("retry_key")))
                    ctrl.failed_modules.append(item["module"])
                    ctrl.failed_addrs.extend(item.get("addrs") or [])
                    rel_arch = os.path.relpath(arch, path())
                    print(f"[{_now_str()}] [ROLLED BACK] {item['module']} ({reason}) -> archived {rel_arch}", flush=True)
                    lg_rb = batch_driver.Ledger(path("build", "ledger", f"{area}.jsonl")).summary()
                    rec = {
                        "id": area, "provider": provider, "time": _now_str(), "module": item["module"],
                        "mode": item["mode"], "area": area, "status": "FAILED", "delta": 0, "delta_t3": 0,
                        "cost": max(0.0, lg_rb["cost_usd"] - ledger_before) if provider == "claude" else 0.0,
                        "calls": _item_calls(lg_rb), "worker_s": worker_s, "verify_s": 0.0,
                        "w4_outcome": (w4_out or {}).get("outcome"), "method": (w4_out or {}).get("method"),
                        "commit": "", "note": f"{reason}; archived {rel_arch}",
                        "addrs": list(item.get("addrs") or []),
                    }
                    results.append(rec)
                    ctrl.completed.append(rec)
                    ctrl.active_workers = []
                    current_area = None
                    wave4_base = None
                    ctrl.cur_prog = progress_done_count()
                    last_clean_done = ctrl.cur_prog[0]
                    last_clean_snap = _snapshot_symbol_state()
                    write_summary(results, start_prog, provider=provider, codex_home=codex_home)
                    write_wave4_metrics(results, start_prog, started_at=ctrl.started_at, wave=wave,
                                        provider=provider, reconcile_cache=reconcile_cache,
                                        retry_cache=retry_cache, start_5h_pct=start_5h_pct,
                                        start_7d_pct=start_7d_pct, codex_home=codex_home)
                    ctrl.publish(force=True)
                    completed_runs += 1
                    continue

                has_c_changes = any(p.startswith("src/") and p.endswith(".c") for p in changed)
                # M3: the "rc != 0 and no C files" early stop is Codex-only; a Claude
                # run keeps its old path (verify + bounded repair) for TOML/test-only work.
                if rc == batch_driver.EXIT_EARLY_STOP or (provider == "codex" and rc != 0 and not has_c_changes):
                    reason = "stage2_early_stop" if rc == batch_driver.EXIT_EARLY_STOP else f"batch_driver rc={rc} (no C files)"
                    arch = archive_and_rollback(area, tracked_now, new_untracked, log_text=out_txt)
                    _mark_ledger_rolled_back(area, reason)
                    _record_failed_item(item, unconditional=True)
                    ctrl.failed_modules.append(item["module"])
                    ctrl.failed_addrs.extend(item.get("addrs") or [])
                    rel_arch = os.path.relpath(arch, path())
                    print(f"[{_now_str()}] [EARLY STOP / ROLLED BACK] {item['module']} ({reason}) -> archived {rel_arch}", flush=True)
                    live.append_event(area, "error", f"[ROLLED BACK] {item['module']} ({reason}) -> {rel_arch}")
                    lg_es = batch_driver.Ledger(path("build", "ledger", f"{area}.jsonl")).summary()
                    codex_rl_es = codex.get_latest_rate_limits(codex_home=codex_home) if provider == "codex" else None
                    rec = {
                        "id": area, "provider": provider,
                        "time": _now_str(), "module": item["module"], "mode": item["mode"],
                        "area": area, "status": "FAILED", "delta": 0,
                        "cost": max(0.0, lg_es["cost_usd"] - ledger_before) if provider == "claude" else 0.0,
                        "calls": _item_calls(lg_es),
                        "primary_delta_pp": codex.compute_window_delta(codex_rl_item_before, codex_rl_es, "primary") if provider == "codex" else None,
                        "secondary_delta_pp": codex.compute_window_delta(codex_rl_item_before, codex_rl_es, "secondary") if provider == "codex" else None,
                        "commit": "", "note": f"{reason}; archived {rel_arch}",
                        "addrs": list(item.get("addrs") or []),
                    }
                    results.append(rec)
                    ctrl.completed.append(rec)
                    ctrl.active_workers = []
                    current_area = None
                    ctrl.cur_prog = progress_done_count()
                    last_clean_done = ctrl.cur_prog[0]
                    last_clean_snap = _snapshot_symbol_state()
                    write_summary(results, start_prog, provider=provider, codex_home=codex_home)
                    ctrl.publish(force=True)
                    completed_runs += 1
                    continue

                # Run make verify
                ctrl.sync_active_worker_phase(default_phase="VERIFYING")
                ctrl.status = "STOPPING" if ctrl.stop_requested else "VERIFYING"
                ctrl.status_detail = f"make verify ({item['module']})"
                live.append_event(area, "verify", f"Running make verify for {item['module']}")
                ctrl.publish(force=True)

                # Watched for output only (stall_worker_id None): nothing beats
                # the worker meta while make verify runs.
                t_verify0 = time.monotonic()
                try:
                    v_rc, v_out = _run_subprocess_logged(
                        ["make", "verify"], log_fh, controller=ctrl,
                        worker_id=area, event_kind="verify",
                        stall_timeout=stall_timeout, stall_worker_id=None,
                    )
                except StallError as ex:
                    _record_stall(item, area, ex, ledger_before, "make verify",
                                  log_prefix=out_txt + "\n=== VERIFY ===\n")
                    if ctrl.stop_requested:
                        ctrl.status = "DONE"
                        ctrl.status_detail = f"Gracefully stopped after {item['module']}"
                        break
                    continue
                verify_s = round(time.monotonic() - t_verify0, 2)
                # make's own exit code for a failed recipe is 2: only the marker counts
                if _toolchain_marked(v_rc, v_out, exit_codes=()):
                    _record_toolchain_error(item, area, v_rc, out_txt + "\n=== VERIFY ===\n" + v_out,
                                            ledger_before, "make verify")
                    break
                cheat = _has_forbidden_test_cheat(changed)
                if (v_rc != 0 or cheat) and provider == "codex" and codex_repair_calls > 0 and w4_out is None:
                    repair_aborted_stop = False
                    repair_aborted_rl = False
                    repair_quota_stop = False
                    repair_rl_resets = None
                    verify_stalled = None
                    rl_txt = ""
                    # S9: hard per-item repair call cap (each round may retry once
                    # after a rate-limit sleep), enforced inside call_codex.
                    repair_max_calls = (
                        batch_driver.Ledger(path("build", "ledger", f"{area}.jsonl")).total_calls(provider="codex")
                        + 2 * int(codex_repair_calls)
                    )
                    for repair_round in range(int(codex_repair_calls)):
                        if v_rc != 0:
                            extra_diag = _collect_extra_verify_failures(changed, v_out)
                            fail_info = v_out + ("\n\n" + extra_diag if extra_diag else "")
                        else:
                            fail_info = f"Forbidden xfail/skip cheat detected in {cheat}"

                        for repair_try in range(2):
                            ctrl.sync_active_worker_phase(default_phase="REPAIRING")
                            ctrl.status = "STOPPING" if ctrl.stop_requested else "REPAIRING"
                            ctrl.status_detail = f"Codex patch repair R{repair_round + 1} ({item['module']})"
                            ctrl.publish(force=True)
                            rep_guard = {
                                "window_budget": window_budget,
                                "max_age_s": codex_telemetry_max_age,
                                "max_5h_pct": codex_max_5h_pct,
                                "max_7d_pct": codex_max_7d_pct,
                                "max_7d_delta_pp": codex_max_7d_delta_pp,
                                "start_7d_pct": start_7d_pct,
                                "start_7d_resets_at": start_7d_resets_at,
                                "total_calls_used": codex_run_calls,
                                "max_total_calls": codex_max_total_calls,
                            }
                            rep_guard.update(_after_reset_kwargs(cx_slept_resets_at))
                            if rep_guard.get("after_reset"):
                                cx_slept_resets_at = None  # one-shot (M1)
                            try:
                                applied_any, rl_hit, q_stop, rl_txt, rl_res_at = run_codex_structured_repair(
                                    item, changed, owned_tomls, fail_info, log_fh,
                                    codex_matrix=codex_matrix, codex_bin=codex_bin,
                                    codex_home=codex_home, codex_quota_guard=rep_guard,
                                    max_calls=repair_max_calls,
                                )
                            except batch_driver.ToolchainError as ex:
                                _record_toolchain_error(item, area, batch_driver.EXIT_TOOLCHAIN, str(ex), ledger_before, "codex_repair")
                                repair_quota_stop = True
                                break
                            cx_after_rep = batch_driver.Ledger(path("build", "ledger", f"{area}.jsonl")).summary()["codex_calls"]
                            codex_run_calls += max(0, cx_after_rep - codex_calls_before)
                            codex_calls_before = cx_after_rep
                            if q_stop:
                                repair_quota_stop = True
                                break
                            if not rl_hit:
                                break
                            repair_rl_resets = rl_res_at or codex.extract_codex_reset_ts(
                                rl_txt, rl_info=codex.get_latest_rate_limits(codex_home=codex_home),
                            )
                            if sleep_on_limit and repair_try == 0 and repair_rl_resets is not None:
                                cx_slept_resets_at = float(repair_rl_resets)
                                wait_s = int(max(60, repair_rl_resets - time.time() + 60))
                                _sleep_with_heartbeat(
                                    wait_s, "Codex rate limit during repair (retrying repair)",
                                    log_fh, controller=ctrl,
                                )
                                if ctrl.stop_requested:
                                    repair_aborted_stop = True
                                    break
                                continue
                            repair_aborted_rl = True
                            break

                        if toolchain_failed or repair_quota_stop or repair_aborted_stop or repair_aborted_rl:
                            break
                        if not applied_any:
                            break

                        wired = _wire_verified_t4_after_repair(area, owned_tomls=owned_tomls)
                        if wired:
                            wmsg = f"  [post-repair] mechanically wired {len(wired)} verified T4 node(s) into TOML\n"
                            sys.stdout.write(wmsg)
                            sys.stdout.flush()
                            log_fh.write(wmsg)
                            log_fh.flush()
                            live.append_event(area, "verify", wmsg.strip())

                        tracked_now, untracked_now = git_status()
                        new_untracked = untracked_now - baseline_untracked
                        changed = tracked_now | new_untracked
                        cheat = _has_forbidden_test_cheat(changed)

                        ctrl.sync_active_worker_phase(default_phase="VERIFYING")
                        ctrl.status = "STOPPING" if ctrl.stop_requested else "VERIFYING"
                        ctrl.status_detail = f"Re-verifying {item['module']}"
                        ctrl.publish(force=True)
                        try:
                            v_rc, v_out = _run_subprocess_logged(
                                ["make", "verify"], log_fh, controller=ctrl,
                                worker_id=area, event_kind="verify",
                                stall_timeout=stall_timeout, stall_worker_id=None,
                            )
                        except StallError as ex:
                            verify_stalled = ex
                            break
                        if v_rc == 0 and not cheat:
                            break
                        if _toolchain_marked(v_rc, v_out, exit_codes=()):
                            break

                    if toolchain_failed:
                        break
                    if verify_stalled is not None:
                        _record_stall(item, area, verify_stalled, ledger_before, "make verify (repair)",
                                      log_prefix=out_txt + "\n=== VERIFY (repair) ===\n")
                        if ctrl.stop_requested:
                            ctrl.status = "DONE"
                            ctrl.status_detail = f"Gracefully stopped after {item['module']}"
                            break
                        continue
                    if _toolchain_marked(v_rc, v_out, exit_codes=()):
                        _record_toolchain_error(item, area, v_rc, out_txt + "\n=== VERIFY (repair) ===\n" + v_out,
                                                ledger_before, "make verify (repair)")
                        break
                    if repair_quota_stop:
                        ctrl.active_workers = []
                        current_area = None
                        _cleanup_uncommitted(area, "codex_quota_cap_during_repair", archive=True,
                                             log_text=out_txt + "\n=== VERIFY ===\n" + v_out + "\n" + rl_txt)
                        ctrl.status = "DONE"
                        ctrl.status_detail = "Hard Codex quota ceiling reached during repair"
                        break
                    if repair_aborted_stop or repair_aborted_rl:
                        ctrl.active_workers = []
                        current_area = None
                        reason_rl = "graceful_stop_during_repair_sleep" if repair_aborted_stop else "rate_limit_during_repair"
                        _cleanup_uncommitted(
                            area, reason_rl, archive=True,
                            log_text=out_txt + "\n=== VERIFY ===\n" + v_out + "\n=== REPAIR_RL ===\n" + rl_txt,
                        )
                        if repair_aborted_stop or not sleep_on_limit:
                            ctrl.status = "DONE"
                            ctrl.status_detail = (
                                "Stopped gracefully during repair wait"
                                if repair_aborted_stop
                                else "Codex rate limit during repair (--no-sleep)"
                            )
                            break
                        if repair_rl_resets is None:
                            msg = "Codex rate limit during repair with unknown reset timestamp — stopping."
                            print(f"[{_now_str()}] ERROR: {msg}", file=sys.stderr, flush=True)
                            ctrl.status = "FAILED"
                            ctrl.status_detail = msg
                            fatal_rc = batch_driver.EXIT_RATE_LIMIT
                            break
                        cx_slept_resets_at = float(repair_rl_resets)
                        wait_s = int(max(60, repair_rl_resets - time.time() + 60))
                        _sleep_with_heartbeat(wait_s, "Codex rate limit during repair", log_fh, controller=ctrl)
                        continue

                if (v_rc != 0 or cheat) and provider == "claude" and repair_budget > 0 and w4_out is None:
                    repair_ledger_path = path("build", "ledger", f"{area}.jsonl")
                    repair_ledger_start = batch_driver.Ledger(repair_ledger_path).summary()["cost_usd"]
                    repair_aborted_stop = False
                    repair_aborted_rl = False
                    verify_stalled = None
                    rl_txt = ""
                    for repair_round in range(2):
                        repair_spent = max(
                            0.0,
                            batch_driver.Ledger(repair_ledger_path).summary()["cost_usd"] - repair_ledger_start,
                        )
                        rem_budget = repair_budget - repair_spent
                        if repair_round > 0 and rem_budget < 0.05:
                            break
                        if v_rc != 0:
                            extra_diag = _collect_extra_verify_failures(changed, v_out)
                            fail_info = v_out + ("\n\n" + extra_diag if extra_diag else "")
                        else:
                            fail_info = f"Forbidden xfail/skip cheat detected in {cheat}"

                        for repair_try in range(2):
                            ctrl.sync_active_worker_phase(default_phase="REPAIRING")
                            ctrl.status = "STOPPING" if ctrl.stop_requested else "REPAIRING"
                            ctrl.status_detail = f"Bounded repair R{repair_round + 1} ({item['module']})"
                            ctrl.publish(force=True)

                            _, _, rl_hit, rl_txt = run_bounded_repair(
                                item, changed, fail_info, rem_budget, log_fh, controller=ctrl,
                            )
                            if not rl_hit:
                                break
                            if sleep_on_limit and repair_try == 0:
                                # Keep drafted files in place, wait out the limit, and retry ONLY the repair
                                _, _, oldest_now = rolling_window_spend()
                                wait_s = _compute_rate_limit_wait(rl_txt, rate_limit_sleep, oldest_now)
                                _sleep_with_heartbeat(
                                    wait_s, "Rate limit during repair (retrying repair)",
                                    log_fh, controller=ctrl,
                                )
                                if ctrl.stop_requested:
                                    repair_aborted_stop = True
                                    break
                                continue
                            repair_aborted_rl = True
                            break

                        if repair_aborted_stop or repair_aborted_rl:
                            break

                        # Mechanically wire any pending Stage 4 T4 tests that now pass after repair
                        wired = _wire_verified_t4_after_repair(area, owned_tomls=owned_tomls)
                        if wired:
                            wmsg = f"  [post-repair] mechanically wired {len(wired)} verified T4 node(s) into TOML\n"
                            sys.stdout.write(wmsg)
                            sys.stdout.flush()
                            log_fh.write(wmsg)
                            log_fh.flush()
                            live.append_event(area, "verify", wmsg.strip())

                        tracked_now, untracked_now = git_status()
                        new_untracked = untracked_now - baseline_untracked
                        changed = tracked_now | new_untracked
                        cheat = _has_forbidden_test_cheat(changed)

                        ctrl.sync_active_worker_phase(default_phase="VERIFYING")
                        ctrl.status = "STOPPING" if ctrl.stop_requested else "VERIFYING"
                        ctrl.status_detail = f"Re-verifying {item['module']}"
                        ctrl.publish(force=True)
                        try:
                            v_rc, v_out = _run_subprocess_logged(
                                ["make", "verify"], log_fh, controller=ctrl,
                                worker_id=area, event_kind="verify",
                                stall_timeout=stall_timeout, stall_worker_id=None,
                            )
                        except StallError as ex:
                            verify_stalled = ex
                            break
                        if v_rc == 0 and not cheat:
                            break
                        if _toolchain_marked(v_rc, v_out, exit_codes=()):
                            break

                    if verify_stalled is not None:
                        _record_stall(item, area, verify_stalled, ledger_before, "make verify (repair)",
                                      log_prefix=out_txt + "\n=== VERIFY (repair) ===\n")
                        if ctrl.stop_requested:
                            ctrl.status = "DONE"
                            ctrl.status_detail = f"Gracefully stopped after {item['module']}"
                            break
                        continue
                    if _toolchain_marked(v_rc, v_out, exit_codes=()):
                        _record_toolchain_error(item, area, v_rc, out_txt + "\n=== VERIFY (repair) ===\n" + v_out,
                                                ledger_before, "make verify (repair)")
                        break

                    if repair_aborted_stop or repair_aborted_rl:
                        ctrl.active_workers = []
                        current_area = None
                        reason_rl = "graceful_stop_during_repair_sleep" if repair_aborted_stop else "rate_limit_during_repair"
                        arch = _cleanup_uncommitted(
                            area, reason_rl, archive=True,
                            log_text=out_txt + "\n=== VERIFY ===\n" + v_out + "\n=== REPAIR_RL ===\n" + rl_txt,
                        )
                        if arch:
                            rel_arch = os.path.relpath(arch, path())
                            print(f"[{_now_str()}] [ARCHIVED] {item['module']} ({reason_rl}) -> {rel_arch}", flush=True)
                        if repair_aborted_stop or not sleep_on_limit:
                            ctrl.status = "DONE"
                            ctrl.status_detail = (
                                "Stopped gracefully during repair wait"
                                if repair_aborted_stop
                                else "Rate limit during repair (--no-sleep)"
                            )
                            break
                        _, _, oldest_now = rolling_window_spend()
                        wait_s = _compute_rate_limit_wait(rl_txt, rate_limit_sleep, oldest_now)
                        _sleep_with_heartbeat(wait_s, "Rate limit during repair", log_fh, controller=ctrl)
                        continue

                lg_end_sum = batch_driver.Ledger(path("build", "ledger", f"{area}.jsonl")).summary()
                cost_delta = max(0.0, lg_end_sum["cost_usd"] - ledger_before) if provider == "claude" else 0.0
                calls_delta = _item_calls(lg_end_sum)
                codex_rl_item_after = codex.get_latest_rate_limits(codex_home=codex_home) if provider == "codex" else None
                item_p_delta = codex.compute_window_delta(codex_rl_item_before, codex_rl_item_after, "primary") if provider == "codex" else None
                item_s_delta = codex.compute_window_delta(codex_rl_item_before, codex_rl_item_after, "secondary") if provider == "codex" else None
                if w4_out is not None:
                    # Include any effects of verification in the final path
                    # allowlist and in rollback, not just the driver's edits.
                    tracked_now, untracked_now, staged = _item_status()
                    new_untracked = untracked_now - baseline_untracked
                    changed = tracked_now | new_untracked
                ctrl.cur_prog = progress_done_count()
                done_after = ctrl.cur_prog[0]
                delta_done = done_after - done_before
                delta_t3 = ctrl.cur_prog[2] - t3_before
                delta_t4 = ctrl.cur_prog[3] - t4_before
                after_snap = _snapshot_symbol_state()
                if is_w4a and w4_out is not None:
                    progress_ok = _wave4a_progress_ok(item, w4_out, before_snap, after_snap, changed,
                                                      delta_done, delta_t3, delta_t4)
                elif w4_out is not None:
                    progress_ok = _wave4_progress_ok(item, w4_out, before_snap, after_snap, changed,
                                                     delta_done, delta_t3, delta_t4)
                else:
                    progress_ok = delta_done > 0
                missing_refs = _verify_staged_toml_refs(changed) if v_rc == 0 else []
                if v_rc != 0:
                    disallowed_paths = []
                elif is_w4a and w4_out is not None:
                    disallowed_paths = _check_wave4a_paths(changed, w4_out)
                elif w4_out is not None:
                    disallowed_paths = _check_wave4_paths(changed, w4_out)
                else:
                    disallowed_paths = _check_allowed_paths(changed, item, owned_tomls=owned_tomls)
                regressions = _check_no_regression(before_snap, after_snap) if v_rc == 0 else []
                bad_t4_nodes = (
                    _verify_new_ref_verified_by(before_snap, changed)
                    if (v_rc == 0 and not cheat and not disallowed_paths and not missing_refs and not regressions
                        and progress_ok)
                    else []
                )
                w4a_weaken = (
                    _check_wave4a_test_anti_weakening(changed, wave4_base)
                    if (is_w4a and w4_out is not None and v_rc == 0 and not cheat and not disallowed_paths)
                    else None
                )

                w4_drift = False
                if w4_out is not None:
                    tracked_now, untracked_now, staged = _item_status()
                    new_untracked = untracked_now - baseline_untracked
                    changed = tracked_now | new_untracked
                    w4_drift = (bool(staged) or _wave4_head() != wave4_base
                                or (changed, _wave4_worktree(w4_pin_paths)) != w4_verified_input)
                identical = any(line == "IDENTICAL" or line.startswith("IDENTICAL ") for line in v_out.splitlines())
                if (
                    v_rc == 0
                    and not cheat
                    and not w4a_weaken
                    and not disallowed_paths
                    and not missing_refs
                    and not regressions
                    and not bad_t4_nodes
                    and not w4_drift
                    and progress_ok
                    and (w4_out is None or identical)
                ):
                    ctrl.build_status = "IDENTICAL" if "IDENTICAL" in v_out else "PASS"
                    ctrl.sync_active_worker_phase(default_phase="COMMITTING")
                    ctrl.status = "STOPPING" if ctrl.stop_requested else "COMMITTING"
                    if is_w4a:
                        if delta_t3 > 0:
                            ctrl.status_detail = f"Committing Wave 4A {item['group_id']} (+{delta_t3} T3)"
                        else:
                            ctrl.status_detail = f"Committing Wave 4A {item['group_id']} (reconciled)"
                    else:
                        ctrl.status_detail = f"Committing {item['module']} (+{delta_done} done)" if w4_out is None else f"Committing {item['module']} (+{delta_t3} T3)"
                    ctrl.publish(force=True)

                    paths_to_add = sorted(changed)
                    if is_w4a and w4_out is not None:
                        unres_d = max(0, int((w4_out.get("unresolved_before") or 0) - (w4_out.get("unresolved_after") or 0)))
                        if delta_t3 > 0:
                            commit_msg = (f"T3: reconcile {item['group_id']} (+{delta_t3} T3, "
                                          f"via wc1.overnight wave4a {w4_out.get('method', '')})").replace("  ", " ")
                        else:
                            commit_msg = (f"wave4a: reconcile {item['group_id']} (-{unres_d} unresolved relocs, "
                                          f"via wc1.overnight {w4_out.get('method', '')})").replace("  ", " ")
                    elif w4_out is not None:
                        commit_msg = (f"T3: {item.get('name') or item['module']} {item['addrs'][0]:#x} "
                                      f"(built from C, via wc1.overnight wave4"
                                      + (f", +{delta_t3 - 1} sibling" if delta_t3 > 1 else "") + ")")
                    elif provider == "codex":
                        commit_msg = f"T3/T4: {item['module']} ({area}) +{delta_done} done via wc1.overnight (codex, {calls_delta} calls)"
                    else:
                        commit_msg = f"T3/T4: {item['module']} ({area}) +{delta_done} done via wc1.overnight ({cost_delta:.2f} USD)"
                    if w4_out is not None:
                        if new_untracked:
                            subprocess.run(["git", "--literal-pathspecs", "add", "--", *sorted(new_untracked)],
                                           cwd=path(), check=True)
                        # A promotion edits existing source/TOML (and Wave 4A may add a new TOML/header).
                        # A path-limited commit leaves no unintended staged files.
                        subprocess.run(["git", "--literal-pathspecs", "commit", "--only", "-m", commit_msg,
                                        "--", *paths_to_add],
                                       cwd=path(), check=True)
                        wave4_base = None
                        if is_w4a and w4_out is not None:
                            from . import wave4a as _w4a
                            _w4a.persist_outcome_mappings(w4_out)
                    else:
                        subprocess.run(["git", "add", "--", *paths_to_add], cwd=path(), check=True)
                        subprocess.run(["git", "commit", "-m", commit_msg], cwd=path(), check=True)
                    rev = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                                         capture_output=True, text=True, cwd=path(), check=True).stdout.strip()
                    print(f"[{_now_str()}] [COMMITTED {rev}] {commit_msg}", flush=True)
                    live.append_event(area, "commit", f"[{rev}] {commit_msg}")
                    unres_delta = (
                        max(0, int((w4_out.get("unresolved_before") or 0) - (w4_out.get("unresolved_after") or 0)))
                        if (is_w4a and w4_out is not None) else 0
                    )
                    rec = {
                        "id": area, "provider": provider,
                        "time": _now_str(), "module": item["module"], "mode": item["mode"],
                        "area": area, "status": "COMMITTED",
                        "delta": delta_done if w4_out is None else delta_t3,
                        "delta_t3": delta_t3,
                        "unresolved_delta": unres_delta,
                        "w4_outcome": (w4_out or {}).get("outcome") if w4_out is not None else None,
                        "method": (w4_out or {}).get("method") if w4_out is not None else None,
                        "worker_s": worker_s, "verify_s": verify_s,
                        "cost": cost_delta, "calls": calls_delta,
                        "primary_delta_pp": item_p_delta, "secondary_delta_pp": item_s_delta,
                        "commit": rev, "note": rev,
                        "addrs": list(item.get("addrs") or []),
                    }
                    results.append(rec)
                    ctrl.completed.append(rec)
                    ctrl.commits.append({
                        "rev": rev, "module": item["module"], "area": area,
                        "delta": rec["delta"], "cost": cost_delta, "provider": provider,
                        "time": rec["time"], "message": commit_msg,
                    })
                    last_clean_done = done_after
                    last_clean_snap = after_snap
                else:
                    if v_rc != 0:
                        ctrl.build_status = "FAILED"
                    reason = (f"cheat in {cheat}" if cheat else
                              f"test weakening: {w4a_weaken}" if w4a_weaken else
                              f"disallowed paths: {', '.join(disallowed_paths[:3])}" if disallowed_paths else
                              "Wave 4 worktree or index changed during verification" if v_rc == 0 and w4_drift else
                              f"missing TOML refs: {', '.join(missing_refs[:3])}" if missing_refs else
                              f"regression: {regressions[0]}" if regressions else
                              f"unverified T4 node: {bad_t4_nodes[0]}" if bad_t4_nodes else
                              "make verify did not report Build A IDENTICAL" if v_rc == 0 and progress_ok
                              and w4_out is not None and not identical else
                              (f"delta_done={delta_done} delta_t3={delta_t3} delta_t4={delta_t4}; invalid Wave 4 transition"
                               if w4_out is not None
                               else f"delta_done={delta_done}") if v_rc == 0 else
                              f"make verify rc={v_rc}")
                    arch = archive_and_rollback(area, tracked_now, new_untracked,
                                                log_text=out_txt + "\n=== VERIFY ===\n" + v_out,
                                                **_rollback_options())
                    wave4_base = None
                    _mark_ledger_rolled_back(area, reason)
                    _record_failed_item(item, fp_key=item.get("retry_key"), unconditional=(not item.get("retry_key")))
                    mod_key = (item["mode"], item["module"])
                    module_fail_counts[mod_key] += 1
                    if not is_w4 and module_fail_counts[mod_key] >= 2:
                        failed_keys.add(mod_key)
                    ctrl.failed_modules.append(item["module"])
                    ctrl.failed_addrs.extend(item.get("addrs") or [])
                    rel_arch = os.path.relpath(arch, path())
                    print(f"[{_now_str()}] [ROLLED BACK] {item['module']} ({reason}) -> archived {rel_arch}", flush=True)
                    live.append_event(area, "error", f"[ROLLED BACK] {item['module']} ({reason}) -> {rel_arch}")
                    rec = {
                        "id": area, "provider": provider,
                        "time": _now_str(), "module": item["module"], "mode": item["mode"],
                        "area": area, "status": "FAILED", "delta": 0, "delta_t3": 0,
                        "worker_s": worker_s, "verify_s": verify_s,
                        "w4_outcome": (w4_out or {}).get("outcome") if w4_out is not None else None,
                        "method": (w4_out or {}).get("method") if w4_out is not None else None,
                        "cost": cost_delta, "calls": calls_delta,
                        "primary_delta_pp": item_p_delta, "secondary_delta_pp": item_s_delta,
                        "commit": "", "note": f"{reason}; archived {rel_arch}",
                        "addrs": list(item.get("addrs") or []),
                    }
                    results.append(rec)
                    ctrl.completed.append(rec)
                    ctrl.cur_prog = progress_done_count()
                    last_clean_done = ctrl.cur_prog[0]
                    last_clean_snap = _snapshot_symbol_state()

                ctrl.active_workers = []
                current_area = None
                write_summary(results, start_prog, provider=provider, codex_home=codex_home)
                write_wave4_metrics(results, start_prog, started_at=ctrl.started_at, wave=wave,
                                    provider=provider, stop_reason=ctrl.status_detail,
                                    reconcile_cache=reconcile_cache, retry_cache=retry_cache,
                                    start_5h_pct=start_5h_pct, start_7d_pct=start_7d_pct,
                                    codex_home=codex_home)
                ctrl.publish(force=True)
                completed_runs += 1

                if ctrl.stop_requested:
                    print(f"[{_now_str()}] Graceful stop complete after {item['module']} — exiting cleanly.", flush=True)
                    ctrl.status = "DONE"
                    ctrl.status_detail = f"Gracefully stopped after {item['module']}"
                    break

        except ImmediateKillError as ex:
            print(f"\n[{_now_str()}] [KILLED] {ex} — rolling back active module changes...", flush=True)
            tag = current_area or (resume_item["area"] if resume_item else "killed")
            arch = _cleanup_uncommitted(tag, "killed_by_user", archive=True, log_text=f"Killed by user: {ex}\n")
            if arch:
                rel_arch = os.path.relpath(arch, path())
                print(f"[{_now_str()}] [KILLED] rolled back active changes -> {rel_arch}", flush=True)
                if current_area:
                    live.append_event(current_area, "error", f"[KILLED] rolled back -> {rel_arch}")
            ctrl.active_workers = []
            ctrl.status = "KILLED"
            ctrl.status_detail = "Killed immediately; active module rolled back"
            ctrl.cur_prog = progress_done_count()
            write_summary(results, start_prog, provider=provider, codex_home=codex_home)
            write_wave4_metrics(results, start_prog, started_at=ctrl.started_at, wave=wave,
                                provider=provider, stop_reason=ctrl.status_detail,
                                reconcile_cache=reconcile_cache, retry_cache=retry_cache,
                                start_5h_pct=start_5h_pct, start_7d_pct=start_7d_pct,
                                codex_home=codex_home)
            ctrl.publish(force=True)
            return 143
        except KeyboardInterrupt:
            print(f"\n[{_now_str()}] Interrupted by user (Ctrl-C) — archiving/rolling back active changes...", flush=True)
            tag = current_area or (resume_item["area"] if resume_item else "interrupted")
            arch = _cleanup_uncommitted(tag, "keyboard_interrupt", archive=True, log_text="Interrupted by user (Ctrl-C)\n")
            if arch:
                rel_arch = os.path.relpath(arch, path())
                print(f"[{_now_str()}] [INTERRUPTED] rolled back active changes -> {rel_arch}", flush=True)
            ctrl.active_workers = []
            ctrl.status = "DONE"
            ctrl.status_detail = "Interrupted (Ctrl-C); working tree clean"
            ctrl.cur_prog = progress_done_count()
            write_summary(results, start_prog, provider=provider, codex_home=codex_home)
            write_wave4_metrics(results, start_prog, started_at=ctrl.started_at, wave=wave,
                                provider=provider, stop_reason=ctrl.status_detail,
                                reconcile_cache=reconcile_cache, retry_cache=retry_cache,
                                start_5h_pct=start_5h_pct, start_7d_pct=start_7d_pct,
                                codex_home=codex_home)
            ctrl.publish(force=True)
            return 130
        except Exception as ex:
            tag = current_area or (resume_item["area"] if resume_item else "exception")
            try:
                _cleanup_uncommitted(tag, f"unhandled_exception:{type(ex).__name__}", archive=True, log_text=f"Unhandled error: {ex}\n")
            except Exception:
                pass
            ctrl.active_workers = []
            ctrl.status = "FAILED"
            ctrl.status_detail = f"Unhandled error: {ex}"
            ctrl.publish(force=True)
            raise
        finally:
            ctrl.restore_signals()

    ctrl.active_workers = []
    ctrl.cur_prog = progress_done_count()
    write_summary(results, start_prog, provider=provider, codex_home=codex_home)
    write_wave4_metrics(results, start_prog, started_at=ctrl.started_at, wave=wave,
                        provider=provider, stop_reason=ctrl.status_detail,
                        reconcile_cache=reconcile_cache, retry_cache=retry_cache,
                        start_5h_pct=start_5h_pct, start_7d_pct=start_7d_pct,
                        codex_home=codex_home)
    ctrl.publish(force=True)
    if toolchain_failed:
        return batch_driver.EXIT_TOOLCHAIN
    return fatal_rc


def _build_parser():
    ap = argparse.ArgumentParser(prog="wc1.overnight", description=__doc__.split("\n\n")[0])
    ap.add_argument("--provider", choices=("claude", "codex"), default="claude",
                    help="LLM provider backend (default claude; codex runs headless)")
    ap.add_argument("--codex-model", default=None,
                    help="Default OpenAI model ID for all Codex stages (e.g. gpt-6.2-sol, gpt-6-luna)")
    ap.add_argument("--codex-effort", default=None,
                    help="Default reasoning_effort for all Codex stages (low|medium|high)")
    ap.add_argument("--codex-stage1", default=None, help="Codex Stage 1 override MODEL[:EFFORT]")
    ap.add_argument("--codex-stage2", default=None, help="Codex Stage 2 override MODEL[:EFFORT]")
    ap.add_argument("--codex-stage3", default=None, help="Codex Stage 3 override MODEL[:EFFORT]")
    ap.add_argument("--codex-stage4", default=None, help="Codex Stage 4 override MODEL[:EFFORT]")
    ap.add_argument("--codex-repair", default=None, help="Codex post-verify repair override MODEL[:EFFORT]")
    ap.add_argument("--codex-repair-calls", type=int, default=1,
                    help="Max structured-patch repair rounds after make verify for Codex (0 disables, default 1)")
    ap.add_argument("--codex-bin", default=None, help="Path to codex CLI binary (default codex)")
    ap.add_argument("--codex-home", default=None,
                    help="CODEX_HOME for the codex CLI and its rate-limit rollouts (default $CODEX_HOME or ~/.codex)")
    ap.add_argument("--codex-max-5h-pct", type=float, default=None,
                    help="Hard per-call Codex 5h used_percent cap")
    ap.add_argument("--codex-max-7d-pct", type=float, default=90.0,
                    help="Hard per-call Codex 7d used_percent cap (default 90.0)")
    ap.add_argument("--codex-max-7d-delta-pp", type=float, default=None,
                    help="Hard per-call Codex 7d delta cap in percentage points from run start")
    ap.add_argument("--codex-max-total-calls", type=int, default=None,
                    help="Hard total Codex call ceiling across the run")
    ap.add_argument("--codex-telemetry-max-age", type=int, default=codex.DEFAULT_TELEMETRY_MAX_AGE_S,
                    help=f"Max age in seconds for fresh Codex 5h telemetry (default {codex.DEFAULT_TELEMETRY_MAX_AGE_S})")
    ap.add_argument("--codex-early-stop-stage2", action="store_true",
                    help="Abort immediately after Stage 2 if drafted C fails compile-check (for Stage A screening)")
    ap.add_argument("--window-budget", type=float, default=0.8,
                    help="Fraction of 5h window to use in (0.0, 1.0]; 1.0 = full window until rate-limit (default 0.8)")
    ap.add_argument("--window-capacity", type=float, default=35.0,
                    help="Claude only: estimated 5h Pro window capacity in API-equiv USD (ignored for codex)")
    ap.add_argument("--max-modules", type=int, default=0,
                    help="Optional max modules/chunks to run before stopping (0 = unlimited, default 0)")
    ap.add_argument("--wave", choices=("all", "wave2", "wave3", "wave4", "wave4a", "wave4b"), default="all",
                    help="Which backlog wave to run (default all: wave2 then wave3; "
                         "wave4a = symbol reconciliation, wave4b = codegen recovery, "
                         "wave4 = combined wave4a -> wave4b; never part of 'all')")
    ap.add_argument("--wave4-max-calls", type=int, default=WAVE4_MAX_CALLS,
                    help=f"Wave 4B: max LLM repair calls per T4 function (default {WAVE4_MAX_CALLS})")
    ap.add_argument("--wave4a-max-calls", type=int, default=WAVE4A_MAX_CALLS,
                    help=f"Wave 4A: max LLM research calls per dependency group (0 = mechanical only, default {WAVE4A_MAX_CALLS})")
    ap.add_argument("--wave4-retry", action="store_true",
                    help="Wave 4A/4B: reconsider cached NO_IMPROVEMENT / AMBIGUOUS results (combine with --only)")
    ap.add_argument("--wave4-include-unresolved", action="store_true",
                    help="Wave 4B: allow codegen recovery attempts on functions that still have unresolved relocations")
    ap.add_argument("--chunk-size", type=int, default=12,
                    help="Max functions per chunk for large modules (default 12)")
    ap.add_argument("--max-chunk-insns", type=int, default=DEFAULT_MAX_CHUNK_INSNS,
                    help=f"Max total instructions per chunk (0 = unlimited, default {DEFAULT_MAX_CHUNK_INSNS})")
    ap.add_argument("--module-budget", type=float, default=1.10,
                    help="Claude only: max API-equiv USD per module/chunk (ignored for codex; use --module-calls)")
    ap.add_argument("--module-calls", type=int, default=10,
                    help="Max LLM calls per module/chunk passed to batch_driver (default 10)")
    ap.add_argument("--repair-budget", type=float, default=0.45,
                    help="Claude only: max USD for claude -p repair pass; 0 disables (ignored for codex; use --codex-repair-calls)")
    ap.add_argument("--skip", default=",".join(DEFAULT_SKIP),
                    help=f"Comma-separated module names to skip (default {','.join(DEFAULT_SKIP)})")
    ap.add_argument("--only", default="",
                    help="Optional comma-separated whitelist of module names")
    ap.add_argument("--no-sleep", action="store_true",
                    help="Stop instead of sleeping when window budget / rate limit is reached")
    ap.add_argument("--rate-limit-sleep", type=int, default=900,
                    help="Claude fallback seconds to sleep between retries after a real rate limit (default 900)")
    ap.add_argument("--stall-timeout", type=int, default=DEFAULT_STALL_TIMEOUT,
                    help=f"Kill a batch_driver run that printed nothing and sent no live heartbeat "
                         f"for this many seconds (0 disables, default {DEFAULT_STALL_TIMEOUT})")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print the queue and current quota/spend without calling any LLM")
    ap.add_argument("--tui", action="store_true",
                    help="Open the btop-style Textual dashboard (Claude provider only in V1)")
    ap.add_argument("--headless", action="store_true",
                    help="Run pure CLI backend without opening the interactive TUI")
    return ap


def should_open_launcher(raw_argv, parsed_args, is_tty):
    """True when plain `python3 -m wc1.overnight` is run interactively without flags."""
    if getattr(parsed_args, "provider", "claude") == "codex":
        return False
    if parsed_args.headless or parsed_args.dry_run or parsed_args.tui:
        return False
    return bool(is_tty and len(raw_argv) == 0)


def main(argv=None):
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    ap = _build_parser()
    a = ap.parse_args(raw_argv)
    if a.max_chunk_insns < 0:
        ap.error("--max-chunk-insns must be >= 0")
    if a.stall_timeout < 0:
        ap.error("--stall-timeout must be >= 0")
    if 0 < a.stall_timeout < batch_driver.PYTEST_TIMEOUT + 60:
        ap.error(f"--stall-timeout must be 0 (off) or >= {batch_driver.PYTEST_TIMEOUT + 60}"
                 " (longer than a capped pytest run plus its heartbeat)")
    if a.codex_repair_calls < 0:
        ap.error("--codex-repair-calls must be >= 0")
    if a.provider == "codex" and a.tui:
        ap.error("--tui is not supported with --provider codex in V1 (use --headless)")
    skip = tuple(s.strip() for s in a.skip.split(",") if s.strip())
    only = tuple(s.strip() for s in a.only.split(",") if s.strip()) or None
    cfg = {
        "provider": a.provider,
        "window_budget": a.window_budget,
        "window_capacity": a.window_capacity,
        "max_modules": a.max_modules,
        "wave": a.wave,
        "chunk_size": a.chunk_size,
        "max_chunk_insns": a.max_chunk_insns,
        "module_budget": a.module_budget,
        "module_calls": a.module_calls,
        "repair_budget": a.repair_budget,
        "codex_model": a.codex_model,
        "codex_effort": a.codex_effort,
        "codex_stage1": a.codex_stage1,
        "codex_stage2": a.codex_stage2,
        "codex_stage3": a.codex_stage3,
        "codex_stage4": a.codex_stage4,
        "codex_repair": a.codex_repair,
        "codex_repair_calls": a.codex_repair_calls,
        "codex_bin": a.codex_bin,
        "codex_home": a.codex_home,
        "codex_max_5h_pct": a.codex_max_5h_pct,
        "codex_max_7d_pct": a.codex_max_7d_pct,
        "codex_max_7d_delta_pp": a.codex_max_7d_delta_pp,
        "codex_max_total_calls": a.codex_max_total_calls,
        "codex_telemetry_max_age": a.codex_telemetry_max_age,
        "codex_early_stop_stage2": a.codex_early_stop_stage2,
        "skip": skip,
        "only": only,
        "sleep_on_limit": not a.no_sleep,
        "rate_limit_sleep": a.rate_limit_sleep,
        "stall_timeout": a.stall_timeout,
        "wave4_max_calls": a.wave4_max_calls,
        "wave4a_max_calls": a.wave4a_max_calls,
        "wave4_retry": a.wave4_retry,
        "wave4_include_unresolved": a.wave4_include_unresolved,
    }
    is_tty = sys.stdin.isatty() and sys.stdout.isatty()

    if a.provider == "claude" and not a.dry_run and not a.headless:
        if should_open_launcher(raw_argv, a, is_tty):
            from . import tui
            return tui.launch_tui(open_launcher=True, initial_config=cfg)
        if a.tui and is_tty:
            from . import tui
            explicit_run_flags = [x for x in raw_argv if x != "--tui"]
            return tui.launch_tui(
                open_launcher=False,
                initial_config=cfg,
                autostart=bool(explicit_run_flags) or not tui.is_runner_alive(),
            )

    return run_overnight(
        window_budget=a.window_budget,
        window_capacity=a.window_capacity,
        max_modules=a.max_modules,
        wave=a.wave,
        chunk_size=a.chunk_size,
        max_chunk_insns=a.max_chunk_insns,
        module_budget=a.module_budget,
        module_calls=a.module_calls,
        repair_budget=a.repair_budget,
        skip=skip,
        only=only,
        sleep_on_limit=not a.no_sleep,
        rate_limit_sleep=a.rate_limit_sleep,
        dry_run=a.dry_run,
        stall_timeout=a.stall_timeout,
        provider=a.provider,
        codex_model=a.codex_model,
        codex_effort=a.codex_effort,
        codex_stage1=a.codex_stage1,
        codex_stage2=a.codex_stage2,
        codex_stage3=a.codex_stage3,
        codex_stage4=a.codex_stage4,
        codex_repair=a.codex_repair,
        codex_repair_calls=a.codex_repair_calls,
        codex_bin=a.codex_bin,
        codex_home=a.codex_home,
        codex_max_5h_pct=a.codex_max_5h_pct,
        codex_max_7d_pct=a.codex_max_7d_pct,
        codex_max_7d_delta_pp=a.codex_max_7d_delta_pp,
        codex_max_total_calls=a.codex_max_total_calls,
        codex_telemetry_max_age=a.codex_telemetry_max_age,
        codex_early_stop_stage2=a.codex_early_stop_stage2,
        wave4_max_calls=a.wave4_max_calls,
        wave4a_max_calls=a.wave4a_max_calls,
        wave4_retry=a.wave4_retry,
        wave4_include_unresolved=a.wave4_include_unresolved,
    )


if __name__ == "__main__":
    sys.exit(main())
