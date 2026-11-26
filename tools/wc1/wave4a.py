"""Wave 4A: Symbol and dependency reconciliation orchestrator.

Eliminates unresolved relocation, symbol, ABI, and data-reference blockers across
in-scope T4 functions before Wave 4B spends LLM calls on codegen recovery:

  1. Maintains an incremental per-unit audit state (`build/wave4/audit_state.json`)
     seeded from `build/t3_audit/report.json` and refreshed lazily/incrementally
     for ONLY the T4 units whose source/includes or referenced symbols changed.
  2. Auto-promotes any already `MATCH_BUILDABLE` T4 unit (0 LLM calls).
  3. Applies conservative, syntax-aware mechanical reconciliations for proven-safe
     stale function/data references (0 LLM calls), validating with Watcom 10.0a +
     OW2 compile checks, targeted `wc1.t3_audit`, and cited T4 difftests.
  4. Runs narrowly scoped, fresh-context bounded LLM research for non-mechanical
     blockers (ABI mismatches, interior fields of containing data objects, missing
     functions/data, ambiguous targets), grouping all callers of one target into
     one shared task.
  5. Reprocesses newly unblocked T4 files automatically, promotes every newly
     `MATCH_BUILDABLE` object via `wc1.wave4.promote`, and accepts verified
     reconciliation-only progress (`RECONCILED`) when unresolved relocations
     strictly decrease with zero regressions.
"""
from collections import defaultdict
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import tomllib

from . import batch_driver, match, oldcc, path, symbols, t3_audit, wave4, wave4_deps, wave4_fp

PROMOTED = "PROMOTED"
RECONCILED = "RECONCILED"
NO_IMPROVEMENT = "NO_IMPROVEMENT"
AMBIGUOUS = "AMBIGUOUS"
FAILED = "FAILED"
TOOLCHAIN_ERROR = "TOOLCHAIN_ERROR"
OUTCOMES = (PROMOTED, RECONCILED, NO_IMPROVEMENT, AMBIGUOUS, FAILED, TOOLCHAIN_ERROR)

RECONCILE_VERSION = 2
CODEX_RESEARCH_STAGE = "stage4"
CLAUDE_RESEARCH = ("sonnet", "medium")

OUT_DIR = ("build", "wave4")
AUDIT_STATE_FILE = ("build", "wave4", "audit_state.json")
MAPPINGS_FILE = ("build", "wave4", "mappings.json")

RESEARCH_SCHEMA = {
    "type": "object",
    "properties": {
        "decision": {
            "type": "string",
            "enum": ["apply", "ambiguous", "defer"],
            "description": "apply if a verified reconciliation patch can be proposed; ambiguous/defer otherwise",
        },
        "summary": {
            "type": "string",
            "description": "Concise evidence-backed summary of the dependency resolution or blocker",
        },
        "uncertainties": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Any remaining uncertainties or reasons for ambiguity/deferral",
        },
        "toml_entries": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "toml_file": {"type": "string", "description": "Repo-relative analysis/symbols/<area>.toml"},
                    "toml_block": {"type": "string", "description": "Complete [[func]] or [[data]] TOML table(s) to append"},
                },
                "required": ["toml_file", "toml_block"],
            },
        },
        "file_patches": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Repo-relative path from the allowed files list"},
                    "old": {"type": "string", "description": "Exact existing substring occurring once (empty ONLY to create a new header)"},
                    "new": {"type": "string", "description": "Replacement text"},
                },
                "required": ["path", "old", "new"],
            },
        },
    },
    "required": ["decision", "summary", "uncertainties", "toml_entries", "file_patches"],
}

RESEARCH_RULES = (
    "You reconcile unresolved external symbols, ABI declarations, and data references for Warcraft I (Watcom 10.0a C89).\n"
    "Base EVERY claim on the provided original disassembly, LE fixups, data bytes, and symbol database entries.\n"
    "HARD RULES:\n"
    "- NEVER invent an address or assume correctness from a symbol's spelling alone.\n"
    "- NEVER create a duplicate [[data]] symbol for an interior field of an existing containing data object (use owner[i].field or typed pointer offset).\n"
    "- NEVER set src=, ref=, ref_verified_by=, t3_blocker=, or confidence='verified' in TOML (the runner promotes verified matches mechanically).\n"
    "- Every new [[func]]/[[data]] entry must have valid addr, name, confidence ('high'|'medium'|'low'), non-empty evidence citing addresses/instructions, and proto/conv or type.\n"
    "- NEVER modify /* codegen-compiler: */ or /* codegen-flags: */ headers.\n"
    "- NEVER edit src/include/war.h, analysis/symbols/codegen_promo.toml, Makefile, or tools/.\n"
    "- Keep every C `extern` declaration on ONE single line and valid under both Watcom 10.0a and Open Watcom 2.\n"
    "- ONLY patch a listed test file when an ABI or canonical symbol update strictly requires a harness adjustment (e.g. T4Stub log_regs or EXTRA); NEVER weaken inputs, drop cases, or add skip/xfail/raises.\n"
    "- If the target is genuinely ambiguous or cannot be proven from the evidence, return decision='ambiguous' with clear uncertainties and empty patches.\n"
)


# ---------------------------------------------------------------------------
# Atomic JSON & receipt helpers
# ---------------------------------------------------------------------------

def _write_json(fn, rec):
    os.makedirs(os.path.dirname(fn), exist_ok=True)
    tmp = f"{fn}.tmp.{os.getpid()}"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, indent=1, sort_keys=True, default=str)
    os.replace(tmp, fn)


