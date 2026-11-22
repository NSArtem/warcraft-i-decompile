"""Stateless, quota-aware Codex Plus (OpenAI CLI) backend for wc1.batch_driver and wc1.overnight.

Invokes `codex exec --json --output-schema ... --ignore-user-config --ignore-rules
--skip-git-repo-check -s read-only -C <stable_empty_dir>` so:
  - Codex never reads or modifies the repo checkout on Stage 1-4 (nor on structured repair);
  - User `~/.codex/config.toml` MCP servers, plugins, memories, and project `AGENTS.md` are excluded;
  - All calls within a module share one stable `-c model_instructions_file=...` prefix;
  - Rollout telemetry (`rate_limits.primary`/`secondary` and `reasoning_output_tokens`) is read
    separately from Claude (`build/live/rate_limits_codex.json` + `$CODEX_HOME/sessions/`),
    and observed quota metrics are strictly separated from historical guesstimations.
"""
import copy
import datetime
import glob
import json
import os
import re
import subprocess
import tempfile
import threading
import time

from . import live, path

STAGES = ("stage1", "stage2", "stage3", "stage4", "repair")

# V1 initial placeholder defaults; Phase 3 A/B benchmark overwrites this with the proven Pareto winner.
DEFAULT_MODEL = "gpt-6.2-sol"
DEFAULT_EFFORT = "low"
DEFAULT_STAGE_MATRIX = {
    "stage1": ("gpt-6.2-sol", "medium"),
    "stage2": ("gpt-6.2-sol", "low"),
    "stage3": ("gpt-6.2-sol", "medium"),
    "stage4": ("gpt-6.2-sol", "low"),
    "repair": ("gpt-6.2-sol", "medium"),
}

ALLOWED_EFFORTS = ("low", "medium", "high")
FORBIDDEN_EFFORTS = ("xhigh", "max", "ultra")
FORBIDDEN_MODEL_SUBSTRINGS = ("astra",)

DEFAULT_TELEMETRY_MAX_AGE_S = 1800  # 30 min freshness ceiling for short-window utilization

# Historical interactive-session guesstimation (pp of 5h primary per 1M weighted units:
# WU = fresh_in + 0.1 * cached_in + 4 * out). Strictly labeled as estimate; NEVER treated as observed.
ESTIMATED_PP_PER_1M_WU = {
    "gpt-6-luna": 4.6,
    "gpt-5.6-luna": 4.9,
    "gpt-6.1-terra": 15.0,   # unverified prior; refined in Phase 3
    "gpt-5.6-terra": 21.8,
    "gpt-6.2-sol": 20.5,
    "gpt-6.1-sol": 23.4,
    "gpt-6-sol": 21.7,
    "gpt-5.6-sol": 27.1,
}

# OpenAI Structured Outputs strict JSON Schema forbids these validation keywords
_UNSUPPORTED_STRICT_KEYWORDS = frozenset({
    "minItems", "maxItems", "uniqueItems", "contains",
    "minLength", "maxLength", "pattern", "format",
    "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf",
    "minProperties", "maxProperties", "patternProperties", "propertyNames",
    "unevaluatedProperties",
})

# Unexpected mutating / command tools that must never run during stateless JSON stages
_FORBIDDEN_TOOL_ITEM_TYPES = frozenset({
    "command_execution", "file_change", "mcp_tool_call", "web_search",
})

# Strict confirmed quota / rate-limit error patterns (avoid false positives on auth/net/CLI/schema)
_CODEX_RATE_LIMIT_RES = (
    re.compile(r"\busage_limit_(?:reached|exceeded)\b", re.I),
    re.compile(r"\brate_limit_(?:reached|exceeded)\b", re.I),
    re.compile(r"\byou(?:'ve|\s+have)\s+hit\s+your\s+(?:usage|rate)\s+limit\b", re.I),
    re.compile(r"\b(?:usage|rate)\s+limit\s+(?:reached|exceeded)\b", re.I),
    re.compile(r"\btoo\s+many\s+requests\b", re.I),
    re.compile(r"\bhttp(?:\s+status)?\s*429\b|\bstatus(?:\s+code)?\s*[:=]?\s*429\b|\berror\s+429\b", re.I),
    re.compile(r"\bquota\s+exceeded\b", re.I),
)

_NON_RATE_LIMIT_RES = (
    re.compile(r"\b401\b|\bunauthorized\b|\bnot\s+logged\s+in\b|\binvalid_api_key\b|\bauthentication\b", re.I),
    re.compile(r"\binvalid_json_schema\b|\bschema\s+validation\b|\bunrecognized\s+argument\b|\bunknown\s+option\b", re.I),
    re.compile(r"\bconnection\s+refused\b|\bdns\b|\bname\s+or\s+service\s+not\s+known\b|\btls\b|\beconnreset\b", re.I),
)


class CodexQuotaError(Exception):
    """Raised when Codex quota/telemetry gate blocks execution before a call."""
    def __init__(self, message, *, action="error", wait_seconds=0, resets_at=None):
        super().__init__(message)
        self.action = action
        self.wait_seconds = wait_seconds
        self.resets_at = resets_at


