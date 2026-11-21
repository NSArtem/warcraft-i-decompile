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
import json
import os
import re
import subprocess
import sys
import threading
import time

from . import analysis, dossier, live, match, path, permuter, progress, symbols

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


class DriverError(Exception):
    pass


class RateLimitError(DriverError):
    pass


class BudgetExceededError(DriverError):
    pass


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
        return sum(float(e.get("cost_usd", 0.0) or 0.0) for e in self.entries)

    def total_calls(self):
        return sum(1 for e in self.entries if e.get("stage") == "claude_call")

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
        return {
            "calls": len(calls),
            "cost_usd": round(cost, 4),
            "input_tokens": inp,
            "cache_create_tokens": cc,
            "cache_read_tokens": cr,
            "output_tokens": out,
            "cache_hit_pct": round(100.0 * cr / max(1, cr + cc + inp), 1),
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


def _rewrite_toml_with_results(toml_path, sem, module_name, area, funcs_db, datas_db,
                               t3_matched, t4_needed, ref_verified=None):
    """Rewrite analysis/symbols/<area>.toml with T3 src= or T4 ref=/t3_blocker/ref_verified_by."""
    ref_verified = ref_verified or {}
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


def _update_existing_toml_entries(t3_matched, t4_needed, ref_verified=None):
    """Update existing TOML entries (for c-only / t4-only modes) cleanly in place."""
    import tomllib
    ref_verified = ref_verified or {}
    funcs_db, _, _ = symbols.load(strict=False)
    by_file = {}
    for a in set(t3_matched) | set(t4_needed) | set(ref_verified):
        e = funcs_db.get(a)
        if e:
            by_file.setdefault(e["_file"], []).append(a)
    for rel_file, addrs in by_file.items():
        full = path(rel_file)
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


def _pytest_output_passed(returncode, out_txt, test_src=None):
    """True only when pytest exited 0, ran >=1 passing test, and had no xfail/xpass cheats."""
    if returncode != 0:
        return False
    out = out_txt or ""
    if re.search(r"\b[1-9]\d*\s+(?:xfailed|xpassed)\b", out):
        return False
    if test_src and re.search(r"@pytest\.mark\.(?:xfail|skip)\b", test_src):
        return False
    return bool(re.search(r"\b[1-9]\d*\s+passed\b", out))


def _run_pytest_file(test_path):
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", test_path],
                       capture_output=True, text=True, cwd=path())
    out = (r.stdout + "\n" + r.stderr).strip()
    src = open(test_path, errors="replace").read() if os.path.exists(test_path) else ""
    ok = _pytest_output_passed(r.returncode, out, test_src=src)
    if r.returncode == 0 and not ok:
        out += "\n[batch_driver ERROR: test file skipped or used @pytest.mark.xfail/@pytest.mark.skip — NEVER xfail/skip failing tests, fix them!]"
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
        "patches": {
            "type": "array",
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
    "required": ["patches"],
}


def _apply_patches(file_path, patches):
    text = open(file_path).read()
    applied = 0
    for p in patches or []:
        old, new = p.get("old", ""), p.get("new", "")
        if old and old in text:
            text = text.replace(old, new, 1)
            applied += 1
    if applied:
        with open(file_path, "w") as fh:
            fh.write(text)
    return applied


