"""Use unchanged production placement/link code with in-memory candidate wiring.

All compiled objects and linked images stay under build/e7. No TOML or C writes.
"""
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack, redirect_stdout
import copy
import io
from pathlib import Path
import shutil
import sys
from unittest.mock import patch

from wc1 import build, match, omf, path, symbols
from .common import SCRATCH, compile_short, compiler_root, digest


def compiler_adapter(functions, configs, scratch):
    from .calibrate import object_path
    native = compile_short
    by_source = {r["source"]: r for r in functions}

    def compile_c(src, flags, out, *args, **kwargs):
        source = str(Path(src).relative_to(Path(path())))
        r = by_source.get(source)
        # A header-proven OW2 object must not be silently replaced by 10.0a.
        if r and r["declared_compiler"] == "10.0a" and flags is None and not kwargs.get("cc"):
            obj = object_path(source, r["declared_config"], scratch)
            if obj.exists():
                Path(out).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(obj, out)
                return omf.parse_object(str(out))
        return native(src, flags, out, *args, **kwargs)
    return compile_c


def scratch_path(scratch):
    def isolated(*parts):
        return str(Path(scratch).joinpath(*parts[1:])) if parts and parts[0] == "build" else path(*parts)
    return isolated


def placement_checks(p, funcs, by_link, functions, units, configs, scratch):
    from .calibrate import object_path
    by_source = {}
    for r in functions:
        by_source.setdefault(r["source"], []).append(r)
    checks = 0
    with ExitStack() as stack:
        stack.enter_context(patch.object(build, "path", scratch_path(scratch)))
        stack.enter_context(patch.object(build, "ThreadPoolExecutor", lambda *a, **k: ThreadPoolExecutor(max_workers=6)))
        stack.enter_context(patch.object(match, "compile_c", compiler_adapter(functions, configs, scratch)))
        stack.enter_context(patch.object(match, "unique_obj", lambda src, *sub:
            str(Path(scratch) / "placecheck" / digest([src, sub])[:20] / "check.obj")))
        for u in units:
            rows = by_source[u["source"]]
            if not any(r["tier"] == "T4" for r in rows):
                continue
            for cid, att in u["attempts"].items():
                if not any(r["tier"] == "T4" and r["cells"][cid]["state"] == "matched" for r in rows):
                    continue
                obj = object_path(u["source"], cid, scratch)
                entries = [by_link[n] for n in att["object_functions"]]
                ok, reason = build.check_t3_buildable(p, funcs, u["source"], str(obj), entries)
                att["placement_check"] = dict(ok=ok, reason=reason)
                att["buildable"] = att["whole_object_match"] and ok
                att["buildable_reason"] = reason if att["whole_object_match"] else "not all bodies/region match E0"
                checks += 1
    print(f"E7 placement: {checks} actual compiled objects checked", flush=True)


def link_once(label, selections, matrix, scratch=SCRATCH):
    from .calibrate import object_path
    folder = Path(scratch) / "links" / label
    folder.mkdir(parents=True, exist_ok=True)
    funcs, datas, layouts = symbols.load()
    modified = copy.deepcopy(funcs)
    units = {u["source"]: u for u in matrix["units"]}
    by_link = {e["link_name"]: e for e in modified.values()}
    for source, cid in selections.items():
        att = units[source]["attempts"][cid]
        assert att["buildable"] and att["whole_object_match"] and att["region"]["verdict"] == "MATCH"
        for name in att["object_functions"]:
            e = by_link[name]
            e.pop("ref", None)
            e["src"] = source
    base_compile = compiler_adapter(matrix["functions"], matrix["configurations"], scratch)

    def compile_for_link(src, flags, out, *args, **kwargs):
        source = str(Path(src).relative_to(Path(path())))
        if source in selections:
            obj = object_path(source, selections[source], scratch)
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(obj, out)
            return omf.parse_object(str(out))
        return base_compile(src, flags, out, *args, **kwargs)

    stdout = io.StringIO()
    with ExitStack() as stack:
        stack.enter_context(patch.object(build, "path", scratch_path(folder)))
        stack.enter_context(patch.object(build, "ThreadPoolExecutor", lambda *a, **k: ThreadPoolExecutor(max_workers=6)))
        stack.enter_context(patch.object(symbols, "load", return_value=(modified, datas, layouts)))
        stack.enter_context(patch.object(match, "compile_c", compile_for_link))
        stack.enter_context(patch.object(sys, "argv", ["e7-build", "--out", str(folder / "war.exe")]))
        stack.enter_context(redirect_stdout(stdout))
        rc = build.main()
    log = stdout.getvalue()
    (folder / "build.log").write_text(log)
    identical = rc == 0 and log.rstrip().splitlines()[-1] == "IDENTICAL (loaded image, entry, stack, fixups)"
    if not identical:
        raise RuntimeError(f"E7 Build A failed ({label}):\n{log}")
    print(f"E7 Build A {label}: IDENTICAL ({len(selections)} additional C objects)", flush=True)
    return dict(label=label, returncode=rc, compare="IDENTICAL", selections=selections,
                log=log.replace(str(Path(path())), "<repo>").replace(str(compiler_root()), "<repo>"))


def representative_links(matrix, scratch=SCRATCH):
    units = {u["source"]: u for u in matrix["units"]}
    new = [r for r in matrix["functions"] if r["tier"] == "T4"]
    reps = {}
    for r in new:
        if r["cells"]["c06"]["state"] == "matched" and units[r["source"]]["attempts"]["c06"].get("buildable"):
            reps.setdefault(r["source"], r)
    if len(reps) < 3:
        raise RuntimeError(f"Only {len(reps)} -5r buildable objects; investigate instead of weakening link controls")
    links = [link_once(f"5r-{r['addr']:x}", {r["source"]: "c06"}, matrix, scratch)
             for r in list(reps.values())[:3]]
    # Prove the ENTIRE placement-approved population together, beyond the three
    # requested individual controls. Select one successful config per C file.
    all_selections = {}
    for r in new:
        for cid in r["compatible_configs"]:
            if units[r["source"]]["attempts"][cid].get("buildable"):
                all_selections.setdefault(r["source"], cid)
                break
    links.append(link_once("all-new-buildable", all_selections, matrix, scratch))
    return links
