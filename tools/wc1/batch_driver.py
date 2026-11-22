"""Stateless, quota-aware Claude Pro batch decompilation driver.

Orchestrates Claude via `claude -p --safe-mode --tools ""
--exclude-dynamic-system-prompt-sections --no-session-persistence
--output-format json --json-schema ...` so:
  - Claude never runs an O(T^2) interactive tool loop;
  - All calls within a module share one `--system-prompt-file` prefix (1h cache);
  - Local compilation, wc1.match --diff, and wc1.permuter run at 0 tokens;
  - Every function has a hard T3 retry cap before recording t3_blocker -> T4;
  - Progress and token/USD usage are recorded in a resumable JSONL ledger.

usage:
  python3 -m wc1.batch_driver full <module> [--area NAME] [--max-cost 1.20] [--max-calls 10] [--dry-run]
  python3 -m wc1.batch_driver c-only <module> [--area NAME] [--max-cost 1.00]
  python3 -m wc1.batch_driver t4-only <module> [--area NAME] [--max-cost 0.60]
  python3 -m wc1.batch_driver stats <ledger.jsonl>
"""
import argparse
import ast
import collections
import faulthandler
import json
import os
import posixpath
import re
import secrets
import signal
import subprocess
import sys
import tempfile
import threading
import time

from . import analysis, build, codex, dossier, live, match, path, permuter, progress, symbols, t4spec

DEFAULT_RULES = """You are an expert 1994 Watcom C/C++ 10.0a (32-bit DOS/4GW, __watcall register convention: args in eax, edx, ebx, ecx, further args on stack callee-popped, return in eax) reverse engineer working on Warcraft: Orcs & Humans (war.exe, CD v1.22h).

HARD RULES:
1. Return ONLY valid JSON matching the provided JSON Schema.
2. Evidence rules (docs/METHODOLOGY.md):
   - Every symbol entry needs concrete evidence citing hex addresses, instructions, strings, or callers from the disassembly.
   - NEVER cite Ghidra in evidence! Ghidra drafts in the dossier are structural hints ONLY.
   - Use honest confidence: "high" (multiple independent lines), "medium" (one strong line), "low" (plausible from context). NEVER emit "verified" until mechanically checked.
3. Watcom 10.0a C codegen rules (docs/subsystems/compiler.md, codegen.md):
   - Every C file begins with:
       /* codegen-compiler: 10.0a */
     plus `/* codegen-flags: ... */` ONLY if flags differ from `-s -ot -ol -4r -zp2`.
   - One function per C file (wcc386 16-byte aligns a second function; war.exe does not).
   - Every file must compile cleanly under BOTH Watcom 10.0a and Open Watcom 2 (strict C89: declare all locals at top of block, no `//` if avoidable, no C99 mid-block decls or mixed decls/code).
   - 10.0a promotes unsigned byte/word compares (`and eax,0xff; cmp eax,imm`), so `test byte [addr], imm` usually comes from an unsigned bitfield or `unsigned long` mask.
   - `mov eax, [addr-2]; sar eax, 0x10` is a dword-view / volatile short read or `*(long *)((char *)&x - 2) >> 16` idiom.
   - `movsx`/`imul` array/ring walks use a `short` loop index.
   - Use DB symbol names via `extern` (never raw numeric addresses, NEVER `#pragma aux` aliases, NEVER pointer-offset `#define` macros to fake missing globals).
   - Every referenced unnamed data address in the module MUST get a `[[data]]` entry in Stage 1 (or be accessed as an indexed field/element of a named array/struct base like `hdr[1]`), so no `unresolved _dat_*` ever occurs!
   - If a function address already exists in another TOML file as a placeholder (`fn_XXXXX`), use the exact existing DB name in C (or follow the prompt's symbol list) so `wc1.match` resolves its link name cleanly.
"""


# A pytest node/file run by the driver is killed (with its descendants) after
# this many seconds (a hung emulator test must not stall the whole overnight
# item); while it runs the worker meta is refreshed every HEARTBEAT_EVERY s so
# wc1.overnight's stall watchdog does not take a silent pytest for a hang.
PYTEST_TIMEOUT = 900
HEARTBEAT_EVERY = 60
_live_area = None       # set by run_full_module/run_t4_only: whose meta to refresh


def _descendants(pid):
    """Every live descendant pid of pid (Linux /proc walk; [] elsewhere)."""
    kids = {}
    try:
        names = os.listdir("/proc")
    except OSError:
        return []
    for d in names:
        if not d.isdigit():
            continue
        try:
            with open(f"/proc/{d}/stat") as fh:
                ppid = int(fh.read().rsplit(")", 1)[1].split()[1])
        except (OSError, ValueError, IndexError):
            continue
        kids.setdefault(ppid, []).append(int(d))
    out, todo = [], [pid]
    while todo:
        c = kids.get(todo.pop(), [])
        out += c
        todo += c
    return out


def _run_capped(argv, cwd, env=None, timeout=None):
    """subprocess.run(argv, capture_output=True, text=True, timeout=...) whose
    timeout also SIGKILLs the child's descendants (emulator, wine compiles; the
    child stays in our process group so wc1.overnight's group kill still
    reaches it) and which refreshes the worker meta while it waits.  Raises
    subprocess.TimeoutExpired carrying the partial output, like subprocess.run."""
    timeout = PYTEST_TIMEOUT if timeout is None else timeout
    p = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         text=True, cwd=cwd, env=env)
    end = time.monotonic() + timeout
    while True:
        if _live_area:
            live.update_worker_meta(_live_area)
        left = end - time.monotonic()
        if left <= 0:
            break
        try:
            out, err = p.communicate(timeout=min(HEARTBEAT_EVERY, left))
            return subprocess.CompletedProcess(argv, p.returncode, out, err)
        except subprocess.TimeoutExpired:
            pass
    for pid in [p.pid] + _descendants(p.pid):
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
    try:
        out, err = p.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        # a killed child's pipe can stay open in a grandchild that escaped the
        # kill (setsid, or forked after _descendants ran): give up on its output
        for fh in (p.stdout, p.stderr):
            try:
                fh.close()
            except OSError:
                pass
        try:
            p.wait(timeout=2)
        except subprocess.TimeoutExpired:
            pass
        out, err = "", ""
    raise subprocess.TimeoutExpired(argv, timeout, output=out, stderr=err)


def _permute(area, stage, fpath, **kw):
    """permuter.permute_file(apply=True, jobs=4) with a live heartbeat.

    Every finished candidate refreshes the worker meta (`updated_at`), which
    wc1.overnight's stall watchdog reads; a compile timeout (stuck Wine)
    raises ToolchainError: the next candidate or function would hang the same
    way, and LLM repairs against a broken toolchain only cost money.
    """
    live.update_worker_meta(area, phase="PERMUTING", stage=stage)

    def _beat(n, label):
        live.update_worker_meta(area, phase="PERMUTING", stage=f"{stage} #{n}")

    pr = permuter.permute_file(fpath, jobs=4, apply=True, on_progress=_beat, **kw)
    if pr.get("env_error"):
        msg = f"[PERMUTER ERROR] {os.path.basename(fpath)}: {pr['env_error']}"
        print(f"  {msg}", flush=True)
        live.append_event(area, "error", msg)
        raise ToolchainError(msg)
    return pr


class DriverError(Exception):
    pass


class RateLimitError(DriverError):
    def __init__(self, msg="", resets_at=None):
        super().__init__(msg)
        self.resets_at = resets_at


class ToolchainError(DriverError):
    """The compiler itself is stuck (a compile timed out): stop, do not retry."""


class BudgetExceededError(DriverError):
    pass


class QuotaCapExceededError(DriverError):
    """Hard account/run quota ceiling hit (e.g. Codex 7d cap or total calls cap): stop immediately."""


# ---- JSON schemas -----------------------------------------------------------

SEMANTIC_SCHEMA = {
    "type": "object",
    "properties": {
        "module_summary": {"type": "string"},
        "header_h": {"type": "string", "description": "Complete C89 header file src/include/<area>.h"},
        "data_symbols": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "addr": {"type": "string", "description": "Hex address like 0x511a4"},
                    "name": {"type": "string"},
                    "type": {"type": "string"},
                    "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                    "evidence": {"type": "array", "items": {"type": "string"}, "minItems": 1},
                },
                "required": ["addr", "name", "type", "confidence", "evidence"],
            },
        },
        "functions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "addr": {"type": "string", "description": "Hex address like 0x2b8e0"},
                    "name": {"type": "string"},
                    "conv": {"type": "string", "enum": ["watcall", "cdecl", "asm", "pascal"]},
                    "proto": {"type": "string"},
                    "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                    "evidence": {"type": "array", "items": {"type": "string"}, "minItems": 1},
                },
                "required": ["addr", "name", "conv", "proto", "confidence", "evidence"],
            },
        },
    },
    "required": ["module_summary", "header_h", "data_symbols", "functions"],
}

BATCH_C_SCHEMA = {
    "type": "object",
    "properties": {
        "header_additions": {"type": "string", "description": "Optional extra decls/typedefs to add before #endif in header"},
        "files": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "addr": {"type": "string"},
                    "func_name": {"type": "string"},
                    "filename": {"type": "string", "description": "snake_case.c basename"},
                    "code": {"type": "string", "description": "Complete C89 source file starting with /* codegen-compiler: 10.0a */"},
                },
                "required": ["addr", "func_name", "filename", "code"],
            },
        },
    },
    "required": ["files"],
}

REPAIR_C_SCHEMA = {
    "type": "object",
    "properties": {
        "fixes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "addr": {"type": "string"},
                    "diagnosis": {"type": "string"},
                    "code": {"type": "string"},
                    "give_up_blocker": {
                        "type": "string",
                        "description": "Empty string to test code, OR '<regalloc|od-frame|codegen>: <evidence>' if T3 is unreachable",
                    },
                },
                "required": ["addr", "diagnosis", "code", "give_up_blocker"],
            },
        },
    },
    "required": ["fixes"],
}

T4_AND_DOC_SCHEMA = {
    "type": "object",
    "properties": {
        "test_py": {"type": "string", "description": "Complete pytest file using wc1.t4spec"},
        "doc_md": {"type": "string", "description": "Concise subsystem doc for docs/subsystems/<area>.md"},
        "ref_verified_by": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "addr": {"type": "string"},
                    "test_node": {"type": "string", "description": "difftest: tests/test_<area>.py::test_<name>"},
                },
                "required": ["addr", "test_node"],
            },
        },
    },
    "required": ["test_py", "doc_md", "ref_verified_by"],
}


# ---- Ledger -----------------------------------------------------------------

class Ledger:
    def __init__(self, ledger_path):
        self.path = ledger_path
        self.entries = []
        os.makedirs(os.path.dirname(os.path.abspath(ledger_path)), exist_ok=True)
        if os.path.exists(ledger_path):
            with open(ledger_path) as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        try:
                            self.entries.append(json.loads(line))
                        except ValueError:
                            pass

    def record(self, stage, **data):
        rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "stage": stage, **data}
        self.entries.append(rec)
        with open(self.path, "a") as fh:
            fh.write(json.dumps(rec) + "\n")
        return rec

    def total_cost(self):
        return sum(
            float(e.get("cost_usd", 0.0) or 0.0)
            for e in self.entries
            if e.get("stage") == "claude_call" or (e.get("provider") in (None, "claude") and e.get("cost_usd") is not None)
        )

    def total_calls(self, provider=None):
        if provider == "claude":
            return sum(1 for e in self.entries if e.get("stage") == "claude_call")
        if provider == "codex":
            return sum(1 for e in self.entries if e.get("stage") == "codex_call")
        return sum(1 for e in self.entries if e.get("stage") in ("claude_call", "codex_call"))

    def has_stage(self, stage, target=None):
        return any(
            e.get("stage") == stage and (target is None or e.get("target") == target) and e.get("ok", True)
            for e in self.entries
        )

    def last_stage(self, stage):
        for e in reversed(self.entries):
            if e.get("stage") == stage and e.get("ok", True):
                return e
        return None

    def drafted_files(self):
        """Return {addr_int: rel_or_abs_path} recorded across all draft batches."""
        out = {}
        for e in self.entries:
            fm = e.get("files_map")
            if isinstance(fm, dict) and e.get("ok", True):
                for a_hex, rel in fm.items():
                    try:
                        out[int(a_hex, 16)] = rel
                    except (TypeError, ValueError):
                        pass
        return out

    def summary(self):
        calls = [e for e in self.entries if e.get("stage") == "claude_call"]
        cc = sum(e.get("usage", {}).get("cache_creation_input_tokens", 0) for e in calls)
        cr = sum(e.get("usage", {}).get("cache_read_input_tokens", 0) for e in calls)
        out = sum(e.get("usage", {}).get("output_tokens", 0) for e in calls)
        inp = sum(e.get("usage", {}).get("input_tokens", 0) for e in calls)
        cost = sum(float(e.get("cost_usd", 0.0) or 0.0) for e in calls)

        codex_calls = [e for e in self.entries if e.get("stage") == "codex_call"]
        cx_in = sum(int((e.get("usage") or {}).get("input_tokens") or 0) for e in codex_calls)
        cx_ca = sum(int((e.get("usage") or {}).get("cached_input_tokens") or 0) for e in codex_calls)
        cx_out = sum(int((e.get("usage") or {}).get("output_tokens") or 0) for e in codex_calls)
        cx_reas = sum(int((e.get("usage") or {}).get("reasoning_output_tokens") or 0) for e in codex_calls)
        cx_p_deltas = [float(e["primary_delta_pp"]) for e in codex_calls if e.get("primary_delta_pp") is not None]
        cx_s_deltas = [float(e["secondary_delta_pp"]) for e in codex_calls if e.get("secondary_delta_pp") is not None]
        cx_est_p = sum(float(e.get("estimated_primary_pp") or 0.0) for e in codex_calls)
        cx_obs_n = sum(1 for e in codex_calls if e.get("telemetry_observed"))

        return {
            "calls": len(calls) + len(codex_calls),
            "claude_calls": len(calls),
            "cost_usd": round(cost, 4),
            "input_tokens": inp,
            "cache_create_tokens": cc,
            "cache_read_tokens": cr,
            "output_tokens": out,
            "cache_hit_pct": round(100.0 * cr / max(1, cr + cc + inp), 1),
            "codex_calls": len(codex_calls),
            "codex_input_tokens": cx_in,
            "codex_cached_input_tokens": cx_ca,
            "codex_output_tokens": cx_out,
            "codex_reasoning_tokens": cx_reas,
            "codex_cache_hit_pct": round(100.0 * cx_ca / max(1, cx_in), 1) if cx_in > 0 else 0.0,
            "codex_primary_delta_pp": round(sum(cx_p_deltas), 2) if cx_p_deltas else None,
            "codex_secondary_delta_pp": round(sum(cx_s_deltas), 2) if cx_s_deltas else None,
            "codex_estimated_primary_pp": round(cx_est_p, 3),
            "codex_telemetry_observed_calls": cx_obs_n,
        }


# ---- Claude CLI wrapper -----------------------------------------------------

def _feed_stdin(pipe, text):
    try:
        pipe.write(text)
    except OSError:
        pass
    finally:
        try:
            pipe.close()
        except OSError:
            pass


def _drain_stream(pipe, sink):
    try:
        for chunk in iter(lambda: pipe.read(4096), ""):
            sink.append(chunk)
    except OSError:
        pass
    finally:
        try:
            pipe.close()
        except OSError:
            pass


