"""Zero-supervisor overnight runner for wc1.batch_driver on Claude Pro.

Runs unattended across the ROI-ordered M2 backlog (Wave 2 `c-only`, then Wave 3
`full`) without any long-lived LLM supervisor:

  1. Builds the live queue from `wc1.progress` (chunking large modules).
  2. Enforces a fractional 5-hour rolling window budget `--window-budget` in
     (0.0, 1.0] (1.0 = use the full Pro window until rate-limited, then sleep
     until recovery and continue).
  3. Invokes stateless `wc1.batch_driver` for each module/chunk.
  4. Runs `make verify`. On failure, optionally invokes ONE bounded, isolated
     `claude -p` repair pass scoped strictly to that module's files, then
     re-runs `make verify`.
  5. If green, commits ONLY the files changed/created by that module atomically.
     If still failing, archives those files into `build/failed/<tag>/`, cleanly
     rolls back only that module's changes (never touching pre-existing
     untracked WIP such as `BULLET.C`), and moves on to the next module.

Usage:
    nix develop -c python3 -m wc1.overnight --dry-run
    nix develop -c python3 -m wc1.overnight
    nix develop -c python3 -m wc1.overnight --window-budget 1.0 --max-modules 25
"""
import argparse
from collections import defaultdict
import datetime
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import time

from . import analysis, batch_driver, path, progress, symbols

WINDOW_SECONDS = 5 * 3600
DEFAULT_SKIP = ("BULLET.C", "STATUS.C")

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


def rolling_window_spend(ledger_dir=None, now=None, window_seconds=WINDOW_SECONDS):
    """Sum Claude API-equivalent USD spent in the rolling 5-hour window across ledgers.

    Returns (total_usd, call_count, oldest_ts_or_None).
    """
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