def validate_model_effort(model, effort):
    """Validate Codex model ID and reasoning_effort (excluding astra and xhigh/max/ultra)."""
    m = str(model or "").strip()
    e = str(effort or "").strip().lower()
    if not m:
        raise ValueError("Codex model cannot be empty")
    ml = m.lower()
    for bad in FORBIDDEN_MODEL_SUBSTRINGS:
        if bad in ml:
            raise ValueError(f"Model {m!r} is excluded from Codex Plus automation ({bad})")
    if e in FORBIDDEN_EFFORTS:
        raise ValueError(f"reasoning_effort {e!r} is excluded from Codex Plus automation")
    if e not in ALLOWED_EFFORTS:
        raise ValueError(f"Invalid Codex reasoning_effort {e!r}; expected one of {ALLOWED_EFFORTS}")
    return m, e


def parse_stage_spec(spec, default_model, default_effort):
    """Parse 'MODEL', 'MODEL:EFFORT', or ':EFFORT' into validated `(model, effort)`."""
    if not spec:
        return validate_model_effort(default_model, default_effort)
    s = str(spec).strip()
    if ":" in s:
        m_part, e_part = s.split(":", 1)
        model = m_part.strip() or default_model
        effort = e_part.strip() or default_effort
    else:
        if s.lower() in ALLOWED_EFFORTS or s.lower() in FORBIDDEN_EFFORTS:
            model = default_model
            effort = s
        else:
            model = s
            effort = default_effort
    return validate_model_effort(model, effort)


def build_stage_matrix(*, default_model=None, default_effort=None, overrides=None):
    """Build validated `{stage: (model, effort)}` dict for all 5 Codex stages."""
    overrides = overrides or {}
    matrix = {}
    for st in STAGES:
        base_m, base_e = DEFAULT_STAGE_MATRIX[st]
        dm = default_model if default_model else base_m
        de = default_effort if default_effort else base_e
        matrix[st] = parse_stage_spec(overrides.get(st), dm, de)
    return matrix


def format_stage_matrix(matrix):
    return " ".join(f"{st}={matrix[st][0]}:{matrix[st][1]}" for st in STAGES if st in matrix)


def strictify_schema(schema):
    """Convert a JSON Schema to OpenAI Structured Outputs strict mode (`strict: true`).

    Recursively:
      - Adds `additionalProperties: false` on every object schema;
      - Lists every key in `properties` inside `required`;
      - Strips unsupported keywords such as `minItems` / `maxItems`.
    """
    out = copy.deepcopy(schema)

    def _walk(node):
        if isinstance(node, list):
            for x in node:
                _walk(x)
            return
        if not isinstance(node, dict):
            return
        for kw in list(node.keys()):
            if kw in _UNSUPPORTED_STRICT_KEYWORDS:
                del node[kw]
        if node.get("type") == "object" or "properties" in node:
            node["type"] = "object"
            props = node.get("properties")
            if isinstance(props, dict):
                node["required"] = list(props.keys())
                for v in props.values():
                    _walk(v)
            else:
                node.setdefault("properties", {})
                node["required"] = []
            node["additionalProperties"] = False
        if "items" in node:
            _walk(node["items"])
        for comb in ("anyOf", "oneOf", "allOf"):
            if comb in node:
                _walk(node[comb])
        if "$defs" in node and isinstance(node["$defs"], dict):
            for v in node["$defs"].values():
                _walk(v)

    _walk(out)
    return out


# ---- Telemetry & quota helpers ----------------------------------------------

def codex_home_dir(codex_home=None):
    return codex_home or os.environ.get("CODEX_HOME") or os.path.expanduser("~/.codex")


def _parse_iso_ts(val):
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str) and val:
        try:
            dt = datetime.datetime.fromisoformat(val.replace("Z", "+00:00"))
            return dt.timestamp()
        except ValueError:
            return None
    return None


def _normalize_window(win):
    if not isinstance(win, dict):
        return None
    up = win.get("used_percent")
    if up is None:
        return None
    try:
        up_f = float(up)
    except (TypeError, ValueError):
        return None
    res = win.get("resets_at")
    try:
        res_f = float(res) if res is not None else None
    except (TypeError, ValueError):
        res_f = None
    wm = win.get("window_minutes")
    try:
        wm_i = int(wm) if wm is not None else None
    except (TypeError, ValueError):
        wm_i = None
    return {
        "used_percent": round(up_f, 2),
        "window_minutes": wm_i,
        "resets_at": res_f,
    }


def normalize_rate_limits(raw_rl, *, observed_at=None, source="unknown"):
    """Normalize a Codex `rate_limits` dict from rollout JSONL or stdout event."""
    if not isinstance(raw_rl, dict):
        return None
    p = _normalize_window(raw_rl.get("primary"))
    s = _normalize_window(raw_rl.get("secondary"))
    if p is None and s is None:
        return None
    obs = _parse_iso_ts(observed_at) if observed_at is not None else None
    if obs is None:
        obs = _parse_iso_ts(raw_rl.get("observed_at")) or time.time()
    out = {
        "observed_at": float(obs),
        "updated_at": time.time(),
        "source": str(source),
        "plan_type": raw_rl.get("plan_type"),
        "limit_id": raw_rl.get("limit_id"),
        "rate_limit_reached_type": raw_rl.get("rate_limit_reached_type"),
    }
    if p is not None:
        out["primary"] = p
    if s is not None:
        out["secondary"] = s
    return out