def call_claude(prompt, schema, sys_prompt_file, *, model="sonnet", effort="medium",
                ledger=None, label="", max_cost=None, max_calls=None, timeout=300,
                worker_id=None, claude_bin="claude"):
    """Invoke stateless `claude -p --safe-mode --tools ""` with live stream-json output."""
    if ledger is not None:
        if max_cost is not None and ledger.total_cost() >= max_cost:
            raise BudgetExceededError(f"cost ${ledger.total_cost():.3f} >= limit ${max_cost:.2f}")
        if max_calls is not None and ledger.total_calls() >= max_calls:
            raise BudgetExceededError(f"calls {ledger.total_calls()} >= limit {max_calls}")

    wid = worker_id or os.environ.get("WC1_LIVE_WORKER") or (label.split(":", 1)[0] if ":" in label else label)
    if wid:
        live.update_worker_meta(wid, phase="THINKING", label=label, model=model, effort=effort, provider="claude")
        live.append_event(wid, "stage", f"Calling Claude ({label}) [{model}/{effort}]...")

    cmd = [
        claude_bin, "-p",
        "--safe-mode",
        "--tools", "",
        "--exclude-dynamic-system-prompt-sections",
        "--no-session-persistence",
        "--model", model,
        "--effort", effort,
        "--output-format", "stream-json",
        "--verbose",
        "--include-partial-messages",
        "--system-prompt-file", os.path.abspath(sys_prompt_file),
        "--json-schema", json.dumps(schema, separators=(",", ":")),
    ]
    t0 = time.time()
    proc = subprocess.Popen(
        cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, bufsize=1, start_new_session=True,
    )
    timed_out = threading.Event()

    def _on_timeout():
        timed_out.set()
        live.terminate_process_tree(proc, grace=1.0)

    timer = threading.Timer(timeout, _on_timeout)
    timer.daemon = True
    timer.start()

    stderr_chunks = []
    writer = threading.Thread(target=_feed_stdin, args=(proc.stdin, prompt), daemon=True)
    err_reader = threading.Thread(target=_drain_stream, args=(proc.stderr, stderr_chunks), daemon=True)
    writer.start()
    err_reader.start()

    parsed = None
    raw_lines = []
    think_buf = ""
    text_buf = ""
    json_buf = ""
    json_chars = 0
    last_json_report = 0

    def _flush_buf(buf, kind, force=False):
        while "\n" in buf:
            ln, buf = buf.split("\n", 1)
            if ln.strip() and wid:
                live.append_event(wid, kind, ln)
        if (force or len(buf) >= 120) and buf.strip() and wid:
            live.append_event(wid, kind, buf)
            buf = ""
        return buf

    try:
        assert proc.stdout is not None
        for raw_line in proc.stdout:
            line = raw_line.strip()
            if not line:
                continue
            raw_lines.append(line)
            if len(raw_lines) > 20:
                raw_lines.pop(0)
            ev = live.parse_stream_json_line(line)
            if not ev:
                continue
            ek = ev["kind"]
            if ek == "thinking_delta":
                think_buf += ev["text"]
                think_buf = _flush_buf(think_buf, "think")
            elif ek == "text_delta":
                text_buf += ev["text"]
                text_buf = _flush_buf(text_buf, "out")
            elif ek == "input_json_delta":
                chunk = ev["text"]
                json_chars += len(chunk)
                json_buf = (json_buf + chunk)[-256:]
                m_fn = re.search(r'"filename"\s*:\s*"([^"]+)"', json_buf)
                if m_fn and wid:
                    live.append_event(wid, "out", f"Drafting {m_fn.group(1)} ({json_chars} chars)...")
                    json_buf = ""
                    last_json_report = json_chars
                elif json_chars - last_json_report >= 2000 and wid:
                    live.append_event(wid, "out", f"Streaming structured output ({json_chars} chars)...")
                    last_json_report = json_chars
            elif ek == "rate_limit":
                rl = ev["rate_limit"]
                live.save_rate_limits(rl)
                if wid:
                    fh5 = (rl.get("five_hour") or {}).get("used_percentage")
                    sd7 = (rl.get("seven_day") or {}).get("used_percentage")
                    if fh5 is not None or sd7 is not None:
                        live.append_event(wid, "info", f"Quota update: 5h={fh5}% 7d={sd7}%")
            elif ek == "result":
                parsed = ev["result"]
    finally:
        timer.cancel()
        timer.join(timeout=1.0)
        if proc.stdout:
            try:
                proc.stdout.close()
            except OSError:
                pass
        if timed_out.is_set():
            live.terminate_process_tree(proc, grace=1.0)
        else:
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                live.terminate_process_tree(proc, grace=1.0)
        writer.join(timeout=1.0)
        err_reader.join(timeout=1.0)

    think_buf = _flush_buf(think_buf, "think", force=True)
    text_buf = _flush_buf(text_buf, "out", force=True)
    elapsed = round(time.time() - t0, 2)
    err = "".join(stderr_chunks).strip()
    raw = "\n".join(raw_lines[-5:])

    if timed_out.is_set():
        if ledger:
            ledger.record("claude_timeout", label=label, timeout=timeout, ok=False)
        if wid:
            live.append_event(wid, "error", f"Claude timed out after {timeout}s ({label})")
        raise DriverError(f"claude -p timed out ({label}, {timeout}s)")

    if proc.returncode != 0 or not parsed or parsed.get("is_error"):
        msg = (parsed or {}).get("result") or err or raw[:300]
        if any(k in msg.lower() for k in ("rate limit", "usage limit", "5-hour", "quota", "overloaded", "429")):
            if ledger:
                ledger.record("rate_limit", label=label, msg=msg[:240], ok=False)
            if wid:
                live.append_event(wid, "error", f"RATE LIMIT: {msg[:180]}")
            raise RateLimitError(msg[:240])
        if ledger:
            ledger.record("claude_error", label=label, rc=proc.returncode, msg=msg[:240], ok=False)
        if wid:
            live.append_event(wid, "error", f"Claude error (rc={proc.returncode}): {msg[:180]}")
        raise DriverError(f"claude -p failed ({label}, rc={proc.returncode}): {msg[:300]}")

    out_obj = parsed.get("structured_output")
    if out_obj is None and isinstance(parsed.get("result"), str):
        try:
            out_obj = json.loads(parsed["result"])
        except ValueError:
            pass
    if out_obj is None:
        raise DriverError(f"claude -p returned no structured_output ({label}): {raw[:300]}")

    cost = float(parsed.get("total_cost_usd") or 0.0)
    usage = parsed.get("usage") or {}
    if ledger:
        ledger.record(
            "claude_call",
            label=label,
            model=model,
            effort=effort,
            cost_usd=cost,
            elapsed_s=elapsed,
            usage={
                "input_tokens": usage.get("input_tokens", 0),
                "cache_creation_input_tokens": usage.get("cache_creation_input_tokens", 0),
                "cache_read_input_tokens": usage.get("cache_read_input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
                "thinking_tokens": (usage.get("output_tokens_details") or {}).get("thinking_tokens", 0),
            },
        )
    summary_line = (
        f"  [claude {label}] {model}/{effort} {elapsed}s ${cost:.4f} "
        f"cc={usage.get('cache_creation_input_tokens',0)} "
        f"cr={usage.get('cache_read_input_tokens',0)} "
        f"out={usage.get('output_tokens',0)}"
    )
    print(summary_line, flush=True)
    if wid:
        live.append_event(wid, "info", summary_line.strip())
    return out_obj, cost, usage


def _call_llm(prompt, schema, sys_prompt_file, *, provider="claude", stage="stage1",
              claude_model="sonnet", claude_effort="medium",
              codex_matrix=None, codex_bin=None, codex_home=None, codex_quota_guard=None,
              ledger=None, label="", max_cost=None, max_calls=None, timeout=300,
              worker_id=None, claude_bin="claude"):
    """Provider-dispatched stateless LLM call (`claude` default or `codex`)."""
    if provider == "claude":
        return call_claude(
            prompt, schema, sys_prompt_file,
            model=claude_model, effort=claude_effort,
            ledger=ledger, label=label,
            max_cost=max_cost, max_calls=max_calls,
            timeout=timeout, worker_id=worker_id, claude_bin=claude_bin,
        )
    if provider != "codex":
        raise DriverError(f"Unknown provider: {provider!r}")

    matrix = codex_matrix or codex.DEFAULT_STAGE_MATRIX
    model, effort = matrix.get(stage, (codex.DEFAULT_MODEL, codex.DEFAULT_EFFORT))
    # Track total_calls_used in quota_guard if caller passed a shared dict
    guard = dict(codex_quota_guard) if isinstance(codex_quota_guard, dict) else None
    if guard is not None:
        base_calls = int(guard.pop("_base_total_calls", 0) or 0)
        for k in [k for k in guard if str(k).startswith("_")]:
            guard.pop(k)
        if ledger is not None and guard.get("max_total_calls") is not None:
            guard["total_calls_used"] = base_calls + ledger.total_calls(provider="codex")
    attempted = False
    try:
        attempted = True
        out_obj, meta = codex.call_codex(
            prompt, schema, sys_prompt_file,
            model=model, effort=effort,
            ledger=ledger, label=label,
            max_calls=max_calls, timeout=timeout,
            worker_id=worker_id, codex_bin=codex_bin,
            codex_home=codex_home, quota_guard=guard,
        )
    except codex.CodexCallLimitError as ex:
        attempted = False  # blocked before the gate: the after-reset pass is not used up
        raise BudgetExceededError(str(ex)) from ex
    except codex.CodexQuotaError as ex:
        if ex.action == "wait":
            raise RateLimitError(str(ex), resets_at=ex.resets_at) from ex
        if ex.action == "stop_budget":
            raise QuotaCapExceededError(str(ex)) from ex
        raise DriverError(str(ex)) from ex
    except (TimeoutError, RuntimeError, ValueError) as ex:
        raise DriverError(str(ex)) from ex
    finally:
        # M1: the after-reset pass covers exactly one resumed call; that call saves fresh
        # telemetry (rollout/stdout), so later calls need fresh telemetry again.
        if attempted and isinstance(codex_quota_guard, dict) and codex_quota_guard.get("after_reset"):
            codex_quota_guard["after_reset"] = False
    _snapshot_start_7d(codex_quota_guard, meta)
    return out_obj, 0.0, meta["usage"]


def _snapshot_start_7d(codex_quota_guard, meta):
    """S5: lazily fix the 7d delta baseline from the first observed telemetry when the run
    did not get one up front (`--codex-start-7d-pct` absent and no fresh telemetry at start)."""
    if not isinstance(codex_quota_guard, dict) or codex_quota_guard.get("max_7d_delta_pp") is None:
        return
    if codex_quota_guard.get("start_7d_pct") is not None or not isinstance(meta, dict):
        return
    for key in ("rate_limits_before", "rate_limits_after"):
        rl = meta.get(key)
        if not isinstance(rl, dict):
            continue
        sec = rl.get("secondary") if isinstance(rl.get("secondary"), dict) else None
        ok, _msg = codex.is_window_fresh(sec, rl.get("observed_at"),
                                         max_age_s=codex_quota_guard.get("max_age_s")
                                         or codex.DEFAULT_TELEMETRY_MAX_AGE_S)
        if ok:
            codex_quota_guard["start_7d_pct"] = float(sec["used_percent"])
            codex_quota_guard["start_7d_resets_at"] = codex._as_float(sec.get("resets_at"))
            return


# ---- TOML & file helpers ----------------------------------------------------

def _sanitize_evidence(ev_list):
    clean = []
    for s in ev_list:
        if "ghidra" in s.lower():
            continue
        clean.append(s)
    return clean or ["observed in disassembly"]


def _toml_str(s):
    return json.dumps(str(s))


def render_toml_entry(kind, e):
    lines = [f"[[{kind}]]"]
    lines.append(f"addr = {e['addr']:#x}")
    lines.append(f"name = {_toml_str(e['name'])}")
    if kind == "func":
        lines.append(f"conv = {_toml_str(e.get('conv', 'watcall'))}")
        if e.get("proto"):
            lines.append(f"proto = {_toml_str(e['proto'])}")
        if e.get("module"):
            lines.append(f"module = {_toml_str(e['module'])}")
        if e.get("src"):
            lines.append(f"src = {_toml_str(e['src'])}")
        if e.get("ref"):
            lines.append(f"ref = {_toml_str(e['ref'])}")
        if e.get("ref_verified_by"):
            lines.append(f"ref_verified_by = {_toml_str(e['ref_verified_by'])}")
        if e.get("t3_blocker"):
            lines.append(f"t3_blocker = {_toml_str(e['t3_blocker'])}")
    else:
        if e.get("type"):
            lines.append(f"type = {_toml_str(e['type'])}")
    lines.append(f"confidence = {_toml_str(e['confidence'])}")
    if e.get("verified_by"):
        lines.append(f"verified_by = {_toml_str(e['verified_by'])}")
    ev = ", ".join(_toml_str(x) for x in _sanitize_evidence(e.get("evidence", [])))
    lines.append(f"evidence = [{ev}]")
    return "\n".join(lines) + "\n"


def _blocker_category(diff_dict, style):
    if style == "OD":
        return "od-frame"
    c = diff_dict.get("counts") or {}
    if c.get("op", 0) == 0 and c.get("imm", 0) == 0 and c.get("reg", 0) > 0:
        return "regalloc"
    return "codegen"


def _write_sys_prompt(area, mod_dossier):
    work = path("build", "driver")
    os.makedirs(work, exist_ok=True)
    sp = os.path.join(work, f"{area}_sys.txt")
    parts = [DEFAULT_RULES, "\n## Matched Watcom 10.0a Exemplars\n"]
    for ex in mod_dossier.get("exemplars", []):
        parts.append(f"### {ex['path']}\n```c\n{ex['source']}\n```\n")
    # Include war.h so every call knows the core types without reading files
    war_h = path("src", "include", "war.h")
    if os.path.exists(war_h):
        parts.append("\n## src/include/war.h\n```c\n" + open(war_h).read() + "\n```\n")
    with open(sp, "w") as fh:
        fh.write("\n".join(parts))
    return sp


def _batch_functions(funcs, max_insns=480, max_count=10):
    batches, cur, cur_insns = [], [], 0
    for fn in funcs:
        if cur and (len(cur) >= max_count or cur_insns + fn["ninsns"] > max_insns):
            batches.append(cur)
            cur, cur_insns = [], 0
        cur.append(fn)
        cur_insns += fn["ninsns"]
    if cur:
        batches.append(cur)
    return batches


LOCKED_TOMLS = {"analysis/symbols/codegen_promo.toml"}


def _git_tracked_files(cwd=None):
    """Return set of git-tracked relative paths, or None if not in a git repo."""
    root = cwd or path()
    try:
        r = subprocess.run(
            ["git", "ls-files"],
            capture_output=True, text=True, cwd=root, check=True,
        )
        return set(r.stdout.splitlines())
    except (OSError, subprocess.CalledProcessError):
        return None


def _is_protected_toml(rel_file, created_rel=None, cwd=None):
    """True if `rel_file` must NOT be modified by automated TOML writers
    (codegen_promo.toml or a pre-existing untracked WIP TOML like bullet.toml)."""
    norm = rel_file.replace("\\", "/")
    if norm in LOCKED_TOMLS:
        return True
    if created_rel and norm == created_rel.replace("\\", "/"):
        return False
    full = os.path.join(cwd or path(), norm)
    if not os.path.exists(full):
        return False
    tracked = _git_tracked_files(cwd=cwd)
    if tracked is not None and norm not in tracked:
        return True
    return False


def _rewrite_toml_with_results(toml_path, sem, module_name, area, funcs_db, datas_db,
                               t3_matched, t4_needed, ref_verified=None,
                               t3_unbuildable=None):
    """Rewrite analysis/symbols/<area>.toml with T3 src=, T4 ref=/t3_blocker/ref_verified_by,
    or unbuildable-T3 verified_by (no src/ref, IntroOpPlaySound precedent)."""
    ref_verified = ref_verified or {}
    t3_unbuildable = t3_unbuildable or {}
    entries_text = [f"# {module_name} ({area}) - reconstructed via wc1.batch_driver\n"]
    for fn in sem["functions"]:
        a = int(fn["addr"], 16)
        if a in funcs_db and funcs_db[a]["_file"] != f"analysis/symbols/{area}.toml":
            continue
        entry = {
            "addr": a,
            "name": fn["name"],
            "conv": fn.get("conv", "watcall"),
            "proto": fn["proto"],
            "module": module_name,
            "confidence": fn["confidence"],
            "evidence": list(fn["evidence"]),
        }
        if a in t3_matched:
            entry["src"] = t3_matched[a]
            entry["confidence"] = "verified"
            entry["verified_by"] = f"match: {t3_matched[a]}"
        elif a in t3_unbuildable:
            rel_u, reason_u = t3_unbuildable[a]
            entry["confidence"] = "verified"
            entry["verified_by"] = f"match: python3 -m wc1.match {rel_u}"
            note = f"not built from C: {reason_u}"
            if note not in entry["evidence"]:
                entry["evidence"].insert(0, note)
        elif a in t4_needed:
            rel_ref, blocker = t4_needed[a]
            entry["ref"] = rel_ref
            entry["t3_blocker"] = blocker
            if a in ref_verified:
                rv = str(ref_verified[a]).strip()
                entry["ref_verified_by"] = rv if rv.startswith("difftest:") else "difftest: " + rv
        entries_text.append(render_toml_entry("func", entry))
    for dt in sem.get("data_symbols", []):
        a = int(dt["addr"], 16)
        if a in datas_db and datas_db[a]["_file"] != f"analysis/symbols/{area}.toml":
            continue
        entries_text.append(render_toml_entry("data", {
            "addr": a,
            "name": dt["name"],
            "type": dt["type"],
            "confidence": dt["confidence"],
            "evidence": dt["evidence"],
        }))
    with open(toml_path, "w") as fh:
        fh.write("\n".join(entries_text))


def _patch_header_decl(hdr, old_name, new_name, addr, decl_fallback,
                       nth_in_batch=0, collides_existing=False):
    """Rename only the colliding declaration in `hdr` (never clobbering an
    earlier intra-batch declaration or an existing extern with `old_name`).
    """
    if not hdr or not old_name:
        return hdr
    pat = re.compile(rf"\b{re.escape(old_name)}\b")
    addr_rx = re.compile(rf"\b(?:0x)?0*{addr:x}\b", re.I)
    lines = hdr.splitlines(keepends=True)

    def _is_decl_line(ln):
        s = ln.lstrip()
        if not s or s.startswith("#") or s.startswith("//") or s.startswith("/*") or s.startswith("*"):
            return False
        return bool(pat.search(ln))

    match_idxs = [i for i, ln in enumerate(lines) if _is_decl_line(ln)]

    # 1) Exact address tag on declaration line wins unambiguously.
    for i in match_idxs:
        if addr_rx.search(lines[i]):
            lines[i] = pat.sub(new_name, lines[i])
            return "".join(lines)

    # 2) Intra-batch duplicate: patch only the nth_in_batch-th matching line.
    if nth_in_batch >= 1 and len(match_idxs) > nth_in_batch:
        i = match_idxs[nth_in_batch]
        lines[i] = pat.sub(new_name, lines[i])
        return "".join(lines)

    # 3) Single non-existing declaration: safe to rename in place.
    if not collides_existing and nth_in_batch == 0 and len(match_idxs) == 1:
        i = match_idxs[0]
        lines[i] = pat.sub(new_name, lines[i])
        return "".join(lines)

    # 4) Otherwise preserve existing declarations and insert `decl_fallback` before #endif.
    if decl_fallback and not re.search(rf"\b{re.escape(new_name)}\b", hdr):
        ins = decl_fallback.rstrip(";") + ";\n"
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].lstrip().startswith("#endif"):
                lines.insert(i, ins)
                return "".join(lines)
        if lines and not lines[-1].endswith("\n"):
            lines[-1] += "\n"
        lines.append(ins)
    return "".join(lines)