def run_t4_only(module_name, area=None, max_cost=0.80, max_calls=6, batch_size=8):
    """Generate declarative wc1.t4spec difftests for existing `ref =` functions missing T4.

    Chunks large modules into batches of `batch_size` (default 8) and uses targeted
    search-and-replace patches on pytest retry so fixes cost ~500 output tokens
    instead of rewriting the whole file.
    """
    area = area or re.sub(r"[^a-z0-9_]+", "_", module_name.lower().replace(".c", "")).strip("_")
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
        prompt = (
            f"Write a compact pytest module `{test_rel}` using `wc1.t4spec` to T4-difftest "
            f"ALL {len(chunk)} reference-C functions below in `{module_name}` (do NOT omit any!):\n{fn_list}\n\n"
            f"Each function MUST have its own `def test_<snake_name>():` so TOML "
            f"`ref_verified_by = \"difftest: {test_rel}::test_<snake_name>\"` maps 1-to-1.\n"
            f"Use EXACTLY this `pytestmark`:\n"
            f"`pytestmark = pytest.mark.skipif(not (os.path.exists(path('original', 'install', 'war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')`\n"
            f"Pass the EXACT Watcom link name (`Foo_` for watcall, `_Foo` for cdecl) to `t4spec.run_spec`.\n"
            f"Stub external hardware/DOS/UI callees with `t4spec.T4Stub(addr, log_regs=(...))` — ALWAYS set "
            f"`log_regs` to ONLY the exact argument registers the callee takes (`()` for void(void), `('eax',)` for 1-arg, etc.), "
            f"and NEVER log stack-local pointer addresses (`esp+...`) whose frame offset differs between original and C.\n"
            f"Pass `out_regs=()` for void functions! Pass `limit=64` to `e.cstr(a, 64)` on stack strings.\n"
            f"Note: `wc1.emu.Emu` has a flat 32-bit GDT (CS=0x08, DS/ES/FS/GS/SS=0x10) so far selectors use `0x10`, and `interrupt=True` works for `__interrupt` functions.\n"
            f"Keep tests concise (3-6 edge cases per function). Leave `doc_md` empty string.\n\n"
            f"wc1.t4spec API:\n```python\n{t4spec_src}\n```\n\n"
            f"Reference C files:\n"
            + "\n".join(f"### {k}\n```c\n{v}\n```" for k, v in ref_sources.items())
            + "\n\nDisassembly & xrefs:\n" + dossier.render_markdown(d)
        )
        res, _c, _u = call_claude(
            prompt, T4_AND_DOC_SCHEMA, sys_file,
            model="sonnet", effort="low",
            ledger=ledger, label=f"{area}:t4gen_c{ci}",
            max_cost=max_cost, max_calls=max_calls,
        )
        with open(test_path, "w") as fh:
            fh.write(res["test_py"].rstrip() + "\n")

        ok, out_txt = _run_pytest_file(test_path)
        for fix_i in range(1, 3):
            if ok:
                break
            print(f"  [t4 pytest fail c{ci} #{fix_i}] sending compact patch request...", flush=True)
            fix_prompt = (
                f"Fix ONLY the failing tests in `{test_rel}` (attempt {fix_i}/2) using minimal search-and-replace patches.\n"
                f"Pytest failure output:\n```\n{out_txt[-3000:]}\n```\n\n"
                f"Current `{test_rel}`:\n```python\n{open(test_path).read()}\n```\n"
            )
            patch_res, _c, _u = call_claude(
                fix_prompt, T4_PATCH_SCHEMA, sys_file,
                model="sonnet", effort="low",
                ledger=ledger, label=f"{area}:t4fix_c{ci}_{fix_i}",
                max_cost=max_cost, max_calls=max_calls,
            )
            _apply_patches(test_path, patch_res.get("patches"))
            ok, out_txt = _run_pytest_file(test_path)

        if ok:
            rv_map = {int(it["addr"], 16): it["test_node"] for it in res.get("ref_verified_by", [])}
            _update_existing_toml_entries({}, {}, ref_verified=rv_map)
            print(f"  [T4 PASS c{ci}] {test_rel} ({len(rv_map)} functions updated in TOML)", flush=True)
            ledger.record(f"t4_c{ci}", count=len(rv_map), test_path=test_rel)
        else:
            all_ok = False
            print(f"  [T4 FAIL c{ci}] {test_rel} still failing:\n{out_txt[-1000:]}", flush=True)
            ledger.record(f"t4_fail_c{ci}", ok=False)
    print("  Summary:", json.dumps(ledger.summary()))
    return 0 if all_ok else 1