def find_rollout_for_thread(thread_id, codex_home=None):
    """Locate `$CODEX_HOME/sessions/**/rollout-*-<thread_id>.jsonl` if persisted."""
    if not thread_id:
        return None
    sessions_dir = os.path.join(codex_home_dir(codex_home), "sessions")
    if not os.path.isdir(sessions_dir):
        return None
    # Check today and yesterday first (O(1) fast path)
    now_dt = datetime.datetime.now()
    for delta_days in (0, 1):
        d = now_dt - datetime.timedelta(days=delta_days)
        day_dir = os.path.join(sessions_dir, f"{d.year:04d}", f"{d.month:02d}", f"{d.day:02d}")
        if os.path.isdir(day_dir):
            hits = glob.glob(os.path.join(day_dir, f"*{thread_id}*.jsonl"))
            if hits:
                return max(hits, key=os.path.getmtime)
    # Fallback recursive search
    hits = glob.glob(os.path.join(sessions_dir, "**", f"*{thread_id}*.jsonl"), recursive=True)
    if hits:
        return max(hits, key=os.path.getmtime)
    return None


def parse_rollout_telemetry(rollout_path):
    """Extract latest `(usage_dict, rate_limits_dict)` from a Codex session rollout JSONL."""
    usage = {}
    rl = None
    if not rollout_path or not os.path.isfile(rollout_path):
        return usage, rl
    bname = os.path.basename(rollout_path)
    try:
        file_mtime = os.path.getmtime(rollout_path)
    except OSError:
        file_mtime = time.time()
    try:
        with open(rollout_path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if '"token_count"' not in line and '"rate_limits"' not in line:
                    continue
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(rec, dict):
                    continue
                pay = rec.get("payload")
                if not isinstance(pay, dict):
                    continue
                if rec.get("type") == "event_msg" and pay.get("type") == "token_count":
                    info = pay.get("info")
                    if isinstance(info, dict):
                        tot = info.get("total_token_usage") or info.get("last_token_usage")
                        if isinstance(tot, dict):
                            usage = {
                                "input_tokens": int(tot.get("input_tokens") or 0),
                                "cached_input_tokens": int(tot.get("cached_input_tokens") or 0),
                                "output_tokens": int(tot.get("output_tokens") or 0),
                                "reasoning_output_tokens": int(tot.get("reasoning_output_tokens") or 0),
                            }
                    raw_rl = pay.get("rate_limits")
                    if isinstance(raw_rl, dict):
                        ts = _parse_iso_ts(rec.get("timestamp")) or file_mtime
                        norm = normalize_rate_limits(raw_rl, observed_at=ts, source=f"rollout:{bname}")
                        if norm:
                            rl = norm
    except OSError:
        pass
    return usage, rl


def read_latest_session_rate_limits(codex_home=None, max_files=16):
    """Scan the newest rollout JSONL files under `$CODEX_HOME/sessions/` for `rate_limits`."""
    sessions_dir = os.path.join(codex_home_dir(codex_home), "sessions")
    if not os.path.isdir(sessions_dir):
        return None
    files = glob.glob(os.path.join(sessions_dir, "**", "*.jsonl"), recursive=True)
    if not files:
        return None
    files.sort(key=lambda p: os.path.getmtime(p) if os.path.exists(p) else 0.0, reverse=True)
    best = None
    best_obs = -1.0
    for fpath in files[:max_files]:
        _u, rl = parse_rollout_telemetry(fpath)
        if rl and float(rl.get("observed_at") or 0.0) > best_obs:
            best = rl
            best_obs = float(rl["observed_at"])
    return best


def get_latest_rate_limits(root=None, codex_home=None):
    """Return the freshest normalized Codex rate-limit snapshot across live cache and sessions."""
    live_rl = live.load_codex_rate_limits(root=root)
    if not isinstance(live_rl, dict) or not (live_rl.get("primary") or live_rl.get("secondary")):
        live_rl = None
    sess_rl = read_latest_session_rate_limits(codex_home=codex_home)
    if live_rl and sess_rl:
        lo = float(live_rl.get("observed_at") or 0.0)
        so = float(sess_rl.get("observed_at") or 0.0)
        return sess_rl if so > lo else live_rl
    return live_rl or sess_rl or {}


def is_window_fresh(win, observed_at, now=None, max_age_s=DEFAULT_TELEMETRY_MAX_AGE_S):
    """Freshness check for Codex quota window telemetry (not just `resets_at > now`).

    Requires:
      1. Numeric `used_percent` in [0, 100];
      2. Numeric `resets_at > now` (window has not rolled over);
      3. `observed_at` within `max_age_s` of `now` (and not >60s in the future).
    """
    now_ts = time.time() if now is None else float(now)
    if not isinstance(win, dict):
        return False, "window missing"
    up = win.get("used_percent")
    res = win.get("resets_at")
    if up is None:
        return False, "used_percent missing"
    try:
        up_f = float(up)
    except (TypeError, ValueError):
        return False, "used_percent non-numeric"
    if not (0.0 <= up_f <= 100.0):
        return False, f"used_percent out of range ({up_f})"
    if res is None:
        return False, "resets_at missing"
    try:
        res_f = float(res)
    except (TypeError, ValueError):
        return False, "resets_at non-numeric"
    if res_f <= now_ts:
        return False, f"window already reset ({int(now_ts - res_f)}s ago)"
    if observed_at is None:
        return False, "observed_at missing"
    try:
        obs_f = float(observed_at)
    except (TypeError, ValueError):
        return False, "observed_at non-numeric"
    age = now_ts - obs_f
    if age < -60.0:
        return False, f"observed_at in future ({int(-age)}s)"
    if max_age_s is not None and age > float(max_age_s):
        return False, f"telemetry stale ({int(age)}s > max {int(max_age_s)}s)"
    return True, f"fresh ({int(max(0.0, age))}s old)"


def check_codex_quota_gate(rl, *, window_budget=0.8, now=None,
                           max_age_s=DEFAULT_TELEMETRY_MAX_AGE_S,
                           max_5h_pct=None, max_7d_pct=90.0,
                           max_7d_delta_pp=None, start_7d_pct=None,
                           total_calls_used=None, max_total_calls=None,
                           margin_seconds=60):
    """Mechanical per-call / pre-module Codex quota gate.

    Returns dict: `{"action": "ok"|"wait"|"stop_budget"|"error", "wait_seconds": int, "reason": str, "resets_at": float|None}`.
    """
    now_ts = time.time() if now is None else float(now)
    if not (0.0 < float(window_budget) <= 1.0):
        return {
            "action": "error", "wait_seconds": 0, "resets_at": None,
            "reason": f"--window-budget must be in (0.0, 1.0], got {window_budget}",
        }
    if max_total_calls is not None and total_calls_used is not None and int(total_calls_used) >= int(max_total_calls):
        return {
            "action": "stop_budget", "wait_seconds": 0, "resets_at": None,
            "reason": f"Codex total call cap reached ({total_calls_used} >= {max_total_calls})",
        }

    rl = rl if isinstance(rl, dict) else {}
    obs = rl.get("observed_at")
    primary = rl.get("primary") if isinstance(rl.get("primary"), dict) else None
    secondary = rl.get("secondary") if isinstance(rl.get("secondary"), dict) else None

    # 1. Check 7d (secondary) window whenever it has not rolled over yet
    if secondary and secondary.get("used_percent") is not None and secondary.get("resets_at") is not None:
        sec_res = float(secondary["resets_at"])
        sec_up = float(secondary["used_percent"])
        if sec_res > now_ts:
            if sec_up >= 100.0:
                wait_s = int(max(60, sec_res - now_ts + margin_seconds))
                return {
                    "action": "wait", "wait_seconds": wait_s, "resets_at": sec_res,
                    "reason": f"Codex 7d quota exhausted ({sec_up:.1f}%)",
                }
            if max_7d_pct is not None and sec_up >= float(max_7d_pct):
                return {
                    "action": "stop_budget", "wait_seconds": 0, "resets_at": sec_res,
                    "reason": f"Codex 7d quota {sec_up:.1f}% >= hard cap {float(max_7d_pct):.1f}%",
                }
            if max_7d_delta_pp is not None and start_7d_pct is not None:
                delta_7d = sec_up - float(start_7d_pct)
                if delta_7d >= float(max_7d_delta_pp):
                    return {
                        "action": "stop_budget", "wait_seconds": 0, "resets_at": sec_res,
                        "reason": (
                            f"Codex 7d delta +{delta_7d:.1f}pp (from {float(start_7d_pct):.1f}% to {sec_up:.1f}%) "
                            f">= cap +{float(max_7d_delta_pp):.1f}pp"
                        ),
                    }

    # 2. Check 5h (primary) window
    fresh_p, fresh_msg = is_window_fresh(primary, obs, now=now_ts, max_age_s=max_age_s)
    if float(window_budget) < 1.0:
        if not fresh_p:
            return {
                "action": "error", "wait_seconds": 0, "resets_at": None,
                "reason": (
                    f"Codex --window-budget {float(window_budget):.2f} (< 1.0) requires fresh confirmed "
                    f"short-window telemetry ({fresh_msg}); refusing to make a hidden probe call or "
                    f"fall back to USD. Re-run with --window-budget 1.0 or refresh Codex telemetry."
                ),
            }
        up_p = float(primary["used_percent"])
        res_p = float(primary["resets_at"])
        thresh = float(window_budget) * 100.0
        if max_5h_pct is not None:
            thresh = min(thresh, float(max_5h_pct))
        if up_p >= thresh or rl.get("rate_limit_reached_type"):
            wait_s = int(max(60, res_p - now_ts + margin_seconds))
            return {
                "action": "wait", "wait_seconds": wait_s, "resets_at": res_p,
                "reason": f"Codex 5h quota {up_p:.1f}% >= {thresh:.1f}% budget",
            }
        return {"action": "ok", "wait_seconds": 0, "resets_at": res_p, "reason": ""}

    # window_budget == 1.0: no pre-emptive short-window threshold; cold start allowed
    if fresh_p:
        up_p = float(primary["used_percent"])
        res_p = float(primary["resets_at"])
        if up_p >= 100.0 or rl.get("rate_limit_reached_type"):
            wait_s = int(max(60, res_p - now_ts + margin_seconds))
            return {
                "action": "wait", "wait_seconds": wait_s, "resets_at": res_p,
                "reason": f"Codex 5h quota exhausted ({up_p:.1f}%)",
            }
        if max_5h_pct is not None and float(max_5h_pct) < 100.0 and up_p >= float(max_5h_pct):
            return {
                "action": "stop_budget", "wait_seconds": 0, "resets_at": res_p,
                "reason": f"Codex 5h quota {up_p:.1f}% >= cap {float(max_5h_pct):.1f}%",
            }
    return {"action": "ok", "wait_seconds": 0, "resets_at": None, "reason": ""}


def estimate_primary_pp(model, usage):
    """Auxiliary guesstimation of 5h primary pp delta from tokens (NEVER treated as observed)."""
    u = usage or {}
    in_t = int(u.get("input_tokens") or 0)
    ca_t = int(u.get("cached_input_tokens") or 0)
    out_t = int(u.get("output_tokens") or 0)
    fresh = max(0, in_t - ca_t)
    wu = fresh + 0.1 * ca_t + 4.0 * out_t
    rate = ESTIMATED_PP_PER_1M_WU.get(str(model or ""), 20.5)
    return round(wu * rate / 1_000_000.0, 3)


def compute_window_delta(rl_before, rl_after, key):
    """Return observed `used_percent` delta if both snapshots share the same `resets_at`, else None."""
    if not isinstance(rl_before, dict) or not isinstance(rl_after, dict):
        return None
    w0 = rl_before.get(key)
    w1 = rl_after.get(key)
    if not isinstance(w0, dict) or not isinstance(w1, dict):
        return None
    if w0.get("used_percent") is None or w1.get("used_percent") is None:
        return None
    if w0.get("resets_at") is None or w1.get("resets_at") is None:
        return None
    if int(float(w0["resets_at"])) != int(float(w1["resets_at"])):
        return None
    return round(float(w1["used_percent"]) - float(w0["used_percent"]), 2)


# ---- Stream parsing & error classification ----------------------------------

def parse_codex_json_line(line):
    """Parse one JSONL line from `codex exec --json`.

    Returns normalized dict with `kind` in:
      `thread_started`, `turn_started`, `reasoning`, `agent_message`, `tool_violation`,
      `turn_completed`, `turn_failed`, `rate_limits`, `error`, `other`, or `None`.
    """
    s = (line or "").strip()
    if not s or not s.startswith("{"):
        return None
    try:
        obj = json.loads(s)
    except ValueError:
        return None
    if not isinstance(obj, dict):
        return None
    etype = str(obj.get("type") or "")
    if etype == "thread.started":
        return {"kind": "thread_started", "thread_id": obj.get("thread_id") or ""}
    if etype == "turn.started":
        return {"kind": "turn_started"}
    if etype == "turn.completed":
        return {"kind": "turn_completed", "usage": obj.get("usage") or {}, "rate_limits": obj.get("rate_limits")}
    if etype == "turn.failed":
        err = obj.get("error")
        msg = err.get("message") if isinstance(err, dict) else str(err or obj.get("message") or "")
        return {"kind": "turn_failed", "message": msg, "raw": obj}
    if etype == "error":
        return {"kind": "error", "message": str(obj.get("message") or obj.get("error") or ""), "raw": obj}
    if etype in ("item.started", "item.updated", "item.completed"):
        item = obj.get("item") if isinstance(obj.get("item"), dict) else {}
        itype = str(item.get("type") or "")
        if itype in _FORBIDDEN_TOOL_ITEM_TYPES:
            return {"kind": "tool_violation", "tool_type": itype, "item": item}
        if itype == "reasoning":
            txt = item.get("text") or ""
            return {"kind": "reasoning", "text": txt, "completed": etype == "item.completed"}
        if itype == "agent_message":
            txt = item.get("text") or ""
            return {"kind": "agent_message", "text": txt, "completed": etype == "item.completed"}
        return {"kind": "other", "raw": obj}
    if etype == "rate_limits" or (isinstance(obj.get("rate_limits"), dict)):
        norm = normalize_rate_limits(obj.get("rate_limits") or obj, source="codex_exec_json")
        if norm:
            return {"kind": "rate_limits", "rate_limits": norm}
    return {"kind": "other", "raw": obj}


def is_codex_rate_limit_error(rc, error_text, rl_after=None):
    """Strict rate-limit classifier for Codex CLI failures.

    Never mistakes ordinary CLI/auth/network/schema errors for quota exhaustion,
    and never flags a clean rc==0 response.
    """
    if rc == 0:
        return False
    txt = str(error_text or "")
    if any(rx.search(txt) for rx in _NON_RATE_LIMIT_RES):
        return False
    if isinstance(rl_after, dict) and rl_after.get("rate_limit_reached_type"):
        return True
    if any(rx.search(txt) for rx in _CODEX_RATE_LIMIT_RES):
        return True
    return False


def parse_codex_reset_text(text, now=None):
    """Extract a future unix timestamp from Codex rate-limit error text, or None if unknown."""
    if not text:
        return None
    now_ts = time.time() if now is None else float(now)
    s = str(text)

    # 1. Explicit unix timestamp `resets_at=1795347607` or `"resets_at": 1795347607`
    m_unix = re.search(r'"?resets_at"?\s*[:=]\s*(\d{10,12})', s)
    if m_unix:
        ts = float(m_unix.group(1))
        if ts > now_ts + 5:
            return ts

    # 2. ISO-8601 timestamp like `2026-11-22T15:30:00Z`
    m_iso = re.search(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2}))", s)
    if m_iso:
        ts = _parse_iso_ts(m_iso.group(1))
        if ts and ts > now_ts + 5:
            return ts

    # 3. Relative duration: "try again in 1h 23m" / "in 45 minutes" / "in 120 seconds" / "resets in 2 hours"
    m_rel = re.search(
        r"(?:try\s+again|resets?|retry)\s+in\s+"
        r"(?:(\d+)\s*(?:h|hr|hrs|hour|hours))?\s*"
        r"(?:(\d+)\s*(?:m|min|mins|minute|minutes))?\s*"
        r"(?:(\d+)\s*(?:s|sec|secs|second|seconds))?",
        s, re.I,
    )
    if m_rel and any(m_rel.groups()):
        h = int(m_rel.group(1) or 0)
        m = int(m_rel.group(2) or 0)
        sec = int(m_rel.group(3) or 0)
        total = h * 3600 + m * 60 + sec
        if total > 0:
            return now_ts + total

    return None