def _disambiguate_semantic_names(sem, funcs_db, datas_db, allow_hdr_patch=True):
    """Ensure every new Stage-1 func/data entry has a globally unique link name.

    Compares via `symbols.link_name(kind, entry)` so cdecl `_X` vs data `_X`
    collisions, `link` overrides, and intra-batch duplicates are caught before
    writing the semantic cache, header, or TOML. Returns True if any entry changed.
    """
    existing_links = {e["link_name"] for t in (funcs_db, datas_db) for e in t.values() if e.get("link_name")}
    used_links = set(existing_links)
    seen_names = {}  # old_name -> count of earlier entries kept/seen in this batch
    changed = False
    hdr = str(sem.get("header_h") or "")

    def _pick_unique(kind, entry, addr):
        base = str(entry.get("name") or "")
        ln = symbols.link_name(kind, entry)
        if ln not in used_links:
            used_links.add(ln)
            return None, False
        collides_existing = ln in existing_links
        suffix = f"{addr:x}"
        k = 0
        while True:
            cand_name = f"{base}_{suffix}" if k == 0 else f"{base}_{suffix}_{k}"
            probe = dict(entry, name=cand_name)
            probe.pop("link", None)
            cand_ln = symbols.link_name(kind, probe)
            if cand_ln not in used_links:
                used_links.add(cand_ln)
                return cand_name, collides_existing
            k += 1

    for fn in sem.get("functions", []):
        try:
            a = int(fn["addr"], 16) if isinstance(fn.get("addr"), str) else int(fn["addr"])
        except (TypeError, ValueError):
            continue
        if a in funcs_db:
            continue
        old_name = fn.get("name", "")
        nth = seen_names.get(old_name, 0)
        new_name, collides_existing = _pick_unique("func", fn, a)
        seen_names[old_name] = nth + 1
        if new_name:
            fn["name"] = new_name
            if "proto" in fn and old_name:
                fn["proto"] = re.sub(rf"\b{re.escape(old_name)}\b", new_name, fn["proto"])
            if allow_hdr_patch and old_name and hdr:
                fallback = fn.get("proto") or f"void {new_name}(void)"
                hdr = _patch_header_decl(
                    hdr, old_name, new_name, a, fallback,
                    nth_in_batch=nth, collides_existing=collides_existing,
                )
            changed = True

    for dt in sem.get("data_symbols", []):
        try:
            a = int(dt["addr"], 16) if isinstance(dt.get("addr"), str) else int(dt["addr"])
        except (TypeError, ValueError):
            continue
        if a in datas_db:
            continue
        old_name = dt.get("name", "")
        nth = seen_names.get(old_name, 0)
        new_name, collides_existing = _pick_unique("data", dt, a)
        seen_names[old_name] = nth + 1
        if new_name:
            dt["name"] = new_name
            if allow_hdr_patch and old_name and hdr:
                dtype = dt.get("type", "int")
                m_arr = re.match(r"^(.+?)(\[.*\])$", dtype.strip())
                fallback = f"extern {m_arr.group(1).strip()} {new_name}{m_arr.group(2)}" if m_arr else f"extern {dtype} {new_name}"
                hdr = _patch_header_decl(
                    hdr, old_name, new_name, a, fallback,
                    nth_in_batch=nth, collides_existing=collides_existing,
                )
            changed = True

    if changed and allow_hdr_patch and "header_h" in sem:
        sem["header_h"] = hdr
    return changed


def _update_existing_toml_entries(t3_matched, t4_needed, ref_verified=None,
                                  t3_unbuildable=None, created_toml=None, cwd=None):
    """Update existing TOML entries (for c-only / t4-only / post-repair wiring) cleanly in place.

    Refuses to modify locked TOMLs (`codegen_promo.toml`) or pre-existing untracked
    WIP TOML files (e.g. `analysis/symbols/bullet.toml`).
    """
    ref_verified = ref_verified or {}
    t3_unbuildable = t3_unbuildable or {}
    root = cwd or path()
    funcs_db, _, _ = symbols.load(
        root=os.path.join(root, "analysis", "symbols"), strict=False, repo_root=root,
    )
    by_file = {}
    for a in set(t3_matched) | set(t4_needed) | set(ref_verified) | set(t3_unbuildable):
        e = funcs_db.get(a)
        if e:
            rel_f = os.path.relpath(os.path.join(path(), e["_file"]), root).replace("\\", "/")
            by_file.setdefault(rel_f, []).append(a)
    for rel_file, addrs in by_file.items():
        if _is_protected_toml(rel_file, created_rel=created_toml, cwd=root):
            print(f"  [skip protected TOML] {rel_file} ({[hex(x) for x in addrs]})", flush=True)
            continue
        full = os.path.join(root, rel_file)
        text = open(full).read()
        for a in addrs:
            # Find the [[func]] block whose addr matches `a`
            pat = re.compile(
                rf"(\[\[func\]\]\s*\naddr\s*=\s*0x0*{a:x}\b.*?)(?=\n\[\[|\Z)",
                re.I | re.S,
            )
            m = pat.search(text)
            if not m:
                continue
            blk = m.group(1)
            if a in t3_matched:
                # Remove ref/ref_verified_by/t3_blocker if promoting
                blk = re.sub(r"\n(?:ref|ref_verified_by|t3_blocker|src|verified_by)\s*=.*", "", blk)
                blk = re.sub(r'\nconfidence\s*=\s*"[^"]*"', '\nconfidence = "verified"', blk)
                blk = blk.rstrip() + f'\nsrc = "{t3_matched[a]}"\nverified_by = "match: {t3_matched[a]}"'
            elif a in t3_unbuildable:
                rel_u, _reason_u = t3_unbuildable[a]
                blk = re.sub(r"\n(?:ref|ref_verified_by|t3_blocker|src|verified_by)\s*=.*", "", blk)
                blk = re.sub(r'\nconfidence\s*=\s*"[^"]*"', '\nconfidence = "verified"', blk)
                blk = blk.rstrip() + f'\nverified_by = "match: python3 -m wc1.match {rel_u}"'
            else:
                if a in t4_needed:
                    rel_ref, blocker = t4_needed[a]
                    if not re.search(r"\nref\s*=", blk):
                        blk = blk.rstrip() + f'\nref = "{rel_ref}"'
                    if not re.search(r"\nt3_blocker\s*=", blk):
                        blk = blk.rstrip() + f'\nt3_blocker = {json.dumps(blocker)}'
                if a in ref_verified:
                    rv = str(ref_verified[a]).strip()
                    if not rv.startswith("difftest:"):
                        rv = "difftest: " + rv
                    blk = re.sub(r"\nref_verified_by\s*=.*", "", blk)
                    blk = blk.rstrip() + f'\nref_verified_by = {json.dumps(rv)}'
            text = text[:m.start(1)] + blk + text[m.end(1):]
        with open(full, "w") as fh:
            fh.write(text)


def find_forbidden_test_cheat(test_src):
    """Return a short reason string if `test_src` contains skip/xfail, oracle-suppression,
    or oracle-tampering cheats, else None.

    Delegates to the single shared AST prefilter in `wc1.symbols.check_t4_test_source`.
    """
    return symbols.check_t4_test_source(test_src, strict_pytestmark=True)


def _extract_test_invariants(tree):
    """Extract structural invariants from a T4 test AST for anti-weakening checks."""
    test_funcs = set()
    t4case_dumps = collections.Counter()
    case_list_lens = {}
    oracle_addrs = set()
    oracle_count = 0
    rand_cases_by_fn = {}
    has_watch_or_stubs = {}

    def _int_val(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, int) and not isinstance(node.value, bool):
            return int(node.value)
        return None

    def _is_nonempty_seq(node):
        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            return len(node.elts) > 0
        # Calls / names / variables (e.g. `watch=W` or `stubs=STUBS()`) count as non-empty
        return not (isinstance(node, ast.Constant) and not node.value)

    def _scan_fn(fn_name, node):
        nonlocal oracle_count
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call):
                chain = symbols._attr_chain(sub.func)
                if chain and chain[-1] == "T4Case":
                    t4case_dumps[ast.dump(sub, include_attributes=False)] += 1
                if chain and chain[-1] in ("run_spec", "run_pair"):
                    oracle_count += 1
                    addr_arg = None
                    if chain[-1] == "run_spec" and len(sub.args) >= 3:
                        addr_arg = _int_val(sub.args[2])
                    elif chain[-1] == "run_pair" and len(sub.args) >= 2:
                        addr_arg = _int_val(sub.args[1])
                    for kw in sub.keywords:
                        if kw.arg == "orig_addr":
                            v = _int_val(kw.value)
                            if v is not None:
                                addr_arg = v
                        elif kw.arg == "rand_cases":
                            v = _int_val(kw.value)
                            if v is not None:
                                rand_cases_by_fn[fn_name] = max(rand_cases_by_fn.get(fn_name, 0), v)
                        elif kw.arg in ("watch", "stubs") and _is_nonempty_seq(kw.value):
                            has_watch_or_stubs[fn_name] = has_watch_or_stubs.get(fn_name, set()) | {kw.arg}
                    if addr_arg is not None:
                        oracle_addrs.add(addr_arg)
            elif isinstance(sub, ast.Assign):
                for tgt in sub.targets:
                    if isinstance(tgt, ast.Name) and tgt.id.lower() in ("cases", "bl"):
                        val = sub.value
                        if isinstance(val, ast.Lambda):
                            val = val.body
                        if isinstance(val, (ast.List, ast.Tuple)):
                            key = f"{fn_name}:{tgt.id}"
                            case_list_lens[key] = max(case_list_lens.get(key, 0), len(val.elts))

    for stmt in tree.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if stmt.name.startswith("test_"):
                test_funcs.add(stmt.name)
            _scan_fn(stmt.name, stmt)
        elif isinstance(stmt, ast.ClassDef):
            for sub in stmt.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    qname = f"{stmt.name}::{sub.name}"
                    if sub.name.startswith("test_"):
                        test_funcs.add(qname)
                    _scan_fn(qname, sub)
        else:
            _scan_fn("<module>", stmt)

    return {
        "test_funcs": test_funcs,
        "t4case_dumps": t4case_dumps,
        "case_list_lens": case_list_lens,
        "oracle_addrs": oracle_addrs,
        "oracle_count": oracle_count,
        "rand_cases_by_fn": rand_cases_by_fn,
        "has_watch_or_stubs": has_watch_or_stubs,
    }