def build_queue(wave="all", chunk_size=12, skip=DEFAULT_SKIP, only=None,
                failed_keys=None):
    """Build the ROI-ordered queue of overnight work items from live progress."""
    p = analysis.run()
    funcs_db, _, _ = symbols.load(strict=False)
    mods = progress.load_modules()
    rows = progress.classify([f["start"] for f in p.functions], funcs_db, mods)
    by_addr = {f["start"]: f for f in p.functions}

    skip_set = set(skip or ())
    only_set = set(only) if only else None
    failed_set = set(failed_keys or ())

    w2 = defaultdict(list)
    w3 = defaultdict(list)
    for r in rows:
        if r["scope"] != "in" or r["done"]:
            continue
        m = r["module"]
        if m in skip_set:
            continue
        if only_set is not None and m not in only_set:
            continue
        ninsns = by_addr[r["addr"]]["ninsns"]
        if r["named"] and r["c"] == "none":
            w2[m].append((r["addr"], ninsns))
        elif not r["named"]:
            w3[m].append((r["addr"], ninsns))

    items = []

    def _next_free_area(base, mode, idx_hint=0):
        """Pick an area tag whose ledger is NOT already completed (stage4_done)."""
        suffix = "c" if mode == "c-only" else "f"
        cands = ([f"{base}_{suffix}" if mode == "c-only" else base]
                 if idx_hint == 0 else [])
        cands += [f"{base}_{suffix}{k}" for k in range(idx_hint + 1, idx_hint + 50)]
        for c in cands:
            lp = path("build", "ledger", f"{c}.jsonl")
            if not os.path.exists(lp):
                return c
            if not batch_driver.Ledger(lp).has_stage("stage4_done"):
                return c  # unfinished (e.g. rate-limited mid-run) -> resume it!
        return f"{base}_{suffix}_{int(time.time()) % 10000}"

    def _add_module_items(mode, m, fns):
        base = AREA_OVERRIDES.get(m, _slug(m))
        hdr = KNOWN_HEADERS.get(m)
        if hdr and not os.path.exists(path(hdr)):
            hdr = None
        count = len(fns)
        total_insns = sum(x[1] for x in fns)
        avg = total_insns / max(1, count)
        n_chunks = max(1, (count + chunk_size - 1) // chunk_size)
        for ci in range(n_chunks):
            tag = _next_free_area(base, mode, idx_hint=ci if n_chunks > 1 else 0)
            key = (mode, m, ci)
            if key in failed_set or (mode, m) in failed_set:
                continue
            lim = chunk_size if n_chunks > 1 else None
            # Keep generated files in a dedicated src subdir for this module
            src_sub = _slug(m)
            items.append({
                "key": key,
                "mode": mode,
                "module": m,
                "area": tag,
                "src_subdir": src_sub,
                "header": hdr,
                "limit": lim,
                "count": min(chunk_size, count - ci * chunk_size),
                "module_total": count,
                "total_insns": total_insns,
                "avg_insns": round(avg, 1),
            })

    if wave in ("all", "wave2"):
        # Prioritize multi-function named modules with low insns/fn first
        for m, fns in sorted(w2.items(), key=lambda kv: (len(kv[1]) < 3, sum(x[1] for x in kv[1]) / len(kv[1]), -len(kv[1]))):
            _add_module_items("c-only", m, fns)

    if wave in ("all", "wave3"):
        for m, fns in sorted(w3.items(), key=lambda kv: (sum(x[1] for x in kv[1]) / len(kv[1]), len(kv[1]))):
            _add_module_items("full", m, fns)

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


def progress_done_count():
    p = analysis.run()
    funcs_db, _, _ = symbols.load(strict=False)
    rows = progress.classify([f["start"] for f in p.functions], funcs_db, progress.load_modules())
    in_scope = [r for r in rows if r["scope"] == "in"]
    done = sum(1 for r in in_scope if r["done"])
    t3 = sum(1 for r in in_scope if r["c"] == "t3")
    t4 = sum(1 for r in in_scope if r["c"] == "t4")
    return done, len(in_scope), t3, t4


def archive_and_rollback(area, tracked_mods, new_untracked, log_text="", cwd=None):
    """Save failed module changes to build/failed/ and cleanly restore git tree."""
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
    if tracked_mods:
        subprocess.run(["git", "checkout", "--", *sorted(tracked_mods)],
                       cwd=root, check=True)
    dirs_to_prune = set()
    for rel in sorted(new_untracked):
        full = os.path.join(root, rel)
        if os.path.isfile(full) or os.path.islink(full):
            os.unlink(full)
            dirs_to_prune.add(os.path.dirname(full))
    # Prune empty newly created subdirectories under src/
    for d in sorted(dirs_to_prune, key=len, reverse=True):
        try:
            if os.path.isdir(d) and not os.listdir(d):
                os.rmdir(d)
        except OSError:
            pass
    return dest


def _has_forbidden_test_cheat(paths_list, cwd=None):
    root = cwd or path()
    for rel in paths_list:
        if rel.startswith("tests/") and rel.endswith(".py"):
            full = os.path.join(root, rel)
            if os.path.isfile(full):
                txt = open(full, errors="replace").read()
                if re.search(r"@pytest\.mark\.(?:xfail|skip)\b", txt):
                    return rel
    return None


def _run_subprocess_logged(cmd, log_fh, cwd=None):
    """Run command, streaming output to both stdout and log_fh; return (rc, text)."""
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, cwd=cwd or path(), bufsize=1,
    )
    buf = []
    assert proc.stdout is not None
    for line in proc.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()
        log_fh.write(line)
        log_fh.flush()
        buf.append(line)
    rc = proc.wait()
    return rc, "".join(buf)


