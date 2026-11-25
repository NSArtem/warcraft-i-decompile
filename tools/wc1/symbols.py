"""Symbol database: names, types, module assignments and the evidence for them.

Source of truth: analysis/symbols/*.toml (one file per area so that parallel
analysts never edit the same file). Every entry must carry evidence and a
confidence level; see docs/METHODOLOGY.md.

    [[func]]
    addr = 0x1d7cc
    name = "InitPaths"            # C identifier
    conv = "watcall"              # watcall (name_) | cdecl (_name) | asm (name)
    proto = "void InitPaths(void)"
    module = "INIT.C"             # optional; must equal the analysis/modules.toml range name
    src = "src/init.c"            # optional: C that wc1.match reports MATCH for (T3); the build uses it
    # Non-matching C (docs/GOAL.md), all optional, never together with src:
    #   ref = "src/x/y_reference.c"            reference C defining this function (not built)
    #   ref_verified_by = "difftest: tests/..." the compiled ref C run against the original (T4)
    #   t3_blocker = "regalloc: ..."            why T3 is out of reach; category one of T3_BLOCKERS
    confidence = "high"           # verified | high | medium | low | speculative
    verified_by = ""              # required iff confidence == "verified"
    evidence = ["...", "..."]

    [[data]]
    addr = 0x59870
    name = "cd_path"
    type = "char[0x90]"
    confidence = "medium"
    evidence = ["..."]

usage: python3 -m wc1.symbols [--check | --srcs]   (--srcs: C files named by src =)
"""
import ast
import bisect
import glob
import hashlib
import io
import os
import re
import sys
import tomllib

from . import path

# Both caches are verified by content: the file is read and hashed on every use
# and a hit needs the same sha256 (mtimes miss same-size edits within a tick and
# reused temp-repo paths).  One entry per path, so an edited file replaces its own.
_TOML_CACHE = {}  # abspath -> (sha256, parsed document; private, see read_toml)
_AST_CACHE = {}   # abspath -> (sha256, _T4TestFile)

CONFIDENCE = ("verified", "high", "medium", "low", "speculative")
CONVS = ("watcall", "cdecl", "asm", "pascal")
T3_BLOCKERS = ("od-frame", "regalloc", "codegen")
IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
# Names NASM would read as registers/keywords if used bare.
NASM_RESERVED = {"eax", "ebx", "ecx", "edx", "esi", "edi", "ebp", "esp", "ax", "bx", "cx", "dx",
                 "si", "di", "bp", "sp", "al", "ah", "bl", "bh", "cl", "ch", "dl", "dh", "cs",
                 "ds", "es", "fs", "gs", "ss", "byte", "word", "dword", "qword", "tword",
                 "near", "far", "short", "strict", "seg", "wrt", "abs", "rel", "nosplit"}


class SymbolError(Exception):
    pass


def link_name(kind, e):
    """Assembler/linker symbol for an entry, matching Open Watcom conventions."""
    if "link" in e:
        return e["link"]
    n = e["name"]
    if kind == "func":
        conv = e.get("conv", "watcall")
        return {"watcall": n + "_", "cdecl": "_" + n, "asm": n,
                "pascal": n.upper()}.get(conv, n + "_")
    return "_" + n


def _copy_toml(v):
    """Copy of a parsed TOML value (every container is new; scalars are immutable)."""
    if isinstance(v, dict):
        return {k: _copy_toml(x) if isinstance(x, (dict, list)) else x for k, x in v.items()}
    if isinstance(v, list):
        return [_copy_toml(x) if isinstance(x, (dict, list)) else x for x in v]
    return v


def read_toml(filename):
    """`tomllib.load` of a file with a content-verified cache.  The result is a
    fresh copy the caller owns.  Raises like open/tomllib.load (errors are not
    cached)."""
    with open(filename, "rb") as fh:
        raw = fh.read()
    key, digest = os.path.abspath(filename), hashlib.sha256(raw).digest()
    hit = _TOML_CACHE.get(key)
    if hit is None or hit[0] != digest:
        hit = _TOML_CACHE[key] = (digest, tomllib.loads(raw.decode()))
    return _copy_toml(hit[1])


