"""Wave 4A: deterministic dependency inventory, ABI validation, and syntax-aware C rewriting.

Constructs a structured inventory of all unresolved external OMF relocations across
in-scope T4 functions (reading every attempt's structured `unresolved` records from
`wc1.t3_audit` / `wc1.match`, never truncated `problems` or `first_diff`), corroborates
original target addresses against actual disassembly/LE fixups and cited T4 test
fixtures (never from identifier spelling alone), detects containing data owners
generically from `src/include/*.h`, groups shared dependencies by underlying target,
and provides a conservative, syntax-aware mechanical reconciliation transform for
demonstrably safe cases (0 LLM calls).
"""
import ast
from collections import defaultdict
import glob
import os
import re

from . import match, path, symbols

# Classifications (in deterministic priority order for Wave 4A)
MECHANICAL_FUNC_RENAME = "MECHANICAL_FUNC_RENAME"
MECHANICAL_DATA_RENAME = "MECHANICAL_DATA_RENAME"
ABI_MISMATCH = "ABI_MISMATCH"
CONTAINING_OWNER_FIELD = "CONTAINING_OWNER_FIELD"
MISSING_FUNC = "MISSING_FUNC"
MISSING_DATA = "MISSING_DATA"
AMBIGUOUS = "AMBIGUOUS"

CLASS_PRIORITY = {
    MECHANICAL_FUNC_RENAME: 0,
    MECHANICAL_DATA_RENAME: 1,
    ABI_MISMATCH: 2,
    CONTAINING_OWNER_FIELD: 3,
    MISSING_FUNC: 4,
    MISSING_DATA: 5,
    AMBIGUOUS: 6,
}

_ADDR_LEAD_RE = re.compile(r"^(?:_?dat_|fn_|_?cd_)([0-9a-fA-F]{4,6})_?$", re.I)
_TRIGRAPH_RE = re.compile(r"\?\?[=/'()!<>-]")
_HEADER_META_RE = re.compile(r"codegen-(?:compiler|flags)")

# ---------------------------------------------------------------------------
# Syntax-aware C lexer (C89 / Watcom)
# ---------------------------------------------------------------------------

_C_TOK_RE = re.compile(
    r"(?P<COMMENT>/\*[\s\S]*?\*/|//(?:\\(?:\r?\n)|[^\r\n])*)"
    r"|(?P<STRING>\"(?:\\[\s\S]|[^\"\\\r\n])*\")"
    r"|(?P<CHAR>'(?:\\[\s\S]|[^'\\\r\n])*')"
    r"|(?P<ARROW>->)"
    r"|(?P<IDENT>[A-Za-z_][A-Za-z0-9_]*)"
    r"|(?P<NUM>0[xX][0-9a-fA-F]+|\d+)"
    r"|(?P<WS>[ \t\r\n\f\v]+)"
    r"|(?P<OTHER>.)",
)


def tokenize_c(text):
    """Tokenize C source into `(kind, value, start, end)` tuples.

    Preprocessor lines (starting with `#` at beginning of logical line, including
    leading whitespace/block-comments and backslash-continued lines) are emitted
    intact as `PREPROC` tokens so identifier rewriting never alters `#include`
    paths, `#define` names, or macro directives.
    Raises `ValueError` on C90 trigraphs or unterminated block comments/strings.
    """
    if _TRIGRAPH_RE.search(text):
        raise ValueError("C90 trigraph in C source; refusing mechanical transform")
    tokens = []
    n = len(text)
    pos = 0
    line_start = True
    while pos < n:
        if line_start:
            # Consume leading horizontal whitespace to test for preprocessor directive
            ws_end = pos
            while ws_end < n and text[ws_end] in " \t\f\v":
                ws_end += 1
            if ws_end < n and text[ws_end] == "#":
                if ws_end > pos:
                    tokens.append(("WS", text[pos:ws_end], pos, ws_end))
                p_end = ws_end
                while p_end < n:
                    nl = text.find("\n", p_end)
                    if nl == -1:
                        p_end = n
                        break
                    line_seg = text[p_end:nl].rstrip("\r")
                    p_end = nl + 1
                    if not line_seg.endswith("\\"):
                        break
                tokens.append(("PREPROC", text[ws_end:p_end], ws_end, p_end))
                pos = p_end
                line_start = True
                continue
        m = _C_TOK_RE.match(text, pos)
        if not m:
            raise ValueError(f"lexer failed at offset {pos}")
        kind = m.lastgroup
        val = m.group()
        if kind == "OTHER" and val == "/" and text[pos:pos + 2] == "/*":
            raise ValueError(f"unterminated block comment at offset {pos}")
        if kind == "OTHER" and val in ('"', "'"):
            raise ValueError(f"unterminated string/char literal at offset {pos}")
        tokens.append((kind, val, m.start(), m.end()))
        pos = m.end()
        if kind == "WS":
            if "\n" in val or "\r" in val:
                line_start = True
        elif kind == "COMMENT":
            if val.startswith("//"):
                line_start = False
            elif "\n" in val or "\r" in val:
                line_start = val.endswith("\n") or val.endswith("\r")
            # Single-line block comment preserves line_start (e.g. `/* c */ #define X 1`)
        else:
            line_start = False
    return tokens


def link_to_c_ident(link_name, kind="function"):
    """Best-effort C identifier corresponding to an OMF external link name."""
    if not link_name:
        return ""
    if kind == "function":
        if link_name.endswith("_"):
            return link_name[:-1]
        if link_name.startswith("_"):
            return link_name[1:]
        return link_name
    if link_name.startswith("_"):
        return link_name[1:]
    if link_name.endswith("_"):
        return link_name[:-1]
    return link_name


# ---------------------------------------------------------------------------
# Generic C type & struct size calculator (Watcom 32-bit, -zp2)
# ---------------------------------------------------------------------------

_PRIM_SIZES = {
    "char": 1, "signed char": 1, "unsigned char": 1,
    "short": 2, "signed short": 2, "short int": 2, "signed short int": 2,
    "unsigned short": 2, "unsigned short int": 2,
    "int": 4, "signed": 4, "signed int": 4,
    "unsigned": 4, "unsigned int": 4,
    "long": 4, "signed long": 4, "long int": 4, "signed long int": 4,
    "unsigned long": 4, "unsigned long int": 4,
    "float": 4, "double": 8,
    "FILE": 28,  # Watcom FILE struct; only used when non-pointer
}

_TYPEDEF_STRUCT_RE = re.compile(
    r"typedef\s+struct(?:\s+([A-Za-z_]\w*))?\s*\{([^{}]*)\}\s*([A-Za-z_]\w*)\s*;",
    re.S,
)
_BARE_STRUCT_RE = re.compile(
    r"(?<!typedef\s)\bstruct\s+([A-Za-z_]\w*)\s*\{([^{}]*)\}\s*;",
    re.S,
)
_TYPEDEF_ALIAS_RE = re.compile(
    r"typedef\s+(?!struct\b|union\b|enum\b)([^;{}]+?)\s+([A-Za-z_]\w*)\s*;"
)


def _strip_c_comments(text):
    return re.sub(r"/\*[\s\S]*?\*/|//[^\r\n]*", " ", text)


def _eval_int_const(expr):
    s = expr.strip()
    if not s:
        return None
    if re.fullmatch(r"0[xX][0-9a-fA-F]+|\d+", s):
        return int(s, 0)
    return None


