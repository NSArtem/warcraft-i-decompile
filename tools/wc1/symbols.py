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
import glob
import os
import re
import sys
import tomllib

from . import path

_AST_CACHE = {}  # (abspath, mtime_ns) -> (ast.Module | None, str_src_or_err)

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


def load(root=None, strict=True, repo_root=None):
    root = root or path("analysis", "symbols")
    funcs, datas, errors = {}, {}, []
    for f in sorted(glob.glob(os.path.join(root, "*.toml"))):
        try:
            with open(f, "rb") as fh:
                doc = tomllib.load(fh)
        except tomllib.TOMLDecodeError as ex:
            errors.append(f"{f}: {ex}")
            continue
        for kind, table in (("func", funcs), ("data", datas)):
            for e in doc.get(kind, []):
                e = dict(e)
                e["_file"] = os.path.relpath(f, path())
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
                    errors += check_c_fields(e, where)
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


def check_c_fields(e, where):
    """src / ref / ref_verified_by / t3_blocker consistency (docs/GOAL.md)."""
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
            with open(path(ref), encoding="latin-1") as fh:
                text = fh.read()
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


def _parse_ast_cached(full_path):
    """Parse a Python test file with (abspath, mtime_ns) caching."""
    ap = os.path.abspath(full_path)
    try:
        st = os.stat(ap)
    except OSError as ex:
        return None, None, str(ex)
    key = (ap, st.st_mtime_ns)
    cached = _AST_CACHE.get(key)
    if cached is not None:
        return cached
    try:
        with open(ap, encoding="utf-8", errors="replace") as fh:
            src = fh.read()
        tree = ast.parse(src, filename=ap)
        val = (tree, src, None)
    except (OSError, SyntaxError) as ex:
        val = (None, None, str(ex))
    _AST_CACHE[key] = val
    return val