def _read_json(fn):
    try:
        with open(fn, encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def outcome_file(group_id):
    return path(*OUT_DIR, "reconcile_outcomes", f"{group_id}.json")


def write_outcome(group_id, outcome, **data):
    rec = dict(
        data,
        group_id=group_id,
        outcome=outcome,
        ts=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )
    _write_json(outcome_file(group_id), rec)
    return rec


def read_outcome(group_id):
    return _read_json(outcome_file(group_id))


def clear_outcome(group_id):
    fn = outcome_file(group_id)
    if not os.path.exists(fn):
        return
    archive = path(*OUT_DIR, "reconcile_history", group_id)
    os.makedirs(archive, exist_ok=True)
    try:
        os.replace(fn, os.path.join(archive, f"{time.time_ns()}.json"))
    except FileNotFoundError:
        pass


# ---------------------------------------------------------------------------
# Persistent established mappings store
# ---------------------------------------------------------------------------

def load_mappings():
    data = _read_json(path(*MAPPINGS_FILE))
    return data if isinstance(data, dict) else {"version": RECONCILE_VERSION, "mappings": {}}


def record_mapping(old_symbol, target_addr, canonical_link, canonical_name, kind, method):
    store = load_mappings()
    store.setdefault("mappings", {})[old_symbol] = {
        "target_addr": int(target_addr) if target_addr is not None else None,
        "target_addr_hex": f"{int(target_addr):#x}" if target_addr is not None else None,
        "canonical_link": canonical_link,
        "canonical_name": canonical_name,
        "kind": kind,
        "method": method,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    _write_json(path(*MAPPINGS_FILE), store)


def persist_outcome_mappings(outcome):
    """Persist verified candidate mappings from a committed Wave 4A outcome into `mappings.json`."""
    if not isinstance(outcome, dict):
        return 0
    written = 0
    for m in outcome.get("proposed_mappings") or ():
        if not isinstance(m, dict) or not m.get("old_symbol") or not m.get("canonical_link"):
            continue
        record_mapping(
            m["old_symbol"], m.get("target_addr"),
            m["canonical_link"], m.get("canonical_name"),
            m.get("kind") or "data", m.get("method") or "reconcile",
        )
        written += 1
    return written


# ---------------------------------------------------------------------------
# Incremental dependency-aware audit state (Phase 3.4 & Phase 5)
# ---------------------------------------------------------------------------

def _unit_source_digest(ref_rel, repo_root=None):
    """Hash a ref C file and its recursively included headers; returns None on
    any conservative preprocessor failure (never silently ignores headers)."""
    dig, _hashes, _err = wave4_fp.unit_source_digest(ref_rel, repo_root=repo_root or path())
    return dig


def _row_dep_snapshot(row, by_link):
    """Map every symbol relevant to `row` (its link_name, unresolved symbols, and
    exact OMF external/_TEXT symbols when available) to its current DB address."""
    syms = {row.get("link_name")}
    for att in row.get("attempts") or ():
        for u in att.get("unresolved") or ():
            if u.get("symbol"):
                syms.add(u["symbol"])
    omf_d = row.get("omf_deps")
    if isinstance(omf_d, dict):
        syms.update(omf_d.get("external_symbols") or ())
        syms.update(omf_d.get("text_symbols") or ())
    syms.discard(None)
    syms.discard("")
    return {s: (by_link[s]["addr"] if s in by_link else None) for s in sorted(syms)}


def _unit_extents_snapshot(cs, starts_by_addr):
    out = {}
    for c in cs:
        a = c.get("addr")
        f = starts_by_addr.get(a)
        out[str(a)] = [f["start"], f.get("end")] if f else [a, None]
    return out


def _tool_signature():
    try:
        cc_root = Path(oldcc.root())
        files = [Path(path("original", "install", "war.exe")),
                 cc_root / "binnt/wcc386.exe", cc_root / "binb/wcc386.exe"]
        return hashlib.sha256(b"".join(hashlib.sha256(f.read_bytes()).digest() for f in files)).hexdigest()
    except OSError:
        return None


def _git_changed_src_analysis_since(commit_hash):
    """Return `(ok, changed_paths_set)` for `src/` and `analysis/` between `commit_hash` and working tree."""
    if not commit_hash:
        return False, set()
    try:
        r1 = subprocess.run(
            ["git", "diff", "--name-only", commit_hash, "--", "src", "analysis"],
            cwd=path(), capture_output=True, text=True, timeout=15,
        )
        r2 = subprocess.run(
            ["git", "status", "--porcelain", "--", "src", "analysis"],
            cwd=path(), capture_output=True, text=True, timeout=15,
        )
        if r1.returncode != 0 or r2.returncode != 0:
            return False, set()
        changed = {l.strip().replace("\\", "/") for l in r1.stdout.splitlines() if l.strip()}
        for l in r2.stdout.splitlines():
            if len(l) >= 4:
                changed.add(l[3:].strip().replace("\\", "/"))
        return True, changed
    except (OSError, subprocess.SubprocessError):
        return False, set()


def load_audit_report_incremental(inputs=None, report_file=None, refresh_stale=True,
                                  objdir=None, log=None):
    """Return an up-to-date audit report dict for all eligible T4 functions.

    Uses `build/wave4/audit_state.json` (bootstrapped from `build/t3_audit/report.json`
    when available), refreshing ONLY those T4 units whose source/includes changed,
    whose referenced symbols entered/changed in `by_link`, or that are missing from
    the cached state. Never invalidates the entire audit because HEAD moved or
    unrelated tools/tests changed.
    """
    p, funcs, by_link, rows, issues = inputs or t3_audit.load_inputs()
    cands, _d_issues = t3_audit.discover(funcs, rows)
    t4_cands = [c for c in cands if wave4.eligible(c)]
    t4_by_addr = {c["addr"]: c for c in t4_cands}
    units_by_ref = defaultdict(list)
    for c in t4_cands:
        units_by_ref[c["ref"]].append(c)

    tool_sig = _tool_signature()
    state_path = path(*AUDIT_STATE_FILE)
    state = _read_json(state_path)
    starts_by_addr = {
        f["start"]: f for f in (getattr(p, "functions", None) or [])
        if isinstance(f, dict) and "start" in f
    }
    cur_known_links = {s: e["addr"] for s, e in by_link.items() if isinstance(e.get("addr"), int)}
    if not state or (tool_sig and state.get("tool_sig") != tool_sig):
        state = {
            "version": RECONCILE_VERSION, "tool_sig": tool_sig,
            "known_links": dict(cur_known_links), "results": {}, "unit_meta": {},
        }
        # Bootstrap from build/t3_audit/report.json if complete (regardless of HEAD/tools changes)
        rep_fn = report_file or wave4.report_path()
        rep = _read_json(rep_fn)
        rep_meta = (rep or {}).get("meta") or {}
        rep_opts = rep_meta.get("options") if isinstance(rep_meta.get("options"), dict) else {}
        rep_tc = rep_meta.get("toolchain") if isinstance(rep_meta.get("toolchain"), dict) else {}
        rep_tool = rep_tc.get("tool_sig")
        stale_rep = bool(
            ("presets" in rep_opts and rep_opts["presets"] != t3_audit.current_presets())
            or ("base_flags" in rep_opts and rep_opts["base_flags"] != match.BASE_CFLAGS)
            or ("plan" in rep_opts and "presets" not in rep_opts)
            or (rep_tool is not None and tool_sig is not None and rep_tool != tool_sig)
        )
        if rep and not stale_rep and (rep.get("meta") or {}).get("completion", {}).get("status") == "complete":
            for r in rep.get("results", []):
                if (r.get("tier") == "T4" and isinstance(r.get("addr"), int)
                        and r.get("audited") is not False
                        and r.get("status") not in ("SKIPPED", "TOOLCHAIN_ERROR")):
                    state["results"][str(r["addr"])] = r
            rep_commit = (rep.get("meta") or {}).get("git_commit")
            ok_diff, changed_sa = _git_changed_src_analysis_since(rep_commit)
            if ok_diff and not (rep.get("meta") or {}).get("git_dirty"):
                changed_headers = {x for x in changed_sa if x.endswith(".h")}
                changed_tomls = {x for x in changed_sa if x.startswith("analysis/symbols/")}
                for ref, cs in units_by_ref.items():
                    if ref in changed_sa:
                        continue
                    if changed_headers:
                        incs = set(wave4_deps._resolve_local_includes(ref, path()))
                        if incs & changed_headers:
                            continue
                    if changed_tomls and any(c.get("toml") in changed_tomls for c in cs):
                        continue
                    if any(str(c["addr"]) not in state["results"] for c in cs):
                        continue
                    dig = _unit_source_digest(ref)
                    if dig is None:
                        continue
                    deps_snap = {}
                    unit_omf = None
                    for c in cs:
                        rr = state["results"].get(str(c["addr"]))
                        if rr:
                            deps_snap.update(_row_dep_snapshot(rr, by_link))
                            if unit_omf is None and isinstance(rr.get("omf_deps"), dict):
                                unit_omf = rr["omf_deps"]
                    if changed_tomls and any(v is not None for s, v in deps_snap.items()
                                             if s not in {c["link_name"] for c in cs}):
                        continue
                    meta_boot = {
                        "source_digest": dig,
                        "deps": deps_snap,
                        "cand_addrs": sorted(c["addr"] for c in cs),
                        "extents": _unit_extents_snapshot(cs, starts_by_addr),
                        "plan": [list(x) for x in t3_audit.attempt_plan(cs[0].get("declared_cflags"))],
                    }
                    if unit_omf is not None:
                        stamped = wave4_fp.stamp_omf_deps(
                            ref, unit_omf,
                            declared_cflags=cs[0].get("declared_cflags"),
                            tool_sig=tool_sig,
                            source_digest=dig,
                            repo_root=path(),
                        )
                        if stamped is not None:
                            meta_boot["omf_deps"] = stamped
                            state.setdefault("omf_deps_cache", {})[ref] = stamped
                            for c in cs:
                                rr = state["results"].get(str(c["addr"]))
                                if rr is not None:
                                    rr["omf_deps"] = stamped
                    state["unit_meta"][ref] = meta_boot

    # Detect previously-resolved symbols that were removed or moved to another address
    old_known = state.get("known_links") or {}
    removed_or_moved = {
        s for s, old_a in old_known.items()
        if cur_known_links.get(s) != old_a
    }
    moved_idents = set()
    for s in removed_or_moved:
        moved_idents.add(wave4_deps.link_to_c_ident(s, kind="function"))
        moved_idents.add(wave4_deps.link_to_c_ident(s, kind="data"))
    moved_idents.discard("")

    # Prune entries no longer T4 (e.g. promoted to T3)
    live_keys = {str(a) for a in t4_by_addr}
    for k in list(state["results"].keys()):
        if k not in live_keys:
            state["results"].pop(k, None)
    for ref in list(state["unit_meta"].keys()):
        if ref not in units_by_ref:
            state["unit_meta"].pop(ref, None)

    # Identify stale or missing T4 units
    env_override = wave4_fp.env_override_reason()
    stale_refs = []
    for ref, cs in sorted(units_by_ref.items()):
        if env_override:
            stale_refs.append(ref)
            continue
        meta = state["unit_meta"].get(ref)
        missing = any(str(c["addr"]) not in state["results"] for c in cs)
        if missing or not meta:
            stale_refs.append(ref)
            continue
        cur_dig = _unit_source_digest(ref)
        if cur_dig is None or cur_dig != meta.get("source_digest"):
            stale_refs.append(ref)
            continue
        cur_plan = t3_audit.attempt_plan(cs[0].get("declared_cflags"))
        if wave4_fp._has_unsafe_include_flags(cur_plan):
            stale_refs.append(ref)
            continue
        # Check if sibling set changed (when recorded)
        if "cand_addrs" in meta and sorted(c["addr"] for c in cs) != meta.get("cand_addrs"):
            stale_refs.append(ref)
            continue
        # Check if function boundaries/extents changed (when recorded)
        if "extents" in meta and _unit_extents_snapshot(cs, starts_by_addr) != meta.get("extents"):
            stale_refs.append(ref)
            continue
        # Check if attempt plan changed (the preset list is audit provenance, so a
        # preset change must invalidate even units with no recorded omf_deps)
        if meta.get("plan") != [list(x) for x in cur_plan]:
            stale_refs.append(ref)
            continue
        # Check if any previously unresolved/external symbol (or function link_name) changed in by_link
        old_deps = meta.get("deps") or {}
        if any((by_link[s]["addr"] if s in by_link else None) != old_addr for s, old_addr in old_deps.items()):
            stale_refs.append(ref)
            continue
        # Check if any previously-resolved symbol was removed/moved and appears in this unit's C/includes
        if moved_idents:
            unit_hit = False
            for inc in wave4_deps._resolve_local_includes(ref, path()):
                try:
                    txt = open(path(inc), encoding="latin-1").read()
                except OSError:
                    continue
                if any(re.search(rf"\b{re.escape(idn)}\b", txt) for idn in moved_idents):
                    unit_hit = True
                    break
            if unit_hit:
                stale_refs.append(ref)
                continue
        # Also check if any candidate metadata changed (cflags, cc, link_name, ref, test citation, TOML, name, module)
        for c in cs:
            rr = state["results"].get(str(c["addr"])) or {}
            if (rr.get("link_name") != c.get("link_name")
                    or rr.get("declared_cflags") != c.get("declared_cflags")
                    or rr.get("declared_cc") != c.get("declared_cc")
                    or rr.get("ref") != c.get("ref")
                    or rr.get("ref_verified_by") != c.get("ref_verified_by")
                    or rr.get("toml") != c.get("toml")
                    or rr.get("name") != c.get("name")
                    or rr.get("module") != c.get("module")):
                stale_refs.append(ref)
                break

    if refresh_stale and stale_refs:
        od = objdir or path(*OUT_DIR, "obj", "audit_state")
        shutil.rmtree(od, ignore_errors=True)
        ctx = t3_audit.Ctx(p, funcs, by_link, od)
        synced_omf = {}
        try:
            for ref in stale_refs:
                cs = units_by_ref[ref]
                if log:
                    log(f"[wave4a] refreshing audit for {ref} ({len(cs)} T4 fn)")
                out_rows = t3_audit.audit_unit(ctx, {"ref": ref, "cands": cs})
                deps_snap = {}
                unit_omf = None
                for rr in out_rows:
                    deps_snap.update(_row_dep_snapshot(rr, by_link))
                    if unit_omf is None and isinstance(rr.get("omf_deps"), dict):
                        unit_omf = rr["omf_deps"]
                src_dig = _unit_source_digest(ref)
                meta_rec = {
                    "source_digest": src_dig,
                    "deps": deps_snap,
                    "cand_addrs": sorted(c["addr"] for c in cs),
                    "extents": _unit_extents_snapshot(cs, starts_by_addr),
                    "plan": [list(x) for x in t3_audit.attempt_plan(cs[0].get("declared_cflags"))],
                }
                stamped = None
                if unit_omf is not None:
                    stamped = wave4_fp.stamp_omf_deps(
                        ref, unit_omf,
                        declared_cflags=cs[0].get("declared_cflags"),
                        tool_sig=tool_sig,
                        source_digest=src_dig,
                        repo_root=path(),
                    )
                    if stamped is not None:
                        meta_rec["omf_deps"] = stamped
                        state.setdefault("omf_deps_cache", {})[ref] = stamped
                        if stamped.get("complete") and stamped.get("source_digest"):
                            synced_omf[ref] = stamped
                for rr in out_rows:
                    if stamped is not None:
                        rr["omf_deps"] = stamped
                    state["results"][str(rr["addr"])] = rr
                state["unit_meta"][ref] = meta_rec
        finally:
            shutil.rmtree(od, ignore_errors=True)
        state["known_links"] = dict(cur_known_links)
        _write_json(state_path, state)
        if synced_omf:
            omf_path = path(*wave4_fp.OMF_DEPS_FILE)
            omf_store = _read_json(omf_path) or {"version": wave4_fp.CACHE_SCHEMA_VERSION, "units": {}}
            if not isinstance(omf_store.get("units"), dict):
                omf_store["units"] = {}
            omf_store["version"] = wave4_fp.CACHE_SCHEMA_VERSION
            for ref, st_d in synced_omf.items():
                omf_store["units"][ref.replace("\\", "/")] = st_d
            try:
                _write_json(omf_path, omf_store)
            except OSError:
                pass
    elif (not os.path.exists(state_path) or removed_or_moved) and state["results"]:
        if not stale_refs:
            state["known_links"] = dict(cur_known_links)
        _write_json(state_path, state)

    ordered = [state["results"][str(a)] for a in sorted(t4_by_addr) if str(a) in state["results"]]
    return {
        "schema": t3_audit.SCHEMA,
        "meta": {"completion": {"status": "complete"}, "incremental": True, "refreshed_units": len(stale_refs)},
        "results": ordered,
    }


def invalidate_audit_refs(refs=(), symbols_changed=()):
    """Mark specific ref files (and any unit referencing `symbols_changed`) stale in audit_state.json."""
    state_path = path(*AUDIT_STATE_FILE)
    state = _read_json(state_path)
    if not state:
        return 0
    ref_set = {str(r).replace("\\", "/") for r in (refs or ())}
    sym_set = set(symbols_changed or ())
    removed = 0
    for ref, meta in list((state.get("unit_meta") or {}).items()):
        deps = meta.get("deps") or {}
        if ref in ref_set or (sym_set and (sym_set & set(deps.keys()))):
            state["unit_meta"].pop(ref, None)
            removed += 1
    if removed:
        _write_json(state_path, state)
    return removed


# ---------------------------------------------------------------------------
# Input-sensitive Wave 4A retry cache
# ---------------------------------------------------------------------------

def _complete_reconcile_miss(result, group_id, max_calls):
    if (not isinstance(result, dict) or result.get("group_id") != group_id
            or result.get("outcome") not in (NO_IMPROVEMENT, AMBIGUOUS)
            or result.get("complete_search") is not True):
        return False
    calls = result.get("llm_calls")
    if type(calls) is not int:
        return False
    if result["outcome"] == NO_IMPROVEMENT and (max_calls < 1 or calls != max_calls):
        return False
    return isinstance(result.get("ts"), str)


class ReconcileCache:
    """Dependency-scoped retry suppression for Wave 4A misses and ambiguous dependencies (schema v2)."""

    def __init__(self, provider, model_effort, max_calls, max_cost=None):
        self.max_calls = int(max_calls)
        self.cache_schema = wave4_fp.CACHE_SCHEMA_VERSION
        self.settings = None
        self.init_bypass_reason = None
        self.skipped = 0
        self.diag = wave4_fp.CacheDiagnostics("wave4a")
        self.ow2_headers = wave4_fp.ow2_include_dir()
        env_reason = wave4_fp.env_override_reason()
        if env_reason:
            self.init_bypass_reason = env_reason
            return
        try:
            cc_root = Path(oldcc.root())
            self.system_headers = cc_root / "h"
            files = [Path(path("original", "install", "war.exe")),
                     cc_root / "binnt/wcc386.exe", cc_root / "binb/wcc386.exe"]
            self.settings = {
                "cache_schema": self.cache_schema,
                "version": RECONCILE_VERSION,
                "compiler": t3_audit.CC,
                "base_flags": match.BASE_CFLAGS,
                "tool_inputs": [hashlib.sha256(f.read_bytes()).hexdigest() for f in files],
                "ow2_compiler_sha256": wave4_fp.ow2_compiler_digest(),
                "provider": provider,
                "model_effort": list(model_effort),
                "max_calls": self.max_calls,
                "max_cost": max_cost if provider == "claude" else None,
            }
        except OSError:
            self.init_bypass_reason = "missing_tool_inputs"

    def begin_pass(self):
        self.skipped = 0
        self.diag.begin_pass()

    def compute_fingerprint(self, group, matcher_sig=None, *, dep_ctx=None):
        return wave4_fp.wave4a_fingerprint(
            self.settings, getattr(self, "system_headers", None), group,
            dep_ctx=dep_ctx, matcher_sig=matcher_sig,
            ow2_headers=self.ow2_headers,
            init_bypass_reason=self.init_bypass_reason, repo_root=path(),
        )

    def fingerprint(self, group, matcher_sig=None, *, dep_ctx=None):
        return self.compute_fingerprint(group, matcher_sig=matcher_sig, dep_ctx=dep_ctx).key

    def _dir(self, group_id):
        return path(*OUT_DIR, "reconcile_cache", group_id)

    def _file(self, group_id, key):
        return os.path.join(self._dir(group_id), f"{key}.json")

    def lookup(self, group_id, fp_res, *, repo_state_hint=None):
        return wave4_fp.classify_cache_lookup(
            self._dir(group_id), fp_res, self.settings,
            lambda res: _complete_reconcile_miss(res, group_id, self.max_calls),
            repo_state_hint=repo_state_hint,
        )

    def contains(self, group_id, key):
        if not key:
            return False
        return self.lookup(group_id, key).hit

    def remember(self, group_id, key_or_fp, result, *, repo_state_hint=None):
        key = key_or_fp.key if isinstance(key_or_fp, wave4_fp.FingerprintResult) else key_or_fp
        if key and _complete_reconcile_miss(result, group_id, self.max_calls):
            wave4_fp.write_cache_entry(
                self._file(group_id, key), key_or_fp, self.settings, result,
                repo_state_hint=repo_state_hint,
            )

    def diagnostics_summary(self):
        return self.diag.summary()


# ---------------------------------------------------------------------------
# Discovery: Wave 4A queue (auto-promotions + dependency groups)
# ---------------------------------------------------------------------------

def discover(inputs=None, audit_report=None, refresh_stale=True, log=None):
    """Discover Wave 4A work items:
      1. Already `MATCH_BUILDABLE` T4 objects (0 LLM auto-promotions).
      2. Unresolved dependency groups from `wave4_deps.build_dependency_inventory`,
         ordered mechanical-first, then highest zero-score-blocked & shared leverage.

    Returns `(items, info)` where `info` includes `inventory` and `matcher_signature`.
    """
    p, funcs, by_link, rows, issues = inputs or t3_audit.load_inputs()
    datas = {e["addr"]: e for e in by_link.values() if e.get("_kind") == "data"}
    rep = audit_report if audit_report is not None else load_audit_report_incremental(
        inputs=(p, funcs, by_link, rows, issues), refresh_stale=refresh_stale, log=log,
    )
    est = load_mappings().get("mappings", {})
    inv = wave4_deps.build_dependency_inventory(
        rep, p, funcs, datas, by_link, repo_root=path(), established_mappings=est,
    )
    msig = wave4.matcher_signature(p.functions, by_link)
    dep_ctx = wave4_fp.DependencyContext(
        p, funcs, datas, by_link,
        repo_root=path(),
        audit_rows=rep.get("results"),
        established_mappings=est,
        repo_matcher_sig=msig,
    )

    items = []
    # 1. Auto-promotion items for any ref file already MATCH_BUILDABLE
    by_ref_buildable = defaultdict(list)
    for r in rep.get("results", []):
        if r.get("tier") == "T4" and r.get("status") == "MATCH_BUILDABLE" and r.get("ref"):
            by_ref_buildable[r["ref"]].append(r)
    for ref, rs in sorted(by_ref_buildable.items(), key=lambda kv: kv[1][0]["addr"]):
        addrs = sorted(r["addr"] for r in rs)
        gid = f"promote_{addrs[0]:x}"
        items.append({
            "group_id": gid,
            "task_kind": "auto_promote",
            "classification": "MATCH_BUILDABLE",
            "mechanical": True,
            "kind": "function",
            "target_address": addrs[0],
            "target_address_hex": f"{addrs[0]:#x}",
            "symbols": [],
            "dependencies": [],
            "affected_functions": [
                {
                    "addr": r["addr"], "addr_hex": f"{r['addr']:#x}",
                    "name": r.get("name"), "link_name": r.get("link_name"),
                    "ref": r.get("ref"), "toml": r.get("toml"),
                    "module": r.get("module"), "ref_verified_by": r.get("ref_verified_by"),
                    "zero_score_blocked": True,
                }
                for r in sorted(rs, key=lambda x: x["addr"])
            ],
            "affected_refs": [ref],
            "affected_modules": sorted({r.get("module") for r in rs if r.get("module")}),
            "zero_score_blocked_count": len(rs),
            "db_entry": None,
        })

    # 2. Unresolved dependency groups
    for g in inv["groups"]:
        items.append(dict(g, task_kind="reconcile"))

    return items, {
        "inventory": inv,
        "matcher_signature": msig,
        "dep_ctx": dep_ctx,
        "issues": issues,
        "total_items": len(items),
        "auto_promote_items": len(by_ref_buildable),
        "dependency_groups": len(inv["groups"]),
    }


# ---------------------------------------------------------------------------
# Targeted compilation, audit & validation helpers
# ---------------------------------------------------------------------------

def _count_unresolved(audit_rows, target_symbols=None):
    """Count `(total_unresolved_refs, target_symbol_refs)` across best attempts of `audit_rows`."""
    total = 0
    targeted = 0
    sym_set = set(target_symbols) if target_symbols is not None else None
    for r in audit_rows:
        if r.get("status") in ("MATCH_BUILDABLE", "MATCH_UNBUILDABLE"):
            continue
        best = r.get("best") or {}
        unres = best.get("unresolved") or []
        total += len(unres)
        if sym_set is not None:
            targeted += sum(1 for u in unres if u.get("symbol") in sym_set)
    return total, targeted


def _compile_check_files(rel_paths, repo_root=None):
    """Compile-check modified C files under both Watcom 10.0a and OW2.

    Raises `t3_audit.ToolchainAbort` on `match.CompileTimeout`.
    Returns `(ok, error_detail)`.
    """
    root = repo_root or path()
    c_files = sorted({p for p in rel_paths if p.endswith(".c") and os.path.isfile(os.path.join(root, p))})
    # If any header under src/include/ was modified, also compile-check every src/**/*.c
    # that includes it directly OR transitively.
    hdr_rels = {p.replace("\\", "/") for p in rel_paths if p.endswith(".h")}
    if hdr_rels:
        src_root = os.path.join(root, "src")
        for dp, _ds, fns in os.walk(src_root):
            for fn in fns:
                if not fn.endswith(".c"):
                    continue
                full = os.path.join(dp, fn)
                rel = os.path.relpath(full, root).replace("\\", "/")
                if rel in c_files:
                    continue
                incs = set(wave4_deps._resolve_local_includes(rel, root))
                if incs & hdr_rels:
                    c_files.append(rel)
        c_files = sorted(set(c_files))
    if not c_files:
        return True, ""
    buf = io.StringIO()
    out_text = ""
    try:
        fulls = [os.path.join(root, r) for r in c_files]
        with contextlib.redirect_stdout(buf):
            fails = match.compile_check(fulls, jobs=1)
    except match.CompileTimeout as ex:
        raise t3_audit.ToolchainAbort(f"compile_check timeout: {ex}") from ex
    finally:
        out_text = buf.getvalue()
        if out_text:
            sys.stdout.write(out_text)
            sys.stdout.flush()
    if fails:
        diag_by_key = {}
        cur_key = None
        for line in out_text.splitlines():
            m = re.match(r"^DOES NOT COMPILE\s+(.+?)\s+\(([^()]+)\):\s*(.*)$", line)
            if m:
                cur_key = (m.group(1).strip(), m.group(2).strip())
                msg0 = m.group(3).strip()
                diag_by_key[cur_key] = [msg0] if msg0 else []
            elif cur_key is not None and not line.startswith("compile check:"):
                stripped = line.strip()
                if stripped and len(diag_by_key[cur_key]) < 6:
                    diag_by_key[cur_key].append(stripped)
        lines = []
        for item in fails[:8]:
            if len(item) >= 3:
                fn, cc, msg = item[0], item[1], item[2]
                detail = str(msg).strip().splitlines()[0] if msg else "error"
            else:
                fn, cc = item[0], item[1]
                diag = diag_by_key.get((fn, cc))
                detail = " | ".join(d for d in (diag or []) if d)[:400] or "compile failed"
            lines.append(f"{fn} ({cc}): {detail}")
        return False, "\n".join(lines)
    return True, ""


def _audit_refs(refs, inputs=None, objdir=None):
    """Run `t3_audit.audit_unit` for each ref file in `refs`. Returns `(rows_by_ref, all_rows)`."""
    p, funcs, by_link, rows, _issues = inputs or t3_audit.load_inputs()
    cands, _ = t3_audit.discover(funcs, rows)
    by_ref = defaultdict(list)
    for c in cands:
        if wave4.eligible(c) and c["ref"] in set(refs):
            by_ref[c["ref"]].append(c)
    od = objdir or path(*OUT_DIR, "obj", "w4a_check")
    shutil.rmtree(od, ignore_errors=True)
    ctx = t3_audit.Ctx(p, funcs, by_link, od)
    rows_by_ref = {}
    all_rows = []
    try:
        for ref in sorted(by_ref):
            res = t3_audit.audit_unit(ctx, {"ref": ref, "cands": by_ref[ref]})
            rows_by_ref[ref] = res
            all_rows.extend(res)
    finally:
        shutil.rmtree(od, ignore_errors=True)
    return rows_by_ref, all_rows


def _run_pytest_files(test_files, difftest_nodes, runner=None):
    """Run cited difftest nodes plus every modified test file IN FULL (0 skips/xfails allowed)."""
    mod_files = sorted(set(test_files or ()))
    nodes = list(mod_files)
    for n in difftest_nodes or ():
        # If the whole file is already queued in `mod_files`, no need to run the single node twice
        if any(n == tf or n.startswith(tf + "::") for tf in mod_files):
            continue
        if n not in nodes:
            nodes.append(n)
    if not nodes:
        return True, "no difftests required"
    if runner:
        return runner(nodes)
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", *nodes],
            cwd=path(), capture_output=True, text=True, timeout=900,
        )
    except subprocess.TimeoutExpired:
        return False, "difftest timeout (900 s)"
    out = r.stdout + r.stderr
    return r.returncode == 0 and wave4._all_passed(out, len(nodes)), out[-3000:]


def _collect_difftest_nodes(rows):
    nodes = []
    for r in rows:
        ns, err = symbols.parse_ref_verified_by_nodes(r.get("ref_verified_by") or "")
        if err:
            continue
        for f, n in ns:
            node = f"{f}::{n}"
            if node not in nodes:
                nodes.append(node)
    return nodes


def _promote_buildable_units(rows_by_ref, difftest_runner=None):
    """Promote every ref file where all T4 rows are `MATCH_BUILDABLE` and difftests pass.

    Returns `(promoted_entries, promoted_tomls, promoted_refs, failed_detail)`.
    """
    promoted_entries = []
    promoted_tomls = set()
    promoted_refs = []
    for ref, rs in sorted(rows_by_ref.items()):
        if not rs or not all(r.get("status") == "MATCH_BUILDABLE" for r in rs):
            continue
        ref_fn = path(ref)
        orig_bytes = open(ref_fn, "rb").read()
        try:
            normalized = wave4.set_flags_header(
                orig_bytes.decode("latin-1"), t3_audit.CC, rs[0]["match_flags"],
            ).encode("latin-1")
            if normalized != orig_bytes:
                with open(ref_fn, "wb") as fh:
                    fh.write(normalized)
            ok, detail = wave4.run_difftests(rs, runner=difftest_runner)
            if not ok:
                with open(ref_fn, "wb") as fh:
                    fh.write(orig_bytes)
                return [], [], [], f"{ref}: difftest failed on promoted candidate: {detail}"
            done = wave4.promote(rs)
            promoted_entries.extend(done)
            promoted_tomls.update(t for _a, t in done)
            promoted_refs.append(ref)
        except Exception as ex:
            with open(ref_fn, "wb") as fh:
                fh.write(orig_bytes)
            return [], [], [], f"{ref}: promotion failed: {ex}"
    return promoted_entries, sorted(promoted_tomls), promoted_refs, ""


# ---------------------------------------------------------------------------
# Snapshot / restore manager for atomic multi-file rollback
# ---------------------------------------------------------------------------

class _FileTxn:
    """In-memory snapshot/rollback for tracked & newly created files."""

    def __init__(self, repo_root=None):
        self.root = repo_root or path()
        self.originals = {}   # rel -> bytes | None (None means created by us)

    def snapshot(self, rel):
        rel = rel.replace("\\", "/")
        if rel in self.originals:
            return
        full = os.path.join(self.root, rel)
        self.originals[rel] = open(full, "rb").read() if os.path.isfile(full) else None

    def write(self, rel, text, encoding="utf-8"):
        rel = rel.replace("\\", "/")
        self.snapshot(rel)
        full = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "wb") as fh:
            fh.write(text.encode(encoding) if isinstance(text, str) else text)

    def restore(self):
        for rel, data in list(self.originals.items()):
            full = os.path.join(self.root, rel)
            if data is None:
                try:
                    os.unlink(full)
                except FileNotFoundError:
                    pass
            else:
                os.makedirs(os.path.dirname(full), exist_ok=True)
                with open(full, "wb") as fh:
                    fh.write(data)
        self.originals.clear()

    def changed_files(self):
        out = []
        for rel, orig in sorted(self.originals.items()):
            full = os.path.join(self.root, rel)
            cur = open(full, "rb").read() if os.path.isfile(full) else None
            if cur != orig:
                out.append(rel)
        return out

    def created_files(self):
        return [rel for rel, orig in sorted(self.originals.items())
                if orig is None and os.path.isfile(os.path.join(self.root, rel))]