def extract_codex_reset_ts(error_text, rl_info=None, now=None):
    """Best-effort confirmed future reset timestamp from telemetry or error text; None if unknown."""
    now_ts = time.time() if now is None else float(now)
    rl = rl_info if isinstance(rl_info, dict) else {}
    # Prefer the exhausted window's resets_at (secondary first if exhausted, then primary)
    for key in ("secondary", "primary"):
        win = rl.get(key)
        if isinstance(win, dict) and win.get("resets_at"):
            res = float(win["resets_at"])
            up = win.get("used_percent")
            if res > now_ts + 5 and (up is not None and float(up) >= 100.0):
                return res
    if rl.get("rate_limit_reached_type"):
        for key in ("primary", "secondary"):
            win = rl.get(key)
            if isinstance(win, dict) and win.get("resets_at"):
                res = float(win["resets_at"])
                if res > now_ts + 5:
                    return res
    parsed = parse_codex_reset_text(error_text, now=now_ts)
    if parsed and parsed > now_ts + 5:
        return parsed
    # Fallback to fresh primary resets_at ONLY if observed very recently (<= 120s)
    obs = rl.get("observed_at")
    if obs is not None and (now_ts - float(obs)) <= 120.0:
        for key in ("primary", "secondary"):
            win = rl.get(key)
            if isinstance(win, dict) and win.get("resets_at") and float(win["resets_at"]) > now_ts + 5:
                return float(win["resets_at"])
    return None