def _parse_type_size_and_align(type_str, structs, aliases=None, pack=2):
    """Return `(size_bytes, align_bytes)` or `(None, None)` for a C type string."""
    aliases = aliases or {}
    s = " ".join(_strip_c_comments(type_str).split()).strip()
    if not s:
        return None, None
    # Strip leading qualifiers/storage classes
    s = re.sub(r"\b(?:extern|static|const|volatile|register|far|near|__cdecl|__watcall)\b", "", s)
    s = " ".join(s.split()).strip()
    # Function pointer: e.g. `void (*)(...)` or `int (*foo[4])(...)`
    fp_arr = re.search(r"\(\s*\*\s*(?:[A-Za-z_]\w*)?\s*((?:\[[^\]]+\])+)\s*\)\s*\(", s)
    if fp_arr:
        total = 4
        for dim in re.findall(r"\[([^\]]+)\]", fp_arr.group(1)):
            v = _eval_int_const(dim)
            if v is None:
                return None, None
            total *= v
        return total, min(4, pack)
    if re.search(r"\(\s*\*\s*[A-Za-z_0-9_]*\s*\)\s*\(", s):
        return 4, min(4, pack)
    # Trailing array dimensions: `T[A][B]`
    dims = []
    while True:
        m = re.search(r"\[\s*([^\]]*)\s*\]\s*$", s)
        if not m:
            break
        v = _eval_int_const(m.group(1))
        if v is None:
            return None, None
        dims.append(v)
        s = s[:m.start()].strip()
    dims.reverse()
    if s.endswith("*"):
        elem_sz, elem_al = 4, min(4, pack)
    else:
        s_nostruct = re.sub(r"^struct\s+", "", s).strip()
        if s_nostruct in _PRIM_SIZES:
            elem_sz = _PRIM_SIZES[s_nostruct]
            elem_al = min(elem_sz, pack)
        elif s_nostruct in structs:
            elem_sz, elem_al = structs[s_nostruct]["size"], structs[s_nostruct]["align"]
        elif s_nostruct in aliases:
            elem_sz, elem_al = _parse_type_size_and_align(aliases[s_nostruct], structs, aliases, pack=pack)
            if elem_sz is None:
                return None, None
        else:
            return None, None
    total = elem_sz
    for d in dims:
        total *= d
    return total, elem_al


def parse_header_structs(include_dir=None, pack=2):
    """Parse flat struct definitions across `src/include/*.h` under Watcom `-zp2`.

    Returns `{name: {"size": int, "align": int, "fields": [(off, sz, field_name, field_type)]}}`.
    """
    inc = include_dir or path("src", "include")
    if not os.path.isdir(inc):
        return {}, {}
    raw_structs = []
    aliases = {}
    for fn in sorted(glob.glob(os.path.join(inc, "*.h"))):
        try:
            text = _strip_c_comments(open(fn, encoding="latin-1").read())
        except OSError:
            continue
        for m in _TYPEDEF_ALIAS_RE.finditer(text):
            base = " ".join(m.group(1).split())
            alias = m.group(2)
            if "(" not in base and alias not in aliases:
                aliases[alias] = base
        for m in _TYPEDEF_STRUCT_RE.finditer(text):
            tag, body, tname = m.group(1), m.group(2), m.group(3)
            raw_structs.append((tname, tag, body))
        for m in _BARE_STRUCT_RE.finditer(text):
            tag, body = m.group(1), m.group(2)
            raw_structs.append((tag, tag, body))

    structs = {}
    # Multi-pass resolution so nested structs (e.g. Rect inside Layer) resolve
    for _ in range(4):
        progressed = False
        for name, tag, body in raw_structs:
            if name in structs:
                continue
            off = 0
            max_al = 1
            fields = []
            ok = True
            for decl in body.split(";"):
                decl = " ".join(decl.split()).strip()
                if not decl:
                    continue
                # Function pointer field: `void (*draw)(...)`
                mfp = re.match(r"^(.+?)\(\s*\*\s*([A-Za-z_]\w*)\s*((?:\[[^\]]+\])*)\s*\)\s*\(.*\)$", decl)
                if mfp:
                    fname = mfp.group(2)
                    arr = mfp.group(3) or ""
                    sz, al = _parse_type_size_and_align(f"void (*{arr})()", structs, aliases, pack=pack)
                    if sz is None:
                        ok = False
                        break
                    if al > 1 and (off % al):
                        off += al - (off % al)
                    fields.append((off, sz, fname, decl))
                    off += sz
                    max_al = max(max_al, al)
                    continue
                # Handle comma-separated declarators: `short x, y, w, h`
                # Find base type before first declarator
                parts = [p.strip() for p in decl.split(",")]
                first = parts[0]
                m0 = re.match(r"^(.+?)\s*(\*+\s*)?([A-Za-z_]\w*)((?:\s*\[[^\]]*\])*)$", first)
                if not m0:
                    ok = False
                    break
                base_type = m0.group(1).strip()
                decls_list = [(m0.group(2) or "", m0.group(3), m0.group(4) or "")]
                for rest in parts[1:]:
                    mr = re.match(r"^(\*+\s*)?([A-Za-z_]\w*)((?:\s*\[[^\]]*\])*)$", rest)
                    if not mr:
                        ok = False
                        break
                    decls_list.append((mr.group(1) or "", mr.group(2), mr.group(3) or ""))
                if not ok:
                    break
                for stars, fname, arr in decls_list:
                    ftype = f"{base_type} {stars}{arr}".strip()
                    sz, al = _parse_type_size_and_align(ftype, structs, aliases, pack=pack)
                    if sz is None:
                        ok = False
                        break
                    if al > 1 and (off % al):
                        off += al - (off % al)
                    fields.append((off, sz, fname, ftype))
                    off += sz
                    max_al = max(max_al, al)
                if not ok:
                    break
            if ok and fields:
                if max_al > 1 and (off % max_al):
                    off += max_al - (off % max_al)
                info = {"size": off, "align": max_al, "fields": fields}
                structs[name] = info
                if tag and tag not in structs:
                    structs[tag] = info
                progressed = True
        if not progressed:
            break
    return structs, aliases