def run_bounded_repair(item, changed_paths, failure_tail, repair_budget, log_fh):
    """Run ONE isolated claude -p repair pass scoped strictly to this module's files."""
    if repair_budget <= 0:
        return False, 0.0, False
    area = item["area"]
    ledger = batch_driver.Ledger(path("build", "ledger", f"{area}.jsonl"))
    files_str = "\n".join(f"  - {p}" for p in sorted(changed_paths))
    prompt = (
        f"Fix the failing verification/tests for module `{item['module']}` (area `{area}`).\n"
        f"ONLY edit files belonging to this module:\n{files_str}\n\n"
        f"HARD RULES:\n"
        f"- NEVER add `@pytest.mark.xfail` or `@pytest.mark.skip`.\n"
        f"- NEVER edit Makefile, tools/, war.h, or unrelated modules.\n"
        f"- NEVER run `git commit` or `git add`.\n"
        f"- Keep every `extern` declaration in `*_reference.c` on ONE single line.\n"
        f"- Allocate test buffers ONLY inside `init_emu(emu)` so they never overlap C code at 0x800000.\n"
        f"- After editing, verify with `python3 -m pytest -q <test_file>` and `python3 -m wc1.symbols`.\n\n"
        f"Failure output:\n```\n{failure_tail[-3500:]}\n```\n"
    )
    cmd = [
        "claude", "-p",
        "--model", "sonnet",
        "--effort", "medium",
        "--allowedTools", "Read,Edit,Bash",
        "--max-turns", "10",
        "--max-budget-usd", f"{repair_budget:.2f}",
        "--no-session-persistence",
        "--output-format", "json",
    ]
    t0 = time.time()
    p = subprocess.run(cmd, input=prompt, capture_output=True, text=True, cwd=path())
    dt = round(time.time() - t0, 2)
    combined = (p.stdout or "") + "\n" + (p.stderr or "")
    low = combined.lower()
    if any(k in low for k in ("rate_limit", "rate limit", "usage limit", "5-hour", "overloaded")):
        log_fh.write(f"[{_now_str()}] [RATE_LIMIT during repair {area}]\n")
        log_fh.flush()
        return False, 0.0, True
    cost = 0.0
    usage = {}
    try:
        data = json.loads(p.stdout)
        cost = float(data.get("total_cost_usd") or 0.0)
        usage = data.get("usage") or {}
    except Exception:
        pass
    ledger.record("claude_call", label=f"{area}:overnight_repair", model="sonnet",
                  effort="medium", cost_usd=cost, duration_s=dt, usage=usage)
    msg = f"  [repair {area}] rc={p.returncode} {dt}s cost=${cost:.4f}\n"
    sys.stdout.write(msg)
    sys.stdout.flush()
    log_fh.write(msg)
    log_fh.flush()
    return p.returncode == 0, cost, False