def load(root=None, strict=True, repo_root=None):
    root = root or path("analysis", "symbols")
    funcs, datas, errors = {}, {}, []
    ref_texts = {}                           # each ref C file is read once per load
    for f in sorted(glob.glob(os.path.join(root, "*.toml"))):
        try:
            doc = read_toml(f)
        except tomllib.TOMLDecodeError as ex:
            errors.append(f"{f}: {ex}")
            continue
        rel = os.path.relpath(f, path())
        for kind, table in (("func", funcs), ("data", datas)):
            for e in doc.get(kind, []):
                e = dict(e)
                e["_file"] = rel
                e["_kind"] = kind
                where = f"{e['_file']}: {kind} {e.get('addr', '?'):#x}" if isinstance(e.get("addr"), int) \
                    else f"{e['_file']}: {kind} {e.get('name')}"
                for req in ("addr", "name", "confidence", "evidence"):
                    if req not in e:
                        errors.append(f"{where}: missing '{req}'")
                if not isinstance(e.get("addr"), int):
                    continue
                if not IDENT.match(str(e.get("name", ""))):
                    errors.append(f"{where}: bad identifier {e.get('name')!r}")
                if e.get("confidence") not in CONFIDENCE:
                    errors.append(f"{where}: confidence must be one of {CONFIDENCE}")
                if e.get("confidence") == "verified" and not e.get("verified_by"):
                    errors.append(f"{where}: 'verified' requires verified_by (a mechanical check)")
                if not e.get("evidence"):
                    errors.append(f"{where}: evidence must be a non-empty list")
                if kind == "func" and e.get("conv", "watcall") not in CONVS:
                    errors.append(f"{where}: conv must be one of {CONVS}")
                if kind == "func":
                    errors += check_c_fields(e, where, ref_texts)
                if kind == "func" and e.get("conv", "watcall") not in CONVS:
                    e["link_name"] = ""          # reported above; do not crash on it
                ln = link_name(kind, e) if "name" in e and e.get("link_name") != "" else ""
                if ln.lower() in NASM_RESERVED:
                    errors.append(f"{where}: link name {ln!r} is reserved")
                if "link" in e and (not IDENT.match(ln) or ln.lower() in NASM_RESERVED):
                    # the asm emitter uses link as a NASM label; library-internal
                    # labels such as "<_TEXT+0>" must stay in the evidence text
                    errors.append(f"{where}: 'link' {ln!r} is not a NASM label "
                                  f"(use a valid identifier; record the library label in the evidence)")
                e["link_name"] = ln
                if e["addr"] in table:
                    o = table[e["addr"]]
                    errors.append(f"{where}: duplicate address (also {o['_file']} as {o['name']})")
                    continue
                table[e["addr"]] = e
    errors += check_modules(funcs)
    errors += check_ref_verified_by(funcs, repo_root=repo_root)
    names = {}
    for table in (funcs, datas):
        for a, e in table.items():
            ln = e["link_name"]
            if ln in names and names[ln] != a:
                errors.append(f"{e['_file']}: link name {ln} used for {a:#x} and {names[ln]:#x}")
            names[ln] = a
    if errors and strict:
        raise SymbolError("\n".join(errors))
    return funcs, datas, errors


def check_c_fields(e, where, ref_texts=None):
    """src / ref / ref_verified_by / t3_blocker consistency (docs/GOAL.md).
    `ref_texts` (path -> text) shares the ref files' contents between the calls
    of one load()."""
    errors = []
    ref = e.get("ref")
    if ref is not None:
        if e.get("src"):
            errors.append(f"{where}: 'src' and 'ref' are exclusive (a matched function needs no reference C)")
        if not (isinstance(ref, str) and ref.endswith(".c")):
            errors.append(f"{where}: ref must be the path of a .c file")
        elif not os.path.exists(path(ref)):
            errors.append(f"{where}: ref {ref!r} does not exist")
        else:
            text = ref_texts.get(path(ref)) if ref_texts is not None else None
            if text is None:
                with open(path(ref), encoding="latin-1") as fh:
                    text = fh.read()
                if ref_texts is not None:
                    ref_texts[path(ref)] = text
            # variants of one function in one file are allowed as Name_a, Name_b, ...
            if not re.search(r"\b" + re.escape(str(e.get("name", ""))) + r"\w*\s*\(", text):
                errors.append(f"{where}: ref {ref!r} does not define {e.get('name')}")
    for key in ("ref_verified_by", "t3_blocker"):
        if key in e and ref is None:
            errors.append(f"{where}: '{key}' requires 'ref'")
    rvb = e.get("ref_verified_by")
    if rvb is not None and not str(rvb).startswith("difftest:"):
        errors.append(f"{where}: ref_verified_by must start with 'difftest:' (compiled C vs original)")
    tb = e.get("t3_blocker")
    if tb is not None and not re.match(r"^(" + "|".join(T3_BLOCKERS) + r"): \S", str(tb)):
        errors.append(f"{where}: t3_blocker must be '<category>: <evidence>', category one of {T3_BLOCKERS}")
    return errors


_ORACLE_NAMES = frozenset({"run_spec", "run_pair", "assert_t3_matches", "assert_ref_mismatch"})
_AUDIT_ENV_VARS = frozenset({"WC1_T4_AUDIT_LOG", "WC1_T4_AUDIT_NONCE"})


def _walk(tree):
    """`list(ast.walk(tree))` (same breadth-first order), without the generator
    overhead and without the Load/Store/Del context nodes, which no check uses."""
    nodes = [tree]
    add = nodes.append
    for node in nodes:                       # grows while it is iterated
        for name in node._fields:
            v = getattr(node, name, None)
            if isinstance(v, ast.AST):
                if not isinstance(v, ast.expr_context):
                    add(v)
            elif isinstance(v, list):
                for x in v:
                    if isinstance(x, ast.AST):
                        add(x)
    return nodes