def find_containing_owner(addr, datas, structs, aliases=None):
    """Find an existing `[[data]]` object whose storage strictly contains `addr`.

    Rejects bogus oversized pointer-typed-as-array DB entries (e.g. a 4-byte heap
    pointer annotated as `T[4096]` whose nominal span covers dozens of unrelated
    globals). Returns a dict `{addr, name, link_name, type, file, size, offset,
    element_index, field_offset, field_name}` or None.
    """
    best = None
    all_addrs = sorted(datas)
    for daddr, e in sorted(datas.items()):
        if daddr >= addr:
            continue
        dtype = str(e.get("type") or "").strip()
        if not dtype:
            continue
        sz, _ = _parse_type_size_and_align(dtype, structs, aliases)
        if sz is None or sz <= 1:
            continue
        if daddr < addr < daddr + sz:
            # Guard against 4-byte heap pointers mistakenly typed as huge arrays in TOML:
            # if nominal size >= 0x400 and dozens of other DB symbols live inside its span
            # (or a distinct non-struct DB entry already starts at daddr + 4), it's a pointer.
            if sz >= 0x400:
                interior = [x for x in all_addrs if daddr < x < daddr + sz]
                if len(interior) >= 30 or ((daddr + 4) in datas and not any(
                    re.sub(r"^(?:const\s+|volatile\s+)?(?:struct\s+)?", "", dtype.split("[", 1)[0]).strip() in structs
                    for _ in (0,)
                )):
                    continue
            rel = addr - daddr
            # Compute array element & struct field info when available
            elem_idx = None
            field_off = rel
            field_name = None
            m_arr = re.match(r"^(.+?)\s*\[\s*([^\]]+)\s*\]\s*$", dtype)
            elem_type = m_arr.group(1).strip() if m_arr else dtype
            if m_arr:
                esz, _ = _parse_type_size_and_align(elem_type, structs, aliases)
                if esz and esz > 0:
                    elem_idx, field_off = divmod(rel, esz)
            st_key = re.sub(r"^(?:const\s+|volatile\s+)?(?:struct\s+)?", "", elem_type).strip()
            if st_key in structs:
                for foff, fsz, fname, _ft in structs[st_key]["fields"]:
                    if foff <= field_off < foff + fsz:
                        field_name = fname
                        break
            cand = {
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
            # Prefer tightest containing owner
            if best is None or sz < best["size"]:
                best = cand
    return best


# ---------------------------------------------------------------------------
# Conservative C prototype & data-declaration parsing / ABI validation
# ---------------------------------------------------------------------------

def _norm_c_type(t):
    """Normalize a C type for conservative Watcom 32-bit ABI compatibility checks."""
    s = " ".join(_strip_c_comments(t).split()).strip()
    s = re.sub(r"\b(?:extern|static|register|volatile|near|far)\b", "", s)
    s = " ".join(s.split()).strip()
    is_const = bool(re.search(r"\bconst\b", s))
    s_nc = " ".join(re.sub(r"\bconst\b", "", s).split()).strip()
    # Function pointer
    if re.search(r"\(\s*\*\s*[A-Za-z0-9_]*\s*\)\s*\(", s_nc):
        return ("funcptr", s_nc, is_const)
    # Array dimensions
    m_arr = re.match(r"^(.+?)\s*((?:\[[^\]]*\])+)\s*$", s_nc)
    if m_arr:
        base_n = _norm_c_type(m_arr.group(1))
        dims = tuple(_eval_int_const(d) for d in re.findall(r"\[([^\]]*)\]", m_arr.group(2)))
        return ("array", base_n, dims, is_const)
    # Pointer
    if s_nc.endswith("*"):
        depth = 0
        cur = s_nc
        while cur.endswith("*"):
            depth += 1
            cur = cur[:-1].strip()
        base = re.sub(r"^struct\s+", "", cur).strip()
        return ("ptr", depth, base, is_const)
    base = re.sub(r"^struct\s+", "", s_nc).strip()
    aliases = {
        "signed": "int", "signed int": "int", "long": "int", "signed long": "int", "long int": "int",
        "unsigned": "unsigned int", "unsigned long": "unsigned int", "unsigned long int": "unsigned int",
        "signed short": "short", "short int": "short", "signed short int": "short",
        "unsigned short int": "unsigned short",
    }
    base = aliases.get(base, base)
    return ("scalar", base, is_const)


def _split_c_params(param_str):
    parts = []
    cur = []
    depth = 0
    for ch in param_str:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "," and depth == 0:
            parts.append("".join(cur).strip())
            cur = []
            continue
        cur.append(ch)
    tail = "".join(cur).strip()
    if tail:
        parts.append(tail)
    return parts


def parse_c_func_decl(decl_str):
    """Parse a single C function prototype into `{conv, ret, name, params, variadic}` or None."""
    s = " ".join(_strip_c_comments(decl_str).split()).strip().rstrip(";").strip()
    if not s:
        return None
    conv = "cdecl" if re.search(r"\b__cdecl\b|\bcdecl\b", s) else "watcall"
    s = re.sub(r"\b(?:extern|static|__cdecl|cdecl|__watcall|watcall|__interrupt)\b", "", s)
    s = " ".join(s.split()).strip()
    # Find the outer parameter list `( ... )` at the end
    if not s.endswith(")"):
        return None
    depth = 0
    open_idx = -1
    for i in range(len(s) - 1, -1, -1):
        if s[i] == ")":
            depth += 1
        elif s[i] == "(":
            depth -= 1
            if depth == 0:
                open_idx = i
                break
    if open_idx <= 0:
        return None
    head = s[:open_idx].strip()
    param_raw = s[open_idx + 1:-1].strip()
    # Reject function pointer variables like `void (*fn)(int)`
    if head.endswith(")"):
        return None
    m_name = re.search(r"([A-Za-z_]\w*)\s*$", head)
    if not m_name:
        return None
    name = m_name.group(1)
    ret_str = head[:m_name.start()].strip()
    if not ret_str:
        return None
    variadic = False
    params = []
    if param_raw == "":
        return None  # K&R empty `()` is ambiguous for mechanical ABI proof
    if param_raw != "void":
        for p in _split_c_params(param_raw):
            if p == "...":
                variadic = True
                continue
            # Function pointer param: keep intact
            if re.search(r"\(\s*\*", p):
                params.append(_norm_c_type(p))
                continue
            # Strip optional trailing parameter identifier ONLY when separated by whitespace
            # or `*`, never splitting a single type token (`short`, `signed`, `int`) or a
            # `struct`/`union`/`enum` tag name (`struct Unit`).
            mp = re.match(r"^(.+?(?:\s+|\*+\s*))([A-Za-z_]\w*)\s*((?:\[[^\]]*\])*)$", p)
            _TYPE_KW = {
                "char", "short", "int", "long", "unsigned", "signed",
                "void", "const", "volatile", "float", "double", "FILE",
            }
            if mp:
                head_t = mp.group(1).strip()
                tail_id = mp.group(2)
                arr_s = mp.group(3)
                head_words = head_t.split()
                prev_word = head_words[-1] if head_words else ""
                if tail_id not in _TYPE_KW and prev_word not in ("struct", "union", "enum"):
                    ptype = (head_t + (" *" if arr_s else "")).strip()
                else:
                    ptype = p
            else:
                ptype = p
            params.append(_norm_c_type(ptype))
    return {"conv": conv, "ret": _norm_c_type(ret_str), "name": name,
            "params": params, "variadic": variadic}


def parse_c_data_decl(decl_str, ident):
    """Parse `extern <type> ident[...];` into normalized type tuple or None."""
    s = " ".join(_strip_c_comments(decl_str).split()).strip().rstrip(";").strip()
    if not s or not re.search(rf"\b{re.escape(ident)}\b", s):
        return None
    # Function pointer data global? e.g. `extern void (*ident)(void);`
    if re.search(rf"\(\s*\*\s*{re.escape(ident)}\b", s):
        return _norm_c_type(re.sub(rf"\b{re.escape(ident)}\b", "", s, count=1))
    # Reject function prototypes
    if "(" in s and ")" in s:
        return None
    # Strip `extern` and replace identifier cleanly
    s2 = re.sub(r"^\s*extern\s+", "", s)
    m = re.match(rf"^(.+?)\b{re.escape(ident)}\b\s*((?:\[[^\]]*\])*)\s*$", s2)
    if not m:
        return None
    tstr = (m.group(1).strip() + " " + m.group(2).strip()).strip()
    return _norm_c_type(tstr)


def _types_abi_compatible(t1, t2, *, is_param=False, is_data=False):
    """Conservative type compatibility check. False -> defer to LLM research."""
    if t1 is None or t2 is None:
        return False
    if t1[0] != t2[0]:
        # Pointer vs array of same element type in parameter position is compatible,
        # NOT in extern data object position (pointer loads indirection vs array takes address!).
        if is_param and {t1[0], t2[0]} == {"ptr", "array"}:
            ptr = t1 if t1[0] == "ptr" else t2
            arr = t2 if t1[0] == "ptr" else t1
            if ptr[1] == 1 and arr[1][0] == "scalar" and ptr[2] == arr[1][1]:
                return True
        return False
    kind = t1[0]
    if kind == "scalar":
        if t1[1] != t2[1]:
            return False
        if is_data and t1[2] != t2[2]:
            # const mismatch on data can cause compile warnings/errors in callers
            return False
        return True
    if kind == "ptr":
        _, d1, b1, _c1 = t1
        _, d2, b2, _c2 = t2
        if d1 != d2:
            return False
        if b1 == b2:
            return True
        # In parameter/return position, `void *` is compatible with any single-level object pointer;
        # for data globals (`extern void *flic_file` vs `extern FILE *flic_file`), be strict!
        if not is_data and d1 == 1 and ("void" in (b1, b2)):
            return True
        return False
    if kind == "array":
        _, b1, dims1, c1 = t1
        _, b2, dims2, c2 = t2
        if is_data and c1 != c2:
            return False
        if not _types_abi_compatible(b1, b2, is_param=is_param, is_data=is_data):
            return False
        # Compatible if same rank and all known dimensions agree (allowing `T[]` vs `T[N]`)
        if len(dims1) != len(dims2):
            return False
        for x, y in zip(dims1, dims2):
            if x is not None and y is not None and x != y:
                return False
        return True
    if kind == "funcptr":
        return t1[1] == t2[1]
    return False


def prototypes_compatible(local_decl, db_proto, db_conv="watcall", expected_ident=None):
    """True only when local C prototype declares `expected_ident` (if given) and matches DB ABI."""
    if db_conv not in ("watcall", "cdecl"):
        return False
    loc = parse_c_func_decl(local_decl)
    db = parse_c_func_decl(db_proto or "")
    if not loc or not db:
        return False
    if expected_ident is not None and loc["name"] != expected_ident:
        return False
    if loc["conv"] != db_conv:
        return False
    if loc["variadic"] != db["variadic"]:
        return False
    if len(loc["params"]) != len(db["params"]):
        return False
    if not _types_abi_compatible(loc["ret"], db["ret"], is_param=False):
        return False
    for lp, dp in zip(loc["params"], db["params"]):
        if not _types_abi_compatible(lp, dp, is_param=True):
            return False
    return True


def data_decls_compatible(local_decl, ident, db_type):
    """True only when local extern data decl and DB type match in storage shape and width."""
    if not db_type:
        return False
    loc = parse_c_data_decl(local_decl, ident)
    db = _norm_c_type(db_type)
    if not loc or not db:
        return False
    return _types_abi_compatible(loc, db, is_data=True)


# ---------------------------------------------------------------------------
# Source declaration scanning & T4 test `extra` AST extraction
# ---------------------------------------------------------------------------

def _resolve_local_includes(ref_rel, repo_root):
    """Return `[ref_rel, included_header_rel, ...]` for local `#include "..."` files."""
    out = []
    seen = set()
    q = [ref_rel]
    while q:
        rel = q.pop(0).replace("\\", "/")
        if rel in seen:
            continue
        full = os.path.join(repo_root, rel)
        if not os.path.isfile(full):
            continue
        seen.add(rel)
        out.append(rel)
        try:
            text = open(full, encoding="latin-1").read()
        except OSError:
            continue
        for inc in re.findall(r'^\s*#include\s+"([^"]+)"', text, flags=re.M):
            for base_dir in (os.path.dirname(rel), "src/include"):
                cand = os.path.normpath(os.path.join(base_dir, inc)).replace("\\", "/")
                if os.path.isfile(os.path.join(repo_root, cand)):
                    q.append(cand)
                    break
    return out


def find_declarations_in_unit(ref_rel, ident, repo_root=None):
    """Find declaration lines for `ident` across `ref_rel` and its local `#include` headers.

    Returns list of `{"file": rel, "line": int, "text": str, "in_ref": bool}`.
    """
    root = repo_root or path()
    if not ident:
        return []
    pat = re.compile(rf"\b{re.escape(ident)}\b")
    decl_start = re.compile(
        r"^\s*(?:extern\s+|static\s+|(?:const|volatile|unsigned|signed|void|short|long|int|char|struct|FILE|[A-Z]\w*)\b)"
    )
    found = []
    for rel in _resolve_local_includes(ref_rel, root):
        try:
            lines = open(os.path.join(root, rel), encoding="latin-1").read().splitlines()
        except OSError:
            continue
        for lineno, line in enumerate(lines, 1):
            stripped = _strip_c_comments(line).strip()
            if not stripped or stripped.startswith("#"):
                continue
            if pat.search(stripped) and decl_start.match(stripped) and stripped.endswith(";"):
                # Avoid matching plain assignments/calls inside function bodies (indented lines)
                if line[:1] not in (" ", "\t"):
                    found.append({"file": rel, "line": lineno, "text": stripped, "in_ref": rel == ref_rel})
    return found


def find_header_declarations(ident, repo_root=None):
    """Find declarations of canonical `ident` across `src/include/*.h`."""
    root = repo_root or path()
    inc_dir = os.path.join(root, "src", "include")
    if not ident or not os.path.isdir(inc_dir):
        return []
    pat = re.compile(rf"\b{re.escape(ident)}\b")
    out = []
    for fn in sorted(glob.glob(os.path.join(inc_dir, "*.h"))):
        rel = os.path.relpath(fn, root).replace("\\", "/")
        try:
            lines = open(fn, encoding="latin-1").read().splitlines()
        except OSError:
            continue
        for lineno, line in enumerate(lines, 1):
            s = _strip_c_comments(line).strip()
            if not s or s.startswith("#"):
                continue
            if pat.search(s) and s.endswith(";") and line[:1] not in (" ", "\t"):
                out.append({"file": rel, "line": lineno, "text": s})
    return out


def extract_test_extra_mappings(ref_verified_by, repo_root=None):
    """Parse explicit `{link_name: addr}` dicts from the cited T4 test file via AST.

    Captures top-level dict literals (e.g. `EXTRA = {"MapInputRestore_": 0x1a328}`) and
    `extra={...}` keyword arguments, resolving simple module-level integer constants.
    """
    root = repo_root or path()
    nodes, err = symbols.parse_ref_verified_by_nodes(ref_verified_by or "")
    if err or not nodes:
        return {}
    mapping = {}
    for file_rel, _node in nodes:
        full = os.path.join(root, file_rel)
        if not os.path.isfile(full):
            continue
        try:
            tree = ast.parse(open(full, encoding="utf-8", errors="replace").read(), filename=full)
        except (OSError, SyntaxError):
            continue
        consts = {}
        for stmt in tree.body:
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                val = _ast_int(stmt.value, consts)
                if val is not None:
                    consts[stmt.targets[0].id] = val
        for node in ast.walk(tree):
            if isinstance(node, ast.Dict):
                for k, v in zip(node.keys, node.values):
                    if isinstance(k, ast.Constant) and isinstance(k.value, str):
                        addr = _ast_int(v, consts)
                        if addr is not None and 0x10000 <= addr < 0x70000:
                            mapping.setdefault(k.value, set()).add((addr, file_rel))
    return mapping


def _ast_int(node, consts):
    if isinstance(node, ast.Constant) and isinstance(node.value, int) and not isinstance(node.value, bool):
        return int(node.value)
    if isinstance(node, ast.Name) and node.id in consts:
        return consts[node.id]
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub)):
        l = _ast_int(node.left, consts)
        r = _ast_int(node.right, consts)
        if l is not None and r is not None:
            return l + r if isinstance(node.op, ast.Add) else l - r
    return None