def check_test_patch_not_weakening(old_src, new_src, *, allow_case_edits=False):
    """Compare old and new T4 test ASTs and reject patches that weaken test coverage.

    Rejects:
      - syntax errors or cheat patterns in `new_src`;
      - dropping existing `test_*` functions;
      - reducing total `run_spec`/`run_pair` calls or changing any literal `orig_addr`;
      - reducing `rand_cases` or deleting/shrinking `T4Case(...)` / `cases = [...]` lists;
      - modifying existing `T4Case(...)` literals when `allow_case_edits=False`;
      - clearing `watch` or `stubs` completely when previously non-empty.
    Returns a reason string if weakening is detected, else None.
    """
    cheat = find_forbidden_test_cheat(new_src)
    if cheat:
        return f"cheat in patched test: {cheat}"
    try:
        old_tree = ast.parse(old_src)
    except SyntaxError:
        return None
    try:
        new_tree = ast.parse(new_src)
    except SyntaxError as ex:
        return f"syntax error in patched test: {ex}"

    old_inv = _extract_test_invariants(old_tree)
    new_inv = _extract_test_invariants(new_tree)

    dropped_tests = sorted(old_inv["test_funcs"] - new_inv["test_funcs"])
    if dropped_tests:
        return f"dropped test function(s): {', '.join(dropped_tests)}"
    if new_inv["oracle_count"] < old_inv["oracle_count"]:
        return f"reduced run_spec/run_pair calls ({old_inv['oracle_count']} -> {new_inv['oracle_count']})"
    missing_addrs = sorted(old_inv["oracle_addrs"] - new_inv["oracle_addrs"])
    if missing_addrs:
        return f"changed/removed orig_addr target(s): {', '.join(hex(a) for a in missing_addrs)}"
    for fn_name, old_rc in old_inv["rand_cases_by_fn"].items():
        new_rc = new_inv["rand_cases_by_fn"].get(fn_name, 0)
        if new_rc < old_rc:
            return f"reduced rand_cases in {fn_name} ({old_rc} -> {new_rc})"
    old_total_cases = sum(old_inv["t4case_dumps"].values())
    new_total_cases = sum(new_inv["t4case_dumps"].values())
    if new_total_cases < old_total_cases:
        return f"reduced T4Case count ({old_total_cases} -> {new_total_cases})"
    if not allow_case_edits:
        for dump, cnt in old_inv["t4case_dumps"].items():
            if new_inv["t4case_dumps"].get(dump, 0) < cnt:
                return "modified or deleted an existing T4Case(...) literal"
    for key, old_len in old_inv["case_list_lens"].items():
        new_len = new_inv["case_list_lens"].get(key)
        if new_len is not None and new_len < old_len:
            return f"shrank case list {key} ({old_len} -> {new_len})"
    for fn_name, old_obs in old_inv["has_watch_or_stubs"].items():
        new_obs = new_inv["has_watch_or_stubs"].get(fn_name, set())
        if "watch" in old_obs and "watch" not in new_obs and "stubs" not in new_obs:
            return f"removed all watch/stubs observations in {fn_name}"
    return None


def _pytest_output_passed(returncode, out_txt, test_src=None):
    """True only when pytest exited 0, ran >=1 passing test, and had ZERO skipped/xfailed/xpassed/cheats."""
    if returncode != 0:
        return False
    out = out_txt or ""
    if re.search(r"\b[1-9]\d*\s+(?:skipped|xfailed|xpassed|failed|errors?)\b", out):
        return False
    if test_src and find_forbidden_test_cheat(test_src):
        return False
    return bool(re.search(r"\b[1-9]\d*\s+passed\b", out))


def _test_file_exercises_ref(test_src, ref_rel):
    """Verify a T4 test file actually invokes t4spec/cemu on the function's `ref` file."""
    if not test_src or not ref_rel:
        return False
    if not re.search(r"\b(?:t4spec\.run_spec|run_spec|cemu\.run_pair|run_pair)\b", test_src):
        return False
    base = os.path.basename(ref_rel)
    if base in test_src:
        return True
    # Also accept normalized relative path match (e.g. without basename helper)
    norm = ref_rel.replace("\\", "/")
    return norm in test_src


def verify_t4_node(test_node, ref_rel=None, orig_addr=None, func_name=None,
                   cwd=None, require_audit=None):
    """Mechanically verify a single `difftest: tests/x.py::test_fn` node passes on its own.

    Checks:
      1) Valid `file::test_fn` node path and file exists.
      2) No forbidden skip/xfail, oracle-suppression, or oracle-tampering cheats (shared AST prefilter).
      3) If `ref_rel` is given, the test file references `t4spec`/`cemu` AND `ref_rel`.
      4) Running `pytest -q <file>::<test_fn>` exits 0 with >=1 passed and 0 skipped/xfailed/xpassed.
      5) Runtime oracle audit (`WC1_T4_AUDIT_LOG` + per-run `WC1_T4_AUDIT_NONCE`): when enabled
         (default whenever `orig_addr` is given and `war.exe` + `$WATCOM` are present), proves
         `cemu.run_pair` actually executed on exact realpath of `ref_rel` vs `orig_addr` (and
         `func_name`) for >=1 case with >0 original instructions, 0 diffs, full `run_spec`
         completion, non-empty observations, and neither stubbing nor patching `orig_addr`.

    Returns `(ok, reason)`.
    """
    root = cwd or path()
    node = str(test_node or "").strip()
    rvb = node if node.startswith("difftest:") else f"difftest: {node}"
    ast_errs = symbols.validate_ref_verified_by_entry(rvb, ref_rel=ref_rel, repo_root=root)
    if ast_errs:
        return False, ast_errs[0]
    parsed_nodes, perr = symbols.parse_ref_verified_by_nodes(rvb)
    if perr or not parsed_nodes:
        return False, perr or f"invalid test node: {test_node!r}"
    if require_audit is None:
        has_env = (
            os.path.exists(os.path.join(root, "original", "install", "war.exe"))
            and bool(os.environ.get("WATCOM"))
        )
        do_audit = bool(orig_addr is not None and has_env)
    else:
        do_audit = bool(require_audit)

    for file_rel, fn_part in parsed_nodes:
        full_test = os.path.join(root, file_rel)
        src = open(full_test, errors="replace").read()
        cheat = find_forbidden_test_cheat(src)
        if cheat:
            return False, f"cheat in {file_rel}: {cheat}"
        if ref_rel and not _test_file_exercises_ref(src, ref_rel):
            return False, f"{file_rel} does not invoke t4spec/cemu on {os.path.basename(ref_rel)}"

        audit_file = None
        nonce = None
        env = os.environ.copy()
        if do_audit:
            fd, audit_file = tempfile.mkstemp(prefix="wc1_t4_audit_", suffix=".jsonl")
            os.close(fd)
            nonce = secrets.token_hex(16)
            env["WC1_T4_AUDIT_LOG"] = audit_file
            env["WC1_T4_AUDIT_NONCE"] = nonce
        try:
            try:
                r = _run_capped(
                    [sys.executable, "-m", "pytest", "-q", f"{file_rel}::{fn_part}"],
                    cwd=root, env=env,
                )
            except subprocess.TimeoutExpired:
                return False, f"node {file_rel}::{fn_part} timed out after {PYTEST_TIMEOUT}s"
            out = (r.stdout + "\n" + r.stderr).strip()
            if not _pytest_output_passed(r.returncode, out, test_src=src):
                tail = out.splitlines()[-1] if out.splitlines() else f"rc={r.returncode}"
                return False, f"node {file_rel}::{fn_part} did not pass cleanly: {tail}"
            if do_audit:
                a_ok, a_info = t4spec.audit_t4_log(
                    audit_file, ref_rel=ref_rel, orig_addr=orig_addr,
                    func_name=func_name, repo_root=root, expected_nonce=nonce,
                )
                if not a_ok:
                    return False, f"runtime oracle audit failed for {file_rel}::{fn_part}: {a_info}"
        finally:
            if audit_file and os.path.exists(audit_file):
                try:
                    os.unlink(audit_file)
                except OSError:
                    pass
    return True, ""


def _run_pytest_file(test_path):
    try:
        r = _run_capped([sys.executable, "-m", "pytest", "-q", test_path], cwd=path())
    except subprocess.TimeoutExpired as ex:
        def _s(b):
            return b.decode(errors="replace") if isinstance(b, bytes) else (b or "")
        out = (_s(ex.stdout) + "\n" + _s(ex.stderr)).strip()
        return False, out + f"\n[batch_driver ERROR: pytest {test_path} timed out after {PYTEST_TIMEOUT}s]"
    out = (r.stdout + "\n" + r.stderr).strip()
    src = open(test_path, errors="replace").read() if os.path.exists(test_path) else ""
    ok = _pytest_output_passed(r.returncode, out, test_src=src)
    if r.returncode == 0 and not ok:
        cheat = find_forbidden_test_cheat(src)
        extra = f" ({cheat})" if cheat else ""
        out += f"\n[batch_driver ERROR: test file skipped or used xfail/skip cheat{extra} — NEVER skip/xfail failing tests, fix them!]"
    return ok, out


def _pick_nonclobber_test_rel(area, default_rel=None):
    """Return a tests/ relative path that will not overwrite an existing committed test file."""
    rel = default_rel or f"tests/test_{area}.py"
    if not os.path.exists(path(rel)):
        return rel
    base = re.sub(r"\.py$", "", rel)
    cand = f"{base}_batch.py"
    if not os.path.exists(path(cand)):
        return cand
    i = 2
    while os.path.exists(path(f"{base}_batch_{i}.py")):
        i += 1
    return f"{base}_batch_{i}.py"


T4_PATCH_SCHEMA = {
    "type": "object",
    "properties": {
        "diagnosis": {
            "type": "object",
            "properties": {
                "kind": {"type": "string", "enum": ["ref_bug", "harness_bug", "proto_bug"]},
                "reason": {
                    "type": "string",
                    "description": "One-line diagnosis citing exact disassembly address/instruction",
                },
            },
            "required": ["kind", "reason"],
        },
        "ref_patches": {
            "type": "array",
            "description": "Search-and-replace patches for this item's *_reference.c files ONLY when diagnosis.kind == 'ref_bug'",
            "items": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path of the *_reference.c file"},
                    "old": {"type": "string", "description": "Exact existing substring in the ref C file"},
                    "new": {"type": "string", "description": "Replacement substring"},
                },
                "required": ["path", "old", "new"],
            },
        },
        "test_patches": {
            "type": "array",
            "description": "Search-and-replace patches for the test file ONLY for harness fixes (stubs/watch/out_regs/init_emu/new cases); NEVER weaken/delete existing cases or add raises/skip/try-except",
            "items": {
                "type": "object",
                "properties": {
                    "old": {"type": "string", "description": "Exact existing substring in the test file"},
                    "new": {"type": "string", "description": "Replacement substring"},
                },
                "required": ["old", "new"],
            },
        },
    },
    "required": ["diagnosis", "ref_patches", "test_patches"],
}


def _apply_patches_text(text, patches):
    applied = 0
    for p in patches or []:
        old, new = p.get("old", ""), p.get("new", "")
        if old and old in text:
            text = text.replace(old, new, 1)
            applied += 1
    return text, applied


def _apply_patches(file_path, patches):
    text = open(file_path).read()
    new_text, applied = _apply_patches_text(text, patches)
    if applied:
        with open(file_path, "w") as fh:
            fh.write(new_text)
    return applied


def _render_subset_disasm(d, target_addrs):
    """Render compact disassembly & xrefs markdown for ONLY `target_addrs` from dossier `d`."""
    if not d or not target_addrs:
        return ""
    addr_set = {int(a) for a in target_addrs}
    sub_fns = [fn for fn in d.get("functions", []) if fn.get("addr_int") in addr_set]
    if not sub_fns:
        return ""
    sub_d = dict(d, functions=sub_fns)
    return dossier.render_markdown(sub_d)


def _apply_t4_patch_result(test_path, patch_res, allowed_ref_rels, *, cwd=None, compile_check_fn=None):
    """Safely apply a `T4_PATCH_SCHEMA` response (`diagnosis` + `ref_patches` + `test_patches`).

    - `ref_patches` are restricted strictly to `allowed_ref_rels` and compile-checked under
      both compilers (reverted automatically if compilation fails).
    - `test_patches` are checked in memory via `check_test_patch_not_weakening` and
      `find_forbidden_test_cheat` before writing (rejected if cheating or weakening).
    """
    root = cwd or path()
    allowed_norm = {str(r).replace("\\", "/") for r in (allowed_ref_rels or ())}
    diag = patch_res.get("diagnosis") if isinstance(patch_res, dict) else {}
    diag = diag if isinstance(diag, dict) else {}
    diag_kind = str(diag.get("kind") or "harness_bug")
    diag_reason = str(diag.get("reason") or "")

    rejected = []
    ref_applied = 0
    by_ref = {}
    for rp in (patch_res.get("ref_patches") or []):
        if diag_kind != "ref_bug":
            rejected.append(f"ref_patch rejected under diagnosis={diag_kind!r} (only allowed for 'ref_bug')")
            continue
        raw_p = str(rp.get("path") or "").replace("\\", "/")
        rrel = posixpath.normpath(raw_p)
        if posixpath.isabs(rrel) or rrel.startswith("..") or "/../" in rrel or rrel not in allowed_norm:
            rejected.append(f"ref_patch disallowed path: {raw_p!r}")
            continue
        by_ref.setdefault(rrel, []).append(rp)

    cc_fn = compile_check_fn or (lambda files: match.compile_check(files, jobs=1))
    for rrel, plist in by_ref.items():
        full_ref = os.path.join(root, rrel)
        if not os.path.isfile(full_ref):
            rejected.append(f"ref_patch missing file: {rrel}")
            continue
        old_c = open(full_ref, errors="replace").read()
        new_c, cnt = _apply_patches_text(old_c, plist)
        if not cnt or new_c == old_c:
            continue
        with open(full_ref, "w") as fh:
            fh.write(new_c)
        try:
            bad_cc = cc_fn([full_ref])
        except match.CompileTimeout as ex:
            with open(full_ref, "w") as fh:
                fh.write(old_c)
            raise ToolchainError(f"compile-check of {rrel} timed out: {ex}") from ex
        except Exception as ex:
            bad_cc = [(full_ref, str(ex))]
        if bad_cc:
            with open(full_ref, "w") as fh:
                fh.write(old_c)
            rejected.append(f"ref_patch reverted {rrel} (compile-check failed: {bad_cc[:1]})")
        else:
            ref_applied += cnt

    test_patches = patch_res.get("test_patches")
    if test_patches is None:
        test_patches = patch_res.get("patches") or []
    test_applied = 0
    if test_patches and os.path.isfile(test_path):
        old_test = open(test_path, errors="replace").read()
        cand_test, cnt = _apply_patches_text(old_test, test_patches)
        if cnt and cand_test != old_test:
            # NEVER allow mutating/deleting existing T4Case(...) inputs, even under harness_bug
            weak = check_test_patch_not_weakening(old_test, cand_test, allow_case_edits=False)
            if weak:
                rejected.append(f"test_patch rejected ({weak})")
            else:
                with open(test_path, "w") as fh:
                    fh.write(cand_test)
                test_applied = cnt

    return {
        "diag_kind": diag_kind,
        "diag_reason": diag_reason,
        "ref_applied": ref_applied,
        "test_applied": test_applied,
        "rejected": rejected,
    }


