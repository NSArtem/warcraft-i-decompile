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
import glob
import os
import re
import sys
import tomllib

from . import path

CONFIDENCE = ("verified", "high", "medium", "low", "speculative")
CONVS = ("watcall", "cdecl", "asm", "pascal")
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
        return {"watcall": n + "_", "cdecl": "_" + n, "asm": n, "pascal": n.upper()}[conv]
    return "_" + n


def load(root=None, strict=True):
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
                ln = link_name(kind, e) if "name" in e else ""
                if ln.lower() in NASM_RESERVED:
                    errors.append(f"{where}: link name {ln!r} is reserved")
                e["link_name"] = ln
                if e["addr"] in table:
                    o = table[e["addr"]]
                    errors.append(f"{where}: duplicate address (also {o['_file']} as {o['name']})")
                    continue
                table[e["addr"]] = e
    errors += check_modules(funcs)
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