def _collect_skip_aliases(tree, nodes=None):
    """Collect module/symbol import aliases for skip/xfail and oracle-suppression checks.
    `nodes` is `_walk(tree)` when the caller already has it."""
    pytest_mods = {"pytest"}
    mark_objs = set()
    skip_fns = set()
    xfail_fns = set()
    importorskip_fns = set()
    raises_fns = set()
    contextlib_mods = {"contextlib"}
    suppress_fns = set()
    t4spec_mods = set()
    cemu_mods = set()
    oracle_fns = set()
    mock_mods = {"mock"}
    patch_fns = set()
    unittest_mods = {"unittest"}
    unittest_skip_decs = set()
    skip_excs = {"SkipTest"}
    assigns = []                             # single-name assignments, in walk order

    for node in _walk(tree) if nodes is None else nodes:
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                asname = alias.asname or name.split(".", 1)[0]
                if name == "pytest":
                    pytest_mods.add(asname)
                elif name == "unittest":
                    unittest_mods.add(asname)
                elif name == "contextlib":
                    contextlib_mods.add(asname)
                elif name == "unittest.mock":
                    mock_mods.add(asname)
                elif name == "wc1.t4spec":
                    t4spec_mods.add(asname)
                elif name == "wc1.cemu":
                    cemu_mods.add(asname)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            for alias in node.names:
                name = alias.name
                asname = alias.asname or name
                if mod == "pytest":
                    if name == "mark":
                        mark_objs.add(asname)
                    elif name == "skip":
                        skip_fns.add(asname)
                    elif name == "xfail":
                        xfail_fns.add(asname)
                    elif name == "importorskip":
                        importorskip_fns.add(asname)
                    elif name == "raises":
                        raises_fns.add(asname)
                elif mod == "pytest.mark":
                    if name == "skip":
                        skip_fns.add(asname)
                    elif name == "xfail":
                        xfail_fns.add(asname)
                elif mod == "contextlib":
                    if name == "suppress":
                        suppress_fns.add(asname)
                elif mod == "unittest" or mod.startswith("unittest."):
                    if name in ("skip", "skipIf", "skipUnless"):
                        unittest_skip_decs.add(asname)
                    elif name == "SkipTest":
                        skip_excs.add(asname)
                    elif name == "mock":
                        mock_mods.add(asname)
                    elif name == "patch":
                        patch_fns.add(asname)
                elif mod in ("wc1", "tools.wc1"):
                    if name == "t4spec":
                        t4spec_mods.add(asname)
                    elif name == "cemu":
                        cemu_mods.add(asname)
                elif mod.endswith("t4spec") or mod.endswith("cemu"):
                    if name in _ORACLE_NAMES:
                        oracle_fns.add(asname)
        elif isinstance(node, ast.Assign):
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                assigns.append(node)

    # Also track simple local rebindings like `r = pytest.raises`, `go = t4spec.run_spec`,
    # or `go = functools.partial(cemu.run_pair, ...)`
    changed = True
    while changed:
        changed = False
        for node in assigns:
            tgt = node.targets[0].id
            val = node.value
            # functools.partial(cemu.run_pair, ...)
            if isinstance(val, ast.Call):
                vc = _attr_chain(val.func)
                if vc and vc[-1] == "partial" and val.args:
                    ac = _attr_chain(val.args[0])
                    if ac and (ac[-1] in _ORACLE_NAMES or (len(ac) == 1 and ac[0] in oracle_fns)):
                        if tgt not in oracle_fns:
                            oracle_fns.add(tgt)
                            changed = True
                continue
            chain = _attr_chain(val)
            if not chain:
                continue
            if (len(chain) == 2 and chain[0] in pytest_mods and chain[1] == "raises") or (
                len(chain) == 1 and chain[0] in raises_fns
            ):
                if tgt not in raises_fns:
                    raises_fns.add(tgt)
                    changed = True
            elif (len(chain) == 2 and chain[0] in contextlib_mods and chain[1] == "suppress") or (
                len(chain) == 1 and chain[0] in suppress_fns
            ):
                if tgt not in suppress_fns:
                    suppress_fns.add(tgt)
                    changed = True
            elif (len(chain) == 2 and chain[0] in pytest_mods and chain[1] == "skip") or (
                len(chain) == 1 and chain[0] in skip_fns
            ):
                if tgt not in skip_fns:
                    skip_fns.add(tgt)
                    changed = True
            elif (len(chain) == 2 and chain[0] in pytest_mods and chain[1] == "xfail") or (
                len(chain) == 1 and chain[0] in xfail_fns
            ):
                if tgt not in xfail_fns:
                    xfail_fns.add(tgt)
                    changed = True
            elif (len(chain) >= 2 and chain[-1] in _ORACLE_NAMES) or (
                len(chain) == 1 and chain[0] in oracle_fns
            ):
                if tgt not in oracle_fns:
                    oracle_fns.add(tgt)
                    changed = True

    return {
        "pytest_mods": pytest_mods,
        "mark_objs": mark_objs,
        "skip_fns": skip_fns,
        "xfail_fns": xfail_fns,
        "importorskip_fns": importorskip_fns,
        "raises_fns": raises_fns,
        "contextlib_mods": contextlib_mods,
        "suppress_fns": suppress_fns,
        "t4spec_mods": t4spec_mods,
        "cemu_mods": cemu_mods,
        "oracle_fns": oracle_fns,
        "mock_mods": mock_mods,
        "patch_fns": patch_fns,
        "unittest_mods": unittest_mods,
        "unittest_skip_decs": unittest_skip_decs,
        "skip_excs": skip_excs,
    }


def _attr_chain(node):
    """Return dotted attribute chain like ['pytest', 'mark', 'skip'], or None."""
    parts = []
    cur = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
        parts.reverse()
        return parts
    return None


def _is_statically_truthy(expr):
    """True when `expr` is trivially/statically truthy (e.g. `True`, `not False`, `True or x`, `1`)."""
    if isinstance(expr, ast.Constant):
        return bool(expr.value)
    if isinstance(expr, ast.UnaryOp) and isinstance(expr.op, ast.Not):
        return _is_statically_falsy(expr.operand)
    if isinstance(expr, ast.BoolOp):
        if isinstance(expr.op, ast.Or):
            return any(_is_statically_truthy(v) for v in expr.values)
        if isinstance(expr.op, ast.And):
            return all(_is_statically_truthy(v) for v in expr.values)
    return False