def run_t4_only(module_name, area=None, max_cost=0.80, max_calls=6, batch_size=8,
                provider="claude", codex_matrix=None, codex_bin=None,
                codex_home=None, codex_quota_guard=None):
    """Generate declarative wc1.t4spec difftests for existing `ref =` functions missing T4.

    Chunks large modules into batches of `batch_size` (default 8) and uses targeted
    search-and-replace patches on pytest retry so fixes cost ~500 output tokens
    instead of rewriting the whole file.
    """
    area = area or re.sub(r"[^a-z0-9_]+", "_", module_name.lower().replace(".c", "")).strip("_")
    global _live_area
    _live_area = area
    ledger = Ledger(path("build", "ledger", f"{area}_t4.jsonl"))
    p = analysis.run()
    funcs_db, datas_db, _ = symbols.load(strict=False)
    mods = progress.load_modules()
    rows = progress.classify([f["start"] for f in p.functions], funcs_db, mods)
    todo = [r for r in rows if r["module"] == module_name and r["scope"] == "in" and r["c"] == "ref"]
    if not todo:
        print(f"{module_name}: 0 unchecked ref functions.")
        return 0

    t4spec_src = open(path("tools", "wc1", "t4spec.py")).read()
    all_ok = True
    chunks = [todo[i:i + batch_size] for i in range(0, len(todo), batch_size)]

    for ci, chunk in enumerate(chunks):
        suffix = f"_{ci}" if len(chunks) > 1 or os.path.exists(path("tests", f"test_{area}_t4.py")) else ""
        test_rel = f"tests/test_{area}_t4{suffix}.py"
        while os.path.exists(path(test_rel)) and not ledger.has_stage(f"t4_c{ci}"):
            ci_tag = f"{ci}_{int(time.time()) % 1000}"
            test_rel = f"tests/test_{area}_t4_{ci_tag}.py"
        test_path = path(test_rel)
        if ledger.has_stage(f"t4_c{ci}"):
            continue

        addrs = [f"{r['addr']:#x}" for r in chunk]
        d = dossier.build_dossier(addrs, include_ghidra=False, include_exemplars=False)
        sys_file = _write_sys_prompt(f"{area}_t4", d)

        ref_sources = {}
        for r in chunk:
            e = funcs_db[r["addr"]]
            rf = e["ref"]
            if rf not in ref_sources and os.path.exists(path(rf)):
                ref_sources[rf] = open(path(rf), errors="replace").read()

        fn_list = "\n".join(
            f"- {funcs_db[r['addr']]['name']} ({r['addr']:#x}, link={funcs_db[r['addr']]['link_name']}, "
            f"proto={funcs_db[r['addr']].get('proto','')}, ref={funcs_db[r['addr']]['ref']})"
            for r in chunk
        )
        disasm_md = dossier.render_markdown(d)
        prompt = (
            f"wc1.t4spec API:\n```python\n{t4spec_src}\n```\n\n"
            f"Disassembly & xrefs:\n{disasm_md}\n\n"
            f"Reference C files:\n"
            + "\n".join(f"### {k}\n```c\n{v}\n```" for k, v in ref_sources.items())
            + f"\n\nWrite a compact pytest module `{test_rel}` using `wc1.t4spec` to T4-difftest "
            f"ALL {len(chunk)} reference-C functions below in `{module_name}` (do NOT omit any!):\n{fn_list}\n\n"
            f"Each function MUST have its own `def test_<snake_name>():` so TOML "
            f"`ref_verified_by = \"difftest: {test_rel}::test_<snake_name>\"` maps 1-to-1.\n"
            f"Use EXACTLY this `pytestmark`:\n"
            f"`pytestmark = pytest.mark.skipif(not (os.path.exists(path('original', 'install', 'war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')`\n"
            f"Pass the EXACT Watcom link name (`Foo_` for watcall, `_Foo` for cdecl) to `t4spec.run_spec`.\n"
            f"Stub external hardware/DOS/UI callees with `t4spec.T4Stub(addr, log_regs=(...))` — ALWAYS set "
            f"`log_regs` to ONLY the exact argument registers the callee takes (`()` for void(void), `('eax',)` for 1-arg, etc.), "
            f"and NEVER log stack-local pointer addresses (`esp+...`) whose frame offset differs between original and C.\n"
            f"Pass `out_regs=()` for void functions, and ALWAYS watch the modified memory/buffers or stub logs so outputs are actually compared! "
            f"(For heap buffers allocated inside `init_emu(emu)`, pass `watch = []` and populate `watch[:] = [...]` inside `init_emu`.)\n"
            f"NEVER use `pytest.raises`, `contextlib.suppress`, `try/except` around `run_spec`, or skip/xfail. "
            f"Pass `limit=64` to `e.cstr(a, 64)` on stack strings.\n"
            f"Note: `wc1.emu.Emu` has a flat 32-bit GDT (CS=0x08, DS/ES/FS/GS/SS=0x10) so far selectors use `0x10`, and `interrupt=True` works for `__interrupt` functions.\n"
            f"Keep tests concise (3-6 edge cases per function). Leave `doc_md` empty string.\n"
        )
        res, _c, _u = _call_llm(
            prompt, T4_AND_DOC_SCHEMA, sys_file,
            provider=provider, stage="stage4",
            claude_model="sonnet", claude_effort="low",
            codex_matrix=codex_matrix, codex_bin=codex_bin,
            codex_home=codex_home, codex_quota_guard=codex_quota_guard,
            ledger=ledger, label=f"{area}:t4gen_c{ci}",
            max_cost=max_cost, max_calls=max_calls,
        )
        with open(test_path, "w") as fh:
            fh.write(res["test_py"].rstrip() + "\n")

        allowed_refs = sorted(ref_sources.keys())
        ok, out_txt = _run_pytest_file(test_path)
        for fix_i in range(1, 3):
            if ok:
                break
            print(f"  [t4 pytest fail c{ci} #{fix_i}] sending diagnostic patch request...", flush=True)
            cur_refs_md = "\n".join(
                f"### {k}\n```c\n{open(path(k), errors='replace').read()}\n```"
                for k in allowed_refs if os.path.exists(path(k))
            )
            fix_prompt = (
                f"Disassembly & xrefs:\n{disasm_md}\n\n"
                f"Reference C files (editable via `ref_patches` when `diagnosis.kind == 'ref_bug'`):\n"
                f"{cur_refs_md}\n\n"
                f"Current `{test_rel}`:\n```python\n{open(test_path).read()}\n```\n\n"
                f"Pytest failure output (attempt {fix_i}/2):\n```\n{out_txt[-3000:]}\n```\n\n"
                f"RULES:\n"
                f"- First diagnose `ref_bug` vs `harness_bug` vs `proto_bug`, citing an exact disassembly address.\n"
                f"- If the reference C disagrees with the disassembly, fix it via `ref_patches` and leave `test_patches` empty.\n"
                f"- NEVER wrap `run_spec`/`run_pair` in `pytest.raises`, `contextlib.suppress`, or `try/except`.\n"
                f"- NEVER add `pytest.skip` / `pytest.mark.skipif` / `pytest.mark.xfail`.\n"
                f"- NEVER weaken, drop, or alter failing test inputs to avoid a bug in `*_reference.c`.\n"
                f"- If the failure requires a header prototype change (`proto_bug`), return empty patches.\n"
            )
            patch_res, _c, _u = _call_llm(
                fix_prompt, T4_PATCH_SCHEMA, sys_file,
                provider=provider, stage="stage4",
                claude_model="sonnet", claude_effort="low",
                codex_matrix=codex_matrix, codex_bin=codex_bin,
                codex_home=codex_home, codex_quota_guard=codex_quota_guard,
                ledger=ledger, label=f"{area}:t4fix_c{ci}_{fix_i}",
                max_cost=max_cost, max_calls=max_calls,
            )
            pres = _apply_t4_patch_result(test_path, patch_res, allowed_refs)
            print(f"  [t4fix #{fix_i}] diag={pres['diag_kind']}: {pres['diag_reason'][:100]} "
                  f"(ref={pres['ref_applied']} test={pres['test_applied']})", flush=True)
            for rej in pres["rejected"]:
                print(f"  [t4fix #{fix_i} rejected] {rej}", flush=True)
            if pres["diag_kind"] == "proto_bug" and not pres["ref_applied"] and not pres["test_applied"]:
                break
            ok, out_txt = _run_pytest_file(test_path)

        raw_rv_map = {int(it["addr"], 16): it["test_node"] for it in res.get("ref_verified_by", [])}
        verified_rv = {}
        for a, node in raw_rv_map.items():
            e = funcs_db.get(a)
            ref_rel = e.get("ref") if e else None
            fn_link = e.get("link_name") if e else None
            v_ok, v_reason = verify_t4_node(node, ref_rel=ref_rel, orig_addr=a, func_name=fn_link)
            if v_ok:
                verified_rv[a] = node
            else:
                print(f"  [T4 node unverified] {a:#x} {node}: {v_reason}", flush=True)
        if verified_rv:
            _update_existing_toml_entries({}, {}, ref_verified=verified_rv)
        if ok and len(verified_rv) == len(raw_rv_map):
            print(f"  [T4 PASS c{ci}] {test_rel} ({len(verified_rv)} functions updated in TOML)", flush=True)
            ledger.record(f"t4_c{ci}", count=len(verified_rv), test_path=test_rel)
        else:
            all_ok = False
            print(f"  [T4 FAIL c{ci}] {test_rel} ({len(verified_rv)}/{len(raw_rv_map)} verified):\n{out_txt[-1000:]}", flush=True)
            ledger.record(f"t4_fail_c{ci}", ok=False, verified=len(verified_rv),
                          pending_ref_verified_by={f"{a:#x}": n for a, n in raw_rv_map.items()},
                          test_path=test_rel)
    print("  Summary:", json.dumps(ledger.summary()))
    return 0 if all_ok else 1


EXIT_RATE_LIMIT = 75
EXIT_ADDR_MISMATCH = 76
EXIT_NOTHING_TO_DO = 77
EXIT_TOOLCHAIN = 78         # a compile timed out (stuck Wine/wcc386): wc1.overnight stops
EXIT_QUOTA_STOP = 79        # hard account/run quota ceiling hit (e.g. Codex 7d cap)
EXIT_EARLY_STOP = 80        # Stage 2 early-stop (uncompilable C during screening)


def _parse_addrs_arg(addrs):
    """Parse list or comma-separated hex address string into ordered unique ints."""
    if not addrs:
        return None
    raw = addrs.split(",") if isinstance(addrs, str) else list(addrs)
    out = []
    seen = set()
    for tok in raw:
        s = str(tok).strip()
        if not s:
            continue
        v = int(s, 16) if s.lower().startswith("0x") else int(s, 10)
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out or None


def _eligible_module_addrs(module_name, skip_semantic=False, cwd=None):
    """Return ordered list of eligible addresses for `module_name` in `c-only` or `full` mode,
    excluding data-in-code entries, locked codegen_promo.toml entries, untracked WIP TOMLs,
    already-matched unbuildable T3s, and (in full mode) existing cross-TOML entries."""
    root = cwd or path()
    p = analysis.run()
    funcs_db, datas_db, _ = symbols.load(strict=False)
    mods = progress.load_modules()
    rows = progress.classify([f["start"] for f in p.functions], funcs_db, mods)
    tracked = _git_tracked_files(cwd=root)

    eligible = []
    for r in rows:
        if r["module"] != module_name or r["scope"] != "in" or r["done"]:
            continue
        a = r["addr"]
        if a in datas_db:
            continue
        e = funcs_db.get(a)
        if e is not None:
            ef = e["_file"].replace("\\", "/")
            if ef in LOCKED_TOMLS:
                continue
            if tracked is not None and ef not in tracked:
                continue
            if r["c"] == "none" and str(e.get("verified_by", "")).startswith("match:"):
                continue
        if skip_semantic:
            if r["named"] and r["c"] == "none":
                eligible.append(a)
        else:
            if not r["named"] and r["c"] == "none" and e is None:
                eligible.append(a)
    return eligible


def _verify_and_wire_t4_nodes(raw_rv_map, t4_needed, funcs_db, toml_path, toml_rel,
                              module_name, area, skip_semantic, toml_preexisted,
                              sem_cache_path, t3_matched, t3_unbuildable, datas_db):
    """Verify each claimed T4 node individually and wire ONLY nodes that genuinely pass."""
    verified_rv = {}
    for a, node in sorted(raw_rv_map.items()):
        if a not in t4_needed:
            continue
        rel_ref = t4_needed[a][0]
        e = funcs_db.get(a)
        fn_link = e.get("link_name") if e else None
        v_ok, v_reason = verify_t4_node(node, ref_rel=rel_ref, orig_addr=a, func_name=fn_link)
        if v_ok:
            verified_rv[a] = node
        else:
            print(f"  [T4 node unverified] {a:#x} {node}: {v_reason}", flush=True)
    if verified_rv:
        if not skip_semantic and not toml_preexisted and os.path.exists(sem_cache_path):
            _rewrite_toml_with_results(toml_path, json.load(open(sem_cache_path)),
                                       module_name, area, funcs_db, datas_db,
                                       t3_matched, t4_needed, ref_verified=verified_rv,
                                       t3_unbuildable=t3_unbuildable)
            other_t3 = {a: v for a, v in t3_matched.items() if a in funcs_db and funcs_db[a]["_file"] != toml_rel}
            other_t4 = {a: v for a, v in t4_needed.items() if a in funcs_db and funcs_db[a]["_file"] != toml_rel}
            other_rv = {a: v for a, v in verified_rv.items() if a in funcs_db and funcs_db[a]["_file"] != toml_rel}
            other_ub = {a: v for a, v in t3_unbuildable.items() if a in funcs_db and funcs_db[a]["_file"] != toml_rel}
            if other_t3 or other_t4 or other_rv or other_ub:
                _update_existing_toml_entries(other_t3, other_t4, ref_verified=other_rv,
                                              t3_unbuildable=other_ub, created_toml=toml_rel)
        else:
            _update_existing_toml_entries(t3_matched, t4_needed, ref_verified=verified_rv,
                                          t3_unbuildable=t3_unbuildable, created_toml=toml_rel)
    return verified_rv