# ---------------------------------------------------------------------------
# Research evidence packet builder (Phase 3.3 — narrow, fresh context)
# ---------------------------------------------------------------------------

def _disasm_target_func(p, target_addr, funcs, datas, max_insns=100):
    """Compact disassembly of a target function plus its direct callers."""
    starts = {f["start"]: f for f in (getattr(p, "functions", None) or [])}
    f = starts.get(target_addr)
    if not f:
        return ""
    by_addr = {a: e["name"] for t in (funcs, datas) for a, e in t.items()}
    insns = getattr(p, "insns", None) or {}
    fix_at = getattr(p, "fix_at", None) or {}
    lines = [f"Disassembly of {target_addr:#x}..{f['end']:#x} ({f.get('ninsns', '?')} insns):"]
    count = 0
    for pc in range(target_addr, f["end"]):
        ins = insns.get(pc)
        if ins is None:
            continue
        notes = []
        if ins.mnemonic in ("call", "jmp") and re.fullmatch(r"0x[0-9a-fA-F]+", ins.op_str):
            t = int(ins.op_str, 16)
            if t in by_addr:
                notes.append(by_addr[t])
        for off in range(pc, pc + ins.size):
            if off in fix_at:
                t = fix_at[off][1]
                notes.append(f"fixup->{t:#x}" + (f" ({by_addr[t]})" if t in by_addr else ""))
        suffix = f"   ; {', '.join(notes)}" if notes else ""
        lines.append(f"  {pc:05x}  {ins.mnemonic} {ins.op_str}{suffix}")
        count += 1
        if count >= max_insns:
            lines.append(f"  ... ({f['end'] - pc} bytes truncated)")
            break
    # Also list callers from p.insns (capped)
    callers = []
    for st, finfo in sorted(starts.items()):
        for pc in range(st, finfo["end"]):
            ins = insns.get(pc)
            if ins and ins.mnemonic in ("call", "jmp") and ins.op_str == f"{target_addr:#x}":
                callers.append(f"{st:#x} ({by_addr.get(st, f'fn_{st:x}')}) at {pc:#x}")
                break
        if len(callers) >= 12:
            break
    if callers:
        lines.append("Direct callers: " + ", ".join(callers))
    return "\n".join(lines)