def write_summary(results, start_progress, summary_path=None):
    done, total, t3, t4 = progress_done_count()
    sp_done, _, sp_t3, sp_t4 = start_progress
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
    out = summary_path or path("build", "overnight_summary.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as fh:
        fh.write("\n".join(lines) + "\n")


def _sleep_with_heartbeat(seconds, reason, log_fh):
    end = time.time() + max(1, seconds)
    wake_str = datetime.datetime.fromtimestamp(end).strftime("%H:%M:%S")
    msg = f"[{_now_str()}] [SLEEP] {reason} — sleeping {int(seconds // 60)}m{int(seconds % 60)}s (until ~{wake_str})\n"
    sys.stdout.write(msg)
    sys.stdout.flush()
    log_fh.write(msg)
    log_fh.flush()
    while True:
        rem = end - time.time()
        if rem <= 0:
            break
        time.sleep(min(rem, 600))
        rem2 = end - time.time()
        if rem2 > 30:
            hb = f"[{_now_str()}] [SLEEP] still waiting ({int(rem2 // 60)}m remaining)...\n"
            sys.stdout.write(hb)
            sys.stdout.flush()
            log_fh.write(hb)
            log_fh.flush()


def run_overnight(window_budget=0.8, window_capacity=35.0, max_modules=0,
                  wave="all", chunk_size=12, module_budget=1.10,
                  module_calls=10, repair_budget=0.45, skip=DEFAULT_SKIP,
                  only=None, sleep_on_limit=True, rate_limit_sleep=900,
                  dry_run=False):
    if not (0.0 < window_budget <= 1.0):
        raise ValueError(f"--window-budget must be in (0.0, 1.0], got {window_budget}")

    if dry_run:
        q = build_queue(wave=wave, chunk_size=chunk_size, skip=skip, only=only)
        if max_modules > 0:
            q = q[:max_modules]
        w_spend, w_calls, oldest = rolling_window_spend()
        cap_desc = "FULL (until rate-limit)" if window_budget >= 1.0 else f"${window_budget * window_capacity:.2f} ({int(window_budget * 100)}% of ${window_capacity:.0f})"
        print(f"wc1.overnight DRY RUN: {len(q)} queue items | rolling 5h spend=${w_spend:.4f} ({w_calls} calls) | window_budget={cap_desc}")
        for i, it in enumerate(q, 1):
            hdr_s = f" hdr={it['header']}" if it["header"] else ""
            lim_s = f" limit={it['limit']}" if it["limit"] else ""
            print(f"  {i:2d}. [{it['mode']:6s}] {it['module']:16s} area={it['area']:18s} "
                  f"fn={it['count']:2d}/{it['module_total']:2d} avg={it['avg_insns']:5.1f} insns/fn{lim_s}{hdr_s}")
        return 0

    tracked0, baseline_untracked = git_status()
    if tracked0:
        print(f"ERROR: dirty tracked files in working tree: {sorted(tracked0)}", file=sys.stderr)
        print("Commit or stash tracked modifications before running wc1.overnight.", file=sys.stderr)
        return 2

    os.makedirs(path("build"), exist_ok=True)
    log_path = path("build", "overnight.log")
    start_prog = progress_done_count()
    results = []
    failed_keys = set()
    completed_runs = 0
    observed_capacity = float(window_capacity)

    with open(log_path, "a") as log_fh:
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
                if max_modules > 0 and completed_runs >= max_modules:
                    print(f"[{_now_str()}] Reached --max-modules={max_modules}, stopping cleanly.")
                    break

                q = build_queue(wave=wave, chunk_size=chunk_size, skip=skip,
                                only=only, failed_keys=failed_keys)
                if not q:
                    print(f"[{_now_str()}] Queue empty — all eligible modules done!")
                    break
                item = q[0]

                # Check rolling 5h window budget before starting
                w_spend, w_calls, oldest_ts = rolling_window_spend()
                if should_wait_for_window(window_budget, w_spend, observed_capacity):
                    if not sleep_on_limit:
                        print(f"[{_now_str()}] Rolling 5h spend ${w_spend:.2f} reached "
                              f"{int(window_budget * 100)}% of ${observed_capacity:.1f} (--no-sleep set), stopping.")
                        break
                    wait_s = compute_wait_seconds(oldest_ts)
                    _sleep_with_heartbeat(
                        wait_s,
                        f"rolling 5h spend ${w_spend:.2f} >= {int(window_budget * 100)}% of ${observed_capacity:.1f}",
                        log_fh,
                    )
                    continue

                area = item["area"]
                done_before = progress_done_count()[0]
                ledger_before = batch_driver.Ledger(path("build", "ledger", f"{area}.jsonl")).summary()["cost_usd"]
                banner = (
                    f"\n[{_now_str()}] >>> [{completed_runs + 1}] {item['mode']} {item['module']} "
                    f"(area={area}, ~{item['count']} fn, avg={item['avg_insns']} insns/fn) | "
                    f"5h spend=${w_spend:.2f}\n"
                )
                sys.stdout.write(banner)
                sys.stdout.flush()
                log_fh.write(banner)
                log_fh.flush()

                cmd = [
                    sys.executable, "-m", "wc1.batch_driver",
                    item["mode"], item["module"],
                    "--area", area,
                    "--src-subdir", item["src_subdir"],
                    "--max-cost", f"{module_budget:.2f}",
                    "--max-calls", str(module_calls),
                ]
                if item["header"]:
                    cmd += ["--header", item["header"]]
                if item["limit"]:
                    cmd += ["--limit", str(item["limit"])]

                rc, out_txt = _run_subprocess_logged(cmd, log_fh)
                if rc == batch_driver.EXIT_RATE_LIMIT or "[RATE_LIMIT]" in out_txt:
                    w_now, _, oldest_now = rolling_window_spend()
                    if w_now > 5.0 and w_now < observed_capacity:
                        observed_capacity = w_now
                    if not sleep_on_limit:
                        print(f"[{_now_str()}] Rate limit hit (--no-sleep set), stopping cleanly.")
                        break
                    wait_s = min(rate_limit_sleep, compute_wait_seconds(oldest_now, fallback_seconds=rate_limit_sleep))
                    _sleep_with_heartbeat(max(300, wait_s), "Claude Pro rate limit hit (resuming same module)", log_fh)
                    continue

                tracked_now, untracked_now = git_status()
                new_untracked = untracked_now - baseline_untracked
                changed = tracked_now | new_untracked

                if not changed:
                    failed_keys.add(item["key"])
                    cost_delta = max(0.0, batch_driver.Ledger(path("build", "ledger", f"{area}.jsonl")).summary()["cost_usd"] - ledger_before)
                    results.append({
                        "time": _now_str(), "module": item["module"], "mode": item["mode"],
                        "area": area, "status": "NOOP", "delta": 0, "cost": cost_delta,
                        "note": f"batch_driver produced no file changes (rc={rc})",
                    })
                    write_summary(results, start_prog)
                    completed_runs += 1
                    continue

                # Run make verify
                v_rc, v_out = _run_subprocess_logged(["make", "verify"], log_fh)
                cheat = _has_forbidden_test_cheat(changed)
                if (v_rc != 0 or cheat) and repair_budget > 0:
                    fail_info = v_out if v_rc != 0 else f"Forbidden xfail/skip cheat detected in {cheat}"
                    _, _, rl_hit = run_bounded_repair(item, changed, fail_info, repair_budget, log_fh)
                    if rl_hit:
                        if not sleep_on_limit:
                            break
                        _sleep_with_heartbeat(rate_limit_sleep, "Rate limit during repair", log_fh)
                        continue
                    tracked_now, untracked_now = git_status()
                    new_untracked = untracked_now - baseline_untracked
                    changed = tracked_now | new_untracked
                    cheat = _has_forbidden_test_cheat(changed)
                    v_rc, v_out = _run_subprocess_logged(["make", "verify"], log_fh)

                cost_delta = max(0.0, batch_driver.Ledger(path("build", "ledger", f"{area}.jsonl")).summary()["cost_usd"] - ledger_before)
                done_after = progress_done_count()[0]
                delta_done = done_after - done_before

                if v_rc == 0 and not cheat and delta_done > 0:
                    paths_to_add = sorted(changed)
                    subprocess.run(["git", "add", "--", *paths_to_add], cwd=path(), check=True)
                    commit_msg = f"T3/T4: {item['module']} ({area}) +{delta_done} done via wc1.overnight ({cost_delta:.2f} USD)"
                    subprocess.run(["git", "commit", "-m", commit_msg], cwd=path(), check=True)
                    rev = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                                         capture_output=True, text=True, cwd=path(), check=True).stdout.strip()
                    print(f"[{_now_str()}] [COMMITTED {rev}] {commit_msg}", flush=True)
                    results.append({
                        "time": _now_str(), "module": item["module"], "mode": item["mode"],
                        "area": area, "status": "COMMITTED", "delta": delta_done,
                        "cost": cost_delta, "note": rev,
                    })
                else:
                    reason = (f"cheat in {cheat}" if cheat else
                              f"delta_done={delta_done}" if v_rc == 0 else
                              f"make verify rc={v_rc}")
                    arch = archive_and_rollback(area, tracked_now, new_untracked,
                                                log_text=out_txt + "\n=== VERIFY ===\n" + v_out)
                    # Mark this module failed so we don't spin on it overnight
                    failed_keys.add((item["mode"], item["module"]))
                    print(f"[{_now_str()}] [ROLLED BACK] {item['module']} ({reason}) -> archived {os.path.relpath(arch, path())}", flush=True)
                    results.append({
                        "time": _now_str(), "module": item["module"], "mode": item["mode"],
                        "area": area, "status": "FAILED", "delta": 0, "cost": cost_delta,
                        "note": f"{reason}; archived {os.path.relpath(arch, path())}",
                    })

                write_summary(results, start_prog)
                completed_runs += 1
        except KeyboardInterrupt:
            print(f"\n[{_now_str()}] Interrupted by user (Ctrl-C). Writing summary...")
            write_summary(results, start_prog)
            return 130

    write_summary(results, start_prog)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="wc1.overnight", description=__doc__.split("\n\n")[0])
    ap.add_argument("--window-budget", type=float, default=0.8,
                    help="Fraction of 5h Pro window to use in (0.0, 1.0]; 1.0 = full window until rate-limit (default 0.8)")
    ap.add_argument("--window-capacity", type=float, default=35.0,
                    help="Estimated 5h Pro window capacity in API-equiv USD for fractional budgets < 1.0 (default 35.0, auto-calibrates on rate-limit)")
    ap.add_argument("--max-modules", type=int, default=0,
                    help="Optional max modules/chunks to run before stopping (0 = unlimited, default 0)")
    ap.add_argument("--wave", choices=("all", "wave2", "wave3"), default="all",
                    help="Which backlog wave to run (default all: wave2 then wave3)")
    ap.add_argument("--chunk-size", type=int, default=12,
                    help="Max functions per chunk for large modules (default 12)")
    ap.add_argument("--module-budget", type=float, default=1.10,
                    help="Max API-equiv USD per module/chunk passed to batch_driver (default 1.10)")
    ap.add_argument("--module-calls", type=int, default=10,
                    help="Max Claude calls per module/chunk passed to batch_driver (default 10)")
    ap.add_argument("--repair-budget", type=float, default=0.45,
                    help="Max USD for one isolated claude -p repair pass on verify failure; 0 disables repair (default 0.45)")
    ap.add_argument("--skip", default=",".join(DEFAULT_SKIP),
                    help="Comma-separated module names to skip (default BULLET.C,STATUS.C)")
    ap.add_argument("--only", default="",
                    help="Optional comma-separated whitelist of module names")
    ap.add_argument("--no-sleep", action="store_true",
                    help="Stop instead of sleeping when window budget / rate limit is reached")
    ap.add_argument("--rate-limit-sleep", type=int, default=900,
                    help="Seconds to sleep between retries after a real rate limit (default 900)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print the queue and current 5h spend without calling Claude")
    a = ap.parse_args(argv)
    skip = tuple(s.strip() for s in a.skip.split(",") if s.strip())
    only = tuple(s.strip() for s in a.only.split(",") if s.strip()) or None
    return run_overnight(
        window_budget=a.window_budget,
        window_capacity=a.window_capacity,
        max_modules=a.max_modules,
        wave=a.wave,
        chunk_size=a.chunk_size,
        module_budget=a.module_budget,
        module_calls=a.module_calls,
        repair_budget=a.repair_budget,
        skip=skip,
        only=only,
        sleep_on_limit=not a.no_sleep,
        rate_limit_sleep=a.rate_limit_sleep,
        dry_run=a.dry_run,
    )


if __name__ == "__main__":
    sys.exit(main())