# ---------------------------------------------------------------------------
# Original-binary target corroboration & dependency inventory
# ---------------------------------------------------------------------------

def _orig_function_refs(p, start_addr, starts_by_addr):
    """All direct `call`/`jmp` targets and LE fixup targets inside `[start_addr, end)`."""
    f = starts_by_addr.get(start_addr)
    if not f:
        return {}
    refs = defaultdict(list)
    end = f["end"]
    insns = getattr(p, "insns", None) or {}
    fix_at = getattr(p, "fix_at", None) or {}
    for pc in range(start_addr, end):
        ins = insns.get(pc)
        if ins is None:
            continue
        if ins.mnemonic in ("call", "jmp") and re.fullmatch(r"0x[0-9a-fA-F]+", ins.op_str):
            t = int(ins.op_str, 16)
            if not (start_addr <= t < end):
                refs[t].append(f"{pc:#x} {ins.mnemonic} {ins.op_str}")
        for off in range(pc, pc + ins.size):
            if off in fix_at:
                t = fix_at[off][1]
                refs[t].append(f"{pc:#x} {ins.mnemonic} {ins.op_str} (LE fixup {off:#x})")
    return refs


def _infer_symbol_kind(symbol, reloc_kinds):
    if any(sr for sr, _loc, _op in reloc_kinds):
        return "function"
    if symbol.startswith("_") and not symbol.endswith("_"):
        return "data"
    if symbol.startswith("cd_"):
        return "data"
    if symbol.endswith("_"):
        return "function"
    return "data"


