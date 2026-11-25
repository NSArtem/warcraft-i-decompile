"""Exhaustive read-only calibration, six independent compile/matcher processes.

Each TU is compiled under EVERY applicable configuration, even after a match.
Only byte/relocation-identical runtime objects reuse matcher work within a TU.
No source extraction, source editing, LLM, or production search driver is used.
"""
from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import Counter
import copy
import multiprocessing
from pathlib import Path
import re
import subprocess

from wc1 import analysis, build, match, oldcc, path, progress, symbols
from experiments.build_codegen.e0 import matcher_proto as e0
from .common import (BASELINE, RESULTS, SCRATCH, STATES, cell_state, compile_short, compiler_root,
                     configurations, digest, dump, file_hash, finding_summary, flag_key, short_flags)

CTX = None


def discover(p, funcs):
    rows = progress.classify([f["start"] for f in p.functions], funcs, progress.load_modules())
    selected = []
    for r in rows:
        if r["scope"] != "in" or r["c"] not in ("T3", "T4"):
            continue
        e = funcs[r["addr"]]
        source = e.get("src") or e["ref"]
        selected.append(dict(addr=r["addr"], name=e["name"], link_name=e["link_name"],
                             module=r["module"], tier=r["c"], source=source,
                             source_sha256=file_hash(path(source)),
                             declared_compiler=match.file_cc(path(source)),
                             declared_flags=short_flags(match.file_cflags(path(source)))))
    return selected


def dependencies(mod, by_link):
    relocations = []
    for seg in mod.segments:
        if seg.cls in ("DEBSYM", "DEBTYP"):
            continue
        for f in seg.fixups:
            if f.target_kind == "ext":
                relocations.append(dict(segment=seg.name, offset=f.offset, symbol=f.target,
                                        resolved=f.target in by_link or f.target in mod.publics or f.target in mod.statics))
    return dict(external_relocations=relocations,
                unresolved_relocations=sum(not r["resolved"] for r in relocations),
                unresolved_symbols=sorted({r["symbol"] for r in relocations if not r["resolved"]}))


def runtime_key(mod):
    def runtime_symbol(item):
        return mod.segments[item[1][0]-1].cls not in ("DEBSYM", "DEBTYP")
    # Preserve segment INDEX and duplicate names: OMF references are indexed,
    # and a name-keyed dictionary could conceal a changed second segment.
    segments = [dict(index=i,name=s.name,cls=s.cls,length=s.length,
                     data=bytes(s.data).hex(),fixups=[vars(f) for f in s.fixups])
                for i,s in enumerate(mod.segments,1) if s.cls not in ("DEBSYM","DEBTYP")]
    return digest(dict(segments=segments,
                       publics=dict(filter(runtime_symbol, mod.publics.items())),
                       statics=dict(filter(runtime_symbol, mod.statics.items())),
                       externs=mod.externs, comdefs=mod.comdefs))


def object_path(source, config, scratch=SCRATCH):
    return Path(scratch) / "calibration" / digest(source)[:16] / (config + ".obj")


def compile_one(source, flags, obj):
    # Timeout is a fatal infrastructure error, not a compile_error cell.
    # compile_short keeps every compiler-facing path bounded, so a checkout
    # root deeper than Watcom 10.0a's fixed path buffers still compiles.
    return compile_short(path(source), match.BASE_CFLAGS + " " + flags, obj,
                         cc="10.0a", includes=(str(Path(path(source)).parent),),
                         timeout=30, quiet=True)


def evaluate(mod, rows):
    p, funcs, by_link, index, configs, scratch = CTX
    # The unmodified E0 prototype is the ONLY source of exact match verdicts.
    result = e0.match_module(p, mod, by_link, index)
    cells = {}
    for row in rows:
        fr = result["functions"].get(row["link_name"])
        if fr is None:
            # e.g. path_reference.c defines _a/_b/_c alternatives, but the DB
            # requests PathPeekStep_. Do not invent an original-public mapping
            # or let diff_function silently choose its first public as the DB
            # function. Keep ALL alternative scores as diagnostic evidence.
            ti,_=mod.seg('_TEXT')
            alternatives={n:match.diff_function(p,mod,by_link,name=n,orig_addr=row['addr'],context=0)['score']
                          for n,(si,_) in mod.publics.items() if si==ti}
            cells[row['addr']]=dict(state='matcher_unsupported',function=None,score=None,
                reason=f"E0 returned no FunctionMatch for missing requested public {row['link_name']}",
                alternative_public_scores=alternatives,first_diff=None,score_unresolved=[],score_counts=None,
                legacy_function_match=False)
            continue
        dd = match.diff_function(p, mod, by_link, name=row["link_name"], orig_addr=row["addr"], context=0)
        cells[row["addr"]] = dict(state=cell_state(fr["verdict"]), function=finding_summary(fr),
                                  score=list(dd["score"]), first_diff=dd["first_diff"],
                                  score_unresolved=dd["unresolved"], score_counts=dd["counts"],
                                  legacy_function_match=dd["matched"])
    all_fn = bool(result["functions"]) and all(f["verdict"] == "MATCH" for f in result["functions"].values())
    # Whole-object is deliberately strong: every body AND the entire E0 region,
    # including leading code/data and local pointer fields, must be proven.
    whole = all_fn and result["region"]["verdict"] == "MATCH"
    return cells, dict(region=finding_summary(result["region"]), whole_object_match=whole,
                       all_function_bodies_match=all_fn,
                       object_functions={n: f["verdict"] for n, f in result["functions"].items()}), result