# ---- Process execution ------------------------------------------------------

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


def _prepare_codex_sys_prompt(sys_prompt_file):
    """Create a deterministic Codex system-instructions file adding strict no-tool rules."""
    base_txt = open(sys_prompt_file, encoding="utf-8", errors="replace").read() if os.path.exists(sys_prompt_file) else ""
    no_tools_addon = (
        "\n\n## HEADLESS EXECUTION CONTRACT (MANDATORY)\n"
        "- Do NOT call any tools, shell commands, file tools, or subagents.\n"
        "- Everything you need is already provided in these instructions and the user prompt.\n"
        "- Reply directly with ONLY the single JSON object matching the required output schema.\n"
    )
    out_path = os.path.splitext(sys_prompt_file)[0] + "_codex.txt"
    content = base_txt.rstrip() + no_tools_addon
    if not os.path.exists(out_path) or open(out_path, encoding="utf-8", errors="replace").read() != content:
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(content)
    return out_path


def _stable_empty_cwd(root=None):
    d = os.path.join(root, "build", "driver", "codex_empty_cwd") if root else path("build", "driver", "codex_empty_cwd")
    os.makedirs(d, exist_ok=True)
    return os.path.abspath(d)


def call_codex(prompt, schema, sys_prompt_file, *, model=DEFAULT_MODEL, effort=DEFAULT_EFFORT,
               ledger=None, label="", max_calls=None, timeout=300, worker_id=None,
               codex_bin=None, codex_home=None, quota_guard=None, root=None):
    """Invoke stateless `codex exec --json --output-schema ...` with strict isolation & quota guards.

    Returns `(out_obj, meta_dict)` where `meta_dict` separates observed tokens/rate_limits from estimates.
    Raises `CodexQuotaError` (pre-call gate), or caller-mapped exceptions via `batch_driver` wrappers.
    """
    model, effort = validate_model_effort(model, effort)
    codex_bin = codex_bin or os.environ.get("WC1_CODEX_BIN") or "codex"

    if ledger is not None and max_calls is not None:
        if ledger.total_calls(provider="codex") >= int(max_calls):
            raise CodexQuotaError(
                f"codex calls {ledger.total_calls(provider='codex')} >= limit {max_calls}",
                action="stop_budget",
            )

    rl_before = get_latest_rate_limits(root=root, codex_home=codex_home)
    if quota_guard is not None:
        gate = check_codex_quota_gate(rl_before, **quota_guard)
        if gate["action"] != "ok":
            raise CodexQuotaError(
                gate["reason"],
                action=gate["action"],
                wait_seconds=gate["wait_seconds"],
                resets_at=gate["resets_at"],
            )

    wid = worker_id or os.environ.get("WC1_LIVE_WORKER") or (label.split(":", 1)[0] if ":" in label else label)
    if wid:
        live.update_worker_meta(wid, root=root, phase="THINKING", label=label,
                                model=model, effort=effort, provider="codex")
        live.append_event(wid, "stage", f"Calling Codex ({label}) [{model}/{effort}]...", root=root)

    strict_schema = strictify_schema(schema)
    codex_sys = _prepare_codex_sys_prompt(sys_prompt_file)
    empty_cwd = _stable_empty_cwd(root=root)

    schema_fd, schema_path = tempfile.mkstemp(prefix="wc1_codex_schema_", suffix=".json")
    out_fd, out_msg_path = tempfile.mkstemp(prefix="wc1_codex_out_", suffix=".txt")
    os.close(schema_fd)
    os.close(out_fd)
    try:
        with open(schema_path, "w", encoding="utf-8") as fh:
            json.dump(strict_schema, fh, separators=(",", ":"))

        cmd = [
            codex_bin, "exec",
            "--json",
            "--color", "never",
            "--ignore-user-config",
            "--ignore-rules",
            "--skip-git-repo-check",
            "-s", "read-only",
            "-C", empty_cwd,
            "-m", model,
            "-c", f"model_reasoning_effort={json.dumps(effort)}",
            "-c", 'approval_policy="never"',
            "-c", "project_doc_max_bytes=0",
            "-c", "include_environment_context=false",
            "-c", f"model_instructions_file={json.dumps(os.path.abspath(codex_sys))}",
            "-c", 'web_search="disabled"',
            "-c", "features.shell_tool=false",
            "-c", "features.unified_exec=false",
            "-c", "features.plugins=false",
            "-c", "features.apps=false",
            "-c", "features.memories=false",
            "-c", "features.multi_agent=false",
            "-c", "features.view_image=false",
            "-c", "features.hooks=false",
            "-c", "features.skill_search=false",
            "-c", "features.goals=false",
            "-c", "features.sleep_tool=false",
            "-c", "features.computer_use=false",
            "-c", "features.browser_use=false",
            "-c", "features.image_generation=false",
            "-c", "features.tool_suggest=false",
            "--output-schema", schema_path,
            "-o", out_msg_path,
            "-",
        ]
        env = os.environ.copy()
        if codex_home:
            env["CODEX_HOME"] = codex_home

        t0 = time.time()
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            start_new_session=True,
            env=env,
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

        thread_id = ""
        usage = {}
        stdout_rl = None
        last_agent_text = ""
        error_msgs = []
        tool_violations = []
        raw_lines = []

        try:
            assert proc.stdout is not None
            for raw_line in proc.stdout:
                line = raw_line.strip()
                if not line:
                    continue
                raw_lines.append(line)
                if len(raw_lines) > 25:
                    raw_lines.pop(0)
                ev = parse_codex_json_line(line)
                if not ev:
                    continue
                k = ev["kind"]
                if k == "thread_started":
                    thread_id = ev["thread_id"]
                elif k == "reasoning":
                    if ev["text"].strip() and wid:
                        live.append_event(wid, "think", ev["text"].strip()[:240], root=root)
                elif k == "agent_message":
                    if ev["text"]:
                        last_agent_text = ev["text"]
                elif k == "tool_violation":
                    tool_violations.append(ev["tool_type"])
                    if wid:
                        live.append_event(wid, "error", f"Codex attempted forbidden tool: {ev['tool_type']}", root=root)
                elif k == "turn_completed":
                    if isinstance(ev.get("usage"), dict):
                        usage = dict(ev["usage"])
                    if isinstance(ev.get("rate_limits"), dict):
                        norm = normalize_rate_limits(ev["rate_limits"], source="codex_exec_json")
                        if norm:
                            stdout_rl = norm
                elif k == "rate_limits":
                    stdout_rl = ev["rate_limits"]
                elif k in ("turn_failed", "error"):
                    if ev.get("message"):
                        error_msgs.append(ev["message"])
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

        elapsed = round(time.time() - t0, 2)
        err_txt = "".join(stderr_chunks).strip()

        # Enrich usage & rate_limits from persisted rollout file for this thread_id
        rollout_rl = None
        rollout_usage = {}
        if thread_id:
            rpath = find_rollout_for_thread(thread_id, codex_home=codex_home)
            if rpath:
                rollout_usage, rollout_rl = parse_rollout_telemetry(rpath)

        rl_after = stdout_rl or rollout_rl
        if rl_after:
            live.save_codex_rate_limits(rl_after, root=root)
            if wid:
                p5 = (rl_after.get("primary") or {}).get("used_percent")
                s7 = (rl_after.get("secondary") or {}).get("used_percent")
                if p5 is not None or s7 is not None:
                    live.append_event(wid, "info", f"Codex quota update: 5h={p5}% 7d={s7}%", root=root)

        if timed_out.is_set():
            if ledger:
                ledger.record("codex_timeout", provider="codex", label=label,
                              model=model, effort=effort, timeout=timeout, ok=False)
            if wid:
                live.append_event(wid, "error", f"Codex timed out after {timeout}s ({label})", root=root)
            raise TimeoutError(f"codex exec timed out ({label}, {timeout}s)")

        if tool_violations:
            msg = f"codex exec attempted forbidden tool(s) during stateless call ({label}): {sorted(set(tool_violations))}"
            if ledger:
                ledger.record("codex_error", provider="codex", label=label,
                              model=model, effort=effort, msg=msg[:240], ok=False)
            raise RuntimeError(msg)

        combined_err = "\n".join(x for x in (*error_msgs, err_txt) if x).strip()
        if proc.returncode != 0 or (error_msgs and not last_agent_text):
            msg = combined_err or "\n".join(raw_lines[-5:])[:300]
            if is_codex_rate_limit_error(proc.returncode, msg, rl_after=rl_after):
                resets_at = extract_codex_reset_ts(msg, rl_info=(rl_after or rl_before))
                if ledger:
                    ledger.record("rate_limit", provider="codex", label=label,
                                  model=model, effort=effort, msg=msg[:240],
                                  resets_at=resets_at, ok=False)
                if wid:
                    live.append_event(wid, "error", f"CODEX RATE LIMIT: {msg[:180]}", root=root)
                raise CodexQuotaError(msg[:240], action="wait", resets_at=resets_at)
            if ledger:
                ledger.record("codex_error", provider="codex", label=label,
                              model=model, effort=effort, rc=proc.returncode, msg=msg[:240], ok=False)
            if wid:
                live.append_event(wid, "error", f"Codex error (rc={proc.returncode}): {msg[:180]}", root=root)
            raise RuntimeError(f"codex exec failed ({label}, rc={proc.returncode}): {msg[:300]}")

        # Recover final structured JSON from agent_message or `-o` output-last-message file
        out_text = last_agent_text.strip()
        if not out_text and os.path.isfile(out_msg_path):
            out_text = open(out_msg_path, encoding="utf-8", errors="replace").read().strip()
        if not out_text:
            raise RuntimeError(f"codex exec returned empty output ({label})")
        try:
            out_obj = json.loads(out_text)
        except ValueError as ex:
            raise RuntimeError(f"codex exec returned invalid JSON ({label}): {ex} ({out_text[:200]})") from ex
        if not isinstance(out_obj, dict):
            raise RuntimeError(f"codex exec JSON root is not object ({label})")

        # Merge observed tokens (stdout turn.completed + rollout reasoning_output_tokens)
        in_tok = int(usage.get("input_tokens") or rollout_usage.get("input_tokens") or 0)
        ca_tok = int(usage.get("cached_input_tokens") or rollout_usage.get("cached_input_tokens") or 0)
        out_tok = int(usage.get("output_tokens") or rollout_usage.get("output_tokens") or 0)
        reas_tok = int(usage.get("reasoning_output_tokens") or rollout_usage.get("reasoning_output_tokens") or 0)
        cache_pct = round(100.0 * ca_tok / max(1, in_tok), 1) if in_tok > 0 else 0.0
        merged_usage = {
            "input_tokens": in_tok,
            "cached_input_tokens": ca_tok,
            "output_tokens": out_tok,
            "reasoning_output_tokens": reas_tok,
            "cache_hit_pct": cache_pct,
        }

        p_delta = compute_window_delta(rl_before, rl_after, "primary")
        s_delta = compute_window_delta(rl_before, rl_after, "secondary")
        est_p = estimate_primary_pp(model, merged_usage)
        telemetry_obs = bool(rl_after and (rl_after.get("primary") or rl_after.get("secondary")))

        meta = {
            "provider": "codex",
            "model": model,
            "effort": effort,
            "elapsed_s": elapsed,
            "thread_id": thread_id,
            "usage": merged_usage,
            "telemetry_observed": telemetry_obs,
            "rate_limits_before": rl_before if rl_before else None,
            "rate_limits_after": rl_after,
            "primary_delta_pp": p_delta,
            "secondary_delta_pp": s_delta,
            "estimated_primary_pp": est_p,
        }

        if ledger:
            ledger.record(
                "codex_call",
                provider="codex",
                label=label,
                model=model,
                effort=effort,
                elapsed_s=elapsed,
                thread_id=thread_id,
                usage=merged_usage,
                telemetry_observed=telemetry_obs,
                primary_used_pct=(rl_after.get("primary") or {}).get("used_percent") if rl_after else None,
                secondary_used_pct=(rl_after.get("secondary") or {}).get("used_percent") if rl_after else None,
                primary_delta_pp=p_delta,
                secondary_delta_pp=s_delta,
                estimated_primary_pp=est_p,
            )

        q_str = (
            f"5h={(rl_after.get('primary') or {}).get('used_percent')}% "
            f"(d={p_delta if p_delta is not None else '?'}pp) "
            f"7d={(rl_after.get('secondary') or {}).get('used_percent')}%"
            if telemetry_obs
            else f"5h=unobserved (est~{est_p:.2f}pp)"
        )
        summary_line = (
            f"  [codex {label}] {model}/{effort} {elapsed}s "
            f"in={in_tok} cached={ca_tok} ({cache_pct}%) out={out_tok} reas={reas_tok} | {q_str}"
        )
        print(summary_line, flush=True)
        if wid:
            live.append_event(wid, "info", summary_line.strip(), root=root)
        return out_obj, meta
    finally:
        for p_tmp in (schema_path, out_msg_path):
            if os.path.exists(p_tmp):
                try:
                    os.unlink(p_tmp)
                except OSError:
                    pass