def run_full_module(module_name, area=None, max_cost=1.20, max_calls=10,
                    max_t3_retries=2, permute_trials=50, dry_run=False,
                    skip_semantic=False, header=None, limit=None,
                    src_subdir=None, addrs=None, provider="claude",
                    codex_matrix=None, codex_bin=None, codex_home=None,
                    codex_quota_guard=None, early_stop_stage2=False):
    area = area or re.sub(r"[^a-z0-9_]+", "_", module_name.lower().replace(".c", "")).strip("_")
    global _live_area
    _live_area = area
    ledger = Ledger(path("build", "ledger", f"{area}.jsonl"))
    req_addrs = _parse_addrs_arg(addrs)
    frozen_rec = ledger.last_stage("target_addrs")
    frozen_addrs = frozen_rec.get("addrs") if isinstance(frozen_rec, dict) else None
    if frozen_addrs:
        frozen_ints = [int(x, 16) for x in frozen_addrs]
        if req_addrs is not None and set(req_addrs) != set(frozen_ints):
            print(f"ERROR: --addrs {[hex(x) for x in req_addrs]} does not match "
                  f"resumed ledger target_addrs {frozen_addrs}", file=sys.stderr, flush=True)
            return EXIT_ADDR_MISMATCH
        d = dossier.build_dossier(frozen_addrs, only_undone=False,
                                  only_missing_c=False,
                                  include_ghidra=True, include_exemplars=True)
    elif req_addrs is not None:
        elig = set(_eligible_module_addrs(module_name, skip_semantic=skip_semantic))
        chosen = [a for a in req_addrs if a in elig]
        if not chosen or len(chosen) != len(req_addrs):
            dropped = [hex(a) for a in req_addrs if a not in elig]
            print(f"{module_name}: --addrs eligibility mismatch (ineligible={dropped}, "
                  f"eligible={len(chosen)}/{len(req_addrs)}), exiting without fallback.",
                  file=sys.stderr, flush=True)
            return EXIT_NOTHING_TO_DO
        d = dossier.build_dossier([f"{a:#x}" for a in chosen], only_undone=False,
                                  only_missing_c=False,
                                  include_ghidra=True, include_exemplars=True)
    else:
        elig = _eligible_module_addrs(module_name, skip_semantic=skip_semantic)
        if limit and len(elig) > limit:
            elig = elig[:limit]
        if not elig:
            print(f"{module_name}: 0 eligible undone functions, nothing to do.")
            return 0
        d = dossier.build_dossier([f"{a:#x}" for a in elig], only_undone=False,
                                  only_missing_c=False,
                                  include_ghidra=True, include_exemplars=True)
    if d["function_count"] == 0:
        print(f"{module_name}: 0 undone functions, nothing to do.")
        return 0
    if not dry_run and not frozen_addrs:
        ledger.record("target_addrs", addrs=[f"{fn['addr_int']:#x}" for fn in d["functions"]])

    dossier_md_path = path("build", "driver", f"{area}_dossier.md")
    os.makedirs(os.path.dirname(dossier_md_path), exist_ok=True)
    md_text = dossier.render_markdown(d)
    with open(dossier_md_path, "w") as fh:
        fh.write(md_text)
    sys_file = _write_sys_prompt(area, d)
    print(f"== batch_driver: {module_name} (area={area}, {d['function_count']} fn, "
          f"{d['total_insns']} insns, style={d['dominant_style']}, flags={d['recommended_cflags']}) ==",
          flush=True)

    if dry_run:
        print(f"DRY RUN: dossier={dossier_md_path} ({len(md_text)} chars), sys={sys_file}")
        return 0

    toml_rel = f"analysis/symbols/{area}.toml"
    toml_path = path("analysis", "symbols", f"{area}.toml")
    hdr_rel = header or f"src/include/{area}.h"
    hdr_path = path(hdr_rel)
    hdr_inc = os.path.basename(hdr_rel)
    src_dir = path("src", src_subdir or area)
    os.makedirs(src_dir, exist_ok=True)
    os.makedirs(os.path.dirname(hdr_path), exist_ok=True)
    if not os.path.exists(hdr_path) and skip_semantic:
        guard = re.sub(r"[^A-Z0-9]+", "_", hdr_inc.upper()).strip("_")
        with open(hdr_path, "w") as fh:
            fh.write(f"#ifndef {guard}\n#define {guard}\n\n#endif\n")

    funcs_db, datas_db, _ = symbols.load(strict=False)
    mod_by_addr = {fn["addr_int"]: fn for fn in d["functions"]}
    toml_preexisted = os.path.exists(toml_path) and not ledger.has_stage("semantic_done")
    if toml_preexisted:
        ledger.record("toml_preexisted", path=toml_path)
    else:
        toml_preexisted = ledger.has_stage("toml_preexisted")

    # ---- Stage 1: Semantic pass (1 call) ------------------------------------
    sem_cache_path = path("build", "driver", f"{area}_semantic.json")
    if not skip_semantic:
        if ledger.has_stage("semantic_done") and os.path.exists(sem_cache_path):
            sem = json.load(open(sem_cache_path))
            if _disambiguate_semantic_names(sem, funcs_db, datas_db, allow_hdr_patch=False):
                with open(sem_cache_path, "w") as fh:
                    json.dump(sem, fh, indent=2)
        else:
            existing_names = sorted({
                f"{e['name']} ({e['addr']:#x}, {e.get('proto','')})"
                for fn in d["functions"]
                for c in fn["callees"] + fn["callers"]
                if (e := funcs_db.get(int(c["addr"], 16))) is not None
            })[:60]
            unnamed_data = sorted({
                (dr["addr"], dr.get("ascii", ""), dr.get("hex", ""))
                for fn in d["functions"]
                for dr in fn["data_refs"]
                if dr["name"].startswith("dat_")
            })
            unnamed_data_str = "\n".join(
                f"  - {a}" + (f" ascii={s!r}" if s else (f" hex={h}" if h else ""))
                for a, s, h in unnamed_data
            )
            prompt = (
                f"Perform the semantic analysis pass for module `{module_name}` (area `{area}`).\n"
                f"Emit semantic names, exact watcall prototypes, honest confidence, concrete disassembly-based "
                f"evidence (NEVER cite Ghidra), and a clean C89 header `src/include/{area}.h`.\n"
                f"CONFIDENCE RULES (docs/METHODOLOGY.md): use `high` when multiple independent lines of "
                f"evidence agree (e.g. strings + callers + body), `medium` when one strong line of evidence "
                f"shows what the body unambiguously implements (e.g. clear register/field/callee behaviour), "
                f"and `low` ONLY when the function's role is genuinely uncertain from the disassembly. "
                f"Never inflate confidence without concrete disassembly evidence, and do not under-rate a "
                f"clear disassembly body as `low`.\n"
                f"CRITICAL — COMPLETE DATA COVERAGE: Emit a `data_symbols` entry for EVERY unnamed data "
                f"address below (unless it is literally an interior offset like `arr[1]` of another entry "
                f"you define in `data_symbols`, in which case document that in `header_h`!). Leaving any "
                f"referenced global unnamed causes `wc1.match` and `wc1.cemu` relocation failures!\n"
                f"CRITICAL — VALID IDENTIFIERS: Every function and data `name` MUST be a valid C identifier "
                f"matching `[A-Za-z_][A-Za-z0-9_]*` — NEVER put array brackets like `[1]` or offsets like `+4` in `name` "
                f"(put array dimensions in `type`, e.g. `short[2]`).\n"
                f"CRITICAL — SELF-CONTAINED HEADER: `src/include/{area}.h` MUST compile cleanly on its own under C89 "
                f"when included with ONLY `#include \"war.h\"` (notice `war.h` does NOT define `Unit`, `Rect`, `Dialog`, etc. — "
                f"if any prototype uses `Unit *` or another non-`war.h` struct typedef, add `typedef struct Unit Unit;` or `void *` in `header_h`!). "
                f"Also declare `extern` for EVERY global data symbol referenced by the module's disassembly (including already-named globals not in `war.h`), "
                f"each on ONE single line.\n"
                f"DO NOT duplicate any function or data address already present in another symbol file.\n\n"
                f"Unnamed data addresses referenced by this module ({len(unnamed_data)}):\n"
                f"{unnamed_data_str}\n\n"
                f"Known neighbour prototypes:\n" + "\n".join(existing_names) + "\n\n"
                f"Module dossier:\n{md_text}"
            )
            sem, _c, _u = _call_llm(
                prompt, SEMANTIC_SCHEMA, sys_file,
                provider=provider, stage="stage1",
                claude_model="sonnet", claude_effort="medium",
                codex_matrix=codex_matrix, codex_bin=codex_bin,
                codex_home=codex_home, codex_quota_guard=codex_quota_guard,
                ledger=ledger, label=f"{area}:semantic",
                max_cost=max_cost, max_calls=max_calls,
            )
            hdr_existed = os.path.exists(hdr_path)
            _disambiguate_semantic_names(sem, funcs_db, datas_db, allow_hdr_patch=not hdr_existed)
            with open(sem_cache_path, "w") as fh:
                json.dump(sem, fh, indent=2)
            if not hdr_existed:
                with open(hdr_path, "w") as fh:
                    fh.write(sem["header_h"].rstrip() + "\n")

            if toml_preexisted and _is_protected_toml(toml_rel):
                raise DriverError(f"refusing to write protected/untracked pre-existing TOML {toml_rel}")

            # Write initial TOML (never overwrite pre-existing committed TOML; append new entries only)
            entries_text = [f"# {module_name} ({area}) - generated by wc1.batch_driver\n"]
            for fn in sem["functions"]:
                a = int(fn["addr"], 16)
                if a in funcs_db:
                    if toml_preexisted or funcs_db[a]["_file"] != toml_rel:
                        continue
                entries_text.append(render_toml_entry("func", {
                    "addr": a,
                    "name": fn["name"],
                    "conv": fn.get("conv", "watcall"),
                    "proto": fn["proto"],
                    "module": module_name,
                    "confidence": fn["confidence"],
                    "evidence": fn["evidence"],
                }))
            for dt in sem.get("data_symbols", []):
                a = int(dt["addr"], 16)
                if a in datas_db:
                    if toml_preexisted or datas_db[a]["_file"] != toml_rel:
                        continue
                entries_text.append(render_toml_entry("data", {
                    "addr": a,
                    "name": dt["name"],
                    "type": dt["type"],
                    "confidence": dt["confidence"],
                    "evidence": dt["evidence"],
                }))
            if toml_preexisted:
                if len(entries_text) > 1:
                    with open(toml_path, "a") as fh:
                        fh.write("\n" + "\n".join(entries_text))
            else:
                with open(toml_path, "w") as fh:
                    fh.write("\n".join(entries_text))
            _, _, errs = symbols.load(strict=False)
            if errs:
                raise DriverError(f"symbols errors after semantic pass: {errs[:5]}")
            ledger.record("semantic_done", funcs=len(sem["functions"]), data=len(sem.get("data_symbols", [])))

    # Reload DB & dossier with fresh semantic names, keeping the frozen target_addrs invariant!
    funcs_db, datas_db, _ = symbols.load(strict=False)
    by_link = {e["link_name"]: e for t in (funcs_db, datas_db) for e in t.values()}
    target_addrs = [f"{fn['addr_int']:#x}" for fn in d["functions"]]
    d2 = dossier.build_dossier(target_addrs, only_undone=False, only_missing_c=False,
                               include_ghidra=True, include_exemplars=False)
    hdr_text = open(hdr_path).read() if os.path.exists(hdr_path) else ""

    # ---- Stage 2: Batched C drafting (replay keyed by function address) -----
    batches = _batch_functions(d2["functions"], max_insns=480, max_count=10)
    generated_files = {}  # addr -> path
    recorded_drafts = ledger.drafted_files()
    for a_int, rel_or_abs in recorded_drafts.items():
        cand = rel_or_abs if os.path.isabs(rel_or_abs) else path(rel_or_abs)
        if os.path.isfile(cand):
            generated_files[a_int] = cand

    for b_idx, batch in enumerate(batches):
        b_key = f"draft_b{b_idx}"
        if not recorded_drafts and ledger.has_stage(b_key):
            # Legacy ledger fallback (recorded before files_map existed)
            for fn in batch:
                e = funcs_db.get(fn["addr_int"])
                if e:
                    for f in os.listdir(src_dir):
                        if f.endswith(".c") and e["name"] in open(os.path.join(src_dir, f), errors="replace").read():
                            generated_files[fn["addr_int"]] = os.path.join(src_dir, f)
                            break
            continue
        todo_batch = [fn for fn in batch if fn["addr_int"] not in generated_files]
        if not todo_batch:
            continue
        sub_d = dict(d2, functions=todo_batch, function_count=len(todo_batch),
                     total_insns=sum(x["ninsns"] for x in todo_batch))
        sub_md = dossier.render_markdown(sub_d)
        db_names_for_batch = "\n".join(
            f"  - {fn['addr']}: MUST define C function `{funcs_db[fn['addr_int']]['name']}` "
            f"(link `{funcs_db[fn['addr_int']]['link_name']}`, proto `{funcs_db[fn['addr_int']].get('proto','')}`)"
            for fn in todo_batch if fn["addr_int"] in funcs_db
        )
        prompt = (
            f"Write matching Watcom 10.0a C89 source files (one function per file) for these "
            f"{len(todo_batch)} functions in `{module_name}` (area `{area}`).\n"
            f"Each file must start with `/* codegen-compiler: 10.0a */`, `#include \"{hdr_inc}\"`, "
            f"and compile cleanly under both Watcom 10.0a and OW2.\n"
            f"CRITICAL: Use ONLY exact DB symbol names (no `#pragma aux`, no `#define dat_...` offset hacks). "
            f"Keep every `extern` prototype on ONE single line (multi-line externs break `test_progress.py`).\n"
            f"Exact required C function names for this batch:\n{db_names_for_batch}\n\n"
            f"Match flags: `{d2['recommended_cflags']}` (try `-oa` too if aliasing helps).\n\n"
            f"Current `{hdr_rel}`:\n```c\n{hdr_text}\n```\n\n"
            f"{sub_md}"
        )
        res, _c, _u = _call_llm(
            prompt, BATCH_C_SCHEMA, sys_file,
            provider=provider, stage="stage2",
            claude_model="sonnet", claude_effort="low",
            codex_matrix=codex_matrix, codex_bin=codex_bin,
            codex_home=codex_home, codex_quota_guard=codex_quota_guard,
            ledger=ledger, label=f"{area}:{b_key}",
            max_cost=max_cost, max_calls=max_calls,
        )
        if res.get("header_additions") and os.path.exists(hdr_path):
            ht = open(hdr_path).read()
            if "#endif" in ht:
                ht = ht.replace("#endif", res["header_additions"].rstrip() + "\n\n#endif", 1)
                with open(hdr_path, "w") as fh:
                    fh.write(ht)
                hdr_text = ht
        batch_files_map = {}
        for item in res["files"]:
            a = int(item["addr"], 16)
            fname = os.path.basename(item["filename"])
            if not fname.endswith(".c"):
                fname += ".c"
            fpath = os.path.join(src_dir, fname)
            with open(fpath, "w") as fh:
                fh.write(item["code"].rstrip() + "\n")
            generated_files[a] = fpath
            batch_files_map[f"{a:#x}"] = os.path.relpath(fpath, path())
        ledger.record(b_key, files=len(res["files"]), files_map=batch_files_map)

    if early_stop_stage2:
        if not generated_files:
            msg = "[EARLY STOP Stage 2] Stage 2 drafted 0 C files"
            print(f"  {msg}", flush=True)
            live.append_event(area, "error", msg)
            ledger.record("stage2_early_stop", ok=False, failed=0, total=0)
            return EXIT_EARLY_STOP
        draft_paths = sorted({p_c for p_c in generated_files.values() if os.path.isfile(p_c)})
        try:
            bad_s2 = match.compile_check(draft_paths, jobs=4)
        except match.CompileTimeout as ex:
            raise ToolchainError(f"stage2 compile-check timed out: {ex}") from ex
        if bad_s2:
            msg = f"[EARLY STOP Stage 2] {len(bad_s2)}/{len(draft_paths)} drafted file(s) failed compile-check: {bad_s2[:2]}"
            print(f"  {msg}", flush=True)
            live.append_event(area, "error", msg)
            ledger.record("stage2_early_stop", ok=False, failed=len(bad_s2), total=len(draft_paths))
            return EXIT_EARLY_STOP

    # ---- Stage 3: Local match + permuter + batched hard-capped repair loop --
    live.update_worker_meta(area, phase="PERMUTING", stage="stage3:permute")
    live.append_event(area, "perm", f"Stage 3: permuting {len(d2['functions'])} functions locally")
    p = analysis.run()
    t3_matched = {}      # addr -> rel src path (buildable T3)
    t3_unbuildable = {}  # addr -> (rel path, reason) (matches locally, cannot be built from C yet)
    t4_needed = {}       # addr -> (rel ref path, t3_blocker)
    mismatches = []      # list of (fn_dict, e_dict, fpath)
    live_funcs_db = {k: dict(v) for k, v in funcs_db.items()}

    def _classify_t3_match(a, e, fpath, via_label):
        rel = os.path.relpath(fpath, path())
        fn_label = f"{e['name']}@{a:#x}"
        try:
            tmp_obj = match.unique_obj(fpath, "driver", "place")
            os.makedirs(os.path.dirname(tmp_obj), exist_ok=True)
            match.compile_c(fpath, None, tmp_obj, cc=match.file_cc(fpath))
            build_ok, build_reason = build.check_t3_buildable(p, live_funcs_db, rel, tmp_obj, [e])
        except match.CompileTimeout as ex:
            raise ToolchainError(f"{fn_label}: {ex}") from ex
        except (SystemExit, Exception) as ex:
            build_ok, build_reason = False, f"buildability check failed: {ex}"
        if build_ok:
            t3_matched[a] = rel
            live_funcs_db[a] = dict(live_funcs_db[a], src=rel)
            msg = f"[T3 MATCH {via_label}] {fn_label} -> {rel}"
            print(f"  {msg}", flush=True)
            live.append_event(area, "match", msg)
            ledger.record("fn_t3", addr=f"{a:#x}", name=e["name"], via=via_label)
        else:
            # IntroOpPlaySound precedent: keep C + verified_by="match: ...", NO src/ref
            t3_unbuildable[a] = (rel, build_reason)
            msg = f"[T3 UNBUILDABLE {via_label}] {fn_label} -> {rel} ({build_reason})"
            print(f"  {msg}", flush=True)
            live.append_event(area, "match", msg)
            ledger.record("fn_t3_unbuildable", addr=f"{a:#x}", name=e["name"], via=via_label, reason=build_reason)

    for fn in d2["functions"]:
        a = fn["addr_int"]
        fpath = generated_files.get(a)
        if not fpath or not os.path.exists(fpath):
            continue
        e = funcs_db.get(a)
        if not e:
            continue
        fn_label = f"{e['name']}@{a:#x}"
        pr = _permute(area, f"permute:{e['name']}", fpath, max_trials=permute_trials,
                      orig_addr=a, rounds=2)
        if pr["matched"]:
            _classify_t3_match(a, e, fpath, f"local ({pr['label']}, {pr['trials']} trials)")
        else:
            live.append_event(area, "perm", f"miss {fn_label} ({pr['trials']} trials): {pr.get('first_diff') or 'mismatch'}")
            mismatches.append((fn, e, fpath))

    # Reserve 2 calls + $0.25 (Claude) for Stage 4 (T4 tests + doc)
    repair_max_calls = max(ledger.total_calls(provider=provider), max_calls - 2)
    repair_max_cost = None if provider == "codex" else max(ledger.total_cost(), max_cost - 0.25)

    def _collect_diff(fn, e, fpath):
        a = fn["addr_int"]
        try:
            out_obj = match.unique_obj(fpath, "driver", "diff")
            os.makedirs(os.path.dirname(out_obj), exist_ok=True)
            mod = match.compile_c(fpath, None, out_obj, cc=match.file_cc(fpath))
            dd = match.diff_function(p, mod, by_link, name=e["link_name"], orig_addr=a)
            dt = (f"status={dd['status']} counts={dd['counts']}\n"
                  f"first_diff: {dd['first_diff']}\n" + "\n".join(dd["lines"][:35]))
            return dd, dt
        except match.CompileTimeout as ex:
            raise ToolchainError(f"{e['name']}@{a:#x}: {ex}") from ex
        except SystemExit as ex:
            return {"counts": {"op": 1}, "first_diff": str(ex)}, f"COMPILE ERROR: {ex}"

    pending = list(mismatches)
    for attempt in range(1, max_t3_retries + 1):
        if not pending:
            break
        next_pending = []
        # Pack up to 5 mismatching functions per batched repair call!
        for chunk_i in range(0, len(pending), 5):
            chunk = pending[chunk_i:chunk_i + 5]
            blocks = []
            diff_cache = {}
            for fn, e, fpath in chunk:
                a = fn["addr_int"]
                dd, dt = _collect_diff(fn, e, fpath)
                diff_cache[a] = dd
                blocks.append(
                    f"### {e['name']} ({a:#x}, file={os.path.relpath(fpath, path())})\n"
                    f"Current C:\n```c\n{open(fpath).read()}\n```\n"
                    f"Diff:\n```\n{dt}\n```\n"
                    f"Original asm:\n```asm\n{fn['asm']}\n```\n"
                )
            rep_prompt = (
                f"Fix Watcom 10.0a T3 mismatches for these {len(chunk)} functions in `{module_name}` "
                f"(repair round {attempt}/{max_t3_retries}).\n"
                f"For each function: if fixable via C89 Watcom 10.0a idioms, emit the complete updated C "
                f"with `give_up_blocker=\"\"`. If clearly an unavoidable regalloc/codegen blocker, set "
                f"`give_up_blocker` to '<regalloc|od-frame|codegen>: <exact first_diff evidence>' and return "
                f"clean, behaviorally identical reference C.\n"
                f"Header `{hdr_rel}`:\n```c\n{hdr_text}\n```\n\n"
                + "\n".join(blocks)
            )
            try:
                rep, _c, _u = _call_llm(
                    rep_prompt, REPAIR_C_SCHEMA, sys_file,
                    provider=provider, stage="stage3",
                    claude_model="sonnet", claude_effort="medium",
                    codex_matrix=codex_matrix, codex_bin=codex_bin,
                    codex_home=codex_home, codex_quota_guard=codex_quota_guard,
                    ledger=ledger, label=f"{area}:repair_r{attempt}_c{chunk_i//5}",
                    max_cost=repair_max_cost, max_calls=repair_max_calls,
                )
            except BudgetExceededError:
                print(f"  [repair budget cap] freezing remaining {len(chunk)} functions as T4 ref", flush=True)
                for fn, e, fpath in chunk:
                    a = fn["addr_int"]
                    dd = diff_cache[a]
                    cat = _blocker_category(dd, fn["style"])
                    t4_needed[a] = (fpath, f"{cat}: {dd.get('first_diff') or 'budget cap'}")
                continue

            fix_by_addr = {int(fx["addr"], 16): fx for fx in rep.get("fixes", [])}
            for fn, e, fpath in chunk:
                a = fn["addr_int"]
                fx = fix_by_addr.get(a)
                dd = diff_cache[a]
                if fx and fx.get("code"):
                    with open(fpath, "w") as fh:
                        fh.write(fx["code"].rstrip() + "\n")
                if fx and fx.get("give_up_blocker"):
                    t4_needed[a] = (fpath, fx["give_up_blocker"])
                    continue
                pr2 = _permute(area, f"permute_r{attempt}:{e['name']}", fpath,
                               max_trials=permute_trials, orig_addr=a, rounds=1)
                if pr2["matched"]:
                    _classify_t3_match(a, e, fpath, f"r{attempt}+{pr2['label']}")
                elif attempt == max_t3_retries:
                    cat = _blocker_category(dd, fn["style"])
                    t4_needed[a] = (fpath, f"{cat}: {pr2['first_diff'] or dd.get('first_diff') or 'mismatch after repair'}")
                else:
                    next_pending.append((fn, e, fpath))
        pending = next_pending

    # Finalize reference filenames & blockers
    final_t4 = {}
    for a, (fpath, blocker) in t4_needed.items():
        stem = os.path.splitext(fpath)[0]
        ref_path = stem + "_reference.c" if not stem.endswith("_reference") else fpath
        if os.path.exists(fpath) and ref_path != fpath:
            os.replace(fpath, ref_path)
        rel_ref = os.path.relpath(ref_path, path())
        if not re.match(r"^(od-frame|regalloc|codegen): \S", str(blocker or "")):
            blocker = f"codegen: {blocker or 'mismatch under Watcom 10.0a'}"
        final_t4[a] = (rel_ref, blocker)
        e = funcs_db.get(a)
        print(f"  [T4 REF] {(e['name'] if e else hex(a))} -> {rel_ref} ({blocker[:70]})", flush=True)
        ledger.record("fn_ref", addr=f"{a:#x}", name=(e["name"] if e else hex(a)), ref=rel_ref, blocker=blocker)
    t4_needed = final_t4

    # Check OW2 + 10.0a compile-check across all area files
    area_srcs = sorted(os.path.join(src_dir, f) for f in os.listdir(src_dir) if f.endswith(".c"))
    if area_srcs:
        try:
            bad_cc = match.compile_check(area_srcs, jobs=4)
        except match.CompileTimeout as ex:
            raise ToolchainError(f"compile-check of {src_dir} timed out: {ex}") from ex
        if bad_cc:
            print(f"  [warn] compile-check failures: {bad_cc}", flush=True)

    # Update TOML with T3/ref/unbuildable results right away (before Stage 4 tests)
    if not skip_semantic and not toml_preexisted and os.path.exists(sem_cache_path):
        sem_loaded = json.load(open(sem_cache_path))
        _rewrite_toml_with_results(toml_path, sem_loaded, module_name, area,
                                   funcs_db, datas_db, t3_matched, t4_needed,
                                   t3_unbuildable=t3_unbuildable)
        # Also update any functions whose entry lives in a pre-existing other TOML file
        other_t3 = {a: v for a, v in t3_matched.items() if a in funcs_db and funcs_db[a]["_file"] != toml_rel}
        other_t4 = {a: v for a, v in t4_needed.items() if a in funcs_db and funcs_db[a]["_file"] != toml_rel}
        other_ub = {a: v for a, v in t3_unbuildable.items() if a in funcs_db and funcs_db[a]["_file"] != toml_rel}
        if other_t3 or other_t4 or other_ub:
            _update_existing_toml_entries(other_t3, other_t4, t3_unbuildable=other_ub,
                                          created_toml=toml_rel)
    else:
        _update_existing_toml_entries(t3_matched, t4_needed, t3_unbuildable=t3_unbuildable,
                                      created_toml=toml_rel)

    # ---- Stage 4: Declarative T4 tests + subsystem doc ----------------------
    doc_path = path("docs", "subsystems", f"{area}.md")
    doc_exists = os.path.exists(doc_path)
    test_rel = _pick_nonclobber_test_rel(area)
    test_path = path(test_rel)
    src_rel_dir = os.path.relpath(src_dir, path())
    if not ledger.has_stage("stage4_done"):
        t4spec_src = open(path("tools", "wc1", "t4spec.py")).read()
        t3_list = sorted(
            [os.path.basename(v) for v in t3_matched.values()]
            + [os.path.basename(v[0]) for v in t3_unbuildable.values()]
        )
        ref_list = sorted(os.path.basename(v[0]) for v in t4_needed.values())
        ref_details = []
        for a, (rel_ref, blocker) in sorted(t4_needed.items()):
            e = funcs_db.get(a)
            if not e:
                continue
            code = open(path(rel_ref), errors="replace").read()
            ref_details.append(
                f"### {e['name']} ({a:#x}, link={e['link_name']}, proto={e.get('proto','')})\n"
                f"ref={rel_ref}, blocker={blocker}\n```c\n{code}\n```\n"
            )
        doc_instr = (
            f"2. `docs/subsystems/{area}.md` ALREADY EXISTS — leave `doc_md` empty string.\n\n"
            if doc_exists else
            f"2. In `docs/subsystems/{area}.md`: concise evidence-backed subsystem doc (function table, data layouts, T3/T4 notes; NEVER cite Ghidra).\n\n"
        )
        ref_disasm_md = _render_subset_disasm(d, sorted(t4_needed.keys()))
        s4_prompt = (
            f"wc1.t4spec API:\n```python\n{t4spec_src}\n```\n\n"
            + (f"Disassembly & xrefs for reference functions:\n{ref_disasm_md}\n\n" if ref_disasm_md else "")
            + f"Header `{hdr_rel}`:\n```c\n{hdr_text}\n```\n\n"
            + ("Reference functions needing T4 difftests:\n" + "\n".join(ref_details) if ref_details else "No reference functions; all matched T3!\n")
            + f"\nGenerate `{test_rel}` (using `wc1.t4spec`)"
            + ("" if doc_exists else f" AND `docs/subsystems/{area}.md`")
            + f" for module `{module_name}` (area `{area}`).\n"
            f"1. In `{test_rel}`:\n"
            f"   - Include EXACTLY: `pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')`.\n"
            f"   - Test T3 files still match via `t4spec.assert_t3_matches(path('{src_rel_dir}'), {t3_list!r})` (if non-empty).\n"
            f"   - Near-miss guard for reference files via `t4spec.assert_ref_mismatch(path('{src_rel_dir}'), {ref_list!r})` (if non-empty).\n"
            f"   - For EVERY reference function above, write a `def test_<snake_name>():` using `t4spec.run_spec(...)` on its exact `*_reference.c` file with exact Watcom link name (`Foo_` / `_Foo`), "
            f"`out_regs=()` for void functions, exact callee arity in `T4Stub(addr, log_regs=(...))`, never logging stack pointers, and `limit=64` on `e.cstr(a, 64)`.\n"
            f"   - ALWAYS observe outputs: pass non-empty `watch` (for heap buffers allocated in `init_emu(emu)`, pass `watch = []` and assign `watch[:] = [...]` inside `init_emu`), `out_regs`, or `stubs`! NEVER stub or overwrite `orig_addr`.\n"
            f"   - CRITICAL: NEVER call `Emu().alloc(...)` outside `init_emu` (buffers MUST be allocated inside `init_emu(emu)` so they never overlap the C module at `0x800000`). "
            f"NEVER use `pytest.raises`, `contextlib.suppress`, `try/except` around `run_spec`, `@pytest.mark.xfail`, `@pytest.mark.skip`, `@pytest.mark.skipif`, or inline `pytest.skip(...)`.\n"
            f"   - Populate `ref_verified_by` with `difftest: {test_rel}::test_<snake_name>` for each.\n"
            f"{doc_instr}"
        )
        try:
            s4, _c, _u = _call_llm(
                s4_prompt, T4_AND_DOC_SCHEMA, sys_file,
                provider=provider, stage="stage4",
                claude_model="sonnet", claude_effort="low",
                codex_matrix=codex_matrix, codex_bin=codex_bin,
                codex_home=codex_home, codex_quota_guard=codex_quota_guard,
                ledger=ledger, label=f"{area}:stage4_t4_doc",
                max_cost=max_cost, max_calls=max_calls,
            )
            with open(test_path, "w") as fh:
                fh.write(s4["test_py"].rstrip() + "\n")
            if s4.get("doc_md") and not doc_exists:
                with open(doc_path, "w") as fh:
                    fh.write(s4["doc_md"].rstrip() + "\n")

            raw_rv_map = {int(it["addr"], 16): it["test_node"] for it in s4.get("ref_verified_by", [])}
            pending_rv_hex = {f"{a:#x}": node for a, node in raw_rv_map.items()}
            ledger.record("stage4_pending", test_path=test_rel,
                          pending_ref_verified_by=pending_rv_hex)

            allowed_refs = sorted({v[0] for v in t4_needed.values()})
            live.update_worker_meta(area, phase="VERIFYING", stage=f"pytest:{test_rel}")
            ok, out_txt = _run_pytest_file(test_path)
            for fix_i in range(1, 3):
                if ok:
                    break
                live.append_event(area, "error", f"Stage 4 pytest fail #{fix_i} on {test_rel}")
                print(f"  [stage4 pytest fail #{fix_i}] sending diagnostic patch request...", flush=True)
                cur_refs_md = "\n".join(
                    f"### {rel_r}\n```c\n{open(path(rel_r), errors='replace').read()}\n```"
                    for rel_r in allowed_refs if os.path.exists(path(rel_r))
                )
                # Stable content first (disasm -> header -> ref C -> test -> failure tail) for prompt caching
                fix_prompt = (
                    (f"Disassembly & xrefs for reference functions:\n{ref_disasm_md}\n\n" if ref_disasm_md else "")
                    + f"Header `{hdr_rel}`:\n```c\n{hdr_text}\n```\n\n"
                    + f"Reference C files (editable via `ref_patches` when `diagnosis.kind == 'ref_bug'`):\n{cur_refs_md}\n\n"
                    + f"Current `{test_rel}`:\n```python\n{open(test_path).read()}\n```\n\n"
                    + f"Pytest failure output (attempt {fix_i}/2):\n```\n{out_txt[-3000:]}\n```\n\n"
                    + f"RULES:\n"
                    + f"- Diagnose `ref_bug` vs `harness_bug` vs `proto_bug`, citing an exact disassembly address.\n"
                    + f"- If a `*_reference.c` function disagrees with the disassembly, patch it via `ref_patches` and leave `test_patches` empty.\n"
                    + f"- NEVER wrap `run_spec`/`run_pair` in `pytest.raises`, `contextlib.suppress`, or `try/except`.\n"
                    + f"- NEVER add `pytest.skip` / `pytest.mark.skipif` / `pytest.mark.xfail`.\n"
                    + f"- NEVER weaken, drop, or alter failing test inputs to hide a bug in `*_reference.c`.\n"
                    + f"- If the failure requires editing `{hdr_rel}` (`proto_bug`), return empty patches so bounded repair handles it.\n"
                )
                patch_res, _c, _u = _call_llm(
                    fix_prompt, T4_PATCH_SCHEMA, sys_file,
                    provider=provider, stage="stage4",
                    claude_model="sonnet", claude_effort="low",
                    codex_matrix=codex_matrix, codex_bin=codex_bin,
                    codex_home=codex_home, codex_quota_guard=codex_quota_guard,
                    ledger=ledger, label=f"{area}:stage4_fix{fix_i}",
                    max_cost=max_cost, max_calls=max_calls,
                )
                pres = _apply_t4_patch_result(test_path, patch_res, allowed_refs)
                live.append_event(
                    area, "info",
                    f"stage4_fix{fix_i} diag={pres['diag_kind']}: {pres['diag_reason'][:100]} "
                    f"(ref={pres['ref_applied']} test={pres['test_applied']})",
                )
                for rej in pres["rejected"]:
                    print(f"  [stage4_fix{fix_i} rejected] {rej}", flush=True)
                    live.append_event(area, "error", f"stage4_fix{fix_i} rejected: {rej}")
                if pres["diag_kind"] == "proto_bug" and not pres["ref_applied"] and not pres["test_applied"]:
                    break
                live.update_worker_meta(area, phase="VERIFYING", stage=f"pytest:{test_rel}")
                ok, out_txt = _run_pytest_file(test_path)

            verified_rv = _verify_and_wire_t4_nodes(
                raw_rv_map, t4_needed, funcs_db, toml_path, toml_rel,
                module_name, area, skip_semantic, toml_preexisted,
                sem_cache_path, t3_matched, t3_unbuildable, datas_db,
            )
            if ok and len(verified_rv) == len(t4_needed):
                print(f"  [STAGE 4 PASS] {test_rel} green ({len(verified_rv)} T4 verified)", flush=True)
                live.append_event(area, "verify", f"[STAGE 4 PASS] {test_rel} green ({len(verified_rv)} T4 verified)")
                ledger.record("stage4_done", t4_verified=len(verified_rv), test_path=test_rel)
            else:
                print(f"  [STAGE 4 FAIL] {test_rel} ({len(verified_rv)}/{len(t4_needed)} T4 verified):\n{out_txt[-1200:]}", flush=True)
                live.append_event(area, "error", f"[STAGE 4 FAIL] {test_rel} ({len(verified_rv)}/{len(t4_needed)} T4 verified)")
                ledger.record("stage4_fail", ok=False, t4_verified=len(verified_rv),
                              test_path=test_rel, pending_ref_verified_by=pending_rv_hex)
        except BudgetExceededError as ex:
            print(f"  [budget cap reached before Stage 4] {ex}", flush=True)

    s = ledger.summary()
    if provider == "codex":
        p_d = f"{s['codex_primary_delta_pp']:+.2f}pp" if s["codex_primary_delta_pp"] is not None else f"unobserved (est~{s['codex_estimated_primary_pp']:.2f}pp)"
        s_d = f"{s['codex_secondary_delta_pp']:+.2f}pp" if s["codex_secondary_delta_pp"] is not None else "n/a"
        print(f"\n== {module_name} SUMMARY [codex]: T3={len(t3_matched)} UNBUILDABLE={len(t3_unbuildable)} REF={len(t4_needed)} | "
              f"calls={s['codex_calls']} cache_hit={s['codex_cache_hit_pct']}% "
              f"(in={s['codex_input_tokens']} cached={s['codex_cached_input_tokens']} "
              f"out={s['codex_output_tokens']} reas={s['codex_reasoning_tokens']}) "
              f"5h_delta={p_d} 7d_delta={s_d} ==",
              flush=True)
    else:
        print(f"\n== {module_name} SUMMARY: T3={len(t3_matched)} UNBUILDABLE={len(t3_unbuildable)} REF={len(t4_needed)} | "
              f"calls={s['calls']} cost=${s['cost_usd']:.4f} cache_hit={s['cache_hit_pct']}% "
              f"(cc={s['cache_create_tokens']} cr={s['cache_read_tokens']} out={s['output_tokens']}) ==",
              flush=True)
    return 0