def audit_unit(item):
    source, rows = item
    p, funcs, by_link, index, configs, scratch = CTX
    declared = next(c for c in configs if flag_key(c["flags"]) == flag_key(rows[0]["declared_flags"]))
    baseline_obj = object_path(source, declared["id"], scratch)
    try:
        baseline = compile_one(source, declared["flags"], baseline_obj)
    except match.CompileTimeout:
        raise
    except SystemExit as ex:
        # A baseline compile error prevents dependency classification; still
        # sweep T3, but leave T4 explicitly untested, with the failed baseline.
        baseline, baseline_error = None, str(ex)
    else:
        baseline_error = None
    deps = dependencies(baseline, by_link) if baseline else None
    clean = deps is not None and deps["unresolved_relocations"] == 0
    sweep = any(r["tier"] == "T3" for r in rows) or clean
    cells = {r["addr"]: {} for r in rows}
    attempts, memo = {}, {}
    for cfg in configs:
        cid, flags = cfg["id"], cfg["flags"]
        if not sweep and cid != declared["id"]:
            for r in rows:
                cells[r["addr"]][cid] = dict(state="untested", reason="T4 TU is not dependency-clean on declared 10.0a baseline")
            attempts[cid] = dict(state="untested")
            continue
        obj = object_path(source, cid, scratch)
        try:
            if cid == declared["id"]:
                if baseline is None:
                    raise SystemExit(baseline_error)
                mod = baseline
            else:
                mod = compile_one(source, flags, obj)
        except match.CompileTimeout:
            raise
        except SystemExit as ex:
            message = str(ex).replace(str(Path(path()).resolve()), "<repo>")
            # Compiler diagnostics name the short mirror, not the checkout.
            message = message.replace(str(compiler_root()), "<repo>").replace(
                oldcc.win_path(compiler_root()), "<repo>")
            message = re.sub(r", [0-9.]+s\):", ", <elapsed>):", message)
            for r in rows:
                cells[r["addr"]][cid] = dict(state="compile_error", reason=message)
            attempts[cid] = dict(state="compile_error", reason=message)
            continue
        signature = runtime_key(mod)
        if signature in memo:
            source_cid, fn_cells, att = memo[signature]
            fn_cells, att = copy.deepcopy(fn_cells), copy.deepcopy(att)
            att["evidence_reused_from"] = source_cid
        else:
            fn_cells, att, raw = evaluate(mod, rows)
            # Full E0 findings and normalized obligations are scratch evidence;
            # committed rows retain counts, code histograms and SHA-256, not a
            # silently truncated diagnostic array. All S(f) cells are retained.
            dump(obj.with_suffix(".e0.json"), raw)
            att["buildable"], att["buildable_reason"] = False, "whole object does not match E0"
            memo[signature] = (cid, copy.deepcopy(fn_cells), copy.deepcopy(att))
        # For identical runtime output the placement verdict is identical. The
        # compiled, unpatched object for EACH config remains available for links.
        att.update(state="evaluated", runtime_sha256=signature, dependencies=dependencies(mod, by_link))
        attempts[cid] = att
        for r in rows:
            cells[r["addr"]][cid] = fn_cells[r["addr"]]
    completed = []
    for r in rows:
        rr = dict(r, dependency_clean=clean, cells=cells[r["addr"]], declared_config=declared["id"])
        rr["compatible_configs"] = [c["id"] for c in configs if rr["cells"][c["id"]]["state"] == "matched"]
        completed.append(rr)
    return dict(source=source, declared_config=declared["id"], dependency_clean=clean,
                baseline_dependencies=deps, baseline_error=baseline_error, attempts=attempts), completed