def run_full_module(module_name, area=None, max_cost=1.20, max_calls=10,
                    max_t3_retries=2, permute_trials=50, dry_run=False,
                    skip_semantic=False, header=None, limit=None,
                    src_subdir=None):
    area = area or re.sub(r"[^a-z0-9_]+", "_", module_name.lower().replace(".c", "")).strip("_")
    ledger = Ledger(path("build", "ledger", f"{area}.jsonl"))
    frozen_rec = ledger.last_stage("target_addrs")
    frozen_addrs = frozen_rec.get("addrs") if isinstance(frozen_rec, dict) else None
    if frozen_addrs:
        d = dossier.build_dossier(frozen_addrs, only_undone=False,
                                  only_missing_c=False,
                                  include_ghidra=True, include_exemplars=True)
    else:
        d = dossier.build_dossier([module_name], only_undone=True,
                                  only_missing_c=skip_semantic,
                                  include_ghidra=True, include_exemplars=True)
        if skip_semantic:
            # c-only mode only works on functions that already have a semantic DB entry
            fdb0, _, _ = symbols.load(strict=False)
            d["functions"] = [
                fn for fn in d["functions"]
                if (e0 := fdb0.get(fn["addr_int"])) is not None
                and not e0["name"].startswith("fn_")
                and e0.get("confidence") in ("medium", "high", "verified")
            ]
            d["function_count"] = len(d["functions"])
            d["total_insns"] = sum(x["ninsns"] for x in d["functions"])
        if limit and d["function_count"] > limit:
            d["functions"] = d["functions"][:limit]
            d["function_count"] = len(d["functions"])
            d["total_insns"] = sum(x["ninsns"] for x in d["functions"])
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
                f"Emit semantic names, exact watcall prototypes, confidence, concrete disassembly-based "
                f"evidence (NEVER cite Ghidra), and a clean C89 header `src/include/{area}.h`.\n"
                f"CRITICAL — COMPLETE DATA COVERAGE: Emit a `data_symbols` entry for EVERY unnamed data "
                f"address below (unless it is literally an interior offset like `arr[1]` of another entry "
                f"you define in `data_symbols`, in which case document that in `header_h`!). Leaving any "
                f"referenced global unnamed causes `wc1.match` and `wc1.cemu` relocation failures!\n"
                f"DO NOT duplicate any function or data address already present in another symbol file.\n\n"
                f"Unnamed data addresses referenced by this module ({len(unnamed_data)}):\n"
                f"{unnamed_data_str}\n\n"
                f"Known neighbour prototypes:\n" + "\n".join(existing_names) + "\n\n"
                f"Module dossier:\n{md_text}"
            )
            sem, _c, _u = call_claude(
                prompt, SEMANTIC_SCHEMA, sys_file,
                model="sonnet", effort="medium",
                ledger=ledger, label=f"{area}:semantic",
                max_cost=max_cost, max_calls=max_calls,
            )
            with open(sem_cache_path, "w") as fh:
                json.dump(sem, fh, indent=2)
            if not os.path.exists(hdr_path):
                with open(hdr_path, "w") as fh:
                    fh.write(sem["header_h"].rstrip() + "\n")

            # Write initial TOML (never overwrite pre-existing committed TOML; append new entries only)
            entries_text = [f"# {module_name} ({area}) - generated by wc1.batch_driver\n"]
            for fn in sem["functions"]:
                a = int(fn["addr"], 16)
                if a in funcs_db:
                    if toml_preexisted or funcs_db[a]["_file"] != f"analysis/symbols/{area}.toml":
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
                    if toml_preexisted or datas_db[a]["_file"] != f"analysis/symbols/{area}.toml":
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
                print(f"  [warn] symbols errors after semantic pass: {errs[:5]}", flush=True)
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
        res, _c, _u = call_claude(
            prompt, BATCH_C_SCHEMA, sys_file,
            model="sonnet", effort="low",
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

    # ---- Stage 3: Local match + permuter + batched hard-capped repair loop --
    live.update_worker_meta(area, phase="PERMUTING", stage="stage3:permute")
    live.append_event(area, "perm", f"Stage 3: permuting {len(d2['functions'])} functions locally")
    p = analysis.run()
    t3_matched = {}   # addr -> rel src path
    t4_needed = {}    # addr -> (rel ref path, t3_blocker)
    mismatches = []   # list of (fn_dict, e_dict, fpath, diff_dict, diff_txt)

    for fn in d2["functions"]:
        a = fn["addr_int"]
        fpath = generated_files.get(a)
        if not fpath or not os.path.exists(fpath):
            continue
        e = funcs_db.get(a)
        if not e:
            continue
        fn_label = f"{e['name']}@{a:#x}"
        live.update_worker_meta(area, phase="PERMUTING", stage=f"permute:{e['name']}")
        pr = permuter.permute_file(fpath, max_trials=permute_trials, jobs=4,
                                   orig_addr=a, rounds=2, apply=True)
        if pr["matched"]:
            rel = os.path.relpath(fpath, path())
            t3_matched[a] = rel
            msg = f"[T3 MATCH local] {fn_label} -> {rel} ({pr['label']}, {pr['trials']} trials)"
            print(f"  {msg}", flush=True)
            live.append_event(area, "match", msg)
            ledger.record("fn_t3", addr=f"{a:#x}", name=e["name"], via=pr["label"])
        else:
            live.append_event(area, "perm", f"miss {fn_label} ({pr['trials']} trials): {pr.get('first_diff') or 'mismatch'}")
            mismatches.append((fn, e, fpath))

    # Reserve 2 calls + $0.25 for Stage 4 (T4 tests + doc)
    repair_max_calls = max(ledger.total_calls(), max_calls - 2)
    repair_max_cost = max(ledger.total_cost(), max_cost - 0.25)

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
                rep, _c, _u = call_claude(
                    rep_prompt, REPAIR_C_SCHEMA, sys_file,
                    model="sonnet", effort="medium",
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
                live.update_worker_meta(area, phase="PERMUTING", stage=f"permute_r{attempt}:{e['name']}")
                pr2 = permuter.permute_file(fpath, max_trials=permute_trials, jobs=4,
                                            orig_addr=a, rounds=1, apply=True)
                if pr2["matched"]:
                    rel = os.path.relpath(fpath, path())
                    t3_matched[a] = rel
                    msg = f"[T3 MATCH r{attempt}] {e['name']}@{a:#x} -> {rel} ({pr2['label']})"
                    print(f"  {msg}", flush=True)
                    live.append_event(area, "match", msg)
                    ledger.record("fn_t3", addr=f"{a:#x}", name=e["name"], via=f"r{attempt}+{pr2['label']}")
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
        bad_cc = match.compile_check(area_srcs, jobs=4)
        if bad_cc:
            print(f"  [warn] compile-check failures: {bad_cc}", flush=True)

    # Update TOML with T3/ref results right away (before Stage 4 tests)
    toml_rel = f"analysis/symbols/{area}.toml"
    if not skip_semantic and not toml_preexisted and os.path.exists(sem_cache_path):
        sem_loaded = json.load(open(sem_cache_path))
        _rewrite_toml_with_results(toml_path, sem_loaded, module_name, area,
                                   funcs_db, datas_db, t3_matched, t4_needed)
        # Also update any functions whose entry lives in a pre-existing other TOML file
        other_t3 = {a: v for a, v in t3_matched.items() if a in funcs_db and funcs_db[a]["_file"] != toml_rel}
        other_t4 = {a: v for a, v in t4_needed.items() if a in funcs_db and funcs_db[a]["_file"] != toml_rel}
        if other_t3 or other_t4:
            _update_existing_toml_entries(other_t3, other_t4)
    else:
        _update_existing_toml_entries(t3_matched, t4_needed)

    # ---- Stage 4: Declarative T4 tests + subsystem doc ----------------------
    doc_path = path("docs", "subsystems", f"{area}.md")
    doc_exists = os.path.exists(doc_path)
    test_rel = _pick_nonclobber_test_rel(area)
    test_path = path(test_rel)
    src_rel_dir = os.path.relpath(src_dir, path())
    if not ledger.has_stage("stage4_done"):
        t4spec_src = open(path("tools", "wc1", "t4spec.py")).read()
        t3_list = sorted(os.path.basename(v) for v in t3_matched.values())
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
        s4_prompt = (
            f"Generate `{test_rel}` (using `wc1.t4spec`)"
            + ("" if doc_exists else f" AND `docs/subsystems/{area}.md`")
            + f" for module `{module_name}` (area `{area}`).\n"
            f"1. In `{test_rel}`:\n"
            f"   - Include EXACTLY: `pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')`.\n"
            f"   - Test T3 files still match via `t4spec.assert_t3_matches(path('{src_rel_dir}'), {t3_list!r})` (if non-empty).\n"
            f"   - Near-miss guard for reference files via `t4spec.assert_ref_mismatch(path('{src_rel_dir}'), {ref_list!r})` (if non-empty).\n"
            f"   - For EVERY reference function below, write a `def test_<snake_name>():` using `t4spec.run_spec(...)` with exact Watcom link name (`Foo_` / `_Foo`), "
            f"`out_regs=()` for void functions, exact callee arity in `T4Stub(addr, log_regs=(...))`, never logging stack pointers, and `limit=64` on `e.cstr(a, 64)`.\n"
            f"   - CRITICAL: NEVER call `Emu().alloc(...)` outside `init_emu` (buffers MUST be allocated inside `init_emu(emu)` so they never overlap the C module at `0x800000`). NEVER use `@pytest.mark.xfail` or `@pytest.mark.skip`.\n"
            f"   - Populate `ref_verified_by` with `difftest: {test_rel}::test_<snake_name>` for each.\n"
            f"{doc_instr}"
            f"wc1.t4spec API:\n```python\n{t4spec_src}\n```\n\n"
            f"Header `{hdr_rel}`:\n```c\n{hdr_text}\n```\n\n"
            + ("Reference functions needing T4 difftests:\n" + "\n".join(ref_details) if ref_details else "No reference functions; all matched T3!\n")
        )
        try:
            s4, _c, _u = call_claude(
                s4_prompt, T4_AND_DOC_SCHEMA, sys_file,
                model="sonnet", effort="low",
                ledger=ledger, label=f"{area}:stage4_t4_doc",
                max_cost=max_cost, max_calls=max_calls,
            )
            with open(test_path, "w") as fh:
                fh.write(s4["test_py"].rstrip() + "\n")
            if s4.get("doc_md") and not doc_exists:
                with open(doc_path, "w") as fh:
                    fh.write(s4["doc_md"].rstrip() + "\n")

            live.update_worker_meta(area, phase="VERIFYING", stage=f"pytest:{test_rel}")
            ok, out_txt = _run_pytest_file(test_path)
            for fix_i in range(1, 3):
                if ok:
                    break
                live.append_event(area, "error", f"Stage 4 pytest fail #{fix_i} on {test_rel}")
                print(f"  [stage4 pytest fail #{fix_i}] sending compact patch request...", flush=True)
                fix_prompt = (
                    f"Fix ONLY the failing tests in `{test_rel}` (attempt {fix_i}/2) using minimal search-and-replace patches.\n"
                    f"Pytest output:\n```\n{out_txt[-3000:]}\n```\n\n"
                    f"Current `{test_rel}`:\n```python\n{open(test_path).read()}\n```\n"
                )
                patch_res, _c, _u = call_claude(
                    fix_prompt, T4_PATCH_SCHEMA, sys_file,
                    model="sonnet", effort="low",
                    ledger=ledger, label=f"{area}:stage4_fix{fix_i}",
                    max_cost=max_cost, max_calls=max_calls,
                )
                _apply_patches(test_path, patch_res.get("patches"))
                live.update_worker_meta(area, phase="VERIFYING", stage=f"pytest:{test_rel}")
                ok, out_txt = _run_pytest_file(test_path)

            if ok:
                rv_map = {int(it["addr"], 16): it["test_node"] for it in s4.get("ref_verified_by", [])}
                if not skip_semantic and not toml_preexisted and os.path.exists(sem_cache_path):
                    _rewrite_toml_with_results(toml_path, json.load(open(sem_cache_path)),
                                               module_name, area, funcs_db, datas_db,
                                               t3_matched, t4_needed, ref_verified=rv_map)
                    other_t3 = {a: v for a, v in t3_matched.items() if a in funcs_db and funcs_db[a]["_file"] != toml_rel}
                    other_t4 = {a: v for a, v in t4_needed.items() if a in funcs_db and funcs_db[a]["_file"] != toml_rel}
                    other_rv = {a: v for a, v in rv_map.items() if a in funcs_db and funcs_db[a]["_file"] != toml_rel}
                    if other_t3 or other_t4 or other_rv:
                        _update_existing_toml_entries(other_t3, other_t4, ref_verified=other_rv)
                else:
                    _update_existing_toml_entries(t3_matched, t4_needed, ref_verified=rv_map)
                print(f"  [STAGE 4 PASS] {test_rel} green ({len(rv_map)} T4 verified)", flush=True)
                live.append_event(area, "verify", f"[STAGE 4 PASS] {test_rel} green ({len(rv_map)} T4 verified)")
                ledger.record("stage4_done", t4_verified=len(rv_map), test_path=test_rel)
            else:
                print(f"  [STAGE 4 FAIL] {test_rel} failed:\n{out_txt[-1200:]}", flush=True)
                live.append_event(area, "error", f"[STAGE 4 FAIL] {test_rel} failed")
                ledger.record("stage4_fail", ok=False)
        except BudgetExceededError as ex:
            print(f"  [budget cap reached before Stage 4] {ex}", flush=True)

    s = ledger.summary()
    print(f"\n== {module_name} SUMMARY: T3={len(t3_matched)} REF={len(t4_needed)} | "
          f"calls={s['calls']} cost=${s['cost_usd']:.4f} cache_hit={s['cache_hit_pct']}% "
          f"(cc={s['cache_create_tokens']} cr={s['cache_read_tokens']} out={s['output_tokens']}) ==",
          flush=True)
    return 0


EXIT_RATE_LIMIT = 75


def main(argv=None):
    ap = argparse.ArgumentParser(prog="wc1.batch_driver", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for mode in ("full", "c-only"):
        p1 = sub.add_parser(mode)
        p1.add_argument("module")
        p1.add_argument("--area", default=None)
        p1.add_argument("--header", default=None)
        p1.add_argument("--src-subdir", default=None)
        p1.add_argument("--limit", type=int, default=None)
        p1.add_argument("--max-cost", type=float, default=1.20)
        p1.add_argument("--max-calls", type=int, default=10)
        p1.add_argument("--max-t3-retries", type=int, default=2)
        p1.add_argument("--permute-trials", type=int, default=50)
        p1.add_argument("--dry-run", action="store_true")
    p2 = sub.add_parser("t4-only")
    p2.add_argument("module")
    p2.add_argument("--area", default=None)
    p2.add_argument("--max-cost", type=float, default=0.80)
    p2.add_argument("--max-calls", type=int, default=6)
    p3 = sub.add_parser("stats")
    p3.add_argument("ledger")
    a = ap.parse_args(argv)
    if a.cmd == "stats":
        print(json.dumps(Ledger(a.ledger).summary(), indent=2))
        return 0
    try:
        if a.cmd == "t4-only":
            return run_t4_only(a.module, area=a.area, max_cost=a.max_cost, max_calls=a.max_calls)
        return run_full_module(
            a.module, area=a.area, max_cost=a.max_cost, max_calls=a.max_calls,
            max_t3_retries=a.max_t3_retries, permute_trials=a.permute_trials,
            dry_run=a.dry_run, skip_semantic=(a.cmd == "c-only"),
            header=a.header, limit=a.limit, src_subdir=a.src_subdir,
        )
    except RateLimitError as ex:
        print(f"[RATE_LIMIT] {ex}", file=sys.stderr, flush=True)
        return EXIT_RATE_LIMIT


if __name__ == "__main__":
    sys.exit(main())
