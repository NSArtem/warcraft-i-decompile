"""Shared per-unit dependency fingerprinting and cache diagnostics for Wave 4A & 4B.

Replaces the repository-wide `matcher_signature()` cache key with a sound,
dependency-scoped fingerprint built from:
  - compiler/tool/original-binary identity and recovery/research config;
  - translation unit source(s) and recursively included headers (with fail-open
    handling for trigraphs, non-literal/unsupported/unresolved includes, and
    compiler include-override flags/env vars);
  - exact OMF external relocations and `_TEXT` symbols captured by `wc1.t3_audit`
    in the incremental audit state (`build/wave4/audit_state.json` /
    `build/wave4/omf_deps.json`);
  - original-binary target addresses (`call`/`jmp` + LE fixups) for every
    function in the affected translation unit(s);
  - symbol DB projections (address, canonical name, link_name, ABI/proto/conv,
    type, file ownership) for all referenced/unresolved/target/owner symbols;
  - containing data object ownership and recursive struct/typedef layouts;
  - relevant function boundaries/extents and neighboring `src =` ranges;
  - for Wave 4A groups: multi-caller affected refs, target disassembly/data
    neighbors, canonical header declarations + defining headers, allowed edit
    scope, cited differential tests, and relevant established mappings.

Soundness takes precedence over cache hit rate: whenever complete, reliable
dependency metadata cannot be established, fingerprinting fails open (bypass or
explicit conservative global fallback when only a legacy matcher signature was
supplied). Legacy schema v1 cache entries are never fabricated into v2 keys and
never deleted from disk; they are reported explicitly as legacy invalidations.
"""
from bisect import bisect_left, bisect_right
from collections import defaultdict
from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path
import re
import shutil

from . import match, oldcc, path, symbols, t3_audit, wave4_deps

CACHE_SCHEMA_VERSION = 2
OUT_DIR = ("build", "wave4")
AUDIT_STATE_FILE = ("build", "wave4", "audit_state.json")
OMF_DEPS_FILE = ("build", "wave4", "omf_deps.json")

NEIGHBOR_DATA_RADIUS = 0x60
NEIGHBOR_FUNC_TOML_RADIUS = 0x400
EXTENT_OVERLAP_MARGIN = 0x40

_C_TOKEN = re.compile(
    r"""/\*[\s\S]*?(?:\*/|\Z)|//[^\r\n]*|"(?:\\[^\r\n]|[^"\\\r\n])*"|"""
    r"""'(?:\\[^\r\n]|[^'\\\r\n])*'|["']"""
)
_C_SPLICE = re.compile(r"(?:\\|\?\?/)(?:\r?\n|\r)")
_INCLUDE = re.compile(r"(?:#|%:)[ \t\f\v]*(include\w*|import|embed)\b[ \t\f\v]*([^\r\n]*)")
_TRIGRAPH = re.compile(rb"\?\?[=/'()!<>-]")
_FLAG_OVERRIDE_PREFIXES = ("-i", "/i", "-fi", "/fi", "@")
_PROTECTED_TOMLS = frozenset({"analysis/symbols/codegen_promo.toml", "analysis/symbols/clib.toml"})


# ---------------------------------------------------------------------------
# Preprocessor & source-input hashing (conservative fail-open)
# ---------------------------------------------------------------------------

def _c_comments(text):
    """Yield `(left, right, token_text)` for C comments after line-splice handling."""
    pieces, positions, widths = [], [], [0]
    start = removed = 0
    for splice in _C_SPLICE.finditer(text):
        pieces.append(text[start:splice.start()])
        positions.append(splice.start() - removed)
        removed += splice.end() - splice.start()
        widths.append(removed)
        start = splice.end()
    pieces.append(text[start:])
    for token in _C_TOKEN.finditer("".join(pieces)):
        value = token.group()
        if value in ("'", '"') or (value.startswith("/*") and value.find("*/", 2) == -1):
            raise ValueError("unterminated C token in preprocessor input")
        if value.startswith(("//", "/*")):
            left = token.start() + widths[bisect_right(positions, token.start())]
            last = token.end() - 1
            right = last + widths[bisect_right(positions, last)] + 1
            yield left, right, value


def literal_includes(data):
    """Yield literal include paths from raw C/header bytes; raise ValueError on
    trigraphs, unterminated tokens, or unsupported/non-literal include directives."""
    if _TRIGRAPH.search(data):
        raise ValueError("trigraphs in preprocessor input")
    text = _C_SPLICE.sub("", data.decode("latin-1"))
    pieces, offset = [], 0
    for start, end, _ in _c_comments(text):
        pieces.extend((text[offset:start], " "))
        offset = end
    pieces.append(text[offset:])
    for keyword, directive in _INCLUDE.findall("".join(pieces)):
        m = re.fullmatch(r'(?:"([^"]+)"|<([^>]+)>)[ \t\f\v]*', directive)
        if keyword != "include" or not m:
            raise ValueError("unsupported or nonliteral include")
        yield os.fsdecode((m[1] or m[2]).encode("latin-1")).replace("\\", "/")


def source_inputs(src, include_dirs):
    """Hash a source/header file and all recursively included headers.

    Fails open (raises OSError/ValueError) on any dependency we cannot resolve
    conservatively, rather than caching under an incomplete key.
    """
    hashes, pending = {}, [Path(src).resolve()]
    dirs = [Path(d) for d in include_dirs if d is not None]
    while pending:
        fn = pending.pop()
        if fn in hashes:
            continue
        data = fn.read_bytes()
        hashes[fn] = hashlib.sha256(data).hexdigest()
        for name in literal_includes(data):
            deps = [d / name for d in (fn.parent, *dirs) if (d / name).is_file()]
            if not deps:
                raise ValueError(f"unresolved include: {name}")
            pending.extend(f.resolve() for f in deps)
    return {str(fn): digest for fn, digest in sorted(hashes.items(), key=lambda kv: str(kv[0]))}


def unit_source_digest(ref_rel, system_headers=None, repo_root=None, extra_include_dirs=()):
    """Compute `(digest_hex, hashes_dict, error_reason)` for `ref_rel`.

    Returns `(None, None, reason)` on any conservative preprocessor failure
    instead of silently ignoring headers.
    """
    root = Path(repo_root or path())
    src = (root / ref_rel).resolve()
    if system_headers is None:
        try:
            system_headers = Path(oldcc.root()) / "h"
        except Exception:
            system_headers = root / "original" / "watcom" / "10.0a" / "h"
    inc_dirs = [src.parent, root / "src" / "include", Path(system_headers)]
    for d in extra_include_dirs or ():
        if d is not None:
            inc_dirs.append(Path(d))
    try:
        hashes = source_inputs(src, inc_dirs)
        digest = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
        return digest, hashes, None
    except (OSError, ValueError) as ex:
        return None, None, str(ex)


def _has_unsafe_include_flags(plan):
    return any(
        f.lower().startswith(_FLAG_OVERRIDE_PREFIXES)
        for _lbl, flags in plan
        for f in (flags or "").split()
    )


def env_override_reason():
    """Return a reason string if compiler environment overrides disable safe caching."""
    for var in ("INCLUDE", "WCC386"):
        if os.environ.get(var):
            return f"env_override:{var}"
    return None


def tool_signature(repo_root=None):
    """SHA-256 over `original/install/war.exe` and Watcom 10.0a `wcc386.exe` binaries."""
    root = repo_root or path()
    try:
        cc_root = Path(oldcc.root())
        files = [
            Path(os.path.join(root, "original", "install", "war.exe")),
            cc_root / "binnt/wcc386.exe",
            cc_root / "binb/wcc386.exe",
        ]
        return hashlib.sha256(b"".join(hashlib.sha256(f.read_bytes()).digest() for f in files)).hexdigest()
    except OSError:
        return None


def ow2_compiler_digest():
    """Best-effort content digest of the Open Watcom 2 `wcc386` binary on PATH."""
    exe = shutil.which("wcc386")
    if not exe:
        return None
    try:
        return hashlib.sha256(Path(exe).read_bytes()).hexdigest()
    except OSError:
        return None


def ow2_include_dir():
    watcom = os.environ.get("WATCOM")
    if not watcom:
        return None
    h = Path(watcom) / "h"
    return h if h.is_dir() else None


def _sha256_json(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


def _write_json_atomic(fn, data):
    os.makedirs(os.path.dirname(fn), exist_ok=True)
    tmp = f"{fn}.tmp.{os.getpid()}"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1, sort_keys=True, default=str)
    os.replace(tmp, fn)