def _dump_target_data(p, target_addr, datas, structs, max_bytes=96):
    """Hex + ASCII dump, string preview, LE fixups, and neighbor data symbols around `target_addr`."""
    if not hasattr(p, "le") or not hasattr(p.le, "obj_at"):
        return ""
    o = p.le.obj_at(target_addr)
    if o is None:
        return f"Address {target_addr:#x} is outside the loaded LE image."
    img = p.image[o.index]
    rel = target_addr - o.base
    chunk = bytes(img[rel:rel + max_bytes])
    lines = [f"Image bytes at {target_addr:#x} (object {o.index + 1}, base {o.base:#x}):"]
    for i in range(0, len(chunk), 16):
        row = chunk[i:i + 16]
        hex_s = " ".join(f"{b:02x}" for b in row)
        asc_s = "".join(chr(b) if 32 <= b < 127 else "." for b in row)
        lines.append(f"  {target_addr + i:05x}: {hex_s:<47s}  |{asc_s}|")
    # Printable C string preview if NUL-terminated ASCII
    nul = chunk.find(b"\x00")
    if nul >= 0 and all(b in (9, 10, 13) or 32 <= b < 127 for b in chunk[:nul]):
        lines.append(f"NUL-terminated string ({nul + 1} bytes incl NUL): {chunk[:nul].decode('ascii')!r}")
    fix_at = getattr(p, "fix_at", None) or {}
    fxs = [f"{a:#x} -> {fix_at[a][1]:#x}" for a in range(target_addr, target_addr + max_bytes) if a in fix_at]
    if fxs:
        lines.append("LE fixups in range: " + ", ".join(fxs[:16]))
    neighbors = [
        f"{a:#x} {e['name']} ({e.get('type', '?')}, {e.get('_file')})"
        for a, e in sorted(datas.items())
        if abs(a - target_addr) <= 0x60
    ]
    if neighbors:
        lines.append("Nearby [[data]] entries:\n  " + "\n  ".join(neighbors[:12]))
    return "\n".join(lines)