def _slug_group_id(kind_tag, key):
    s = re.sub(r"[^a-z0-9_]+", "_", str(key).lower()).strip("_")
    return f"{kind_tag}_{s}"


def build_dependency_inventory(audit_report, p, funcs, datas, by_link, repo_root=None,
                               established_mappings=None):
    """Construct the structured Wave 4A dependency inventory from a `t3_audit` report.

    Reads every `attempts[].unresolved` entry on in-scope T4 functions (never truncated
    `best.problems` or `first_diff`), corroborates target addresses against original
    binary evidence, detects containing data owners, classifies each dependency, and
    groups dependencies by underlying target.
    """
    root = repo_root or path()
    est_map = established_mappings if isinstance(established_mappings, dict) else {}
    starts_by_addr = {f["start"]: f for f in (getattr(p, "functions", None) or [])}
    structs, aliases = parse_header_structs(os.path.join(root, "src", "include"))

    # Collect per-symbol unresolved occurrences across all T4 mismatch attempts
    by_sym = defaultdict(lambda: {"affected": {}, "reloc_kinds": set(), "addends": set()})
    orig_refs_cache = {}
    test_extras_cache = {}

    for row in (audit_report or {}).get("results", []):
        if row.get("tier") != "T4":
            continue
        if row.get("status") in ("MATCH_BUILDABLE", "MATCH_UNBUILDABLE"):
            continue
        addr = row["addr"]
        best = row.get("best") or {}
        best_score = list(best.get("score") or [])
        best_unres_syms = {u["symbol"] for u in best.get("unresolved", ()) if u.get("symbol")}
        attempts = row.get("attempts") or []
        for att in attempts:
            unres_list = att.get("unresolved") or []
            if not unres_list:
                continue
            for u in unres_list:
                sym = u.get("symbol")
                if not sym:
                    continue
                bucket = by_sym[sym]
                bucket["reloc_kinds"].add((bool(u.get("self_relative")), u.get("loc"), u.get("operand")))
                if u.get("addend") is not None:
                    bucket["addends"].add(int(u["addend"]))
                af = bucket["affected"].setdefault(addr, {
                    "addr": addr,
                    "addr_hex": f"{addr:#x}",
                    "name": row.get("name"),
                    "link_name": row.get("link_name"),
                    "ref": row.get("ref"),
                    "toml": row.get("toml"),
                    "module": row.get("module"),
                    "ref_verified_by": row.get("ref_verified_by"),
                    "best_score": best_score,
                    "best_unresolved_count": len(best_unres_syms),
                    "zero_score_blocked": (best_score == [0, 0, 0, 0, 0] and sym in best_unres_syms),
                    "occurrences": [],
                })
                occ = {
                    "attempt_index": att.get("index"),
                    "is_best_attempt": (att == best),
                    "cflags": att.get("cflags"),
                    "offset": u.get("offset"),
                    "instruction_offset": u.get("instruction_offset"),
                    "self_relative": bool(u.get("self_relative")),
                    "addend": u.get("addend"),
                    "operand": u.get("operand"),
                    "original_candidate": u.get("original_candidate"),
                }
                if occ not in af["occurrences"]:
                    af["occurrences"].append(occ)

    dependencies = []
    for sym, bucket in sorted(by_sym.items()):
        kind = _infer_symbol_kind(sym, bucket["reloc_kinds"])
        ident = link_to_c_ident(sym, kind=kind)
        m_lead = _ADDR_LEAD_RE.match(sym)
        addr_lead = int(m_lead.group(1), 16) if m_lead else None
        affected_list = sorted(bucket["affected"].values(), key=lambda x: x["addr"])

        # Corroborate target address across all affected functions (and track per-caller coverage)
        corroborated = defaultdict(list)  # addr -> list[str evidence]
        corroborated_callers = defaultdict(set)  # addr -> set[caller_addr]
        for af in affected_list:
            fa = af["addr"]
            if fa not in orig_refs_cache:
                orig_refs_cache[fa] = _orig_function_refs(p, fa, starts_by_addr)
            orefs = orig_refs_cache[fa]
            af["decls"] = find_declarations_in_unit(af["ref"], ident, repo_root=root) if af.get("ref") else []

            def _add_corr(target_a, ev_str):
                corroborated[target_a].append(ev_str)
                corroborated_callers[target_a].add(fa)

            # 1. Structured original_candidate from match.py (from the best attempt only,
            #    so misaligned non-best flag attempts cannot inject bogus same-offset leads)
            for occ in af["occurrences"]:
                if not occ.get("is_best_attempt"):
                    continue
                cand_a = occ.get("original_candidate")
                if cand_a is None:
                    continue
                addend = occ.get("addend") or 0
                eff = cand_a + addend
                if cand_a in orefs:
                    _add_corr(cand_a, f"{af['addr_hex']} same-offset operand -> {orefs[cand_a][0]}")
                elif eff in orefs:
                    _add_corr(cand_a, f"{af['addr_hex']} same-offset operand (+{addend:#x}) -> {orefs[eff][0]}")

            # 2. Address-shaped lead corroborated by actual original call/fixup in this function
            if addr_lead is not None:
                if addr_lead in orefs:
                    _add_corr(addr_lead, f"{af['addr_hex']} lead corroborated -> {orefs[addr_lead][0]}")
                else:
                    for addend in bucket["addends"]:
                        if (addr_lead + addend) in orefs:
                            _add_corr(
                                addr_lead,
                                f"{af['addr_hex']} lead (+{addend:#x}) corroborated -> {orefs[addr_lead + addend][0]}",
                            )

            # 3. Cited T4 test `extra=`/`EXTRA` fixture corroborated by original call/fixup
            rvb = af.get("ref_verified_by") or ""
            if rvb not in test_extras_cache:
                test_extras_cache[rvb] = extract_test_extra_mappings(rvb, repo_root=root)
            for taddr, tfile in sorted(test_extras_cache[rvb].get(sym, ())):
                if taddr in orefs:
                    _add_corr(taddr, f"{af['addr_hex']} test {tfile} extra + {orefs[taddr][0]}")
                else:
                    for addend in bucket["addends"]:
                        if (taddr + addend) in orefs:
                            _add_corr(
                                taddr,
                                f"{af['addr_hex']} test {tfile} extra (+{addend:#x}) + {orefs[taddr + addend][0]}",
                            )

            # 4. Established mapping from earlier verified Wave 4A reconciliations,
            #    STILL corroborated against actual original calls/fixups in this caller.
            est_ent = est_map.get(sym)
            if isinstance(est_ent, dict) and isinstance(est_ent.get("target_addr"), int):
                eaddr = est_ent["target_addr"]
                if eaddr in orefs:
                    _add_corr(eaddr, f"{af['addr_hex']} established mapping -> {orefs[eaddr][0]}")
                else:
                    for addend in bucket["addends"]:
                        if (eaddr + addend) in orefs:
                            _add_corr(
                                eaddr,
                                f"{af['addr_hex']} established mapping (+{addend:#x}) -> {orefs[eaddr + addend][0]}",
                            )

        corr_addrs = sorted(corroborated.keys())
        ambiguous = len(corr_addrs) != 1
        expected_addr = corr_addrs[0] if len(corr_addrs) == 1 else None
        all_callers_corroborated = (
            expected_addr is not None
            and all(af["addr"] in corroborated_callers[expected_addr] for af in affected_list)
        )
        conflict_addrs = corr_addrs if len(corr_addrs) > 1 else []
        ev_list = sorted(set(corroborated.get(expected_addr, ())))[:12] if expected_addr is not None else []

        # DB lookup & containing owner lookup
        db_entry = None
        containing_owner = None
        canon_hdr_decls = []
        if expected_addr is not None:
            raw_db = funcs.get(expected_addr) if kind == "function" else datas.get(expected_addr)
            if raw_db is not None:
                db_entry = {
                    k: raw_db[k]
                    for k in ("addr", "name", "link_name", "conv", "proto", "type", "confidence", "_file", "_kind", "module")
                    if k in raw_db
                }
                canon_hdr_decls = find_header_declarations(raw_db.get("name"), repo_root=root)
            elif kind == "data":
                containing_owner = find_containing_owner(expected_addr, datas, structs, aliases)

        # Classify & compute blockers
        blockers = []
        classification = AMBIGUOUS
        addends_sorted = sorted(bucket["addends"])

        if ambiguous:
            classification = AMBIGUOUS
            if conflict_addrs:
                blockers.append("conflicting corroborated targets: " + ", ".join(f"{a:#x}" for a in conflict_addrs))
            else:
                blockers.append("no independently corroborated target address in original instructions/fixups")
        elif kind == "function":
            if expected_addr not in starts_by_addr and db_entry is None:
                classification = AMBIGUOUS
                blockers.append(f"target {expected_addr:#x} is not a discovered function start")
            elif db_entry is None:
                classification = MISSING_FUNC
                blockers.append(f"no [[func]] entry at {expected_addr:#x}")
            elif db_entry.get("link_name") == sym:
                classification = AMBIGUOUS
                blockers.append(f"canonical link_name already equals {sym}")
            else:
                # Check if ALL affected functions corroborate expected_addr and have proven ABI-compatible decls
                abi_ok = True
                if not all_callers_corroborated:
                    abi_ok = False
                    blockers.append(f"target {expected_addr:#x} not independently corroborated in all affected callers")
                if addends_sorted and addends_sorted != [0]:
                    abi_ok = False
                    blockers.append(f"nonzero function relocation addends: {addends_sorted}")
                if not db_entry.get("proto"):
                    abi_ok = False
                    blockers.append(f"DB entry {db_entry['name']} has no proto")
                for af in affected_list:
                    decls = af.get("decls") or []
                    if not decls:
                        abi_ok = False
                        blockers.append(f"{af['ref']}: no top-level declaration of {ident} found")
                        continue
                    for d in decls:
                        if not prototypes_compatible(
                            d["text"], db_entry.get("proto"), db_entry.get("conv", "watcall"),
                            expected_ident=ident,
                        ):
                            abi_ok = False
                            blockers.append(f"{d['file']}:{d['line']}: ABI differs from DB proto {db_entry.get('proto')!r}")
                classification = MECHANICAL_FUNC_RENAME if abi_ok else (AMBIGUOUS if not all_callers_corroborated else ABI_MISMATCH)
        else:
            # Data dependency
            if db_entry is None:
                if containing_owner is not None:
                    classification = CONTAINING_OWNER_FIELD
                    blockers.append(
                        f"interior address inside {containing_owner['name']} ({containing_owner['addr_hex']} "
                        f"+{containing_owner['offset']:#x})"
                    )
                else:
                    # Check if address is inside code segment (code-segment table/string)
                    o = p.le.obj_at(expected_addr) if hasattr(p, "le") and hasattr(p.le, "obj_at") else None
                    if o is not None and o.index == 0 and expected_addr in starts_by_addr:
                        classification = AMBIGUOUS
                        blockers.append(f"data reference targets discovered function start {expected_addr:#x}")
                    else:
                        classification = MISSING_DATA
                        blockers.append(f"no [[data]] entry at {expected_addr:#x}")
            elif db_entry.get("link_name") == sym:
                classification = AMBIGUOUS
                blockers.append(f"canonical link_name already equals {sym}")
            else:
                type_ok = True
                if not all_callers_corroborated:
                    type_ok = False
                    blockers.append(f"target {expected_addr:#x} not independently corroborated in all affected callers")
                if not db_entry.get("type"):
                    type_ok = False
                    blockers.append(f"DB entry {db_entry['name']} has no type")
                for af in affected_list:
                    decls = af.get("decls") or []
                    if not decls:
                        type_ok = False
                        blockers.append(f"{af['ref']}: no top-level declaration of {ident} found")
                        continue
                    for d in decls:
                        if not data_decls_compatible(d["text"], ident, db_entry.get("type")):
                            type_ok = False
                            blockers.append(f"{d['file']}:{d['line']}: type differs from DB type {db_entry.get('type')!r}")
                classification = MECHANICAL_DATA_RENAME if type_ok else (AMBIGUOUS if not all_callers_corroborated else ABI_MISMATCH)

        dependencies.append({
            "symbol": sym,
            "ident": ident,
            "kind": kind,
            "classification": classification,
            "mechanical": classification in (MECHANICAL_FUNC_RENAME, MECHANICAL_DATA_RENAME),
            "expected_address": expected_addr,
            "expected_address_hex": f"{expected_addr:#x}" if expected_addr is not None else None,
            "address_lead": addr_lead,
            "address_lead_hex": f"{addr_lead:#x}" if addr_lead is not None else None,
            "ambiguous": ambiguous,
            "conflict_addresses": [f"{a:#x}" for a in conflict_addrs],
            "relocation_kinds": [
                {"self_relative": sr, "loc": loc, "operand": op}
                for sr, loc, op in sorted(bucket["reloc_kinds"], key=lambda t: (bool(t[0]), t[1] or 0, str(t[2] or "")))
            ],
            "addends": addends_sorted,
            "evidence": ev_list,
            "db_entry": db_entry,
            "containing_owner": containing_owner,
            "canonical_header_decls": canon_hdr_decls,
            "affected_functions": affected_list,
            "blockers": blockers,
        })

    # Group dependencies by underlying target so N callers/fields share ONE research task
    grouped = {}
    for dep in dependencies:
        if dep["classification"] == CONTAINING_OWNER_FIELD and dep.get("containing_owner"):
            owner = dep["containing_owner"]
            gid = _slug_group_id("owner", f"{owner['addr']:x}")
            gkey = ("owner", owner["addr"])
        elif dep["expected_address"] is not None and not dep["ambiguous"]:
            tag = "func" if dep["kind"] == "function" else "data"
            gid = _slug_group_id(tag, f"{dep['expected_address']:x}")
            gkey = (tag, dep["expected_address"])
        else:
            gid = _slug_group_id("sym", dep["symbol"])
            gkey = ("sym", dep["symbol"])

        g = grouped.setdefault(gkey, {
            "group_id": gid,
            "kind": dep["kind"],
            "target_address": dep["containing_owner"]["addr"] if gkey[0] == "owner" else dep["expected_address"],
            "target_address_hex": (f"{dep['containing_owner']['addr']:#x}" if gkey[0] == "owner"
                                   else dep["expected_address_hex"]),
            "db_entry": dep["containing_owner"] if gkey[0] == "owner" else dep["db_entry"],
            "symbols": [],
            "dependencies": [],
            "_affected_by_addr": {},
        })
        g["symbols"].append(dep["symbol"])
        g["dependencies"].append(dep)
        for af in dep["affected_functions"]:
            prev = g["_affected_by_addr"].get(af["addr"])
            if prev is None:
                g["_affected_by_addr"][af["addr"]] = dict(af)
            else:
                prev["zero_score_blocked"] = prev["zero_score_blocked"] or af["zero_score_blocked"]

    groups = []
    for g in grouped.values():
        deps_g = g["dependencies"]
        affected = sorted(g.pop("_affected_by_addr").values(), key=lambda x: x["addr"])
        g["symbols"] = sorted(set(g["symbols"]))
        g["affected_functions"] = affected
        g["affected_refs"] = sorted({af["ref"] for af in affected if af.get("ref")})
        g["affected_modules"] = sorted({af["module"] for af in affected if af.get("module")})
        g["zero_score_blocked_count"] = sum(1 for af in affected if af.get("zero_score_blocked"))
        g["mechanical"] = all(d["mechanical"] for d in deps_g)
        # Group classification: highest-priority (lowest rank) if mechanical, else most specific non-mechanical
        if g["mechanical"]:
            g["classification"] = min((d["classification"] for d in deps_g), key=lambda c: CLASS_PRIORITY[c])
        else:
            non_mech = [d["classification"] for d in deps_g if not d["mechanical"]]
            g["classification"] = min(non_mech, key=lambda c: CLASS_PRIORITY[c])
        g["priority_key"] = (
            0 if g["mechanical"] else 1,
            -g["zero_score_blocked_count"],
            -len(affected),
            CLASS_PRIORITY.get(g["classification"], 99),
            g["group_id"],
        )
        groups.append(g)

    groups.sort(key=lambda x: x["priority_key"])
    for g in groups:
        g.pop("priority_key", None)

    counts = defaultdict(int)
    for d in dependencies:
        counts[d["classification"]] += 1

    return {
        "total_dependencies": len(dependencies),
        "total_groups": len(groups),
        "affected_functions_count": len({af["addr"] for d in dependencies for af in d["affected_functions"]}),
        "classification_counts": dict(sorted(counts.items())),
        "groups": groups,
        "dependencies": dependencies,
    }