def _is_statically_falsy(expr):
    if isinstance(expr, ast.Constant):
        return not bool(expr.value)
    if isinstance(expr, ast.UnaryOp) and isinstance(expr.op, ast.Not):
        return _is_statically_truthy(expr.operand)
    if isinstance(expr, ast.BoolOp):
        if isinstance(expr.op, ast.And):
            return any(_is_statically_falsy(v) for v in expr.values)
        if isinstance(expr.op, ast.Or):
            return all(_is_statically_falsy(v) for v in expr.values)
    return False


def _is_allowed_env_skipif_cond(cond):
    """Allow only `not <env-check>` skipif conditions referencing war.exe/WATCOM or a single env flag name.

    This is a cheap static prefilter; runtime verification (`verify_t4_node` / `_pytest_output_passed`)
    still enforces 0 skipped tests when the environment is present.
    """
    if not (isinstance(cond, ast.UnaryOp) and isinstance(cond.op, ast.Not)):
        return False
    inner = cond.operand
    if isinstance(inner, ast.Name):
        return True
    has_env_tok = False
    for sub in ast.walk(inner):
        if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
            if sub.value in ("war.exe", "WATCOM", "original"):
                has_env_tok = True
                break
        elif isinstance(sub, ast.Attribute) and sub.attr in ("exists", "environ"):
            has_env_tok = True
    return has_env_tok


def _is_forbidden_mark_expr(expr, aliases, allow_skipif=True, require_env_skipif=False):
    """Return a short description if `expr` is a forbidden skip/xfail mark/decorator."""
    call_args = None
    target = expr
    if isinstance(expr, ast.Call):
        call_args = expr.args
        target = expr.func
    chain = _attr_chain(target)
    if not chain:
        return None
    # pytest.mark.skip / pytest.mark.xfail / pytest.mark.skipif(...)
    if len(chain) == 3 and chain[0] in aliases["pytest_mods"] and chain[1] == "mark":
        mname = chain[2]
        if mname in ("skip", "xfail"):
            return f"{'.'.join(chain)}"
        if mname == "skipif":
            if not allow_skipif:
                return f"{'.'.join(chain)}"
            if call_args and _is_statically_truthy(call_args[0]):
                return f"{'.'.join(chain)}(True, ...)"
            if require_env_skipif and (not call_args or not _is_allowed_env_skipif_cond(call_args[0])):
                return f"{'.'.join(chain)}(non-env condition)"
    # from pytest import mark; mark.skip / mark.xfail / mark.skipif(...)
    if len(chain) == 2 and chain[0] in aliases["mark_objs"]:
        mname = chain[1]
        if mname in ("skip", "xfail"):
            return f"{'.'.join(chain)}"
        if mname == "skipif":
            if not allow_skipif:
                return f"{'.'.join(chain)}"
            if call_args and _is_statically_truthy(call_args[0]):
                return f"{'.'.join(chain)}(True, ...)"
            if require_env_skipif and (not call_args or not _is_allowed_env_skipif_cond(call_args[0])):
                return f"{'.'.join(chain)}(non-env condition)"
    # unittest.skip / skipIf / skipUnless
    if len(chain) == 2 and chain[0] in aliases["unittest_mods"] and chain[1] in ("skip", "skipIf", "skipUnless"):
        return f"{'.'.join(chain)}"
    if len(chain) == 1 and chain[0] in (aliases["unittest_skip_decs"] | aliases["skip_fns"] | aliases["xfail_fns"]):
        return chain[0]
    return None


def _check_pytestmark_stmts(stmts, aliases, require_env_skipif=False):
    """Reject unconditional `pytestmark = pytest.mark.skip / xfail` (and non-env skipif in strict mode)."""
    for stmt in stmts:
        value = None
        if isinstance(stmt, ast.Assign):
            if any(isinstance(t, ast.Name) and t.id == "pytestmark" for t in stmt.targets):
                value = stmt.value
        elif isinstance(stmt, ast.AnnAssign):
            if isinstance(stmt.target, ast.Name) and stmt.target.id == "pytestmark":
                value = stmt.value
        if value is None:
            continue
        items = value.elts if isinstance(value, (ast.List, ast.Tuple)) else [value]
        for item in items:
            bad = _is_forbidden_mark_expr(
                item, aliases, allow_skipif=True, require_env_skipif=require_env_skipif,
            )
            if bad:
                return f"forbidden pytestmark ({bad})"
    return None


def _is_direct_oracle_call(call_node, aliases):
    chain = _attr_chain(call_node.func)
    if not chain:
        return False
    if len(chain) == 1 and chain[0] in (aliases["oracle_fns"] | _ORACLE_NAMES):
        return True
    if len(chain) >= 2 and chain[-1] in _ORACLE_NAMES:
        return True
    return False