PROTECTED_TOMLS = set(wave4_fp.PROTECTED_TOMLS)


def _compile_err_has_external_c_failure(cc_err, scope_refs, repo_root=None):
    """True when `cc_err` reports a compile failure in a `.c` file outside `scope_refs`."""
    root = os.path.realpath(repo_root or path())
    allowed = {os.path.normpath(str(r)).replace("\\", "/") for r in (scope_refs or ())}
    for line in str(cc_err or "").splitlines():
        m = re.match(r"^\s*(.+?\.c)\s+\([^()]+\):", line)
        if not m:
            continue
        raw_p = m.group(1).strip()
        if os.path.isabs(raw_p):
            try:
                rel = os.path.relpath(os.path.realpath(raw_p), root).replace("\\", "/")
            except ValueError:
                rel = raw_p.replace("\\", "/")
        else:
            rel = os.path.normpath(raw_p).replace("\\", "/")
        if rel not in allowed:
            return True
    return False


def _allowed_edit_scope(group, funcs, repo_root=None):
    """Compute the strict allowlist of files a Wave 4A research worker may touch."""
    root = repo_root or path()
    affected_refs = sorted(set(group.get("affected_refs") or ()))
    allowed_headers = set()
    for ref in affected_refs:
        for inc in wave4_deps._resolve_local_includes(ref, root):
            if inc != ref and inc.startswith("src/include/") and inc != "src/include/war.h":
                allowed_headers.add(inc)
    allowed_tests = set()
    allowed_tomls = set()
    for af in group.get("affected_functions") or ():
        if af.get("toml") and af["toml"] not in PROTECTED_TOMLS:
            allowed_tomls.add(af["toml"])
        ns, err = symbols.parse_ref_verified_by_nodes(af.get("ref_verified_by") or "")
        if not err:
            for tf, _node in ns:
                allowed_tests.add(tf.replace("\\", "/"))
    db = group.get("db_entry")
    if db and db.get("_file") and db["_file"] not in PROTECTED_TOMLS:
        allowed_tomls.add(db["_file"])
    # Also allow the TOML owning the target module if target_address falls near known funcs
    target_addr = group.get("target_address")
    if isinstance(target_addr, int):
        for a, e in funcs.items():
            if abs(a - target_addr) <= 0x400 and e.get("_file") and e["_file"] not in PROTECTED_TOMLS:
                allowed_tomls.add(e["_file"])
    return {
        "refs": affected_refs,
        "headers": sorted(allowed_headers),
        "tests": sorted(allowed_tests),
        "tomls": sorted(allowed_tomls),
    }


def build_research_packet(group, p, funcs, datas, scope, audit_rows_by_ref=None,
                          feedback="", repo_root=None):
    """Construct a minimal, narrowly scoped prompt for one Wave 4A dependency group."""
    root = repo_root or path()
    structs, _aliases = wave4_deps.parse_header_structs(os.path.join(root, "src", "include"))
    parts = [
        f"## Wave 4A Dependency Research Task: `{group['group_id']}`",
        f"- Classification: `{group['classification']}` | Kind: `{group['kind']}`",
        f"- Unresolved symbols: `{', '.join(group.get('symbols') or ())}`",
        f"- Corroborated target address: `{group.get('target_address_hex') or 'NONE (ambiguous)'}`",
        f"- Affected T4 functions ({len(group.get('affected_functions') or ())}, "
        f"zero-score blocked: {group.get('zero_score_blocked_count', 0)}):",
    ]
    for af in (group.get("affected_functions") or ())[:10]:
        parts.append(f"  - `{af['addr_hex']}` `{af['name']}` ({af['ref']}, toml={af.get('toml')}, "
                     f"best_score={af.get('best_score')})")

    # Per-dependency diagnostics
    parts.append("\n### Structured Relocation Diagnostics")
    for dep in (group.get("dependencies") or ())[:12]:
        parts.append(
            f"- `{dep['symbol']}` (ident `{dep['ident']}`, class `{dep['classification']}`, "
            f"target={dep.get('expected_address_hex')}, addends={dep.get('addends')}, "
            f"reloc={dep.get('relocation_kinds')})"
        )
        if dep.get("blockers"):
            parts.append("  blockers: " + "; ".join(dep["blockers"][:4]))
        if dep.get("evidence"):
            parts.append("  evidence: " + "; ".join(dep["evidence"][:4]))
        if dep.get("db_entry"):
            parts.append("  db_entry: " + json.dumps(dep["db_entry"], sort_keys=True))
        if dep.get("containing_owner"):
            parts.append("  containing_owner: " + json.dumps(dep["containing_owner"], sort_keys=True))
        if dep.get("canonical_header_decls"):
            parts.append("  canonical_headers: " + "; ".join(
                f"{d['file']}:{d['line']}: {d['text']}" for d in dep["canonical_header_decls"][:4]
            ))

    # Target binary evidence
    taddr = group.get("target_address")
    if isinstance(taddr, int):
        if group["kind"] == "function":
            dis = _disasm_target_func(p, taddr, funcs, datas)
            if dis:
                parts.append("\n### Target Disassembly\n```\n" + dis + "\n```")
        else:
            dump = _dump_target_data(p, taddr, datas, structs)
            if dump:
                parts.append("\n### Target Data Bytes & Neighbors\n```\n" + dump + "\n```")
            # Also dump any distinct interior addresses in the group
            for dep in (group.get("dependencies") or ())[:6]:
                ea = dep.get("expected_address")
                if isinstance(ea, int) and ea != taddr:
                    parts.append(f"\n#### Interior address {ea:#x} ({dep['symbol']})\n```\n"
                                 + _dump_target_data(p, ea, datas, structs, max_bytes=32) + "\n```")

    # Affected C files (capped to keep context tight)
    parts.append("\n### Affected C Files")
    for ref in (scope["refs"])[:6]:
        full = os.path.join(root, ref)
        if os.path.isfile(full):
            txt = open(full, encoding="utf-8", errors="replace").read()
            parts.append(f"#### `{ref}`\n```c\n{txt[:9000]}\n```")
            if audit_rows_by_ref and ref in audit_rows_by_ref:
                for r in audit_rows_by_ref[ref]:
                    b = r.get("best") or {}
                    if b.get("diff"):
                        parts.append(f"Current diff for `{r['name']}` ({r['addr_hex']}, score={b.get('score')}):\n```\n"
                                     + "\n".join(b["diff"][:25]) + "\n```")

    # Relevant area headers (compact)
    if scope["headers"]:
        parts.append("\n### Relevant Included Headers")
        for hdr in scope["headers"][:4]:
            full = os.path.join(root, hdr)
            if os.path.isfile(full):
                txt = open(full, encoding="utf-8", errors="replace").read()
                parts.append(f"#### `{hdr}`\n```c\n{txt[:6000]}\n```")

    # Relevant test snippets (ONLY EXTRA/T4Stub/top lines so worker sees fixture context)
    if scope["tests"]:
        parts.append("\n### Cited T4 Test Files (context; edit ONLY if ABI/symbol fixture requires it)")
        for tf in scope["tests"][:3]:
            full = os.path.join(root, tf)
            if os.path.isfile(full):
                txt = open(full, encoding="utf-8", errors="replace").read()
                parts.append(f"#### `{tf}`\n```python\n{txt[:4500]}\n```")

    parts.append(
        "\n### Allowed Edit Scope\n"
        f"- C files: {scope['refs']}\n"
        f"- Headers (existing, or new `src/include/<name>.h` with `old: \"\"`): {scope['headers']}\n"
        f"- TOMLs for `toml_entries` (append new `[[func]]`/`[[data]]`, or existing area TOMLs): {scope['tomls']}\n"
        f"- Test files (only if strictly needed, anti-weakening enforced): {scope['tests']}\n"
    )
    if feedback:
        parts.append(f"\n### Previous Attempt Validation Feedback (fix all reported errors)\n```\n{feedback[-2500:]}\n```\n")
    parts.append("\n" + RESEARCH_RULES)
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Proposal validation & application
# ---------------------------------------------------------------------------