# ---------------------------------------------------------------------------
# Syntax-aware deterministic C symbol rewriting
# ---------------------------------------------------------------------------

def _has_local_or_macro_collision(tokens, new_ident):
    """Conservative collision check: True if `new_ident` is defined as a macro, parameter,
    local variable (including typedef/comma declarators), typedef alias, enum constant,
    struct/union/enum tag, file-scope static, or non-extern definition."""
    sig = [(kind, val) for kind, val, _s, _e in tokens if kind not in ("WS", "COMMENT")]
    for kind, val in sig:
        if kind == "PREPROC" and re.search(rf"^\s*#\s*define\s+{re.escape(new_ident)}\b", val):
            return True

    # Walk significant tokens tracking brace depth, paren depth, statement head, and aggregate scopes.
    n = len(sig)
    depth = 0
    paren = 0
    stmt_start = 0
    scope_stack = []  # list[str]: "enum" | "struct" | "block"
    pending_agg = None
    _STMT_KW = {
        "return", "if", "else", "for", "while", "do", "switch", "case", "default",
        "goto", "break", "continue", "sizeof",
    }

    for i, (kind, val) in enumerate(sig):
        if kind == "PREPROC":
            continue
        if kind == "IDENT" and val in ("struct", "union", "enum"):
            pending_agg = val
        elif kind == "OTHER" and val == "(":
            paren += 1
        elif kind == "OTHER" and val == ")":
            paren = max(0, paren - 1)
        elif kind == "OTHER" and val == "{":
            scope_stack.append("enum" if pending_agg == "enum" else ("struct" if pending_agg else "block"))
            pending_agg = None
            depth += 1
            stmt_start = i + 1
            continue
        elif kind == "OTHER" and val == "}":
            if scope_stack:
                scope_stack.pop()
            depth = max(0, depth - 1)
            pending_agg = None
            stmt_start = i + 1
            continue
        elif kind == "OTHER" and val == ";" and paren == 0:
            pending_agg = None
            stmt_start = i + 1
            continue

        if kind != "IDENT" or val != new_ident:
            continue

        prev = sig[i - 1] if i > 0 else (None, None)
        if prev[1] in (".", "->"):
            continue
        # Enumerators live in the enclosing namespace -> collision!
        if scope_stack and scope_stack[-1] == "enum":
            return True
        # Struct/union field names are in their own member namespace, NOT a collision
        if "struct" in scope_stack:
            continue
        # Tag name after struct/union/enum -> collision
        if prev[0] == "IDENT" and prev[1] in ("struct", "union", "enum"):
            return True

        # Slice the current statement (up to next `;` or `{` at matching depth)
        stmt_end = i
        while stmt_end < n and not (sig[stmt_end][0] == "OTHER" and sig[stmt_end][1] in (";", "{", "}")):
            stmt_end += 1
        stmt = sig[stmt_start:stmt_end]
        stmt_first = stmt[0][1] if stmt else ""
        stmt_term = sig[stmt_end][1] if stmt_end < n else ""

        if depth == 0:
            # Top-level typedef, static, initialized/defined object, or function definition/parameter
            if stmt_first in ("typedef", "static"):
                return True
            if stmt_term == "{":
                # Function definition header (either the function name itself OR a parameter name!)
                return True
            if any(t[0] == "OTHER" and t[1] == "=" for t in stmt):
                return True
            # Non-extern top-level object definition (not a prototype with `(`)
            if stmt_first != "extern" and not any(t[0] == "OTHER" and t[1] == "(" for t in stmt):
                return True
        else:
            # Inside a function body: any local variable declaration (primitive, typedef, pointer,
            # or comma-separated declarator) shadows the global.
            if stmt_first == "typedef" or stmt_first == "static":
                return True
            # Check if token immediately before `new_ident` (or before leading `*`s) is a type/comma
            j = i - 1
            while j >= stmt_start and sig[j][0] == "OTHER" and sig[j][1] == "*":
                j -= 1
            if j >= stmt_start:
                tk, tv = sig[j]
                if tk == "IDENT" and tv not in _STMT_KW:
                    # `Type new_ident` or `Type *new_ident` (e.g. `Rect Real;` or `int Real;`)
                    return True
                if tk == "OTHER" and tv == "," and paren == 0:
                    # `Type a, new_ident;` — check that statement looks like a declaration, not a call/expr
                    if (stmt and stmt[0][0] == "IDENT" and stmt[0][1] not in _STMT_KW
                            and len(stmt) >= 2 and stmt[1][0] in ("IDENT", "OTHER")
                            and stmt[1][1] not in ("(", "=", "+=", "-=", "*=", "/=", "|=", "&=", "^=", "++", "--", "[", ".", "->")):
                        return True
    return False