def _add_provider_args(p):
    p.add_argument("--provider", choices=("claude", "codex"), default="claude",
                   help="LLM backend provider (default claude)")
    p.add_argument("--codex-model", default=None,
                   help="Default OpenAI model ID for all Codex stages (e.g. gpt-6.2-sol, gpt-6-luna)")
    p.add_argument("--codex-effort", default=None,
                   help="Default reasoning_effort for all Codex stages (low|medium|high)")
    p.add_argument("--codex-stage1", default=None, help="Stage 1 override MODEL[:EFFORT]")
    p.add_argument("--codex-stage2", default=None, help="Stage 2 override MODEL[:EFFORT]")
    p.add_argument("--codex-stage3", default=None, help="Stage 3 override MODEL[:EFFORT]")
    p.add_argument("--codex-stage4", default=None, help="Stage 4 override MODEL[:EFFORT]")
    p.add_argument("--codex-repair", default=None, help="Post-verify repair override MODEL[:EFFORT]")
    p.add_argument("--codex-bin", default=None, help="Path to codex CLI binary (default codex)")
    p.add_argument("--codex-home", default=None,
                   help="CODEX_HOME for telemetry/rollouts (default $CODEX_HOME or ~/.codex)")
    p.add_argument("--codex-after-reset-ts", type=float, default=None,
                   help="Resets_at epoch of a 5h window wc1.overnight just slept through; lets the "
                        "first call resume on telemetry that still describes that expired window")
    p.add_argument("--codex-start-7d-resets-at", type=float, default=None,
                   help="7d window resets_at recorded with --codex-start-7d-pct")
    p.add_argument("--codex-window-budget", type=float, default=1.0,
                   help="Codex 5h window budget fraction in (0.0, 1.0] (default 1.0 for direct batch_driver)")
    p.add_argument("--codex-max-5h-pct", type=float, default=None,
                   help="Hard per-call Codex 5h used_percent ceiling")
    p.add_argument("--codex-max-7d-pct", type=float, default=90.0,
                   help="Hard per-call Codex 7d used_percent ceiling (default 90.0)")
    p.add_argument("--codex-max-7d-delta-pp", type=float, default=None,
                   help="Hard per-call Codex 7d delta ceiling (pp above --codex-start-7d-pct)")
    p.add_argument("--codex-start-7d-pct", type=float, default=None,
                   help="Baseline 7d used_percent recorded at run start for delta cap")
    p.add_argument("--codex-max-total-calls", type=int, default=None,
                   help="Hard cumulative Codex call ceiling (across run / fallback when telemetry unobserved)")
    p.add_argument("--codex-base-total-calls", type=int, default=0,
                   help="Codex calls already spent earlier in this run (passed by wc1.overnight)")
    p.add_argument("--codex-telemetry-max-age", type=int, default=codex.DEFAULT_TELEMETRY_MAX_AGE_S,
                   help=f"Max age in seconds for fresh 5h Codex telemetry (default {codex.DEFAULT_TELEMETRY_MAX_AGE_S})")
    p.add_argument("--codex-early-stop-stage2", action="store_true",
                   help="Abort immediately after Stage 2 if drafted C fails compile-check (for Stage A screening)")