def _build_local_call_graph(tree, aliases):
    """Map local function names to AST nodes, call edges, and transitive oracle callers."""
    local_funcs = {}
    for stmt in tree.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            local_funcs[stmt.name] = stmt
        elif isinstance(stmt, ast.ClassDef):
            for sub in stmt.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    local_funcs[f"{stmt.name}.{sub.name}"] = sub

    calls_by_fn = {}
    oracle_callers = set()
    for fname, fnode in local_funcs.items():
        callees = set()
        for sub in _walk(fnode):
            if isinstance(sub, ast.Call):
                if _is_direct_oracle_call(sub, aliases):
                    oracle_callers.add(fname)
                chain = _attr_chain(sub.func)
                if chain:
                    if len(chain) == 1 and chain[0] in local_funcs:
                        callees.add(chain[0])
                    elif len(chain) == 2 and chain[0] == "self":
                        for k in local_funcs:
                            if k.endswith("." + chain[1]):
                                callees.add(k)
        calls_by_fn[fname] = callees

    changed = True
    while changed:
        changed = False
        for fname, callees in calls_by_fn.items():
            if fname not in oracle_callers and (callees & oracle_callers):
                oracle_callers.add(fname)
                changed = True
    return local_funcs, calls_by_fn, oracle_callers


def _reachable_local_funcs(start_name, calls_by_fn):
    seen = {start_name}
    stack = [start_name]
    while stack:
        cur = stack.pop()
        for nxt in calls_by_fn.get(cur, ()):
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen


def _is_raises_or_suppress_call(call_node, aliases):
    chain = _attr_chain(call_node.func)
    if not chain:
        return None
    if len(chain) == 2 and chain[0] in aliases["pytest_mods"] and chain[1] == "raises":
        return ".".join(chain)
    if len(chain) == 1 and chain[0] in aliases["raises_fns"]:
        return chain[0]
    if len(chain) == 2 and chain[0] in aliases["contextlib_mods"] and chain[1] == "suppress":
        return ".".join(chain)
    if len(chain) == 1 and chain[0] in aliases["suppress_fns"]:
        return chain[0]
    if chain[-1] in ("assertRaises", "assertRaisesRegex"):
        return ".".join(chain)
    return None


def _stmts_call_oracle(stmts, aliases, oracle_callers):
    for stmt in stmts:
        for sub in ast.walk(stmt):
            if isinstance(sub, ast.Call):
                if _is_direct_oracle_call(sub, aliases):
                    return True
                chain = _attr_chain(sub.func)
                if chain:
                    if len(chain) == 1 and chain[0] in oracle_callers:
                        return True
                    if len(chain) == 2 and chain[0] == "self":
                        if any(oc.endswith("." + chain[1]) for oc in oracle_callers):
                            return True
    return False


def _stmts_have_early_exit(stmts):
    """True if `finally:` body contains return/break/continue outside nested defs/loops."""
    for stmt in stmts:
        if isinstance(stmt, (ast.Return, ast.Break, ast.Continue)):
            return True
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        for child in ast.iter_child_nodes(stmt):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            if _stmts_have_early_exit([child]):
                return True
    return False


def _check_oracle_tampering(tree, aliases, nodes=None):
    """Reject shadowing, monkeypatching, or audit-forging of `t4spec`/`cemu`/`emu.call`.
    `nodes` is `_walk(tree)` when the caller already has it."""
    oracle_mods = aliases["t4spec_mods"] | aliases["cemu_mods"] | {"t4spec", "cemu"}
    for stmt in tree.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)) and stmt.name in _ORACLE_NAMES:
            # Allow a thin local wrapper like `def run_pair(...): return cemu.run_pair(...)`
            # ONLY when it does not shadow a `from ... import run_pair` AND actually delegates
            # to a module-qualified oracle call (`cemu.run_pair` / `t4spec.run_spec`).
            delegates = False
            for sub in ast.walk(stmt):
                if isinstance(sub, ast.Call):
                    ch = _attr_chain(sub.func)
                    if ch and len(ch) >= 2 and ch[0] in oracle_mods and ch[-1] == stmt.name:
                        delegates = True
                        break
            if stmt.name in aliases["oracle_fns"] or not delegates:
                return f"forbidden local shadow 'def {stmt.name}'"

    for node in _walk(tree) if nodes is None else nodes:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value in _AUDIT_ENV_VARS:
                return f"forbidden audit env tampering ({node.value!r})"
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for t in targets:
                chain = _attr_chain(t)
                if not chain:
                    continue
                if len(chain) >= 2 and (chain[-1] in _ORACLE_NAMES or chain[-1] == "record_t4_audit"):
                    return f"forbidden oracle monkeypatch '{'.'.join(chain)} = ...'"
                if len(chain) >= 2 and chain[-1] == "call" and chain[-2].lower() in ("emu", "e"):
                    return f"forbidden emulator tampering '{'.'.join(chain)} = ...'"
                if len(chain) == 1 and chain[0] in (_ORACLE_NAMES | {"record_t4_audit"}):
                    return f"forbidden oracle rebinding '{chain[0]} = ...'"
        elif isinstance(node, ast.Call):
            chain = _attr_chain(node.func)
            if not chain:
                continue
            if chain[-1] == "record_t4_audit":
                return f"forbidden direct audit forging '{'.'.join(chain)}()'"
            # Any setattr (builtin `setattr(...)` or fixture `<anything>.setattr(...)`) or mock.patch
            is_setattr = chain[-1] == "setattr"
            is_patch = (
                (len(chain) >= 2 and chain[-1] == "patch" and chain[0] in aliases["mock_mods"])
                or (len(chain) >= 3 and chain[-2] == "patch" and chain[-1] == "object" and chain[0] in aliases["mock_mods"])
                or (len(chain) == 1 and chain[0] in aliases["patch_fns"])
                or (len(chain) == 2 and chain[0] in aliases["patch_fns"] and chain[1] == "object")
            )
            if is_setattr or is_patch:
                for arg in node.args[:2]:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        tail = arg.value.split(".")[-1]
                        if any(on in arg.value for on in (_ORACLE_NAMES | {"record_t4_audit"})) or tail in ("call", "reg", "read", "write"):
                            return f"forbidden oracle patch {'.'.join(chain)}({arg.value!r})"
                    ac = _attr_chain(arg)
                    if ac and (ac[-1] in oracle_mods or ac[-1].lower() == "emu"):
                        return f"forbidden oracle patch {'.'.join(chain)}({'.'.join(ac)}, ...)"
    return None