def _find_extern_decl_spans(tokens, ident, text=""):
    """Find top-level (brace-depth 0) single-declarator `extern`/prototype declaration
    statement spans `(start, end)` that specifically declare `ident`."""
    spans = []
    depth = 0
    stmt_start = None
    stmt_toks = []
    for tok in tokens:
        kind, val, s, e = tok
        if kind in ("WS", "COMMENT"):
            continue
        if kind == "PREPROC":
            if depth == 0:
                stmt_start = None
                stmt_toks = []
            continue
        if kind == "OTHER" and val == "{":
            depth += 1
            stmt_start = None
            stmt_toks = []
            continue
        if kind == "OTHER" and val == "}":
            depth = max(0, depth - 1)
            stmt_start = None
            stmt_toks = []
            continue
        if depth > 0:
            continue
        if stmt_start is None:
            stmt_start = s
        stmt_toks.append(tok)
        if kind == "OTHER" and val == ";":
            first_word = stmt_toks[0][1] if stmt_toks else ""
            has_ident = any(t[0] == "IDENT" and t[1] == ident for t in stmt_toks)
            has_eq = any(t[0] == "OTHER" and t[1] == "=" for t in stmt_toks)
            # Check for top-level `,` outside parameter parens (multi-declarator like `extern short a, b;`)
            pdepth = 0
            has_top_comma = False
            for tk, tv, _ts, _te in stmt_toks:
                if tk == "OTHER":
                    if tv == "(":
                        pdepth += 1
                    elif tv == ")":
                        pdepth = max(0, pdepth - 1)
                    elif tv == "," and pdepth == 0:
                        has_top_comma = True
            if has_ident and not has_eq and not has_top_comma and first_word != "typedef":
                stmt_str = text[stmt_start:e] if text else " ".join(t[1] for t in stmt_toks)
                fdecl = parse_c_func_decl(stmt_str)
                ddecl = parse_c_data_decl(stmt_str, ident) if first_word == "extern" else None
                if (fdecl and fdecl["name"] == ident) or (ddecl is not None):
                    spans.append((stmt_start, e))
            stmt_start = None
            stmt_toks = []
    return spans