def _build_codex_runtime(args):
    if getattr(args, "provider", "claude") != "codex":
        return None, None
    matrix = codex.build_stage_matrix(
        default_model=args.codex_model,
        default_effort=args.codex_effort,
        overrides={
            "stage1": args.codex_stage1,
            "stage2": args.codex_stage2,
            "stage3": args.codex_stage3,
            "stage4": args.codex_stage4,
            "repair": args.codex_repair,
        },
    )
    guard = {
        "window_budget": args.codex_window_budget,
        "max_age_s": args.codex_telemetry_max_age,
        "max_5h_pct": args.codex_max_5h_pct,
        "max_7d_pct": args.codex_max_7d_pct,
        "max_7d_delta_pp": args.codex_max_7d_delta_pp,
        "start_7d_pct": args.codex_start_7d_pct,
        "start_7d_resets_at": getattr(args, "codex_start_7d_resets_at", None),
        "max_total_calls": args.codex_max_total_calls,
        "_base_total_calls": args.codex_base_total_calls,
    }
    after_ts = getattr(args, "codex_after_reset_ts", None)
    if after_ts is not None:
        guard["after_reset"] = True
        guard["slept_resets_at"] = float(after_ts)
    if guard["max_7d_delta_pp"] is not None and guard["start_7d_pct"] is None:
        # S5: a delta cap with no baseline would never fire; snapshot it from fresh
        # telemetry now, or lazily from the first call's telemetry (_snapshot_start_7d).
        try:
            rl = codex.get_latest_rate_limits(codex_home=getattr(args, "codex_home", None))
        except Exception:
            rl = None
        if isinstance(rl, dict):
            _snapshot_start_7d(guard, {"rate_limits_before": rl})
    return matrix, guard


def run_t3_recovery(addr, area=None, max_cost=0.80, max_calls=2, provider="claude",
                    codex_matrix=None, codex_bin=None, codex_home=None, codex_quota_guard=None):
    """Wave 4: one bounded T4 -> T3 recovery attempt for the function at addr
    (wc1.wave4.run_recovery).  The outcome record lands in build/wave4/outcomes/;
    the exit code is 0 for every outcome except a toolchain error (78, via main())."""
    import shutil
    from . import t3_audit, wave4
    area = area or f"w4_{addr:x}"
    global _live_area
    _live_area = area
    inputs = t3_audit.load_inputs()
    queue, _info = wave4.discover(inputs=inputs, report_state="missing")
    cand = next((c for c in queue if c["addr"] == addr), None)
    if cand is None:
        print(f"{addr:#x}: not an eligible T4 function (nothing to do).", flush=True)
        return EXIT_NOTHING_TO_DO
    siblings = [c for c in queue if c["ref"] == cand["ref"]]
    p, funcs, by_link, _rows, _issues = inputs
    objdir = path("build", "wave4", "obj", f"{addr:x}")
    shutil.rmtree(objdir, ignore_errors=True)
    ctx = t3_audit.Ctx(p, funcs, by_link, objdir)
    ledger = Ledger(path("build", "ledger", f"{area}.jsonl"))
    work = path("build", "driver")
    os.makedirs(work, exist_ok=True)
    sys_file = os.path.join(work, f"{area}_sys.txt")
    with open(sys_file, "w") as fh:
        fh.write(wave4.REPAIR_RULES)

    def llm(prompt, schema, label):
        res, _c, _u = _call_llm(
            prompt, schema, sys_file, provider=provider, stage="stage4",
            claude_model="sonnet", claude_effort="medium",
            codex_matrix=codex_matrix, codex_bin=codex_bin, codex_home=codex_home,
            codex_quota_guard=codex_quota_guard, ledger=ledger, label=label,
            max_cost=max_cost, max_calls=None,
        )
        return res

    try:
        out = wave4.run_recovery(cand, siblings, ctx, llm=llm, max_calls=max_calls)
    finally:
        shutil.rmtree(objdir, ignore_errors=True)
    print(f"[wave4] {cand['name']} {addr:#x}: {out['outcome']}", flush=True)
    if out["outcome"] == wave4.TOOLCHAIN_ERROR:
        raise ToolchainError(out.get("reason") or "toolchain error during wave4 recovery")
    return 0


def main(argv=None):
    # `kill -USR1 <pid>` dumps every thread's stack to stderr (wc1.overnight
    # does it before killing a stalled run); registering starts no thread.
    if hasattr(signal, "SIGUSR1"):
        faulthandler.register(signal.SIGUSR1, all_threads=True)
    ap = argparse.ArgumentParser(prog="wc1.batch_driver", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for mode in ("full", "c-only"):
        p1 = sub.add_parser(mode)
        p1.add_argument("module")
        p1.add_argument("--area", default=None)
        p1.add_argument("--header", default=None)
        p1.add_argument("--src-subdir", default=None)
        p1.add_argument("--limit", type=int, default=None)
        p1.add_argument("--addrs", default=None,
                        help="Comma-separated hex addresses to target (strictly intersected with eligible set)")
        p1.add_argument("--max-cost", type=float, default=1.20)
        p1.add_argument("--max-calls", type=int, default=10)
        p1.add_argument("--max-t3-retries", type=int, default=2)
        p1.add_argument("--permute-trials", type=int, default=50)
        p1.add_argument("--dry-run", action="store_true")
        _add_provider_args(p1)
    p2 = sub.add_parser("t4-only")
    p2.add_argument("module")
    p2.add_argument("--area", default=None)
    p2.add_argument("--max-cost", type=float, default=0.80)
    p2.add_argument("--max-calls", type=int, default=6)
    _add_provider_args(p2)
    p4 = sub.add_parser("t3-recovery")
    p4.add_argument("addr", help="hex address of the T4 function to recover")
    p4.add_argument("--area", default=None)
    p4.add_argument("--max-cost", type=float, default=0.80)
    p4.add_argument("--max-calls", type=int, default=2)
    _add_provider_args(p4)
    p3 = sub.add_parser("stats")
    p3.add_argument("ledger")
    a = ap.parse_args(argv)
    if a.cmd == "stats":
        print(json.dumps(Ledger(a.ledger).summary(), indent=2))
        return 0
    try:
        codex_matrix, codex_guard = _build_codex_runtime(a)
        if a.cmd == "t3-recovery":
            return run_t3_recovery(
                int(a.addr, 0), area=a.area, max_cost=a.max_cost, max_calls=a.max_calls,
                provider=a.provider, codex_matrix=codex_matrix, codex_bin=a.codex_bin,
                codex_home=a.codex_home, codex_quota_guard=codex_guard,
            )
        if a.cmd == "t4-only":
            return run_t4_only(
                a.module, area=a.area, max_cost=a.max_cost, max_calls=a.max_calls,
                provider=a.provider, codex_matrix=codex_matrix, codex_bin=a.codex_bin,
                codex_home=a.codex_home, codex_quota_guard=codex_guard,
            )
        return run_full_module(
            a.module, area=a.area, max_cost=a.max_cost, max_calls=a.max_calls,
            max_t3_retries=a.max_t3_retries, permute_trials=a.permute_trials,
            dry_run=a.dry_run, skip_semantic=(a.cmd == "c-only"),
            header=a.header, limit=a.limit, src_subdir=a.src_subdir,
            addrs=a.addrs, provider=a.provider, codex_matrix=codex_matrix,
            codex_bin=a.codex_bin, codex_home=a.codex_home, codex_quota_guard=codex_guard,
            early_stop_stage2=a.codex_early_stop_stage2,
        )
    except RateLimitError as ex:
        res_note = f" resets_at={int(ex.resets_at)}" if getattr(ex, "resets_at", None) else ""
        print(f"[RATE_LIMIT] {ex}{res_note}", file=sys.stderr, flush=True)
        return EXIT_RATE_LIMIT
    except QuotaCapExceededError as ex:
        print(f"[QUOTA_CAP] {ex}", file=sys.stderr, flush=True)
        return EXIT_QUOTA_STOP
    except (ToolchainError, match.CompileTimeout) as ex:
        # CompileTimeout: a compile no stage turned into a ToolchainError
        print(f"[TOOLCHAIN ERROR] {ex}", file=sys.stderr, flush=True)
        return EXIT_TOOLCHAIN
    except (DriverError, ValueError) as ex:
        print(f"[DRIVER ERROR] {ex}", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