def _check_func_for_skips(fn_node, aliases, cls_node=None, allow_skipif=True,
                          oracle_callers=None, check_oracle_suppression=True):
    """Return a short reason if `fn_node` (or enclosing `cls_node`) has skip/xfail or oracle-suppression cheats."""
    oracle_callers = oracle_callers or set()
    for owner in ([cls_node] if cls_node is not None else []) + [fn_node]:
        for dec in owner.decorator_list:
            bad = _is_forbidden_mark_expr(dec, aliases, allow_skipif=allow_skipif)
            if bad:
                return f"forbidden decorator @{bad} on {owner.name}"
    if cls_node is not None:
        bad_pm = _check_pytestmark_stmts(cls_node.body, aliases)
        if bad_pm:
            return f"{bad_pm} on {cls_node.name}"

    try_types = (ast.Try,) + ((ast.TryStar,) if hasattr(ast, "TryStar") else ())
    for sub in _walk(fn_node):
        if isinstance(sub, ast.Call):
            chain = _attr_chain(sub.func)
            if chain:
                if len(chain) == 2 and chain[0] in aliases["pytest_mods"] and chain[1] in ("skip", "xfail", "importorskip"):
                    return f"forbidden inline call {'.'.join(chain)}() in {fn_node.name}"
                if len(chain) == 1 and chain[0] in (aliases["skip_fns"] | aliases["xfail_fns"] | aliases["importorskip_fns"]):
                    return f"forbidden inline call {chain[0]}() in {fn_node.name}"
            if check_oracle_suppression:
                bad_rs = _is_raises_or_suppress_call(sub, aliases)
                if bad_rs:
                    return f"forbidden {bad_rs}() in {fn_node.name}"
        elif isinstance(sub, ast.Raise) and sub.exc is not None:
            exc = sub.exc.func if isinstance(sub.exc, ast.Call) else sub.exc
            chain = _attr_chain(exc)
            if not chain:
                continue
            if len(chain) == 3 and chain[0] in aliases["pytest_mods"] and chain[1] == "skip" and chain[2] == "Exception":
                return f"forbidden raise {'.'.join(chain)} in {fn_node.name}"
            if len(chain) == 2 and chain[0] in aliases["skip_fns"] and chain[1] == "Exception":
                return f"forbidden raise {'.'.join(chain)} in {fn_node.name}"
            if len(chain) == 2 and chain[0] in aliases["unittest_mods"] and chain[1] == "SkipTest":
                return f"forbidden raise {'.'.join(chain)} in {fn_node.name}"
            if len(chain) == 1 and chain[0] in aliases["skip_excs"]:
                return f"forbidden raise {chain[0]} in {fn_node.name}"
        elif check_oracle_suppression and isinstance(sub, try_types):
            if _stmts_call_oracle(sub.body, aliases, oracle_callers):
                if sub.handlers:
                    return f"forbidden try/except around oracle call in {fn_node.name}"
                if sub.finalbody and _stmts_have_early_exit(sub.finalbody):
                    return f"forbidden return/break/continue in finally around oracle call in {fn_node.name}"
    return None


def check_t4_test_source(src, *, strict_pytestmark=False):
    """Shared AST cheat prefilter for T4 test files (used by symbols, batch_driver, overnight).

    Returns a short reason string if `src` contains skip/xfail, oracle-suppression,
    or oracle-tampering cheats, else None.
    """
    if not src:
        return None
    try:
        tree = ast.parse(src)
    except SyntaxError as ex:
        return f"syntax error: {ex}"

    nodes = _walk(tree)
    aliases = _collect_skip_aliases(tree, nodes)
    bad_pm = _check_pytestmark_stmts(tree.body, aliases, require_env_skipif=strict_pytestmark)
    if bad_pm:
        return bad_pm
    if strict_pytestmark:
        # Reject any other module-level skip/xfail/skipif mark call outside validated `pytestmark`
        for stmt in tree.body:
            if isinstance(stmt, (ast.Assign, ast.AnnAssign)):
                targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
                if any(isinstance(t, ast.Name) and t.id == "pytestmark" for t in targets):
                    continue
            if not isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                for sub in ast.walk(stmt):
                    if isinstance(sub, ast.Call):
                        bad_m = _is_forbidden_mark_expr(sub, aliases, allow_skipif=False)
                        if bad_m:
                            return f"forbidden module-level {bad_m}"

    tamper = _check_oracle_tampering(tree, aliases, nodes)
    if tamper:
        return tamper

    local_funcs, _, oracle_callers = _build_local_call_graph(tree, aliases)
    # Check module-level try/with blocks around oracle calls too
    try_types = (ast.Try,) + ((ast.TryStar,) if hasattr(ast, "TryStar") else ())
    for stmt in tree.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        for sub in ast.walk(stmt):
            if isinstance(sub, ast.Call):
                bad_rs = _is_raises_or_suppress_call(sub, aliases)
                if bad_rs:
                    return f"forbidden module-level {bad_rs}()"
            elif isinstance(sub, try_types) and _stmts_call_oracle(sub.body, aliases, oracle_callers):
                if sub.handlers:
                    return "forbidden module-level try/except around oracle call"
                if sub.finalbody and _stmts_have_early_exit(sub.finalbody):
                    return "forbidden module-level finally exit around oracle call"

    for stmt in tree.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            reason = _check_func_for_skips(
                stmt, aliases, cls_node=None,
                allow_skipif=not strict_pytestmark,
                oracle_callers=oracle_callers,
                check_oracle_suppression=True,
            )
            if reason:
                return reason
        elif isinstance(stmt, ast.ClassDef):
            bad_cls_pm = _check_pytestmark_stmts(stmt.body, aliases)
            if bad_cls_pm:
                return f"{bad_cls_pm} on {stmt.name}"
            for dec in stmt.decorator_list:
                bad = _is_forbidden_mark_expr(dec, aliases, allow_skipif=not strict_pytestmark)
                if bad:
                    return f"forbidden decorator @{bad} on {stmt.name}"
            for sub in stmt.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    reason = _check_func_for_skips(
                        sub, aliases, cls_node=stmt,
                        allow_skipif=not strict_pytestmark,
                        oracle_callers=oracle_callers,
                        check_oracle_suppression=True,
                    )
                    if reason:
                        return reason
    return None