_FORBIDDEN_TOML_ENTRY_KEYS = {"src", "ref", "ref_verified_by", "t3_blocker", "verified_by"}


def _is_safe_rel_path(rel, root):
    rel = str(rel or "").replace("\\", "/")
    if not rel or rel.startswith("/") or os.path.isabs(rel) or "\x00" in rel:
        return False
    norm = os.path.normpath(rel).replace("\\", "/")
    if norm != rel.rstrip("/") or norm in (".", "..") or norm.startswith("../"):
        return False
    root_real = os.path.realpath(root)
    full = os.path.join(root, rel)
    if os.path.islink(full):
        return False
    real = os.path.realpath(full)
    return real == root_real or real.startswith(root_real + os.sep)


def _validate_and_apply_proposal(res, scope, txn, repo_root=None):
    """Validate and apply a structured research proposal inside `txn`.

    Returns `(ok, added_symbols, detail)`. Never leaves partial edits on failure.
    """
    root = repo_root or path()
    if not isinstance(res, dict):
        return False, [], "malformed proposal (not a JSON object)"
    toml_entries = res.get("toml_entries") or []
    file_patches = res.get("file_patches") or []
    if not toml_entries and not file_patches:
        return False, [], "empty proposal (no toml_entries or file_patches)"

    allowed_refs = set(scope["refs"])
    allowed_headers = set(scope["headers"])
    allowed_tests = set(scope["tests"])
    allowed_tomls = set(scope["tomls"])
    added_symbols = []

    # Load existing [[data]] + header structs once to block duplicate interior-field [[data]] entries
    existing_datas = {}
    structs, aliases = wave4_deps.parse_header_structs(os.path.join(root, "src", "include"))
    sym_dir = os.path.join(root, "analysis", "symbols")
    if os.path.isdir(sym_dir):
        try:
            _ef, existing_datas, _el = symbols.load(root=sym_dir, strict=False, repo_root=root)
        except Exception:
            existing_datas = {}

    def _check_not_interior_data(addr, tf_label):
        owner = wave4_deps.find_containing_owner(addr, existing_datas, structs, aliases)
        if owner is not None:
            return (f"{tf_label}: [[data]] {addr:#x} is an interior field of existing "
                    f"{owner['name']} ({owner['addr_hex']} +{owner['offset']:#x}); "
                    f"use owner array/field indexing instead of adding a duplicate symbol")
        return None

    # 1. Validate & append TOML entries
    for ent in toml_entries:
        if not isinstance(ent, dict):
            return False, [], "malformed toml_entries item"
        tf = str(ent.get("toml_file") or "").replace("\\", "/")
        blk = str(ent.get("toml_block") or "").strip()
        if not _is_safe_rel_path(tf, root):
            return False, [], f"unsafe toml_file path: {tf!r}"
        if not re.fullmatch(r"analysis/symbols/[a-z0-9_]+\.toml", tf):
            return False, [], f"invalid toml_file name: {tf!r}"
        if tf in PROTECTED_TOMLS:
            return False, [], f"protected TOML cannot be edited: {tf}"
        full_tf = os.path.join(root, tf)
        try:
            parsed = tomllib.loads(blk)
        except Exception as ex:
            return False, [], f"TOML parse error in {tf}: {ex}"
        if not parsed or set(parsed.keys()) - {"func", "data"}:
            return False, [], f"toml_block in {tf} may only contain [[func]] or [[data]] tables"
        for kind in ("func", "data"):
            for item in parsed.get(kind, []):
                if not isinstance(item, dict):
                    return False, [], f"malformed [[{kind}]] entry in {tf}"
                bad_keys = _FORBIDDEN_TOML_ENTRY_KEYS & set(item.keys())
                if bad_keys:
                    return False, [], f"research worker may not set {sorted(bad_keys)} in {tf}"
                if item.get("confidence") == "verified":
                    return False, [], f"research worker may not set confidence='verified' in {tf}"
                if not item.get("evidence") or not isinstance(item.get("addr"), int) or not item.get("name"):
                    return False, [], f"[[{kind}]] entry in {tf} requires addr, name, and non-empty evidence"
                if kind == "data":
                    int_err = _check_not_interior_data(item["addr"], tf)
                    if int_err:
                        return False, [], int_err
                ln = symbols.link_name(kind, item)
                added_symbols.append({"kind": kind, "addr": item["addr"], "name": item["name"],
                                      "link_name": ln, "toml": tf})
        cur = open(full_tf, encoding="utf-8").read() if os.path.isfile(full_tf) else ""
        sep = "\n\n" if cur and not cur.endswith("\n\n") else ("\n" if cur and not cur.endswith("\n") else "")
        txn.write(tf, cur + sep + blk + "\n")

    # 2. Validate & apply file patches
    by_path = defaultdict(list)
    for fp in file_patches:
        if not isinstance(fp, dict):
            return False, [], "malformed file_patches item"
        rel = str(fp.get("path") or "").replace("\\", "/")
        old = fp.get("old")
        new = fp.get("new")
        if not isinstance(old, str) or not isinstance(new, str):
            return False, [], f"invalid old/new in patch for {rel}"
        if not _is_safe_rel_path(rel, root):
            return False, [], f"unsafe patch path: {rel!r}"
        if (rel in ("Makefile", "flake.nix", "AGENTS.md", "src/include/war.h")
                or rel in PROTECTED_TOMLS
                or rel.startswith(("tools/", "asm/", ".claude/", ".opencode/"))):
            return False, [], f"forbidden patch path: {rel}"
        is_new_hdr = (old == "" and re.fullmatch(r"src/include/[a-z0-9_]+\.h", rel)
                      and not os.path.exists(os.path.join(root, rel)))
        if not (rel in allowed_refs or rel in allowed_headers or rel in allowed_tests
                or rel in allowed_tomls or is_new_hdr):
            return False, [], f"path outside allowed Wave 4A scope: {rel}"
        by_path[rel].append((old, new))

    for rel, edits in sorted(by_path.items()):
        full = os.path.join(root, rel)
        exists = os.path.isfile(full)
        is_c_or_h = rel.endswith((".c", ".h"))
        enc = "latin-1" if is_c_or_h else "utf-8"
        orig_text = open(full, encoding=enc, errors="replace").read() if exists else ""
        cur_text = orig_text
        for old, new in edits:
            if old == "" and not exists:
                cur_text = new
                exists = True
            else:
                if not old or cur_text.count(old) != 1:
                    return False, [], f"{rel}: patch 'old' did not match uniquely (count={cur_text.count(old) if old else 0})"
                cur_text = cur_text.replace(old, new, 1)
        if rel.endswith(".c"):
            if not wave4._guard_ok(orig_text, cur_text):
                return False, [], f"{rel}: patch attempted to modify codegen metadata headers"
        elif rel.endswith(".toml"):
            try:
                old_doc = tomllib.loads(orig_text) if orig_text else {}
                new_doc = tomllib.loads(cur_text)
            except Exception as ex:
                return False, [], f"{rel}: invalid TOML after patch: {ex}"
            old_by_a = {f["addr"]: f for f in old_doc.get("func", []) if "addr" in f}
            new_by_a = {f["addr"]: f for f in new_doc.get("func", []) if "addr" in f}
            dropped_funcs = sorted(set(old_by_a) - set(new_by_a))
            if dropped_funcs:
                return False, [], f"{rel}: worker may not delete existing [[func]] {dropped_funcs[0]:#x}"
            for a, nf in new_by_a.items():
                of = old_by_a.get(a, {})
                for k in _FORBIDDEN_TOML_ENTRY_KEYS:
                    if nf.get(k) != of.get(k):
                        return False, [], f"{rel}: worker may not modify {k!r} on {a:#x}"
                if nf.get("confidence") == "verified" and of.get("confidence") != "verified":
                    return False, [], f"{rel}: worker may not promote confidence to verified on {a:#x}"
                if a not in old_by_a and (not nf.get("evidence") or not nf.get("name")):
                    return False, [], f"{rel}: new [[func]] {a:#x} requires name and evidence"
            old_data = {d["addr"]: d for d in old_doc.get("data", []) if "addr" in d}
            new_data = {d["addr"]: d for d in new_doc.get("data", []) if "addr" in d}
            dropped_data = sorted(set(old_data) - set(new_data))
            if dropped_data:
                return False, [], f"{rel}: worker may not delete existing [[data]] {dropped_data[0]:#x}"
            for a, nd in new_data.items():
                od = old_data.get(a, {})
                for k in _FORBIDDEN_TOML_ENTRY_KEYS:
                    if nd.get(k) != od.get(k):
                        return False, [], f"{rel}: worker may not modify [[data]] {k!r} on {a:#x}"
                if nd.get("confidence") == "verified" and od.get("confidence") != "verified":
                    return False, [], f"{rel}: worker may not promote [[data]] confidence to verified on {a:#x}"
                if a not in old_data:
                    if not nd.get("evidence") or not nd.get("name"):
                        return False, [], f"{rel}: new [[data]] {a:#x} requires name and evidence"
                    int_err = _check_not_interior_data(a, rel)
                    if int_err:
                        return False, [], int_err
        elif rel.startswith("tests/") and rel.endswith(".py"):
            reason = batch_driver.check_test_patch_not_weakening(orig_text, cur_text, allow_case_edits=False)
            if reason:
                return False, [], f"{rel}: {reason}"
        txn.write(rel, cur_text, encoding=enc)

    # 3. Validate symbol DB strictly
    try:
        symbols.load(root=os.path.join(root, "analysis", "symbols"), strict=True, repo_root=root)
    except symbols.SymbolError as ex:
        return False, [], f"wc1.symbols validation failed: {ex}"

    return True, added_symbols, ""