def calibrate(capability, jobs=6, output=RESULTS, scratch=SCRATCH):
    global CTX
    if jobs < 1:
        raise ValueError("jobs must be positive")
    p = analysis.run()
    funcs, datas, _ = symbols.load()
    by_link = {e["link_name"]: e for t in (funcs, datas) for e in t.values()}
    rows = discover(p, funcs)
    configs = configurations(r["declared_flags"] for r in rows)
    supported = {r["flag"] for r in capability["flags"] if r["supported"]}
    missing = {f for c in configs for f in c["flags"].split()} - supported
    if missing:
        raise RuntimeError(f"Grid uses options not capability-verified: {sorted(missing)}")
    CTX = p, funcs, by_link, e0.OriginalIndex(p), configs, Path(scratch)
    grouped = {}
    for r in rows:
        grouped.setdefault(r["source"], []).append(r)
    # Redirect production checker's generated caches into the E7 scratch tree.
    # This changes no implementation or verdict; only its output paths.
    original_build_path = build.path
    def isolated_path(*parts):
        return str(Path(scratch).joinpath(*parts[1:])) if parts and parts[0] == "build" else original_build_path(*parts)
    build.path = isolated_path
    units, functions = [], []
    try:
        oldcc.ensure_prefix()
        # fork inherits the immutable Program and E0 index. Processes, not
        # threads, isolate Capstone's mutable disassembler and matcher globals.
        with ProcessPoolExecutor(max_workers=jobs, mp_context=multiprocessing.get_context("fork")) as pool:
            futures = [pool.submit(audit_unit, item) for item in sorted(grouped.items())]
            for n, fut in enumerate(as_completed(futures), 1):
                try:
                    unit, fs = fut.result()
                except BaseException as exc:
                    print(f"E7 worker failure: {type(exc).__name__}: {exc}",flush=True)
                    for pending in futures:
                        pending.cancel()
                    raise
                units.append(unit)
                functions.extend(fs)
                if n % 50 == 0 or n == len(grouped):
                    print(f"E7 calibration: {n}/{len(grouped)} TUs, {len(functions)} functions", flush=True)
    finally:
        build.path = original_build_path
    functions.sort(key=lambda r: r["addr"])
    units.sort(key=lambda r: r["source"])
    from .link_check import placement_checks
    placement_checks(p, funcs, by_link, functions, units, configs, scratch)
    native_controls=[]
    for r in functions:
        if r['tier']=='T3' and r['declared_compiler']!='10.0a':
            obj=Path(scratch)/'native-controls'/(digest(r['source'])[:16]+'.obj')
            obj.parent.mkdir(parents=True,exist_ok=True)
            mod=compile_short(path(r['source']),None,obj,cc=r['declared_compiler'],timeout=30,quiet=True)
            fc,ac,raw=evaluate(mod,[r])
            native_controls.append(dict(addr=r['addr'],source=r['source'],compiler=r['declared_compiler'],
                flags=r['declared_flags'],cell=fc[r['addr']],object=ac,
                scope='Native declared-compiler control, outside S_10.0a(f) and the 10.0a grid'))
    payload = dict(schema=1, experiment="E7", baseline=BASELINE, configurations=configs,
                   native_compiler_controls=native_controls,
                   functions=functions, units=units, states=list(STATES),
                   provenance=dict(fresh_compiles=True, jobs=jobs, compiler_timeout_seconds=30,
                                   capability_sha256=digest(capability),
                                   original_exe_sha256=file_hash(path("original/install/war.exe")),
                                   e0_matcher_sha256=file_hash(e0.__file__),
                                   production_diff=subprocess.check_output(["git", "diff", BASELINE, "--", "tools/", "src/", "analysis/", "tests/", "asm/", "Makefile", "flake.nix", "AGENTS.md"], text=True)),
                   explored_space=dict(policy="Every core and distinct declared configuration for all T3 and every dependency-clean T4 TU; no first-match stopping.",
                       baseline="Declared source flags under 10.0a; dependency-clean means zero unresolved external relocations in all runtime segments.",
                       untested_combinations=dict(state="untested", axes="All combinations outside the explicitly enumerated configurations, including interactions between secondary axes; no Cartesian completeness claimed."),
                       whole_object_definition="Every E0 FunctionMatch plus E0 RegionMatch, including local data pointer fields.",
                       matcher_reuse="Only identical runtime segments, fixups, symbols, externals, communal definitions within the same TU; no compile reuse across runs."))
    dump(Path(output) / "calibration_matrix.json", payload,compact=True)
    return payload