def _collect_skip_aliases(tree):
    """Collect module/symbol import aliases for pytest/unittest skip & xfail constructs."""
    pytest_mods = set()
    mark_objs = set()
    skip_fns = set()
    xfail_fns = set()
    importorskip_fns = set()
    unittest_mods = set()
    unittest_skip_decs = set()
    skip_excs = {"SkipTest"}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                asname = alias.asname or name.split(".", 1)[0]
                if name == "pytest":
                    pytest_mods.add(asname)
                elif name == "unittest":
                    unittest_mods.add(asname)
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
                elif mod == "pytest.mark":
                    if name == "skip":
                        skip_fns.add(asname)
                    elif name == "xfail":
                        xfail_fns.add(asname)
                elif mod == "unittest" or mod.startswith("unittest."):
                    if name in ("skip", "skipIf", "skipUnless"):
                        unittest_skip_decs.add(asname)
                    elif name == "SkipTest":
                        skip_excs.add(asname)
    return {
        "pytest_mods": pytest_mods,
        "mark_objs": mark_objs,
        "skip_fns": skip_fns,
        "xfail_fns": xfail_fns,
        "importorskip_fns": importorskip_fns,
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


def _is_forbidden_mark_expr(expr, aliases, allow_skipif=True):
    """Return a short description if `expr` is a forbidden skip/xfail mark/decorator."""
    call_args = None
    target = expr
    if isinstance(expr, ast.Call):
        call_args = expr.args
        target = expr.func
    chain = _attr_chain(target)
    if not chain:
        return None
    # pytest.mark.skip / pytest.mark.xfail / pytest.mark.skipif(True, ...)
    if len(chain) == 3 and chain[0] in aliases["pytest_mods"] and chain[1] == "mark":
        mname = chain[2]
        if mname in ("skip", "xfail"):
            return f"{'.'.join(chain)}"
        if mname == "skipif":
            if not allow_skipif:
                return f"{'.'.join(chain)}"
            if call_args and isinstance(call_args[0], ast.Constant) and bool(call_args[0].value):
                return f"{'.'.join(chain)}(True, ...)"
    # from pytest import mark; mark.skip / mark.xfail / mark.skipif(True, ...)
    if len(chain) == 2 and chain[0] in aliases["mark_objs"]:
        mname = chain[1]
        if mname in ("skip", "xfail"):
            return f"{'.'.join(chain)}"
        if mname == "skipif":
            if not allow_skipif:
                return f"{'.'.join(chain)}"
            if call_args and isinstance(call_args[0], ast.Constant) and bool(call_args[0].value):
                return f"{'.'.join(chain)}(True, ...)"
    # unittest.skip / skipIf / skipUnless
    if len(chain) == 2 and chain[0] in aliases["unittest_mods"] and chain[1] in ("skip", "skipIf", "skipUnless"):
        return f"{'.'.join(chain)}"
    if len(chain) == 1 and chain[0] in (aliases["unittest_skip_decs"] | aliases["skip_fns"] | aliases["xfail_fns"]):
        return chain[0]
    return None


def _check_pytestmark_stmts(stmts, aliases):
    """Reject unconditional `pytestmark = pytest.mark.skip / xfail` assignments."""
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
            bad = _is_forbidden_mark_expr(item, aliases, allow_skipif=True)
            if bad:
                return f"forbidden pytestmark ({bad})"
    return None


def _check_func_for_skips(fn_node, aliases, cls_node=None):
    """Return a short reason if `fn_node` (or enclosing `cls_node`) has skip/xfail cheats."""
    for owner in ([cls_node] if cls_node is not None else []) + [fn_node]:
        for dec in owner.decorator_list:
            bad = _is_forbidden_mark_expr(dec, aliases, allow_skipif=True)
            if bad:
                return f"forbidden decorator @{bad} on {owner.name}"
    if cls_node is not None:
        bad_pm = _check_pytestmark_stmts(cls_node.body, aliases)
        if bad_pm:
            return f"{bad_pm} on {cls_node.name}"

    for sub in ast.walk(fn_node):
        if isinstance(sub, ast.Call):
            chain = _attr_chain(sub.func)
            if not chain:
                continue
            if len(chain) == 2 and chain[0] in aliases["pytest_mods"] and chain[1] in ("skip", "xfail", "importorskip"):
                return f"forbidden inline call {'.'.join(chain)}() in {fn_node.name}"
            if len(chain) == 1 and chain[0] in (aliases["skip_fns"] | aliases["xfail_fns"] | aliases["importorskip_fns"]):
                return f"forbidden inline call {chain[0]}() in {fn_node.name}"
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
        tree, src, perr = _parse_ast_cached(full)
        if perr is not None or tree is None:
            errors.append(f"ref_verified_by test file {norm!r} failed to parse: {perr}")
            continue
        aliases = _collect_skip_aliases(tree)
        bad_mod_pm = _check_pytestmark_stmts(tree.body, aliases)
        if bad_mod_pm:
            errors.append(f"ref_verified_by {norm!r}: {bad_mod_pm}")
            continue

        # Locate cited test node (last definition wins, matching Python semantics).
        cls_node = None
        fn_node = None
        if "::" in node_part:
            cls_name, fn_name = node_part.split("::", 1)
            for stmt in tree.body:
                if isinstance(stmt, ast.ClassDef) and stmt.name == cls_name:
                    cls_node = stmt
            if cls_node is not None:
                for stmt in cls_node.body:
                    if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)) and stmt.name == fn_name:
                        fn_node = stmt
        else:
            for stmt in tree.body:
                if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)) and stmt.name == node_part:
                    fn_node = stmt

        if fn_node is None:
            errors.append(f"ref_verified_by node {node_part!r} not found in {norm!r}")
            continue
        skip_reason = _check_func_for_skips(fn_node, aliases, cls_node=cls_node)
        if skip_reason:
            errors.append(f"ref_verified_by {norm}::{node_part}: {skip_reason}")
            continue
        if ref_base and (ref_base not in src and ref_norm not in src):
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


def check_modules(funcs, modules_file=None):
    """A function's `module = "X"` must name the analysis/modules.toml range
    that contains it (the module list is the single source for boundaries;
    rename the range there, via wc1.modules_names, to change the name)."""
    modules_file = modules_file or path("analysis", "modules.toml")
    if not os.path.exists(modules_file):
        return []
    with open(modules_file, "rb") as fh:
        mods = tomllib.load(fh).get("module", [])
    errors = []
    for a, e in funcs.items():
        if "module" not in e:
            continue
        m = next((m for m in mods if m["start"] <= a < m["end"]), None)
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