# ---------------------------------------------------------------------------
# Main Wave 4A execution entry point for one item (auto-promote or dep group)
# ---------------------------------------------------------------------------

def run_reconciliation(item, *, llm=None, max_calls=2, difftest_runner=None,
                       compile_checker=None, audit_runner=None, log=print,
                       persist_mappings=False):
    """Process one Wave 4A item (auto-promotion or unresolved dependency group).

    Never leaves modified files on disk unless the outcome is `PROMOTED` or `RECONCILED`.
    Returns the outcome receipt dict (also written to `build/wave4/reconcile_outcomes/`).
    """
    gid = item["group_id"]
    txn = _FileTxn()
    comp_fn = compile_checker or _compile_check_files
    aud_fn = audit_runner or _audit_refs

    # --- Case 0: Auto-promotion of an already MATCH_BUILDABLE ref file (0 LLM) ---
    if item.get("task_kind") == "auto_promote":
        refs = list(item.get("affected_refs") or ())
        try:
            rows_by_ref, _ = aud_fn(refs)
        except t3_audit.ToolchainAbort as ex:
            return write_outcome(gid, TOOLCHAIN_ERROR, reason=str(ex), method="auto_promote", llm_calls=0)
        for ref in refs:
            txn.snapshot(ref)
        for rs in rows_by_ref.values():
            for r in rs:
                if r.get("toml"):
                    txn.snapshot(r["toml"])
        try:
            promoted_entries, promoted_tomls, promoted_refs, err = _promote_buildable_units(
                rows_by_ref, difftest_runner=difftest_runner,
            )
        except BaseException:
            txn.restore()
            raise
        if err or not promoted_entries:
            txn.restore()
            return write_outcome(
                gid, FAILED if err else NO_IMPROVEMENT,
                reason=err or "object is no longer MATCH_BUILDABLE",
                method="auto_promote", llm_calls=0, complete_search=False,
            )
        invalidate_audit_refs(refs=promoted_refs)
        return write_outcome(
            gid, PROMOTED,
            method="auto_promote",
            llm_calls=0,
            promoted=[f"{a:#x}" for a, _t in promoted_entries],
            tomls=promoted_tomls,
            ref_files=promoted_refs,
            headers=[],
            tests=[],
            changed_files=txn.changed_files(),
            created_files=txn.created_files(),
            unresolved_before=0,
            unresolved_after=0,
            affected_refs=refs,
            symbols=[],
            summary=f"Auto-promoted {len(promoted_entries)} newly buildable T3 function(s) from {refs[0]}",
        )

    # --- Measure baseline unresolved counts across this group's affected T4 refs ---
    affected_refs = list(item.get("affected_refs") or ())
    target_syms = list(item.get("symbols") or ())
    try:
        before_by_ref, before_rows = aud_fn(affected_refs)
    except t3_audit.ToolchainAbort as ex:
        return write_outcome(gid, TOOLCHAIN_ERROR, reason=str(ex), method="baseline", llm_calls=0)
    complete_omf_refs = [
        (ref, rs[0]["omf_deps"], rs[0].get("declared_cflags"))
        for ref, rs in before_by_ref.items()
        if rs and isinstance(rs[0].get("omf_deps"), dict) and rs[0]["omf_deps"].get("complete")
    ]
    if complete_omf_refs:
        try:
            _fs, _ds, _errs = symbols.load(strict=False, repo_root=path())
            cur_by_link = {e["link_name"]: e for t in (_fs, _ds) for e in t.values() if e.get("link_name")}
        except Exception:
            cur_by_link = None
        for ref, omf_d, decl_cf in complete_omf_refs:
            wave4_fp.record_unit_omf_deps(
                ref, omf_d,
                declared_cflags=decl_cf,
                by_link=cur_by_link,
                repo_root=path(),
            )
    unres_total_before, unres_target_before = _count_unresolved(before_rows, target_syms)

    # --- Path A: Deterministic mechanical reconciliation (0 LLM calls) ---
    mech_ok, mech_plan, mech_why = wave4_deps.can_apply_mechanical_group(item, repo_root=path())
    mech_error = ""
    if mech_ok:
        by_file = defaultdict(list)
        for step in mech_plan:
            by_file[step["file"]].append(step)
        try:
            for rel, steps in sorted(by_file.items()):
                full = path(rel)
                txt = open(full, encoding="latin-1").read()
                for st in steps:
                    txt, _n = wave4_deps.rewrite_c_symbol(
                        txt, st["old_ident"], st["new_ident"],
                        drop_redundant_decl=st["drop_redundant_decl"],
                    )
                txn.write(rel, txt, encoding="latin-1")
            changed_now = txn.changed_files()
            ok_cc, cc_err = comp_fn(changed_now)
            if not ok_cc:
                mech_error = f"mechanical compile_check failed: {cc_err}"
                txn.restore()
            else:
                after_by_ref, after_rows = aud_fn(affected_refs)
                unres_total_after, unres_target_after = _count_unresolved(after_rows, target_syms)
                has_bad_status = any(
                    r.get("status") in ("COMPILE_ERROR", "SKIPPED", "TOOLCHAIN_ERROR") for r in after_rows
                ) or (len(after_rows) != len(before_rows))
                has_buildable = any(
                    rs and all(r.get("status") == "MATCH_BUILDABLE" for r in rs)
                    for rs in after_by_ref.values()
                )
                improved = (not has_bad_status) and (
                    (has_buildable and unres_total_after <= unres_total_before)
                    or (unres_target_after < unres_target_before and unres_total_after < unres_total_before)
                )
                if not improved:
                    mech_error = (f"mechanical rewrite did not reduce unresolved relocations "
                                  f"(target {unres_target_before}->{unres_target_after}, "
                                  f"total {unres_total_before}->{unres_total_after}, bad_status={has_bad_status})")
                    txn.restore()
                else:
                    # Snapshot TOMLs of any promotable rows
                    for rs in after_by_ref.values():
                        for r in rs:
                            if r.get("toml"):
                                txn.snapshot(r["toml"])
                    promoted_entries, promoted_tomls, promoted_refs, perr = _promote_buildable_units(
                        after_by_ref, difftest_runner=difftest_runner,
                    )
                    if perr:
                        mech_error = perr
                        txn.restore()
                    else:
                        # Difftest all modified still-T4 refs
                        still_t4_rows = [
                            r for ref, rs in after_by_ref.items() if ref not in promoted_refs for r in rs
                        ]
                        dt_nodes = _collect_difftest_nodes(still_t4_rows)
                        ok_dt, dt_err = _run_pytest_files([], dt_nodes, runner=difftest_runner)
                        if not ok_dt:
                            mech_error = f"mechanical difftest failed: {dt_err}"
                            txn.restore()
                        else:
                            # Emit 1-to-1 candidate mappings (persisted by runner ONLY after commit)
                            proposed_mappings = []
                            for dep in item.get("dependencies") or ():
                                db = dep.get("db_entry") or {}
                                if db.get("link_name"):
                                    proposed_mappings.append({
                                        "old_symbol": dep["symbol"],
                                        "target_addr": dep.get("expected_address"),
                                        "canonical_link": db["link_name"],
                                        "canonical_name": db.get("name"),
                                        "kind": dep["kind"],
                                        "method": "mechanical",
                                    })
                            changed = txn.changed_files()
                            invalidate_audit_refs(refs=affected_refs, symbols_changed=target_syms)
                            out_kind = PROMOTED if promoted_entries else RECONCILED
                            rec = write_outcome(
                                gid, out_kind,
                                method="mechanical",
                                llm_calls=0,
                                promoted=[f"{a:#x}" for a, _t in promoted_entries],
                                tomls=sorted(set(promoted_tomls)),
                                ref_files=sorted(f for f in changed if f.startswith("src/") and f.endswith(".c")),
                                headers=sorted(f for f in changed if f.startswith("src/include/") and f.endswith(".h")),
                                tests=[],
                                changed_files=changed,
                                created_files=txn.created_files(),
                                proposed_mappings=proposed_mappings,
                                unresolved_before=unres_total_before,
                                unresolved_after=unres_total_after,
                                target_unresolved_before=unres_target_before,
                                target_unresolved_after=unres_target_after,
                                affected_refs=affected_refs,
                                symbols=target_syms,
                                summary=(
                                    f"Mechanically reconciled {', '.join(target_syms)} "
                                    f"({unres_total_before}->{unres_total_after} unresolved, "
                                    f"+{len(promoted_entries)} T3)"
                                ),
                            )
                            if persist_mappings:
                                persist_outcome_mappings(rec)
                            return rec
        except t3_audit.ToolchainAbort as ex:
            txn.restore()
            return write_outcome(gid, TOOLCHAIN_ERROR, reason=str(ex), method="mechanical", llm_calls=0)
        except BaseException:
            txn.restore()
            raise

    # --- Path B: Bounded LLM research (fresh isolated context) ---
    if llm is None or int(max_calls) <= 0:
        return write_outcome(
            gid, NO_IMPROVEMENT,
            reason=mech_error or mech_why or "non-mechanical dependency and LLM disabled (max_calls=0)",
            method="mechanical_only",
            llm_calls=0,
            complete_search=False,
            symbols=target_syms,
            affected_refs=affected_refs,
        )

    p, funcs, by_link, _rows, _issues = t3_audit.load_inputs()
    datas = {e["addr"]: e for e in by_link.values() if e.get("_kind") == "data"}
    scope = _allowed_edit_scope(item, funcs, repo_root=path())
    calls = 0
    history = []
    feedback = mech_error
    complete_search = True
    last_summary = ""
    last_uncertainties = []

    try:
        while calls < int(max_calls):
            calls += 1
            prompt = build_research_packet(
                item, p, funcs, datas, scope,
                audit_rows_by_ref=before_by_ref, feedback=feedback, repo_root=path(),
            )
            res = llm(prompt, RESEARCH_SCHEMA, f"wave4a:{gid}:research{calls}")
            if not isinstance(res, dict) or res.get("decision") not in ("apply", "ambiguous", "defer"):
                complete_search = False
                history.append({"call": calls, "error": "malformed LLM research response"})
                feedback = "Response was not a valid RESEARCH_SCHEMA object."
                continue
            decision = res["decision"]
            last_summary = str(res.get("summary") or "")
            last_uncertainties = list(res.get("uncertainties") or ())
            history.append({
                "call": calls,
                "decision": decision,
                "summary": last_summary[:200],
                "uncertainties": last_uncertainties[:5],
            })
            if decision == "ambiguous":
                txn.restore()
                return write_outcome(
                    gid, AMBIGUOUS,
                    method="research",
                    llm_calls=calls,
                    complete_search=complete_search,
                    reason=last_summary or "researcher marked dependency ambiguous",
                    uncertainties=last_uncertainties,
                    history=history,
                    symbols=target_syms,
                    affected_refs=affected_refs,
                )
            if decision == "defer":
                txn.restore()
                feedback = last_summary or "deferred"
                continue

            ok_prop, added_syms, prop_err = _validate_and_apply_proposal(res, scope, txn, repo_root=path())
            if not ok_prop:
                txn.restore()
                history[-1]["rejected"] = prop_err
                feedback = f"Proposal rejected: {prop_err}"
                continue

            changed_now = txn.changed_files()
            try:
                ok_cc, cc_err = comp_fn(changed_now)
            except t3_audit.ToolchainAbort as ex:
                txn.restore()
                return write_outcome(gid, TOOLCHAIN_ERROR, reason=str(ex), method="research",
                                     llm_calls=calls, history=history)
            if not ok_cc:
                txn.restore()
                if _compile_err_has_external_c_failure(cc_err, scope["refs"], repo_root=path()):
                    # Do not cache an externally-caused compile failure in a `.c` file
                    # outside `scope["refs"]` as a self-contained Wave 4A miss.
                    complete_search = False
                history[-1]["rejected"] = f"compile_check failed: {cc_err}"
                feedback = f"Compile check (Watcom 10.0a + OW2) failed:\n{cc_err}"
                continue

            # Dependency-driven reprocessing: re-audit affected refs PLUS any T4 ref referencing added symbols
            new_inputs = t3_audit.load_inputs()
            reprocess_refs = set(affected_refs)
            added_links = {s["link_name"] for s in added_syms}
            if added_links:
                state = _read_json(path(*AUDIT_STATE_FILE)) or {}
                for ref_k, meta in (state.get("unit_meta") or {}).items():
                    if added_links & set((meta.get("deps") or {}).keys()):
                        reprocess_refs.add(ref_k)
            try:
                after_by_ref, after_rows = aud_fn(sorted(reprocess_refs), inputs=new_inputs)
            except t3_audit.ToolchainAbort as ex:
                txn.restore()
                return write_outcome(gid, TOOLCHAIN_ERROR, reason=str(ex), method="research",
                                     llm_calls=calls, history=history)

            affected_after_rows = [r for ref in affected_refs for r in after_by_ref.get(ref, ())]
            unres_total_after, unres_target_after = _count_unresolved(affected_after_rows, target_syms)
            has_bad_status = any(
                r.get("status") in ("COMPILE_ERROR", "SKIPPED", "TOOLCHAIN_ERROR") for r in after_rows
            ) or (len(affected_after_rows) != len(before_rows))
            has_buildable = any(
                rs and all(r.get("status") == "MATCH_BUILDABLE" for r in rs)
                for rs in after_by_ref.values()
            )
            improved = (not has_bad_status) and (
                (has_buildable and unres_total_after <= unres_total_before)
                or (unres_total_after < unres_total_before
                    and (unres_target_before == 0 or unres_target_after < unres_target_before))
            )
            if not improved:
                txn.restore()
                msg = (f"No measurable improvement: unresolved total {unres_total_before}->{unres_total_after}, "
                       f"target {unres_target_before}->{unres_target_after}, bad_status={has_bad_status}")
                history[-1]["rejected"] = msg
                feedback = msg
                continue

            # Snapshot TOMLs/refs of any additionally unblocked MATCH_BUILDABLE units
            for ref, rs in after_by_ref.items():
                if rs and all(r.get("status") == "MATCH_BUILDABLE" for r in rs):
                    txn.snapshot(ref)
                    for r in rs:
                        if r.get("toml"):
                            txn.snapshot(r["toml"])

            promoted_entries, promoted_tomls, promoted_refs, perr = _promote_buildable_units(
                after_by_ref, difftest_runner=difftest_runner,
            )
            if perr:
                txn.restore()
                history[-1]["rejected"] = perr
                feedback = perr
                continue

            # Run difftests on all modified still-T4 refs + any modified test files (in full)
            changed_now = txn.changed_files()
            mod_tests = [f for f in changed_now if f.startswith("tests/") and f.endswith(".py")]
            still_t4_rows = [
                r for ref, rs in after_by_ref.items() if ref not in promoted_refs for r in rs
            ]
            dt_nodes = _collect_difftest_nodes(still_t4_rows)
            ok_dt, dt_err = _run_pytest_files(mod_tests, dt_nodes, runner=difftest_runner)
            if not ok_dt:
                txn.restore()
                history[-1]["rejected"] = f"difftest failed: {dt_err[-400:]}"
                feedback = f"Difftest failed:\n{dt_err}"
                continue

            # Success! Emit ONLY unambiguous 1-to-1 candidate mappings (never Cartesian product);
            # runner persists them to mappings.json ONLY after `make verify` + commit succeed.
            proposed_mappings = []
            if len(added_syms) == 1 and len(target_syms) == 1:
                s = added_syms[0]
                proposed_mappings.append({
                    "old_symbol": target_syms[0], "target_addr": s["addr"],
                    "canonical_link": s["link_name"], "canonical_name": s["name"],
                    "kind": s["kind"], "method": "research",
                })
            elif added_syms:
                by_addr_added = {s["addr"]: s for s in added_syms}
                for dep in item.get("dependencies") or ():
                    ea = dep.get("expected_address")
                    if ea in by_addr_added:
                        s = by_addr_added[ea]
                        proposed_mappings.append({
                            "old_symbol": dep["symbol"], "target_addr": s["addr"],
                            "canonical_link": s["link_name"], "canonical_name": s["name"],
                            "kind": s["kind"], "method": "research",
                        })
            changed = txn.changed_files()
            all_tomls = sorted({f for f in changed if f.startswith("analysis/symbols/") and f.endswith(".toml")}
                               | set(promoted_tomls))
            invalidate_audit_refs(refs=sorted(reprocess_refs), symbols_changed=set(target_syms) | added_links)
            out_kind = PROMOTED if promoted_entries else RECONCILED
            rec = write_outcome(
                gid, out_kind,
                method="research",
                llm_calls=calls,
                promoted=[f"{a:#x}" for a, _t in promoted_entries],
                tomls=all_tomls,
                ref_files=sorted(f for f in changed if f.startswith("src/") and f.endswith(".c")),
                headers=sorted(f for f in changed if f.startswith("src/include/") and f.endswith(".h")),
                tests=sorted(f for f in changed if f.startswith("tests/") and f.endswith(".py")),
                changed_files=changed,
                created_files=txn.created_files(),
                added_symbols=added_syms,
                proposed_mappings=proposed_mappings,
                unresolved_before=unres_total_before,
                unresolved_after=unres_total_after,
                target_unresolved_before=unres_target_before,
                target_unresolved_after=unres_target_after,
                affected_refs=sorted(reprocess_refs),
                symbols=target_syms,
                history=history,
                summary=last_summary or f"Reconciled {gid}",
            )
            if persist_mappings:
                persist_outcome_mappings(rec)
            return rec

        txn.restore()
        return write_outcome(
            gid, NO_IMPROVEMENT,
            method="research",
            llm_calls=calls,
            complete_search=(complete_search and calls == int(max_calls) and calls > 0),
            reason=feedback or last_summary or "research budget exhausted without verified improvement",
            uncertainties=last_uncertainties,
            history=history,
            symbols=target_syms,
            affected_refs=affected_refs,
        )
    except BaseException:
        txn.restore()
        raise