def parse_ref_verified_by_nodes(rvb):
    """Extract all `(file_rel, node_name)` citations from a `difftest: ...` string.

    Returns `(nodes, error)`. Every `file::node` token in `rvb` is returned;
    the first non-empty token after `difftest:` must itself be a `file::node`
    citation.
    """
    text = str(rvb or "").strip()
    if not text.startswith("difftest:"):
        return [], "ref_verified_by must start with 'difftest:'"
    body = text[len("difftest:"):].strip()
    if not body:
        return [], "ref_verified_by has no test node after 'difftest:'"
    first_tok = re.split(r"[\s(]", body, maxsplit=1)[0].rstrip(",;")
    if "::" not in first_tok:
        return [], f"ref_verified_by must cite 'tests/<file>.py::<test_name>' (got {first_tok!r})"
    raw_tokens = re.findall(r"(?<![A-Za-z0-9_./\\-])([^\s(,;]+::[^\s),;]+)", body)
    nodes = []
    seen = set()
    for raw in raw_tokens:
        tok = raw.rstrip(",;.")
        if "::" not in tok:
            continue
        file_part, node_part = tok.split("::", 1)
        node_part = re.sub(r"\[.*\]$", "", node_part).strip()
        file_part = file_part.strip()
        if not file_part or not node_part:
            return [], f"malformed test node {raw!r} in ref_verified_by"
        item = (file_part, node_part)
        if item not in seen:
            seen.add(item)
            nodes.append(item)
    if not nodes:
        return [], f"ref_verified_by must cite 'tests/<file>.py::<test_name>' (got {body!r})"
    return nodes, None


class _T4TestFile:
    """The AST findings of one cited test file's content: file-level verdict and,
    on demand, the verdict on each cited node.  Holds no caller-visible state."""

    def __init__(self, raw, ap):
        self.src = self.perr = self.bad = None
        self._nodes = {}                     # node_part -> (found, skip_reason)
        # as open(ap, encoding="utf-8", errors="replace").read()
        src = io.TextIOWrapper(io.BytesIO(raw), encoding="utf-8", errors="replace").read()
        try:
            tree = ast.parse(src, filename=ap)
        except SyntaxError as ex:
            self.perr = str(ex)
            return
        self.src = src
        self._tree = tree
        nodes = _walk(tree)
        self._aliases = _collect_skip_aliases(tree, nodes)
        self.bad = (_check_pytestmark_stmts(tree.body, self._aliases)
                    or _check_oracle_tampering(tree, self._aliases, nodes))
        if not self.bad:
            self._funcs, self._calls, self._oracle_callers = \
                _build_local_call_graph(tree, self._aliases)

    def node(self, node_part):
        """(found, skip_reason) of one cited `test_name` / `Class::test_name`."""
        got = self._nodes.get(node_part)
        if got is None:
            got = self._nodes[node_part] = self._check_node(node_part)
        return got

    def _check_node(self, node_part):
        # Locate cited test node (last definition wins, matching Python semantics).
        cls_node = None
        fn_node = None
        fn_key = None
        if "::" in node_part:
            cls_name, fn_name = node_part.split("::", 1)
            for stmt in self._tree.body:
                if isinstance(stmt, ast.ClassDef) and stmt.name == cls_name:
                    cls_node = stmt
            if cls_node is not None:
                for stmt in cls_node.body:
                    if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)) and stmt.name == fn_name:
                        fn_node = stmt
                        fn_key = f"{cls_name}.{fn_name}"
        else:
            for stmt in self._tree.body:
                if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)) and stmt.name == node_part:
                    fn_node = stmt
                    fn_key = node_part

        if fn_node is None:
            return False, None
        skip_reason = _check_func_for_skips(
            fn_node, self._aliases, cls_node=cls_node,
            oracle_callers=self._oracle_callers, check_oracle_suppression=True,
        )
        if not skip_reason and fn_key:
            for helper_key in sorted(_reachable_local_funcs(fn_key, self._calls)):
                if helper_key == fn_key or helper_key not in self._oracle_callers:
                    continue
                hnode = self._funcs.get(helper_key)
                if hnode is None:
                    continue
                skip_reason = _check_func_for_skips(
                    hnode, self._aliases, cls_node=None,
                    oracle_callers=self._oracle_callers,
                    check_oracle_suppression=True,
                )
                if skip_reason:
                    break
        return True, skip_reason