def _read_json(fn):
    try:
        with open(fn, encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


# ---------------------------------------------------------------------------
# OMF dependency persistence (shared with incremental audit state)
# ---------------------------------------------------------------------------

def stamp_omf_deps(ref_rel, omf_deps, *, declared_cflags=None, plan=None, tool_sig=None,
                   source_digest=None, system_headers=None, repo_root=None):
    """Attach source_digest / plan / tool_sig validity stamps to an `omf_deps` dict."""
    if not isinstance(omf_deps, dict):
        return None
    if source_digest is None:
        source_digest, _h, _err = unit_source_digest(ref_rel, system_headers=system_headers, repo_root=repo_root)
    if plan is None and declared_cflags is not None:
        plan = t3_audit.attempt_plan(declared_cflags)
    if tool_sig is None:
        tool_sig = tool_signature(repo_root=repo_root)
    return {
        "complete": bool(omf_deps.get("complete")),
        "external_symbols": sorted(set(omf_deps.get("external_symbols") or ())),
        "text_symbols": sorted(set(omf_deps.get("text_symbols") or ())),
        "external_relocs": list(omf_deps.get("external_relocs") or ()),
        "has_data_anchors": bool(omf_deps.get("has_data_anchors")),
        "source_digest": source_digest,
        "declared_cflags": declared_cflags,
        "plan": [list(p) for p in plan] if plan is not None else None,
        "tool_sig": tool_sig,
    }


def record_unit_omf_deps(ref_rel, omf_deps, *, declared_cflags=None, plan=None, tool_sig=None,
                         source_digest=None, by_link=None, system_headers=None, repo_root=None):
    """Persist verified OMF dependency metadata for `ref_rel` without corrupting
    or preempting `audit_state.json` bootstrapping."""
    if not ref_rel or not isinstance(omf_deps, dict) or not omf_deps.get("complete"):
        return None
    ref_norm = str(ref_rel).replace("\\", "/")
    root = repo_root or path()
    stamped = stamp_omf_deps(
        ref_norm, omf_deps,
        declared_cflags=declared_cflags, plan=plan, tool_sig=tool_sig,
        source_digest=source_digest, system_headers=system_headers, repo_root=root,
    )
    if not stamped or not stamped.get("source_digest"):
        return None

    # 1. Persist in companion OMF deps cache (`build/wave4/omf_deps.json`)
    omf_path = os.path.join(root, *OMF_DEPS_FILE)
    store = _read_json(omf_path) or {"version": CACHE_SCHEMA_VERSION, "units": {}}
    if not isinstance(store.get("units"), dict):
        store["units"] = {}
    store["version"] = CACHE_SCHEMA_VERSION
    store["units"][ref_norm] = stamped
    try:
        _write_json_atomic(omf_path, store)
    except OSError:
        pass

    # 2. If `audit_state.json` already exists with results, update it in sync too
    state_path = os.path.join(root, *AUDIT_STATE_FILE)
    state = _read_json(state_path)
    if isinstance(state, dict) and isinstance(state.get("results"), dict):
        cache = state.setdefault("omf_deps_cache", {})
        if isinstance(cache, dict):
            cache[ref_norm] = stamped
        um = state.get("unit_meta")
        if isinstance(um, dict) and isinstance(um.get(ref_norm), dict):
            um[ref_norm]["omf_deps"] = stamped
            if isinstance(by_link, dict):
                deps = um[ref_norm].setdefault("deps", {})
                for s in stamped["external_symbols"] + stamped["text_symbols"]:
                    deps[s] = by_link[s]["addr"] if s in by_link else None
        try:
            _write_json_atomic(state_path, state)
        except OSError:
            pass
    return stamped


def load_recorded_omf_deps(repo_root=None):
    """Load persisted OMF dependency metadata from `audit_state.json` and `omf_deps.json`."""
    root = repo_root or path()
    out = {}
    state = _read_json(os.path.join(root, *AUDIT_STATE_FILE))
    if isinstance(state, dict):
        for ref, meta in (state.get("unit_meta") or {}).items():
            if isinstance(meta, dict) and isinstance(meta.get("omf_deps"), dict):
                out[ref.replace("\\", "/")] = dict(meta["omf_deps"], _from_disk=True)
        for ref, d in (state.get("omf_deps_cache") or {}).items():
            if isinstance(d, dict):
                out[ref.replace("\\", "/")] = dict(d, _from_disk=True)
    store = _read_json(os.path.join(root, *OMF_DEPS_FILE))
    if isinstance(store, dict) and isinstance(store.get("units"), dict):
        for ref, d in store["units"].items():
            if isinstance(d, dict):
                out[ref.replace("\\", "/")] = dict(d, _from_disk=True)
    return out


# ---------------------------------------------------------------------------
# Symbol / struct / boundary projection helpers
# ---------------------------------------------------------------------------

def _project_symbol(entry, *, include_confidence=False):
    if not isinstance(entry, dict):
        return None
    kind = entry.get("_kind")
    if kind == "func":
        out = {
            "kind": "func",
            "addr": entry.get("addr"),
            "name": entry.get("name"),
            "link_name": entry.get("link_name"),
            "conv": entry.get("conv", "watcall"),
            "proto": entry.get("proto"),
            "module": entry.get("module"),
            "src": entry.get("src"),
            "ref": entry.get("ref"),
            "ref_verified_by": entry.get("ref_verified_by"),
            "file": entry.get("_file"),
        }
    else:
        out = {
            "kind": kind or "data",
            "addr": entry.get("addr"),
            "name": entry.get("name"),
            "link_name": entry.get("link_name"),
            "type": entry.get("type"),
            "file": entry.get("_file"),
        }
    if include_confidence:
        out["confidence"] = entry.get("confidence")
    return out


def _extract_type_tokens(type_str):
    if not type_str:
        return []
    s = wave4_deps._strip_c_comments(str(type_str))
    return re.findall(r"[A-Za-z_][A-Za-z0-9_]*", s)


def _norm_rel(p_str):
    if not p_str:
        return None
    return os.path.normpath(str(p_str)).replace("\\", "/")


def _extract_c_idents(src_path):
    """Tokenize a single C file (after line-splice expansion) and return its identifiers."""
    raw = Path(src_path).read_bytes()
    if _TRIGRAPH.search(raw):
        raise ValueError("trigraphs in C source")
    text = _C_SPLICE.sub("", raw.decode("latin-1"))
    tokens = wave4_deps.tokenize_c(text)
    return {val for kind, val, _s, _e in tokens if kind == "IDENT"}


def _matching_link_names_for_ident(ident, by_link):
    """Return any keys in `by_link` that match Watcom/C manglings of `ident`."""
    if not ident:
        return []
    cands = (f"{ident}_", f"_{ident}", ident, ident.upper())
    return [k for k in cands if k in by_link]


# ---------------------------------------------------------------------------
# DependencyContext: built once per discovery pass (fast O(N) amortized)
# ---------------------------------------------------------------------------

class DependencyContext:
    """Shared read-only dependency index for computing Wave 4A & 4B fingerprints."""

    def __init__(self, p, funcs, datas, by_link, *, repo_root=None,
                 audit_rows=None, unit_omf_deps=None, established_mappings=None,
                 repo_matcher_sig=None, load_disk_omf_deps=True):
        self.p = p
        self.funcs = funcs if isinstance(funcs, dict) else {}
        if isinstance(datas, dict):
            self.datas = datas
        else:
            self.datas = {
                e["addr"]: e for e in (by_link or {}).values()
                if isinstance(e, dict) and e.get("_kind") == "data" and isinstance(e.get("addr"), int)
            }
        self.by_link = by_link if isinstance(by_link, dict) else {}
        self.repo_root = str(repo_root or path())
        self.established_mappings = established_mappings if isinstance(established_mappings, dict) else {}
        self.repo_matcher_sig = repo_matcher_sig

        # Function boundaries from `p.functions`
        raw_funcs = list(getattr(p, "functions", None) or ())
        self.starts_by_addr = {
            f["start"]: f for f in raw_funcs if isinstance(f, dict) and isinstance(f.get("start"), int)
        }
        self.sorted_starts = sorted(self.starts_by_addr)
        self.sorted_func_addrs = sorted(a for a in self.funcs if isinstance(a, int))
        self.sorted_data_addrs = sorted(a for a in self.datas if isinstance(a, int))

        # Reverse identifier -> DB link names index
        self.by_ident = defaultdict(set)
        for ln, e in self.by_link.items():
            if not isinstance(e, dict):
                continue
            name = e.get("name")
            if name:
                self.by_ident[name].add(ln)
            kind = "function" if e.get("_kind") == "func" else "data"
            cid = wave4_deps.link_to_c_ident(ln, kind=kind)
            if cid:
                self.by_ident[cid].add(ln)

        # DB entries indexed by `ref` or `src` path (captures siblings & mixed T3/T4 files)
        self.entries_by_ref = defaultdict(list)
        by_src_addrs = defaultdict(list)
        for a, e in sorted(self.funcs.items()):
            if not isinstance(e, dict):
                continue
            r = _norm_rel(e.get("ref"))
            s = _norm_rel(e.get("src"))
            if r:
                self.entries_by_ref[r].append(e)
            if s:
                if s != r:
                    self.entries_by_ref[s].append(e)
                by_src_addrs[s].append(a)

        # Existing `src =` object spans for neighboring _TEXT overlap checks
        src_ranges = []
        for s_rel, addrs in by_src_addrs.items():
            lo = min(addrs)
            hi = max(
                (self.starts_by_addr[a]["end"] if a in self.starts_by_addr and self.starts_by_addr[a].get("end") is not None else a + 1)
                for a in addrs
            )
            src_ranges.append((lo, hi, s_rel, tuple(sorted(addrs))))
        src_ranges.sort()
        self.src_ranges = src_ranges
        self.src_range_starts = [x[0] for x in src_ranges]

        # Struct & alias definitions across `src/include/*.h` (parsed once per context!)
        inc_dir = os.path.join(self.repo_root, "src", "include")
        self.structs, self.aliases, self.struct_files, self.alias_files = (
            wave4_deps.parse_header_structs_with_sources(include_dir=inc_dir, repo_root=self.repo_root)
        )

        # Audit rows & OMF dependency metadata
        self.audit_rows_by_addr = {}
        omf_map = load_recorded_omf_deps(repo_root=self.repo_root) if load_disk_omf_deps else {}
        for r in audit_rows or ():
            if not isinstance(r, dict) or not isinstance(r.get("addr"), int):
                continue
            self.audit_rows_by_addr[r["addr"]] = r
            ref = _norm_rel(r.get("ref"))
            if ref and isinstance(r.get("omf_deps"), dict):
                omf_map[ref] = dict(r["omf_deps"])
        if isinstance(unit_omf_deps, dict):
            for ref, d in unit_omf_deps.items():
                if isinstance(d, dict):
                    omf_map[_norm_rel(ref)] = dict(d)
        self.unit_omf_deps = omf_map

        # Lazy per-context caches
        self._orig_refs_cache = {}
        self._source_cache = {}
        self._ident_cache = {}
        self._test_cache = {}
        self._callers_by_target = None
        self._owner_cache = {}
        self._header_decls_cache = {}
        self._header_lines = None
        self._data_spans = None

    def source_inputs_for(self, rel_path, system_headers, extra_include_dirs=()):
        key = (_norm_rel(rel_path), str(system_headers), tuple(str(d) for d in extra_include_dirs if d))
        if key not in self._source_cache:
            self._source_cache[key] = unit_source_digest(
                key[0], system_headers=system_headers, repo_root=self.repo_root,
                extra_include_dirs=extra_include_dirs,
            )
        return self._source_cache[key]

    def c_idents_for(self, rel_path):
        rel = _norm_rel(rel_path)
        if rel not in self._ident_cache:
            try:
                self._ident_cache[rel] = (_extract_c_idents(os.path.join(self.repo_root, rel)), None)
            except (OSError, ValueError) as ex:
                self._ident_cache[rel] = (None, str(ex))
        return self._ident_cache[rel]

    def test_digest(self, test_rel):
        rel = _norm_rel(test_rel)
        if rel not in self._test_cache:
            full = Path(self.repo_root) / rel
            if full.is_file():
                try:
                    self._test_cache[rel] = {
                        "exists": True,
                        "sha256": hashlib.sha256(full.read_bytes()).hexdigest(),
                    }
                except OSError:
                    self._test_cache[rel] = {"exists": False, "unreadable": True}
            else:
                self._test_cache[rel] = {"exists": False}
        return self._test_cache[rel]

    def orig_refs(self, func_addr):
        if func_addr not in self._orig_refs_cache:
            self._orig_refs_cache[func_addr] = wave4_deps._orig_function_refs(
                self.p, func_addr, self.starts_by_addr,
            )
        return self._orig_refs_cache[func_addr]

    def resolve_omf_deps(self, ref_rel, expected_source_digest, expected_plan, expected_tool_sig):
        """Return `(omf_deps_dict, bypass_reason)`. Never returns incomplete or stale OMF deps."""
        rel = _norm_rel(ref_rel)
        d = self.unit_omf_deps.get(rel)
        if not isinstance(d, dict):
            return None, f"missing_omf_deps:{rel}"
        if d.get("complete") is not True:
            return None, f"incomplete_omf_deps:{rel}"
        from_disk = bool(d.get("_from_disk"))
        sd = d.get("source_digest")
        if sd is not None:
            if sd != expected_source_digest:
                return None, f"stale_omf_source_digest:{rel}"
        elif from_disk:
            return None, f"unstamped_omf_deps:{rel}"
        dp = d.get("plan")
        if dp is not None:
            norm_dp = [list(x) for x in dp]
            norm_exp = [list(x) for x in expected_plan]
            if norm_dp != norm_exp:
                return None, f"stale_omf_plan:{rel}"
        elif from_disk:
            return None, f"unstamped_omf_plan:{rel}"
        ts = d.get("tool_sig")
        if expected_tool_sig is not None:
            if ts is not None and ts != expected_tool_sig:
                return None, f"stale_omf_tool_sig:{rel}"
            if ts is None and from_disk:
                return None, f"unstamped_omf_tool_sig:{rel}"
        return {
            "external_symbols": sorted(set(d.get("external_symbols") or ())),
            "text_symbols": sorted(set(d.get("text_symbols") or ())),
            "external_relocs": list(d.get("external_relocs") or ()),
            "has_data_anchors": bool(d.get("has_data_anchors")),
        }, None

    def collect_struct_closure(self, type_str):
        """Recursively collect struct layouts, typedef aliases, and defining header files for `type_str`."""
        sdefs = {}
        adefs = {}
        hdrs = set()
        pending = list(_extract_type_tokens(type_str))
        seen = set()
        while pending:
            tok = pending.pop()
            if tok in seen:
                continue
            seen.add(tok)
            if tok in self.aliases:
                adefs[tok] = self.aliases[tok]
                if tok in self.alias_files:
                    hdrs.add(self.alias_files[tok])
                pending.extend(_extract_type_tokens(self.aliases[tok]))
            if tok in self.structs:
                info = self.structs[tok]
                sdefs[tok] = {
                    "size": info["size"],
                    "align": info["align"],
                    "fields": [list(f) for f in info["fields"]],
                }
                if tok in self.struct_files:
                    hdrs.add(self.struct_files[tok])
                for _off, _sz, _fname, ftype in info["fields"]:
                    pending.extend(_extract_type_tokens(ftype))
        return sdefs, adefs, hdrs

    def _ensure_data_spans(self):
        """Precompute valid containing-owner data spans ONCE per context (O(D) instead of O(N*D))."""
        if self._data_spans is not None:
            return
        spans = []
        all_addrs = self.sorted_data_addrs
        for daddr in all_addrs:
            e = self.datas[daddr]
            dtype = str(e.get("type") or "").strip()
            if not dtype:
                continue
            sz, _ = wave4_deps._parse_type_size_and_align(dtype, self.structs, self.aliases)
            if sz is None or sz <= 1:
                continue
            if sz >= 0x400:
                lo_i = bisect_right(all_addrs, daddr)
                hi_i = bisect_left(all_addrs, daddr + sz)
                interior_n = hi_i - lo_i
                base_st = re.sub(r"^(?:const\s+|volatile\s+)?(?:struct\s+)?", "", dtype.split("[", 1)[0]).strip()
                if interior_n >= 30 or ((daddr + 4) in self.datas and base_st not in self.structs):
                    continue
            m_arr = re.match(r"^(.+?)\s*\[\s*([^\]]+)\s*\]\s*$", dtype)
            elem_type = m_arr.group(1).strip() if m_arr else dtype
            esz = None
            if m_arr:
                esz, _ = wave4_deps._parse_type_size_and_align(elem_type, self.structs, self.aliases)
            st_key = re.sub(r"^(?:const\s+|volatile\s+)?(?:struct\s+)?", "", elem_type).strip()
            spans.append((daddr, daddr + sz, sz, e, dtype, esz, st_key))
        self._data_spans = spans

    def _find_containing_owner_fast(self, addr):
        self._ensure_data_spans()
        best = None
        for daddr, dend, sz, e, dtype, esz, st_key in self._data_spans:
            if daddr >= addr:
                break
            if addr < dend:
                if best is not None and sz >= best["size"]:
                    continue
                rel = addr - daddr
                elem_idx = None
                field_off = rel
                if esz and esz > 0:
                    elem_idx, field_off = divmod(rel, esz)
                field_name = None
                if st_key in self.structs:
                    for foff, fsz, fname, _ft in self.structs[st_key]["fields"]:
                        if foff <= field_off < foff + fsz:
                            field_name = fname
                            break
                best = {
                    "addr": daddr,
                    "addr_hex": f"{daddr:#x}",
                    "name": e.get("name"),
                    "link_name": e.get("link_name"),
                    "type": dtype,
                    "file": e.get("_file"),
                    "size": sz,
                    "offset": rel,
                    "element_index": elem_idx,
                    "field_offset": field_off,
                    "field_name": field_name,
                }
        return best

    def owner_info(self, addr):
        """Containing data owner + exact data type + recursive struct layouts & header files."""
        if addr not in self._owner_cache:
            owner = self._find_containing_owner_fast(addr)
            sdefs = {}
            adefs = {}
            hdrs = set()
            if owner and owner.get("type"):
                sd, ad, hd = self.collect_struct_closure(owner["type"])
                sdefs.update(sd)
                adefs.update(ad)
                hdrs.update(hd)
            exact = self.datas.get(addr)
            if exact and exact.get("type"):
                sd, ad, hd = self.collect_struct_closure(exact["type"])
                sdefs.update(sd)
                adefs.update(ad)
                hdrs.update(hd)
            self._owner_cache[addr] = (owner, sdefs, adefs, hdrs)
        return self._owner_cache[addr]

    def header_declarations(self, ident):
        """Cached equivalent of `wave4_deps.find_header_declarations` reading `src/include/*.h` once."""
        if not ident:
            return []
        if ident in self._header_decls_cache:
            return self._header_decls_cache[ident]
        if self._header_lines is None:
            self._header_lines = []
            inc_dir = os.path.join(self.repo_root, "src", "include")
            if os.path.isdir(inc_dir):
                for fn in sorted(Path(inc_dir).glob("*.h")):
                    rel = os.path.relpath(str(fn), self.repo_root).replace("\\", "/")
                    try:
                        raw_lines = fn.read_text(encoding="latin-1").splitlines()
                    except OSError:
                        continue
                    top_lines = []
                    for lineno, line in enumerate(raw_lines, 1):
                        if line[:1] in (" ", "\t"):
                            continue
                        s = wave4_deps._strip_c_comments(line).strip()
                        if s and not s.startswith("#") and s.endswith(";"):
                            top_lines.append((lineno, s))
                    self._header_lines.append((rel, top_lines))
        pat = re.compile(rf"\b{re.escape(ident)}\b")
        out = []
        for rel, top_lines in self._header_lines:
            for lineno, s in top_lines:
                if pat.search(s):
                    out.append({"file": rel, "line": lineno, "text": s})
        self._header_decls_cache[ident] = out
        return out

    def extents_for_unit(self, func_addrs):
        """Relevant `p.functions` boundaries and neighboring `src =` spans for `func_addrs`."""
        addrs = sorted(a for a in func_addrs if isinstance(a, int))
        if not addrs:
            return {"functions": [], "neighbors": [], "src_neighbors": []}
        own = []
        neighbor_addrs = set()
        lo_span = addrs[0]
        hi_span = addrs[-1]
        for a in addrs:
            f = self.starts_by_addr.get(a)
            end = f.get("end") if f else None
            lim = f.get("limit") if f else None
            own.append([a, end, lim])
            if isinstance(end, int) and end > hi_span:
                hi_span = end
            idx = bisect_right(self.sorted_starts, a)
            if idx < len(self.sorted_starts):
                neighbor_addrs.add(self.sorted_starts[idx])
        # All discovered functions overlapping [lo_span, hi_span + margin]
        i0 = bisect_left(self.sorted_starts, lo_span)
        i1 = bisect_right(self.sorted_starts, hi_span + EXTENT_OVERLAP_MARGIN)
        for j in range(i0, i1):
            neighbor_addrs.add(self.sorted_starts[j])
        neighbors = []
        for na in sorted(neighbor_addrs):
            f = self.starts_by_addr[na]
            neighbors.append([na, f.get("end"), f.get("limit")])
        # Neighboring `src =` ranges that could overlap `_TEXT`
        src_neighbors = []
        s0 = max(0, bisect_left(self.src_range_starts, lo_span - EXTENT_OVERLAP_MARGIN) - 1)
        s1 = bisect_right(self.src_range_starts, hi_span + EXTENT_OVERLAP_MARGIN)
        for lo, hi, s_rel, s_addrs in self.src_ranges[s0:s1]:
            if hi >= lo_span - EXTENT_OVERLAP_MARGIN and lo <= hi_span + EXTENT_OVERLAP_MARGIN:
                src_neighbors.append([lo, hi, s_rel, list(s_addrs)])
        return {"functions": own, "neighbors": neighbors, "src_neighbors": src_neighbors}

    def target_func_evidence(self, target_addr, max_insns=100):
        """Mirror `wave4a._disasm_target_func`: extent, annotated callees/fixups, and direct callers."""
        f = self.starts_by_addr.get(target_addr)
        extent = [target_addr, f.get("end"), f.get("limit")] if f else [target_addr, None, None]
        referenced = {}
        if f and isinstance(f.get("end"), int):
            insns = getattr(self.p, "insns", None) or {}
            fix_at = getattr(self.p, "fix_at", None) or {}
            count = 0
            for pc in range(target_addr, f["end"]):
                ins = insns.get(pc)
                if ins is None:
                    continue
                if ins.mnemonic in ("call", "jmp") and re.fullmatch(r"0x[0-9a-fA-F]+", ins.op_str):
                    t = int(ins.op_str, 16)
                    referenced[t] = {
                        "func": _project_symbol(self.funcs.get(t), include_confidence=True),
                        "data": _project_symbol(self.datas.get(t), include_confidence=True),
                    }
                for off in range(pc, pc + ins.size):
                    if off in fix_at:
                        t = fix_at[off][1]
                        referenced[t] = {
                            "func": _project_symbol(self.funcs.get(t), include_confidence=True),
                            "data": _project_symbol(self.datas.get(t), include_confidence=True),
                        }
                count += 1
                if count >= max_insns:
                    break
        if self._callers_by_target is None:
            by_tgt = defaultdict(list)
            insns = getattr(self.p, "insns", None) or {}
            for st in self.sorted_starts:
                finfo = self.starts_by_addr[st]
                end = finfo.get("end")
                if not isinstance(end, int):
                    continue
                seen_in_fn = set()
                for pc in range(st, end):
                    ins = insns.get(pc)
                    if ins and ins.mnemonic in ("call", "jmp") and re.fullmatch(r"0x[0-9a-fA-F]+", ins.op_str):
                        tgt = int(ins.op_str, 16)
                        if tgt not in seen_in_fn:
                            seen_in_fn.add(tgt)
                            if len(by_tgt[tgt]) < 12:
                                by_tgt[tgt].append([
                                    st, end, _project_symbol(self.funcs.get(st), include_confidence=True),
                                ])
            self._callers_by_target = by_tgt
        return {
            "extent": extent,
            "referenced": {f"{a:#x}": v for a, v in sorted(referenced.items())},
            "callers": list(self._callers_by_target.get(target_addr, ())),
        }

    def target_data_evidence(self, target_addr):
        """Mirror `wave4a._dump_target_data`: `±0x60` nearby `[[data]]` entries + containing owner."""
        lo = bisect_left(self.sorted_data_addrs, target_addr - NEIGHBOR_DATA_RADIUS)
        hi = bisect_right(self.sorted_data_addrs, target_addr + NEIGHBOR_DATA_RADIUS)
        neighbors = []
        sdefs = {}
        adefs = {}
        hdrs = set()
        for a in self.sorted_data_addrs[lo:hi]:
            e = self.datas[a]
            neighbors.append(_project_symbol(e, include_confidence=True))
            if e.get("type"):
                sd, ad, hd = self.collect_struct_closure(e["type"])
                sdefs.update(sd)
                adefs.update(ad)
                hdrs.update(hd)
        owner, osd, oad, ohd = self.owner_info(target_addr)
        sdefs.update(osd)
        adefs.update(oad)
        hdrs.update(ohd)
        return {
            "addr": target_addr,
            "neighbors": neighbors,
            "owner": owner,
            "structs": sdefs,
            "aliases": adefs,
        }, hdrs

    def allowed_edit_scope(self, group):
        """Mirror `wave4a._allowed_edit_scope` using indexed `self.funcs`."""
        affected_refs = sorted({_norm_rel(r) for r in (group.get("affected_refs") or ()) if r})
        allowed_headers = set()
        for ref in affected_refs:
            for inc in wave4_deps._resolve_local_includes(ref, self.repo_root):
                if inc != ref and inc.startswith("src/include/") and inc != "src/include/war.h":
                    allowed_headers.add(inc)
        allowed_tests = set()
        allowed_tomls = set()
        for af in group.get("affected_functions") or ():
            if af.get("toml") and af["toml"] not in _PROTECTED_TOMLS:
                allowed_tomls.add(af["toml"])
            ns, err = symbols.parse_ref_verified_by_nodes(af.get("ref_verified_by") or "")
            if not err:
                for tf, _node in ns:
                    allowed_tests.add(tf.replace("\\", "/"))
        db = group.get("db_entry")
        if isinstance(db, dict) and db.get("_file") and db["_file"] not in _PROTECTED_TOMLS:
            allowed_tomls.add(db["_file"])
        taddr = group.get("target_address")
        if isinstance(taddr, int):
            lo = bisect_left(self.sorted_func_addrs, taddr - NEIGHBOR_FUNC_TOML_RADIUS)
            hi = bisect_right(self.sorted_func_addrs, taddr + NEIGHBOR_FUNC_TOML_RADIUS)
            for a in self.sorted_func_addrs[lo:hi]:
                e = self.funcs[a]
                if e.get("_file") and e["_file"] not in _PROTECTED_TOMLS:
                    allowed_tomls.add(e["_file"])
        return {
            "refs": affected_refs,
            "headers": sorted(allowed_headers),
            "tests": sorted(allowed_tests),
            "tomls": sorted(allowed_tomls),
        }


# ---------------------------------------------------------------------------
# Fingerprint results & calculators (Wave 4B and Wave 4A)
# ---------------------------------------------------------------------------

@dataclass
class FingerprintResult:
    key: str | None
    section_digests: dict = field(default_factory=dict)
    mode: str = "bypass"       # "dependency_scoped" | "fallback_global" | "bypass"
    bypass_reason: str | None = None


def _finalize_fingerprint(sections, mode):
    section_digests = {k: _sha256_json(v) for k, v in sorted(sections.items())}
    key = _sha256_json({"schema": CACHE_SCHEMA_VERSION, "mode": mode, "sections": sections})
    return FingerprintResult(key=key, section_digests=section_digests, mode=mode, bypass_reason=None)


def _bypass(reason):
    return FingerprintResult(key=None, section_digests={}, mode="bypass", bypass_reason=reason)


def _collect_cited_test_digests(entries, repo_root, dep_ctx=None):
    digs = {}
    for e in entries or ():
        rvb = e.get("ref_verified_by") if isinstance(e, dict) else None
        if not rvb:
            continue
        ns, err = symbols.parse_ref_verified_by_nodes(rvb)
        if err:
            continue
        for tf, _node in ns:
            rel = _norm_rel(tf)
            if rel in digs:
                continue
            if dep_ctx is not None:
                digs[rel] = dep_ctx.test_digest(rel)
            else:
                full = Path(repo_root) / rel
                if full.is_file():
                    try:
                        digs[rel] = {
                            "exists": True,
                            "sha256": hashlib.sha256(full.read_bytes()).hexdigest(),
                        }
                    except OSError:
                        digs[rel] = {"exists": False, "unreadable": True}
                else:
                    digs[rel] = {"exists": False}
    return digs


def _tool_sig_from_settings(settings):
    ti = settings.get("tool_inputs") if isinstance(settings, dict) else None
    if isinstance(ti, list) and len(ti) == 3 and all(isinstance(x, str) and len(x) == 64 for x in ti):
        try:
            return hashlib.sha256(b"".join(bytes.fromhex(x) for x in ti)).hexdigest()
        except ValueError:
            return None
    return None


def wave4b_fingerprint(settings, system_headers, cand, siblings, *,
                       dep_ctx=None, matcher_sig=None, init_bypass_reason=None, repo_root=None):
    """Compute dependency-scoped Wave 4B fingerprint for one candidate and its translation unit."""
    env_reason = env_override_reason()
    if env_reason:
        return _bypass(env_reason)
    if settings is None:
        return _bypass(init_bypass_reason or "missing_settings")
    if not isinstance(cand, dict) or not cand.get("ref"):
        return _bypass("invalid_candidate")

    root = str(repo_root or (dep_ctx.repo_root if dep_ctx is not None else path()))
    ref_rel = _norm_rel(cand["ref"])
    try:
        plan = t3_audit.attempt_plan(cand["declared_cflags"])
    except (KeyError, ValueError, TypeError) as ex:
        return _bypass(f"invalid_cflags:{ex}")
    if _has_unsafe_include_flags(plan):
        return _bypass("unsupported_include_flag")

    if dep_ctx is not None:
        src_dig, files, src_err = dep_ctx.source_inputs_for(ref_rel, system_headers)
    else:
        src_dig, files, src_err = unit_source_digest(ref_rel, system_headers=system_headers, repo_root=root)
    if src_err or files is None:
        return _bypass(f"source_inputs:{src_err}")

    unit_fields = ("addr", "name", "link_name", "ref", "declared_cc", "declared_cflags",
                   "ref_verified_by", "conv", "proto", "toml")
    sib_list = list(siblings or ())
    if not any(s.get("addr") == cand.get("addr") for s in sib_list):
        sib_list.append(cand)
    unit_cands = [
        {k: c.get(k) for k in unit_fields}
        for c in sorted(sib_list, key=lambda c: c.get("addr", -1))
    ]
    test_digs = _collect_cited_test_digests(sib_list, root, dep_ctx=dep_ctx)

    # Conservative global fallback when only a legacy matcher_sig was supplied (no DependencyContext)
    if dep_ctx is None:
        if not matcher_sig:
            return _bypass("missing_dependency_context")
        sections = {
            "settings": settings,
            "sources": files,
            "plan": plan,
            "unit": {"addr": cand["addr"], "candidates": unit_cands},
            "tests": test_digs,
            "matcher": matcher_sig,
        }
        return _finalize_fingerprint(sections, "fallback_global")

    # Dependency-scoped mode: require valid, complete, up-to-date OMF metadata for this unit
    exp_tool_sig = _tool_sig_from_settings(settings)
    omf_deps, omf_err = dep_ctx.resolve_omf_deps(ref_rel, src_dig, plan, exp_tool_sig)
    if omf_err or omf_deps is None:
        return _bypass(omf_err or "missing_omf_deps")

    c_idents, id_err = dep_ctx.c_idents_for(ref_rel)
    if id_err or c_idents is None:
        return _bypass(f"tokenize_c:{id_err}")

    # Collect all DB entries sharing this translation unit (T4 siblings + any T3/other DB funcs on ref)
    ref_db_entries = dep_ctx.entries_by_ref.get(ref_rel, ())
    all_unit_entries = list(sib_list) + list(ref_db_entries)
    test_digs.update(_collect_cited_test_digests(ref_db_entries, root, dep_ctx=dep_ctx))

    # Build exact relevant symbol closure
    sym_names = set(omf_deps["external_symbols"]) | set(omf_deps["text_symbols"])
    for c in all_unit_entries:
        ln = c.get("link_name")
        if ln:
            sym_names.add(ln)
    # Include any unresolved symbols reported on cached audit rows for this unit
    unit_func_addrs = set()
    for c in all_unit_entries:
        if isinstance(c.get("addr"), int):
            unit_func_addrs.add(c["addr"])
    for ln in omf_deps["text_symbols"]:
        e = dep_ctx.by_link.get(ln)
        if e and isinstance(e.get("addr"), int):
            unit_func_addrs.add(e["addr"])

    orig_target_addrs = set()
    for a in sorted(unit_func_addrs):
        orig_target_addrs.update(dep_ctx.orig_refs(a).keys())
        arow = dep_ctx.audit_rows_by_addr.get(a)
        if isinstance(arow, dict):
            for att in arow.get("attempts") or ():
                for u in att.get("unresolved") or ():
                    if u.get("symbol"):
                        sym_names.add(u["symbol"])
                    oc = u.get("original_candidate")
                    if isinstance(oc, int):
                        orig_target_addrs.add(oc)
                        if isinstance(u.get("addend"), int) and u["addend"] != 0:
                            orig_target_addrs.add(oc + u["addend"])

    # Also capture any DB symbols whose C identifier appears in this .c file itself
    for ident in c_idents:
        for ln in dep_ctx.by_ident.get(ident, ()):
            sym_names.add(ln)

    # Effective target addresses from resolved OMF relocations + addends
    reloc_eff_addrs = set()
    for rel in omf_deps["external_relocs"]:
        te = dep_ctx.by_link.get(rel.get("symbol"))
        if te and isinstance(te.get("addr"), int):
            base_a = te["addr"]
            reloc_eff_addrs.add(base_a)
            addend = rel.get("addend")
            if isinstance(addend, int) and addend != 0:
                reloc_eff_addrs.add(base_a + addend)

    symbols_proj = {
        s: _project_symbol(dep_ctx.by_link.get(s))
        for s in sorted(sym_names)
    }
    addr_targets = sorted(orig_target_addrs | reloc_eff_addrs)
    addr_proj = {
        f"{a:#x}": {
            "func": _project_symbol(dep_ctx.funcs.get(a)),
            "data": _project_symbol(dep_ctx.datas.get(a)),
        }
        for a in addr_targets
    }

    # Containing data owners & recursive struct definitions for all relevant data addresses
    owners_proj = {}
    struct_defs = {}
    alias_defs = {}
    extra_hdrs = set()
    data_addrs = set(addr_targets)
    for s in sym_names:
        e = dep_ctx.by_link.get(s)
        if e and e.get("_kind") == "data" and isinstance(e.get("addr"), int):
            data_addrs.add(e["addr"])
    for a in sorted(data_addrs):
        if a in dep_ctx.funcs and a not in dep_ctx.datas:
            continue
        owner, sd, ad, hd = dep_ctx.owner_info(a)
        if owner is not None:
            owners_proj[f"{a:#x}"] = owner
        struct_defs.update(sd)
        alias_defs.update(ad)
        extra_hdrs.update(hd)

    # Hash any header file defining a relevant struct/alias not already covered by `files`
    extra_header_hashes = {}
    for hdr in sorted(extra_hdrs):
        hdr_full = Path(root) / hdr
        if hdr_full.is_file():
            _d, h_map, h_err = dep_ctx.source_inputs_for(hdr, system_headers)
            if h_err or h_map is None:
                return _bypass(f"struct_header_inputs:{hdr}:{h_err}")
            extra_header_hashes.update(h_map)

    all_sources = dict(files)
    all_sources.update(extra_header_hashes)

    sections = {
        "settings": settings,
        "sources": all_sources,
        "plan": plan,
        "unit": {
            "addr": cand["addr"],
            "candidates": unit_cands,
            "db_entries_on_ref": [_project_symbol(e) for e in sorted(ref_db_entries, key=lambda x: x.get("addr", -1))],
        },
        "omf": omf_deps,
        "symbols": {"by_link": symbols_proj, "by_addr": addr_proj},
        "owners": {"containing": owners_proj, "structs": struct_defs, "aliases": alias_defs},
        "extents": dep_ctx.extents_for_unit(unit_func_addrs),
        "tests": test_digs,
    }
    return _finalize_fingerprint(sections, "dependency_scoped")


def _summarize_group_deps(group):
    out = []
    for dep in group.get("dependencies") or ():
        if not isinstance(dep, dict):
            continue
        out.append({
            "symbol": dep.get("symbol"),
            "ident": dep.get("ident"),
            "kind": dep.get("kind"),
            "classification": dep.get("classification"),
            "expected_address": dep.get("expected_address"),
            "address_lead": dep.get("address_lead"),
            "ambiguous": dep.get("ambiguous"),
            "conflict_addresses": list(dep.get("conflict_addresses") or ()),
            "relocation_kinds": list(dep.get("relocation_kinds") or ()),
            "addends": list(dep.get("addends") or ()),
            "evidence": list(dep.get("evidence") or ()),
            "blockers": list(dep.get("blockers") or ()),
            "db_entry": dep.get("db_entry"),
            "containing_owner": dep.get("containing_owner"),
            "canonical_header_decls": list(dep.get("canonical_header_decls") or ()),
        })
    out.sort(key=lambda d: (d.get("symbol") or "", d.get("expected_address") or -1))
    return out


def wave4a_fingerprint(settings, system_headers, group, *,
                       dep_ctx=None, matcher_sig=None, ow2_headers=None,
                       init_bypass_reason=None, repo_root=None):
    """Compute dependency-scoped Wave 4A fingerprint for a (potentially multi-caller) group."""
    env_reason = env_override_reason()
    if env_reason:
        return _bypass(env_reason)
    if settings is None:
        return _bypass(init_bypass_reason or "missing_settings")
    if not isinstance(group, dict) or not group.get("group_id"):
        return _bypass("invalid_group")

    root = str(repo_root or (dep_ctx.repo_root if dep_ctx is not None else path()))
    affected_refs = sorted({_norm_rel(r) for r in (group.get("affected_refs") or ()) if r})
    if not affected_refs:
        return _bypass("no_affected_refs")

    extra_inc = (ow2_headers,) if ow2_headers else ()
    sources = {}
    ref_digests = {}
    plans = {}
    for ref in affected_refs:
        ref_full = Path(root) / ref
        try:
            decl_cc = match.file_cc(str(ref_full))
            decl_cflags = t3_audit.short_flags(match.file_cflags(str(ref_full)))
            plan = t3_audit.attempt_plan(decl_cflags)
        except (OSError, SystemExit, ValueError) as ex:
            return _bypass(f"ref_header_flags:{ref}:{ex}")
        if _has_unsafe_include_flags(plan):
            return _bypass(f"unsupported_include_flag:{ref}")
        plans[ref] = {"declared_cc": decl_cc, "declared_cflags": decl_cflags, "plan": plan}
        if dep_ctx is not None:
            dig, hmap, err = dep_ctx.source_inputs_for(ref, system_headers, extra_include_dirs=extra_inc)
        else:
            dig, hmap, err = unit_source_digest(ref, system_headers=system_headers, repo_root=root,
                                                extra_include_dirs=extra_inc)
        if err or hmap is None:
            return _bypass(f"source_inputs:{ref}:{err}")
        sources[ref] = hmap
        ref_digests[ref] = dig

    affected_funcs = list(group.get("affected_functions") or ())
    test_digs = _collect_cited_test_digests(affected_funcs, root, dep_ctx=dep_ctx)

    group_summary = {
        "group_id": group["group_id"],
        "task_kind": group.get("task_kind", "reconcile"),
        "kind": group.get("kind"),
        "classification": group.get("classification"),
        "mechanical": bool(group.get("mechanical")),
        "target_address": group.get("target_address"),
        "symbols": sorted(set(group.get("symbols") or ())),
        "db_entry": group.get("db_entry"),
        "dependencies": _summarize_group_deps(group),
    }

    # Conservative global fallback when only a legacy matcher_sig was supplied (no DependencyContext)
    if dep_ctx is None:
        if not matcher_sig:
            return _bypass("missing_dependency_context")
        sections = {
            "settings": settings,
            "group": group_summary,
            "sources": sources,
            "plans": plans,
            "tests": test_digs,
            "matcher": matcher_sig,
        }
        return _finalize_fingerprint(sections, "fallback_global")

    # Dependency-scoped mode: require complete, up-to-date OMF deps for EVERY affected ref
    exp_tool_sig = _tool_sig_from_settings(settings)
    omf_by_ref = {}
    units_proj = {}
    all_unit_func_addrs = set()
    sym_names = set(group_summary["symbols"])
    orig_target_addrs = set()
    reloc_eff_addrs = set()
    extra_hdrs = set()

    for ref in affected_refs:
        # Note: OMF deps are stamped with the 10.0a source_digest (without OW2 system headers)
        dig_10a, _h10, err_10a = dep_ctx.source_inputs_for(ref, system_headers)
        if err_10a or dig_10a is None:
            return _bypass(f"source_inputs_10a:{ref}:{err_10a}")
        omf_d, omf_err = dep_ctx.resolve_omf_deps(ref, dig_10a, plans[ref]["plan"], exp_tool_sig)
        if omf_err or omf_d is None:
            return _bypass(omf_err or f"missing_omf_deps:{ref}")
        omf_by_ref[ref] = omf_d
        sym_names.update(omf_d["external_symbols"])
        sym_names.update(omf_d["text_symbols"])

        c_idents, id_err = dep_ctx.c_idents_for(ref)
        if id_err or c_idents is None:
            return _bypass(f"tokenize_c:{ref}:{id_err}")
        for ident in c_idents:
            for ln in dep_ctx.by_ident.get(ident, ()):
                sym_names.add(ln)

        ref_db_entries = dep_ctx.entries_by_ref.get(ref, ())
        test_digs.update(_collect_cited_test_digests(ref_db_entries, root, dep_ctx=dep_ctx))
        units_proj[ref] = [
            _project_symbol(e, include_confidence=True)
            for e in sorted(ref_db_entries, key=lambda x: x.get("addr", -1))
        ]
        for e in ref_db_entries:
            if e.get("link_name"):
                sym_names.add(e["link_name"])
            if isinstance(e.get("addr"), int):
                all_unit_func_addrs.add(e["addr"])
        for ln in omf_d["text_symbols"]:
            e = dep_ctx.by_link.get(ln)
            if e and isinstance(e.get("addr"), int):
                all_unit_func_addrs.add(e["addr"])
        for rel in omf_d["external_relocs"]:
            te = dep_ctx.by_link.get(rel.get("symbol"))
            if te and isinstance(te.get("addr"), int):
                reloc_eff_addrs.add(te["addr"])
                addend = rel.get("addend")
                if isinstance(addend, int) and addend != 0:
                    reloc_eff_addrs.add(te["addr"] + addend)

    for af in affected_funcs:
        if isinstance(af.get("addr"), int):
            all_unit_func_addrs.add(af["addr"])
        if af.get("link_name"):
            sym_names.add(af["link_name"])

    # Original-binary target addresses for EVERY function in EVERY affected ref (including siblings)
    for a in sorted(all_unit_func_addrs):
        orig_target_addrs.update(dep_ctx.orig_refs(a).keys())
        arow = dep_ctx.audit_rows_by_addr.get(a)
        if isinstance(arow, dict):
            for att in arow.get("attempts") or ():
                for u in att.get("unresolved") or ():
                    if u.get("symbol"):
                        sym_names.add(u["symbol"])
                    oc = u.get("original_candidate")
                    if isinstance(oc, int):
                        orig_target_addrs.add(oc)
                        if isinstance(u.get("addend"), int) and u["addend"] != 0:
                            orig_target_addrs.add(oc + u["addend"])

    # Group dependencies: match any DB symbol with the same C identifier (for ambiguous/newly added symbols),
    # capture expected/lead/conflict addresses, and capture headers from `canonical_header_decls`
    dep_target_addrs = set()
    taddr = group.get("target_address")
    if isinstance(taddr, int):
        dep_target_addrs.add(taddr)
    for dep in group.get("dependencies") or ():
        if not isinstance(dep, dict):
            continue
        if dep.get("symbol"):
            sym_names.add(dep["symbol"])
        ident = dep.get("ident")
        if ident:
            sym_names.update(dep_ctx.by_ident.get(ident, ()))
            sym_names.update(_matching_link_names_for_ident(ident, dep_ctx.by_link))
        for fld in ("expected_address", "address_lead"):
            v = dep.get(fld)
            if isinstance(v, int):
                dep_target_addrs.add(v)
        for ch in dep.get("conflict_addresses") or ():
            try:
                dep_target_addrs.add(int(str(ch), 16))
            except ValueError:
                pass
        for hd in dep.get("canonical_header_decls") or ():
            if isinstance(hd, dict) and hd.get("file"):
                extra_hdrs.add(_norm_rel(hd["file"]))
        co = dep.get("containing_owner")
        if isinstance(co, dict) and isinstance(co.get("addr"), int):
            dep_target_addrs.add(co["addr"])

    # Target binary/DB evidence (function disassembly callees/callers OR data ±0x60 neighbors)
    target_evidence = {}
    owners_proj = {}
    struct_defs = {}
    alias_defs = {}

    if isinstance(taddr, int):
        if group.get("kind") == "function":
            target_evidence["target_func"] = dep_ctx.target_func_evidence(taddr)
        else:
            td_ev, td_hdrs = dep_ctx.target_data_evidence(taddr)
            target_evidence["target_data"] = td_ev
            extra_hdrs.update(td_hdrs)
            interiors = {}
            for dep in group.get("dependencies") or ():
                ea = dep.get("expected_address") if isinstance(dep, dict) else None
                if isinstance(ea, int) and ea != taddr and f"{ea:#x}" not in interiors:
                    ie, ih = dep_ctx.target_data_evidence(ea)
                    interiors[f"{ea:#x}"] = ie
                    extra_hdrs.update(ih)
            if interiors:
                target_evidence["interior_data"] = interiors

    # Project all relevant symbols and addresses + containing owners & recursive struct definitions
    symbols_proj = {
        s: _project_symbol(dep_ctx.by_link.get(s), include_confidence=True)
        for s in sorted(sym_names)
    }
    all_addrs = sorted(orig_target_addrs | reloc_eff_addrs | dep_target_addrs)
    addr_proj = {
        f"{a:#x}": {
            "func": _project_symbol(dep_ctx.funcs.get(a), include_confidence=True),
            "data": _project_symbol(dep_ctx.datas.get(a), include_confidence=True),
        }
        for a in all_addrs
    }

    data_addrs = set(all_addrs)
    for s in sym_names:
        e = dep_ctx.by_link.get(s)
        if e and e.get("_kind") == "data" and isinstance(e.get("addr"), int):
            data_addrs.add(e["addr"])
    for a in sorted(data_addrs):
        if a in dep_ctx.funcs and a not in dep_ctx.datas:
            continue
        owner, sd, ad, hd = dep_ctx.owner_info(a)
        if owner is not None:
            owners_proj[f"{a:#x}"] = owner
        struct_defs.update(sd)
        alias_defs.update(ad)
        extra_hdrs.update(hd)

    # Also capture canonical header declarations for any DB symbol found at relevant addresses
    # (catches newly added/edited declarations in src/include/*.h for previously missing targets)
    extra_hdr_decls = {}
    for a in all_addrs:
        for tbl in (dep_ctx.funcs, dep_ctx.datas):
            e = tbl.get(a)
            if e and e.get("name") and e["name"] not in extra_hdr_decls:
                decls = dep_ctx.header_declarations(e["name"])
                if decls:
                    extra_hdr_decls[e["name"]] = decls
                    for hd in decls:
                        if hd.get("file"):
                            extra_hdrs.add(_norm_rel(hd["file"]))

    # Hash all extra headers (canonical decl headers + struct-defining headers) recursively
    extra_header_hashes = {}
    for hdr in sorted(extra_hdrs):
        hdr_full = Path(root) / hdr
        if hdr_full.is_file():
            _d, hmap, herr = dep_ctx.source_inputs_for(hdr, system_headers, extra_include_dirs=extra_inc)
            if herr or hmap is None:
                return _bypass(f"extra_header_inputs:{hdr}:{herr}")
            extra_header_hashes[hdr] = hmap

    # Relevant established mappings (for group symbols + any unresolved symbol in affected refs)
    mappings_proj = {
        s: dep_ctx.established_mappings.get(s)
        for s in sorted(sym_names)
        if s in dep_ctx.established_mappings or s in group_summary["symbols"]
    }

    # Extents across all affected units + target/conflict candidate functions
    extent_addrs = set(all_unit_func_addrs)
    for a in dep_target_addrs:
        if a in dep_ctx.starts_by_addr:
            extent_addrs.add(a)

    sections = {
        "settings": settings,
        "group": group_summary,
        "sources": {"refs": sources, "extra_headers": extra_header_hashes},
        "plans": plans,
        "units": {"by_ref": units_proj, "omf": omf_by_ref},
        "symbols": {
            "by_link": symbols_proj,
            "by_addr": addr_proj,
            "canonical_header_decls": extra_hdr_decls,
        },
        "owners": {"containing": owners_proj, "structs": struct_defs, "aliases": alias_defs},
        "target_evidence": target_evidence,
        "extents": dep_ctx.extents_for_unit(extent_addrs),
        "scope": dep_ctx.allowed_edit_scope(group),
        "tests": test_digs,
        "mappings": mappings_proj,
    }
    return _finalize_fingerprint(sections, "dependency_scoped")


# ---------------------------------------------------------------------------
# Cache persistence, schema v2 lookup, legacy detection & diagnostics
# ---------------------------------------------------------------------------

@dataclass
class CacheLookup:
    hit: bool
    status: str         # hit | hit_preserved_unrelated | miss_cold | miss_dep_changed | miss_legacy_schema | bypass_uncertain
    key: str | None = None
    detail: str | None = None


def write_cache_entry(cache_file, fp_res, settings, result, *, repo_state_hint=None):
    """Atomically persist a schema v2 cache entry."""
    key = fp_res.key if isinstance(fp_res, FingerprintResult) else fp_res
    if not key:
        return
    rec = {
        "cache_schema": CACHE_SCHEMA_VERSION,
        "fingerprint": key,
        "fingerprint_mode": fp_res.mode if isinstance(fp_res, FingerprintResult) else "legacy_key",
        "section_digests": fp_res.section_digests if isinstance(fp_res, FingerprintResult) else {},
        "repo_state_hint": repo_state_hint,
        "settings": settings,
        "result": result,
    }
    _write_json_atomic(cache_file, rec)


def _is_valid_v2_record(rec, expected_key, settings, complete_check):
    return (
        isinstance(rec, dict)
        and rec.get("cache_schema") == CACHE_SCHEMA_VERSION
        and rec.get("fingerprint") == expected_key
        and rec.get("settings") == settings
        and complete_check(rec.get("result"))
    )


def _diff_sections(old_digests, new_digests):
    if not isinstance(old_digests, dict) or not isinstance(new_digests, dict):
        return []
    keys = sorted(set(old_digests) | set(new_digests))
    return [k for k in keys if old_digests.get(k) != new_digests.get(k)]


def classify_cache_lookup(cache_dir, fp_res, settings, complete_check, *, repo_state_hint=None):
    """Look up `fp_res` in `cache_dir` and classify hits, preservations,
    relevant invalidations, legacy schema invalidations, and uncertain bypasses.

    Never deletes or mutates legacy or historical files in `cache_dir`.
    """
    if isinstance(fp_res, FingerprintResult):
        key = fp_res.key
        if key is None:
            return CacheLookup(hit=False, status="bypass_uncertain", key=None, detail=fp_res.bypass_reason)
        cur_sections = fp_res.section_digests
    else:
        key = fp_res
        if not key:
            return CacheLookup(hit=False, status="bypass_uncertain", key=None, detail="no_fingerprint")
        cur_sections = {}

    target_file = Path(cache_dir) / f"{key}.json"
    if target_file.is_file():
        try:
            rec = json.loads(target_file.read_bytes())
        except (OSError, ValueError):
            return CacheLookup(hit=False, status="miss_legacy_schema", key=key, detail="malformed_cache_json")
        if _is_valid_v2_record(rec, key, settings, complete_check):
            old_hint = rec.get("repo_state_hint")
            preserved = (
                repo_state_hint is not None
                and old_hint is not None
                and old_hint != repo_state_hint
            )
            return CacheLookup(
                hit=True,
                status="hit_preserved_unrelated" if preserved else "hit",
                key=key,
                detail="unrelated_repo_change" if preserved else None,
            )
        schema = rec.get("cache_schema") if isinstance(rec, dict) else None
        if schema != CACHE_SCHEMA_VERSION:
            return CacheLookup(
                hit=False, status="miss_legacy_schema", key=key,
                detail=f"obsolete_schema:{schema}",
            )
        return CacheLookup(hit=False, status="miss_dep_changed", key=key, detail="settings_or_record_mismatch")

    # Exact key absent: inspect any prior entries in `cache_dir` to distinguish
    # relevant dependency invalidation vs legacy schema invalidation vs cold miss.
    d = Path(cache_dir)
    if not d.is_dir():
        return CacheLookup(hit=False, status="miss_cold", key=key)

    saw_v2_same_settings = None
    saw_v2_diff_settings = False
    saw_legacy_or_invalid = False
    legacy_detail = None

    for fn in sorted(d.glob("*.json")):
        try:
            rec = json.loads(fn.read_bytes())
        except (OSError, ValueError):
            saw_legacy_or_invalid = True
            legacy_detail = legacy_detail or "malformed_cache_json"
            continue
        if not isinstance(rec, dict) or rec.get("cache_schema") != CACHE_SCHEMA_VERSION:
            saw_legacy_or_invalid = True
            old_schema = rec.get("cache_schema") if isinstance(rec, dict) else None
            old_ver = (rec.get("settings") or {}).get("version") if isinstance(rec, dict) and isinstance(rec.get("settings"), dict) else None
            legacy_detail = legacy_detail or f"legacy_schema:{old_schema or 'v1'}(version={old_ver})"
            continue
        if rec.get("settings") == settings:
            if not complete_check(rec.get("result")):
                continue
            # Prefer newest entry for section-diff reporting
            ts = (rec.get("result") or {}).get("ts") or ""
            if saw_v2_same_settings is None or ts >= saw_v2_same_settings[0]:
                saw_v2_same_settings = (ts, rec)
        else:
            res = rec.get("result")
            if isinstance(res, dict) and res.get("complete_search") is True:
                saw_v2_diff_settings = True

    if saw_v2_same_settings is not None:
        changed = _diff_sections(saw_v2_same_settings[1].get("section_digests"), cur_sections)
        detail = ",".join(changed) if changed else "dependency_changed"
        return CacheLookup(hit=False, status="miss_dep_changed", key=key, detail=detail)
    if saw_v2_diff_settings:
        return CacheLookup(hit=False, status="miss_dep_changed", key=key, detail="settings_changed")
    if saw_legacy_or_invalid:
        return CacheLookup(hit=False, status="miss_legacy_schema", key=key, detail=legacy_detail)
    return CacheLookup(hit=False, status="miss_cold", key=key)


class CacheDiagnostics:
    """Observable cache metrics & deduplicated event log for `RetryCache` / `ReconcileCache`."""

    def __init__(self, stage_label):
        self.stage_label = stage_label
        self.last_pass = self._empty_counts()
        self._observed = {}          # (item_id, status, key_or_detail) -> dict
        self._emitted_logs = set()   # deduplicate repeated per-pass log lines

    @staticmethod
    def _empty_counts():
        return {
            "hits": 0,
            "preserved_unrelated": 0,
            "invalidated_dep_change": 0,
            "invalidated_legacy_schema": 0,
            "bypassed_uncertain": 0,
            "cold_misses": 0,
            "in_run_requeued": 0,
        }

    def begin_pass(self):
        self.last_pass = self._empty_counts()

    def record(self, item_id, lookup):
        """Record a `CacheLookup` outcome. Returns a one-line log message if newly observed, else None."""
        st = lookup.status
        if st == "hit":
            self.last_pass["hits"] += 1
        elif st == "hit_preserved_unrelated":
            self.last_pass["hits"] += 1
            self.last_pass["preserved_unrelated"] += 1
        elif st == "miss_dep_changed":
            self.last_pass["invalidated_dep_change"] += 1
        elif st == "miss_legacy_schema":
            self.last_pass["invalidated_legacy_schema"] += 1
        elif st == "bypass_uncertain":
            self.last_pass["bypassed_uncertain"] += 1
        elif st == "miss_cold":
            self.last_pass["cold_misses"] += 1

        if st == "miss_cold":
            return None
        ev_key = (str(item_id), st, lookup.key or lookup.detail or "")
        self._observed[ev_key] = {
            "item": str(item_id), "status": st, "key": lookup.key, "detail": lookup.detail,
        }
        if ev_key in self._emitted_logs:
            return None
        self._emitted_logs.add(ev_key)
        det = f" ({lookup.detail})" if lookup.detail else ""
        if st == "hit_preserved_unrelated":
            return f"[cache:{self.stage_label}] HIT preserved across unrelated repo change: {item_id}"
        if st == "hit":
            return f"[cache:{self.stage_label}] HIT: {item_id}"
        if st == "miss_dep_changed":
            return f"[cache:{self.stage_label}] INVALIDATED relevant dependency change{det}: {item_id}"
        if st == "miss_legacy_schema":
            return f"[cache:{self.stage_label}] INVALIDATED legacy/invalid cache schema{det}: {item_id}"
        if st == "bypass_uncertain":
            return f"[cache:{self.stage_label}] BYPASS uncertain dependencies{det}: {item_id}"
        return None

    def record_in_run_requeue(self, item_id, old_fps, new_fp):
        self.last_pass["in_run_requeued"] += 1
        ev_key = (str(item_id), "in_run_requeued", str(new_fp or ""))
        self._observed[ev_key] = {
            "item": str(item_id), "status": "in_run_requeued", "key": new_fp,
            "detail": f"prev_attempts={len(old_fps)}",
        }
        if ev_key in self._emitted_logs:
            return None
        self._emitted_logs.add(ev_key)
        return f"[cache:{self.stage_label}] REQUEUED IN-RUN relevant dependency changed: {item_id}"

    def summary(self):
        """Deduplicated cumulative metrics dictionary suitable for `build/wave4/metrics.json`."""
        counts = self._empty_counts()
        counts.pop("cold_misses", None)
        for ev in self._observed.values():
            st = ev["status"]
            if st == "hit":
                counts["hits"] += 1
            elif st == "hit_preserved_unrelated":
                counts["hits"] += 1
                counts["preserved_unrelated"] += 1
            elif st == "miss_dep_changed":
                counts["invalidated_dep_change"] += 1
            elif st == "miss_legacy_schema":
                counts["invalidated_legacy_schema"] += 1
            elif st == "bypass_uncertain":
                counts["bypassed_uncertain"] += 1
            elif st == "in_run_requeued":
                counts["in_run_requeued"] += 1
        return dict(schema_version=CACHE_SCHEMA_VERSION, **counts)