def rewrite_c_symbol(text, old_ident, new_ident, *, drop_redundant_decl=False):
    """Syntax-aware rename of `old_ident` -> `new_ident` in C source text.

    - Preserves comments (including codegen-compiler/codegen-flags headers), string/char
      literals, preprocessor directives, and struct member accesses (`.old`, `->old`).
    - Rejects transformations if `new_ident` collides with a local/macro/typedef or if
      `text` contains trigraphs / unterminated tokens.
    - When `drop_redundant_decl=True`, removes top-level `extern`/prototype declaration
      statements of `old_ident` (used when an already-included header declares `new_ident`).

    Returns `(new_text, changed_count)`. Raises `ValueError` if unsafe.
    """
    if not old_ident or not new_ident or old_ident == new_ident:
        raise ValueError("invalid identifiers for rewrite")
    if not symbols.IDENT.match(old_ident) or not symbols.IDENT.match(new_ident):
        raise ValueError(f"non-identifier name: {old_ident!r} -> {new_ident!r}")
    tokens = tokenize_c(text)
    if _has_local_or_macro_collision(tokens, new_ident):
        raise ValueError(f"identifier collision with existing local/macro/typedef {new_ident!r}")

    edits = []  # (start, end, replacement)
    drop_ranges = []
    if drop_redundant_decl:
        for s, e in _find_extern_decl_spans(tokens, old_ident, text=text):
            # Include leading indentation and trailing newline if line has no other code
            ls = text.rfind("\n", 0, s) + 1
            le = text.find("\n", e)
            le = len(text) if le == -1 else le + 1
            before = text[ls:s].strip()
            after = text[e:le].strip()
            if not before and (not after or after.startswith("//") or (after.startswith("/*") and after.endswith("*/"))):
                # Never drop a line containing codegen metadata comments
                if not _HEADER_META_RE.search(text[ls:le]):
                    drop_ranges.append((ls, le))
                    edits.append((ls, le, ""))
                    continue
            drop_ranges.append((s, e))
            edits.append((s, e, ""))

    def _in_dropped(pos):
        return any(a <= pos < b for a, b in drop_ranges)

    renamed = 0
    prev_sig = None
    # Track brace scopes so identifiers inside `struct`/`union`/`enum` bodies are never rewritten.
    scope_stack = []  # list[bool]: True if this `{ ... }` is a struct/union/enum member body
    pending_aggregate = False
    for kind, val, s, e in tokens:
        if kind in ("WS", "COMMENT", "PREPROC"):
            continue
        if kind == "IDENT" and val in ("struct", "union", "enum"):
            pending_aggregate = True
        elif kind == "OTHER" and val == "{":
            scope_stack.append(pending_aggregate)
            pending_aggregate = False
        elif kind == "OTHER" and val == "}":
            if scope_stack:
                scope_stack.pop()
            pending_aggregate = False
        elif kind == "OTHER" and val in (";", ",", ")", "="):
            pending_aggregate = False

        in_aggregate_body = any(scope_stack)
        if kind == "IDENT" and val == old_ident and not _in_dropped(s) and not in_aggregate_body:
            if prev_sig is None or prev_sig[1] not in (".", "->"):
                edits.append((s, e, new_ident))
                renamed += 1
        prev_sig = (kind, val)

    if not edits:
        return text, 0

    edits.sort(key=lambda x: x[0])
    out = []
    cur = 0
    for s, e, rep in edits:
        if s < cur:
            raise ValueError("overlapping edits in rewrite_c_symbol")
        out.append(text[cur:s])
        out.append(rep)
        cur = e
    out.append(text[cur:])
    new_text = "".join(out)
    # Invariant: codegen metadata lines must be completely untouched
    hdr_old = [l for l in text.splitlines() if _HEADER_META_RE.search(l)]
    hdr_new = [l for l in new_text.splitlines() if _HEADER_META_RE.search(l)]
    if hdr_old != hdr_new:
        raise ValueError("rewrite would alter codegen metadata headers")
    return new_text, renamed + len(drop_ranges)


def can_apply_mechanical_group(group, repo_root=None):
    """Check whether a dependency group is strictly eligible for mechanical rewriting.

    Returns `(ok, plan_list, reason)` where `plan_list` is a list of
    `{"file": rel, "old_ident": str, "new_ident": str, "drop_redundant_decl": bool}`.
    """
    root = repo_root or path()
    if not group.get("mechanical"):
        return False, [], "group is not classified as mechanical"
    plans = []
    seen_pairs = set()
    for dep in group.get("dependencies", []):
        db = dep.get("db_entry")
        if not db or not db.get("name"):
            return False, [], f"{dep['symbol']}: missing DB entry"
        old_ident = dep["ident"]
        new_ident = db["name"]
        if not old_ident or not new_ident or old_ident == new_ident:
            return False, [], f"{dep['symbol']}: invalid rename {old_ident!r} -> {new_ident!r}"
        for af in dep.get("affected_functions", []):
            ref = af.get("ref")
            if not ref:
                return False, [], f"{af.get('addr_hex')}: missing ref file"
            # Determine which files declare old_ident: prefer editing ref file;
            # if old_ident is ONLY declared in a header, allow editing the header ONLY if
            # it is not war.h and not a shared header outside this area.
            decls = af.get("decls") or []
            hdr_decls_new = find_declarations_in_unit(ref, new_ident, repo_root=root)
            new_in_included_header = any(not d["in_ref"] for d in hdr_decls_new)
            decl_files = {d["file"] for d in decls}
            for df in sorted(decl_files):
                if df != ref:
                    if df == "src/include/war.h":
                        return False, [], f"{dep['symbol']}: declared in protected war.h"
                    # Refuse mechanical edits to a header included by any C file outside this group
                    affected_ref_set = set(group.get("affected_refs") or ())
                    src_root = os.path.join(root, "src")
                    if os.path.isdir(src_root):
                        for dp, _ds, fns in os.walk(src_root):
                            for fn in fns:
                                if not fn.endswith(".c"):
                                    continue
                                crel = os.path.relpath(os.path.join(dp, fn), root).replace("\\", "/")
                                if crel in affected_ref_set:
                                    continue
                                if df in _resolve_local_includes(crel, root):
                                    return False, [], f"{dep['symbol']}: declared in shared header {df} (used by {crel})"
                    # Check if header already declares new_ident too
                    key = (df, old_ident, new_ident)
                    if key not in seen_pairs:
                        seen_pairs.add(key)
                        plans.append({
                            "file": df,
                            "old_ident": old_ident,
                            "new_ident": new_ident,
                            "drop_redundant_decl": any(d["file"] == df for d in hdr_decls_new),
                        })
            key = (ref, old_ident, new_ident)
            if key not in seen_pairs:
                seen_pairs.add(key)
                plans.append({
                    "file": ref,
                    "old_ident": old_ident,
                    "new_ident": new_ident,
                    "drop_redundant_decl": new_in_included_header,
                })
    if not plans:
        return False, [], "empty mechanical plan"
    # Dry-run tokenize/rewrite validation before touching disk
    by_file = defaultdict(list)
    for step in plans:
        by_file[step["file"]].append(step)
    for rel, steps in by_file.items():
        full = os.path.join(root, rel)
        if not os.path.isfile(full):
            return False, [], f"file missing: {rel}"
        try:
            txt = open(full, encoding="latin-1").read()
            for st in steps:
                txt, _n = rewrite_c_symbol(
                    txt, st["old_ident"], st["new_ident"],
                    drop_redundant_decl=st["drop_redundant_decl"],
                )
        except (OSError, ValueError) as ex:
            return False, [], f"{rel}: {ex}"
    return True, plans, ""