def _t4_test_file(full_path):
    """The _T4TestFile of a file's current content.  Raises OSError."""
    ap = os.path.abspath(full_path)
    with open(ap, "rb") as fh:
        raw = fh.read()
    digest = hashlib.sha256(raw).digest()
    hit = _AST_CACHE.get(ap)
    if hit is None or hit[0] != digest:
        hit = _AST_CACHE[ap] = (digest, _T4TestFile(raw, ap))
    return hit[1]


def validate_ref_verified_by_entry(rvb, ref_rel=None, repo_root=None):
    """Validate every pytest node cited by `rvb` via AST (existence, no skip/xfail cheats, ref mention)."""
    root = repo_root or path()
    nodes, err = parse_ref_verified_by_nodes(rvb)
    if err:
        return [err]
    errors = []
    ref_base = os.path.basename(ref_rel) if ref_rel else None
    ref_norm = ref_rel.replace("\\", "/") if ref_rel else None

    for file_part, node_part in nodes:
        norm = file_part.replace("\\", "/")
        parts = norm.split("/")
        if os.path.isabs(norm) or ".." in parts or not norm.startswith("tests/") or not norm.endswith(".py"):
            errors.append(f"ref_verified_by path must be a relative 'tests/*.py' path (got {file_part!r})")
            continue
        full = os.path.join(root, norm)
        if not os.path.isfile(full):
            errors.append(f"ref_verified_by test file {norm!r} does not exist")
            continue
        try:
            tf = _t4_test_file(full)
            perr = tf.perr
        except OSError as ex:
            perr = str(ex)
        if perr is not None:
            errors.append(f"ref_verified_by test file {norm!r} failed to parse: {perr}")
            continue
        if tf.bad:
            errors.append(f"ref_verified_by {norm!r}: {tf.bad}")
            continue
        found, skip_reason = tf.node(node_part)
        if not found:
            errors.append(f"ref_verified_by node {node_part!r} not found in {norm!r}")
            continue
        if skip_reason:
            errors.append(f"ref_verified_by {norm}::{node_part}: {skip_reason}")
            continue
        if ref_base and (ref_base not in tf.src and ref_norm not in tf.src):
            errors.append(f"ref_verified_by {norm!r} does not reference {ref_base!r}")
    return errors


def check_ref_verified_by(funcs, repo_root=None):
    """Validate that every `ref_verified_by` entry points to real, non-skipped pytest node(s)."""
    errors = []
    for a, e in funcs.items():
        rvb = e.get("ref_verified_by")
        if not rvb or not str(rvb).startswith("difftest:"):
            continue
        where = f"{e.get('_file', '?')}: func {a:#x}"
        for msg in validate_ref_verified_by_entry(rvb, ref_rel=e.get("ref"), repo_root=repo_root):
            errors.append(f"{where}: {msg}")
    return errors


def _disjoint_starts(mods):
    """The starts of well-formed, sorted, disjoint module ranges (as the file is
    kept): at most one range can contain an address, so bisect finds the first
    match in file order.  None for anything else: scan the ranges in order."""
    starts, last = [], None
    for m in mods:
        s, e = (m.get("start"), m.get("end")) if isinstance(m, dict) else (None, None)
        if type(s) is not int or type(e) is not int or s > e or (last is not None and s < last):
            return None
        starts.append(s)
        last = e
    return starts


def check_modules(funcs, modules_file=None):
    """A function's `module = "X"` must name the analysis/modules.toml range
    that contains it (the module list is the single source for boundaries;
    rename the range there, via wc1.modules_names, to change the name)."""
    modules_file = modules_file or path("analysis", "modules.toml")
    if not os.path.exists(modules_file):
        return []
    mods = read_toml(modules_file).get("module", [])
    starts = _disjoint_starts(mods)
    errors = []
    for a, e in funcs.items():
        if "module" not in e:
            continue
        near = mods
        if starts is not None:
            i = max(bisect.bisect_right(starts, a) - 1, 0)
            near = mods[i:i + 1]
        m = next((m for m in near if m["start"] <= a < m["end"]), None)
        if m is None:
            errors.append(f"{e['_file']}: func {a:#x} module {e['module']!r}: address outside analysis/modules.toml")
        elif m["name"] != e["module"]:
            errors.append(f"{e['_file']}: func {a:#x} module {e['module']!r} but analysis/modules.toml "
                          f"names {m['start']:#x}..{m['end']:#x} {m['name']!r}")
    return errors


def label_map(root=None):
    """addr -> link name, for the asm emitter."""
    funcs, datas, _ = load(root)
    out = {a: e["link_name"] for a, e in datas.items()}
    out.update({a: e["link_name"] for a, e in funcs.items()})
    return out


def main():
    funcs, datas, errors = load(strict=False)
    if "--srcs" in sys.argv[1:]:
        print("\n".join(sorted({e["src"] for e in funcs.values() if e.get("src")})))
        return 1 if errors else 0
    for e in errors:
        print("ERROR", e)
    by_conf = {}
    for t in (funcs, datas):
        for e in t.values():
            by_conf[e["confidence"]] = by_conf.get(e["confidence"], 0) + 1
    print(f"{len(funcs)} functions, {len(datas)} data symbols; by confidence: {by_conf}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
