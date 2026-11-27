"""Read-only M2 backlog inventory, blocker classification, and dependency-group analyzer.

Generates deterministic, reconciled reports for every in-scope function that is
not yet DONE according to `wc1.progress`, using the live discovery, symbol,
buildability, and wave-eligibility logic in `wc1.*`.

Never modifies `src/`, `analysis/`, `tests/`, or `build/` caches.

Usage:
    nix develop -c python3 -m wc1.m2_inventory --summary
    nix develop -c python3 -m wc1.m2_inventory --out-dir docs/research/m2-completion
"""
import argparse
import bisect
import collections
import csv
import json
import os
import re
import subprocess
import sys

from capstone import x86

from . import analysis, batch_driver, codegen_survey, emit, overnight, path, progress, symbols, t3_audit, wave4, wave4a

# Map module names to high-level game/engine subsystem labels for reporting.
SUBSYSTEM_MAP = {
    "BULLET.C": "combat_projectiles",
    "INIT.C": "startup_init",
    "PACKET.C": "multiplayer_net",
    "PLACEBOX.C": "ui_placement",
    "PLAYFLIC.C": "cinematics_flic",
    "SCORE.C": "score_endgame",
    "SND.C": "audio_sfx",
    "STATUS.C": "ui_status_panel",
    "mod_110a0": "ai_combat_orders",
    "mod_11530": "ai_production",
    "mod_12c70": "multiplayer_net",
    "mod_13270": "map_unit_footprint",
    "mod_13e60": "demo_main_loop",
    "mod_13f60": "menus_and_orders",
    "mod_19470": "scenario_and_rng",
    "mod_19b80": "game_input_hotkeys",
    "mod_1af20": "viewport_map_input",
    "mod_1b800": "audio_unit_alerts",
    "mod_1bf80": "ui_wait_modal",
    "mod_1c020": "briefing_credits_gfx",
    "mod_1de60": "unit_spawning_map",
    "mod_1e380": "scenario_loader",
    "mod_20c30": "unit_commands_ui",
    "mod_25820": "map_scroll_viewport",
    "mod_25ba0": "unit_selection",
    "mod_2b2f0": "target_mode_ui",
    "mod_2b400": "game_state_misc",
    "mod_2c4e0": "pathfinding",
    "mod_2ced0": "unit_lifecycle_tick",
    "mod_2efd0": "endgame_and_selection",
    "mod_3d040": "blizzard_gfx_lib",
    "mod_3d190": "blizzard_gfx_lib",
    "mod_3df40": "ail_mixer_misclassified",
}


def _git_head():
    try:
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=path(),
                           capture_output=True, text=True, check=True)
        return r.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def _codegen_style(p, f):
    ft = codegen_survey.feat(p, f)
    if ft["epi"] == "leave":
        return "LEAVE"
    if ft["frame"] and ft["sub"] is not None and ft["sub"][1] == "imm32" and ft["sub"][0] < 128:
        return "OD"
    if ft["frame"]:
        return "DBG"
    return "OPT"


def _matched_file_from_vb(vb):
    if not vb:
        return None
    m = re.search(r"(src/[^\s()]+?\.c)\b", str(vb))
    return m.group(1) if m else None


def _owner_func_fn(func_starts, by_addr):
    def owner_func(a):
        i = bisect.bisect_right(func_starts, a) - 1
        if i >= 0:
            s = func_starts[i]
            if s <= a < by_addr[s]["limit"]:
                return s
        return None
    return owner_func


# Narrative metadata for the named dependency groups (DG-08 groups are generic
# per-area groups synthesized in build_inventory).  Kept at module level so the
# text can be tested (tests/test_m2_inventory.py); the classification logic and
# the membership of every group are decided by build_inventory, not here.
GROUP_META = {
    "DG-01-immediate-zero-llm-wiring": {
        "priority": 1,
        "title": "Immediate Zero-LLM TOML Wiring (Already Verified C/Tests)",
        "shared_blocker": "No remaining members: WaitInputOrTimeout 0x1bf94 was wired (commit c9d8733) and IntroOpSyncSound 0x23170 was reclassified to DG-03 (commit e1a4178); retained for history only",
        "mechanism": "Deterministic TOML metadata wiring (0 LLM calls, 0 C changes); no current work",
        "estimated_t3_unlocks_beyond_m2": 0,
        "risk": "very_low",
    },
    "DG-02-build-pre-function-jump-tables": {
        "priority": 2,
        "title": "Pre-Function Switch Jump Tables in wc1.build.place",
        "shared_blocker": "wc1.build.place assumes first public sits at _TEXT + 0x0; Watcom 10.0a emits switch tables before function start (pub[1] > 0)",
        "mechanism": "Generalize build.place base = addr - pub[1] with leading-table byte verification (also unlocks 12 T4 switch functions including MainMenu/owner_5aa90)",
        "estimated_t3_unlocks_beyond_m2": 12,
        "risk": "low",
    },
    "DG-03-build-shared-epilogue-interior-jumps": {
        "priority": 3,
        "title": "Shared-Epilogue Neighbour Branches into Replaced T3 Functions",
        "shared_blocker": "Two variants: neighbour rel8/rel32 branches into a replaced function's shared epilogue (0x1e380, 0x2315c, 0x2e96c, 0x2efd0, 0x2f73c), and IntroOpSyncSound 0x23170, where cutting the function moves IntroOpPlaySound's shared epilogue loc_2316c into the previous asm piece so IntroOpWaitSound 0x231cc's rel8 branch to it becomes an 8-bit external relocation NASM cannot emit (local MATCH and check_t3_buildable true, but a full wc1.build fails)",
        "mechanism": "Emit verified cut-boundary local-label relative jumps (loc_cut_end - k / loc_cut_start + k) and cut-boundary relative branch expressions in wc1.emit/wc1.build; zero external relocs, byte-identical output verified by probe",
        "estimated_t3_unlocks_beyond_m2": 6,
        "risk": "low",
    },
    "DG-04-ref-c-divergences": {
        "priority": 4,
        "title": "Reference-C Behavioural Divergences (4 PLAYFLIC + EndScreen)",
        "shared_blocker": "Existing reference C files have genuine behavioural bugs caught by xfailed T4 difftests",
        "mechanism": "Targeted C bugfixes on 5 already-written functions + remove xfail + wire ref_verified_by",
        "estimated_t3_unlocks_beyond_m2": 0,
        "risk": "low",
    },
    "DG-05-name-only-and-codegen-promo": {
        "priority": 5,
        "title": "Locked codegen_promo.toml Staging: fn_150f0 (No C) & NetLinkHandshake (T4-Only)",
        "shared_blocker": "The 5 name-only functions and the 7 byte-matched samples were named and migrated on 2026-11-27; codegen_promo.toml now protects only fn_150f0 0x150f0 (no C), NetLinkHandshake 0x23edc (T4-only, analysed in SAVE.C but its record is not moved) and 4 shared data symbols (dat_50d7c, dat_51530, dat_516ae, dat_59230)",
        "mechanism": "Reconstruct fn_150f0 as C, then supervised atomic migration of fn_150f0/NetLinkHandshake/data records out of the locked TOML (the former mod_13f60.c sample under src/codegen/ was split and removed); deterministic repo-wide symbol renamer",
        "estimated_t3_unlocks_beyond_m2": 0,
        "risk": "low",
    },
    "DG-06-bullet-c-module": {
        "priority": 6,
        "title": "BULLET.C Projectile Subsystem (10 Clean Wave 3 + 8 mod_104b0 Stubs)",
        "shared_blocker": "BULLET.C was removed from overnight.DEFAULT_SKIP in 2456f0c, so the 10 clean functions are queued for Wave 3; the 8 callee placeholder stubs in mod_104b0.toml stay needs_human",
        "mechanism": "Run Wave 3 on the 10 clean functions + Wave 3R atomic stub-upgrade for the 8 mod_104b0 stubs",
        "estimated_t3_unlocks_beyond_m2": 0,
        "risk": "low",
    },
    "DG-07-low-conf-named-no-c": {
        "priority": 7,
        "title": "Existing Semantically-Named Low-Confidence Functions Without C",
        "shared_blocker": "confidence='low' fails progress.NAMED_CONFIDENCE so overnight routes them out of Wave 2 despite having semantic names & evidence",
        "mechanism": "Extend Wave 2 / Wave 3R to accept low-confidence named entries and upgrade confidence upon T3/T4 verification (no repo-wide rename needed)",
        "estimated_t3_unlocks_beyond_m2": 0,
        "risk": "low",
    },
    "DG-09-discovery-data-in-code": {
        "priority": 9,
        "title": "Data-in-Code Non-Functions (wander_direction_offsets, train_priority_odd)",
        "shared_blocker": "wc1.analysis decoded two read-only byte tables in _TEXT as functions despite datas_db ownership",
        "mechanism": "User-approved discovery fix in wc1.analysis vetoing verified code-segment data tables (removes 2 non-functions from scope)",
        "estimated_t3_unlocks_beyond_m2": 0,
        "risk": "governance_approval",
    },
    "DG-10-status-split-block": {
        "priority": 10,
        "title": "STATUS.C Split Mid-Function Blocks (0x28090 / 0x28093)",
        "shared_blocker": "wc1.analysis splits SelectionHasNoWorkers (0x28074..0x280a2) into 3 functions because 0x28090 is also referenced as a data callback",
        "mechanism": "User-approved discovery change merging shared return/loop-continuation blocks into 0x28074 (AGENTS.md Next Step 7)",
        "estimated_t3_unlocks_beyond_m2": 1,
        "risk": "governance_approval",
    },
    "DG-11-ail-mixer-mod-3df40": {
        "priority": 11,
        "title": "Misclassified Third-Party Miles AIL Digital Mixer Assembly (mod_3df40)",
        "shared_blocker": "0x3fe34..0x400e4 are hand-written MASM/TASM Miles AIL mixer routines called exclusively by ail_dig, misclassified as kind='runtime'",
        "mechanism": "User-approved modules.toml reclassification of 0x3fe34..0x400e4 to kind='ail' (fallback: explicit asm/T4 handling)",
        "estimated_t3_unlocks_beyond_m2": 0,
        "risk": "governance_approval",
    },
}


def build_inventory():
    p = analysis.run()
    funcs_db, datas_db, sym_errs = symbols.load(strict=False)
    if sym_errs:
        raise RuntimeError(f"Symbol database has errors: {sym_errs[:5]}")
    mods = progress.load_modules()
    rows = progress.classify([f["start"] for f in p.functions], funcs_db, mods)
    summary = progress.summarize(rows)

    by_addr = {f["start"]: f for f in p.functions}
    row_by_addr = {r["addr"]: r for r in rows}
    func_starts = sorted(by_addr.keys())
    owner_func = _owner_func_fn(func_starts, by_addr)
    tracked = batch_driver._git_tracked_files()
    dobj = p.le.obj(analysis.DATA_OBJ)
    cobj = p.le.obj(analysis.CODE_OBJ)

    not_done_rows = [r for r in rows if r["scope"] == "in" and not r["done"]]
    not_done_addrs = {r["addr"] for r in not_done_rows}

    # Build call graph, pointer references, data references, and jump table map.
    callees = collections.defaultdict(set)
    callers = collections.defaultdict(set)
    data_refs = collections.defaultdict(set)
    data_ptr_refs = collections.defaultdict(list)
    code_ptr_refs = collections.defaultdict(set)

    for f in p.functions:
        fs, fl = f["start"], f["limit"]
        a = fs
        while a < fl:
            ins = p.insns.get(a)
            if ins is None:
                a += 1
                continue
            m = ins.mnemonic
            if m in (analysis.COND_JUMPS | {"jmp", "call"}) and ins.operands and ins.operands[0].type == x86.X86_OP_IMM:
                t = ins.operands[0].imm & 0xFFFFFFFF
                if t in by_addr and t != fs:
                    callees[fs].add(t)
                    callers[t].add(fs)
            for off in range(ins.size):
                fa = a + off
                if fa in p.fix_at:
                    _, tgt = p.fix_at[fa]
                    if dobj.base <= tgt < dobj.end:
                        data_refs[fs].add(tgt)
                    elif cobj.base <= tgt < cobj.end and tgt in by_addr and tgt != fs:
                        code_ptr_refs[tgt].add(fs)
            a += ins.size

    for src, (_, tgt) in p.fix_at.items():
        if dobj.base <= src < dobj.end and tgt in by_addr:
            data_ptr_refs[tgt].append(src)

    jts_by_fn = collections.defaultdict(list)
    for tbl, (ja, tgts) in sorted(p.jump_tables.items()):
        jf = owner_func(ja)
        if jf is not None:
            jts_by_fn[jf].append({
                "table_addr": f"{tbl:#x}",
                "jmp_addr": f"{ja:#x}",
                "entries": len(tgts),
                "pre_function": tbl < jf,
            })

    # Pre-scan src/ and tests/ for placeholder identifier references.
    src_texts = {}
    for base_dir in ("src", "tests"):
        base_abs = path(base_dir)
        if not os.path.isdir(base_abs):
            continue
        for root, _, files in os.walk(base_abs):
            for fn in sorted(files):
                if fn.endswith((".c", ".h", ".py")):
                    full = os.path.join(root, fn)
                    rel = os.path.relpath(full, path()).replace("\\", "/")
                    with open(full, encoding="utf-8", errors="replace") as fh:
                        src_texts[rel] = fh.read()

    # Determine dominant TOML per module across all DB functions.
    mod_tomls = collections.defaultdict(collections.Counter)
    for r in rows:
        e = funcs_db.get(r["addr"])
        if e:
            mod_tomls[r["module"]][e["_file"].replace("\\", "/")] += 1

    # Inspect live Wave 4A & Wave 4B eligibility sets (non-mutating, no compiles).
    t4_cands, _ = t3_audit.discover(funcs_db, rows)
    w4_eligible_addrs = {c["addr"] for c in t4_cands if wave4.eligible(c)}

    # Build primary inventory rows.
    items = []
    for r in not_done_rows:
        a = r["addr"]
        f = by_addr[a]
        e = funcs_db.get(a)
        m = r["module"]
        ef = e["_file"].replace("\\", "/") if e else None
        name = e["name"] if e else None
        conf = e["confidence"] if e else None
        is_ph = bool(name and progress.PLACEHOLDER.match(name))
        in_datas = a in datas_db
        vb = e.get("verified_by") if e else None
        src_file = e.get("src") if e else None
        ref_file = e.get("ref") if e else None
        rvb = e.get("ref_verified_by") if e else None
        t3_blk = e.get("t3_blocker") if e else None
        matched_unbuilt = _matched_file_from_vb(vb) if (not src_file and str(vb or "").startswith("match:")) else None

        # Interior references into [start, end)
        int_refs = emit.replaced_interior_refs(p, [(f["start"], f["end"])], {f["start"]})
        pre_fn_jts = [jt for jt in jts_by_fn[a] if jt["pre_function"]]

        # Placeholder references in src/ and tests/
        ph_src_files, ph_test_files = [], []
        if is_ph and name:
            pat = re.compile(rf"\b{re.escape(name)}_?\b")
            for rel, txt in src_texts.items():
                if pat.search(txt):
                    if rel.startswith("src/"):
                        ph_src_files.append(rel)
                    else:
                        ph_test_files.append(rel)

        # Ownership class
        slug = overnight.AREA_OVERRIDES.get(m, overnight._slug(m))
        expected_toml = f"analysis/symbols/{slug}.toml"
        top_mod_toml = mod_tomls[m].most_common(1)[0][0] if mod_tomls[m] else None
        if ef is None:
            ownership = "none"
        elif ef in batch_driver.LOCKED_TOMLS:
            ownership = "locked_codegen_promo"
        elif ef == expected_toml or ef == top_mod_toml:
            ownership = "same_module"
        else:
            ownership = "cross_module"

        # Exact overnight Wave 2 / Wave 3 classification (with and without DEFAULT_SKIP)
        def _overnight_class(skip_set):
            if m in skip_set:
                return f"skipped_default:{m}"
            if in_datas:
                return "needs_human:data-in-code"
            if e is not None:
                if ef in batch_driver.LOCKED_TOMLS:
                    return "needs_human:locked_toml"
                if tracked is not None and ef not in tracked:
                    return "needs_human:untracked_toml"
                if r["c"] == "none" and str(vb or "").startswith("match:"):
                    return "needs_human:unbuildable_t3"
                if not r["named"] and r["c"] in ("T3", "T4"):
                    return "needs_human:name-only"
                if not r["named"]:
                    return "needs_human:existing_cross_toml_entry"
            if r["named"] and r["c"] == "none":
                return "eligible:wave2"
            if not r["named"] and r["c"] == "none":
                return "eligible:wave3"
            if r["named"] and r["c"] in ("ref", "T4"):
                return "needs_human:t4_incomplete"
            return "other"

        ov_default = _overnight_class(set(overnight.DEFAULT_SKIP))
        ov_noskip = _overnight_class(set())

        # Exact per-wave eligibility & exclusion reasons
        w2_elig = ov_default == "eligible:wave2"
        w3_elig = ov_default == "eligible:wave3"
        w4a_elig = a in w4_eligible_addrs and r["c"] == "T4"
        w4b_elig = a in w4_eligible_addrs and r["c"] == "T4"

        def _w2_reason():
            if w2_elig:
                return None
            if m in overnight.DEFAULT_SKIP:
                return f"module {m} in overnight.DEFAULT_SKIP"
            if not r["named"]:
                return f"not semantically named (name={name or '-'}, confidence={conf or '-'})"
            if r["c"] != "none":
                return f"already has C (c_status={r['c']})"
            if str(vb or "").startswith("match:"):
                return "already has verified_by='match:...' without src= (needs_human:unbuildable_t3)"
            return ov_default

        def _w3_reason():
            if w3_elig:
                return None
            if m in overnight.DEFAULT_SKIP:
                return f"module {m} in overnight.DEFAULT_SKIP"
            if in_datas:
                return f"address in datas_db ({datas_db[a]['name']} in {datas_db[a]['_file']})"
            if e is not None:
                if ef in batch_driver.LOCKED_TOMLS:
                    return f"entry in LOCKED_TOMLS ({ef})"
                if r["named"]:
                    return "already semantically named (Wave 2 or T4/unbuildable domain)"
                if r["c"] in ("T3", "T4"):
                    return f"already has verified C ({r['c']}); name-only"
                return f"pre-existing DB entry ({name}, {conf}) in {ef} excluded by overnight.build_queue_with_needs_human"
            return ov_default

        w4_reason = (
            None if w4b_elig
            else f"Wave 4A/4B only accept in-scope T4 (ref + ref_verified_by='difftest:...'); current c_status={r['c']}"
        )

        # Primary and secondary blocker taxonomy (mutually exclusive primary_blocker)
        secondary = []
        ev_notes = []
        unlocked_by = []
        blocker_origin = "tooling_or_pipeline"
        requires_llm = True
        det_unlock = False

        if in_datas:
            primary = "discovery_data_in_code"
            blocker_origin = "binary_or_discovery"
            requires_llm = False
            det_unlock = True
            dep_group = "DG-09-discovery-data-in-code"
            res_strategy = "Exclude verified code-segment byte tables from function discovery (user-approved discovery fix)"
            res_phase = "Phase 5: User-Approved Discovery & Scope Governance"
            ev_notes.append(f"In datas_db as {datas_db[a]['name']} ({datas_db[a]['_file']}); {f['end']-a}B raw data table decoded as {f['ninsns']} insns")
            unlocked_by.append("wc1.analysis data-in-code veto")
        elif a in (0x28090, 0x28093):
            primary = "discovery_split_function_block"
            blocker_origin = "binary_or_discovery"
            requires_llm = False
            det_unlock = True
            dep_group = "DG-10-status-split-block"
            res_strategy = "Merge shared return/continuation blocks of SelectionHasNoWorkers (0x28074) in discovery (user-approved scope/discovery fix)"
            res_phase = "Phase 5: User-Approved Discovery & Scope Governance"
            secondary.append("default_skip_status_c")
            ev_notes.append("Mid-function return/loop continuation of SelectionHasNoWorkers (0x28074..0x280a2); 0x28093 branches back to 0x2807d")
            unlocked_by.append("wc1.analysis shared-return merge")
        elif m == "mod_3df40":
            primary = "scope_misclassified_ail_asm"
            blocker_origin = "binary_or_discovery"
            requires_llm = False
            det_unlock = True
            dep_group = "DG-11-ail-mixer-mod-3df40"
            res_strategy = "Reclassify 0x3fe34..0x400e4 in analysis/modules.toml as kind='ail' (user-approved scope fix); fallback: hand-written asm/T4"
            res_phase = "Phase 5: User-Approved Discovery & Scope Governance"
            secondary.append("non_watcom_handwritten_asm")
            ev_notes.append("100% of direct callers are Miles AIL (ail_dig); MASM/TASM prologue push ds/push es/cld; 3x Wave 3 failures")
            unlocked_by.append("modules.toml kind='ail' split for 0x3fe34..0x400e4")
        elif a == 0x23170:
            primary = "unbuildable_t3_shared_epilogue_after_cut"
            blocker_origin = "tooling_or_pipeline"
            requires_llm = False
            det_unlock = True
            dep_group = "DG-03-build-shared-epilogue-interior-jumps"
            res_strategy = "Emit cut-boundary relative branch expressions in wc1.emit/wc1.build, then wire src='src/playflic/intro_op_sync_sound.c' in playflic.toml"
            res_phase = "Phase 1: Immediate Zero-LLM Wins & Buildability Fixes"
            secondary.append("default_skip_playflic_c")
            ev_notes.append("Local MATCH and check_t3_buildable=True, but a full wc1.build fails: IntroOpWaitSound 0x231cc keeps a rel8 branch to loc_2316c, whose epilogue moves into the previous asm piece once 0x23170 is C-replaced (nasm cannot emit an 8-bit external relocation)")
            unlocked_by.append("wc1.emit/wc1.build cut-boundary relative branch emission")
        elif a == 0x1bf94:
            primary = "unwired_passing_t4_difftest"
            blocker_origin = "tooling_or_pipeline"
            requires_llm = False
            det_unlock = True
            dep_group = "DG-01-immediate-zero-llm-wiring"
            res_strategy = "Wire ref_verified_by='difftest: tests/test_mod_1bf80.py::test_wait_input_or_timeout' in mod_1bf80.toml"
            res_phase = "Phase 1: Immediate Zero-LLM Wins & Buildability Fixes"
            ev_notes.append("tests/test_mod_1bf80.py::test_wait_input_or_timeout already exists and passes (3 passed in 1.22s); unwired since commit 5fa133b")
            unlocked_by.append("mod_1bf80.toml ref_verified_by= wiring")
        elif a == 0x157e8:
            primary = "unbuildable_t3_pre_function_jump_table"
            blocker_origin = "tooling_or_pipeline"
            requires_llm = False
            det_unlock = True
            dep_group = "DG-02-build-pre-function-jump-tables"
            res_strategy = "Support pub[1] > 0 pre-function switch jump tables in wc1.build.place, then wire src= in mod_13f60.toml"
            res_phase = "Phase 1: Immediate Zero-LLM Wins & Buildability Fixes"
            ev_notes.append("Already MATCH under Watcom 10.0a; build.place rejects pub[1]=0x10 (4-entry switch table at 0x157d8..0x157e8)")
            unlocked_by.append("wc1.build.place pre-function jump table support")
        elif r["c"] == "none" and str(vb or "").startswith("match:") and ef not in batch_driver.LOCKED_TOMLS:
            primary = "unbuildable_t3_shared_epilogue"
            blocker_origin = "tooling_or_pipeline"
            requires_llm = False
            det_unlock = True
            dep_group = "DG-03-build-shared-epilogue-interior-jumps"
            res_strategy = "Emit verified cut-boundary local-label relative jumps in wc1.emit/wc1.build for in-place T3 objects, then wire src="
            res_phase = "Phase 1: Immediate Zero-LLM Wins & Buildability Fixes"
            if m in overnight.DEFAULT_SKIP:
                secondary.append(f"default_skip_{m.lower().replace('.', '_')}")
            ev_notes.append(f"Already MATCH ({matched_unbuilt}); blocked by {len(int_refs)} neighbour rel8/rel32 interior branch(es) into shared epilogue")
            unlocked_by.append("wc1.emit/wc1.build cut-boundary relative jump support")
        elif r["c"] == "ref":
            primary = "ref_c_behavioural_divergence"
            blocker_origin = "reference_c_bug"
            requires_llm = True
            det_unlock = False
            dep_group = "DG-04-ref-c-divergences"
            res_strategy = "Fix real behavioural bug in reference C so existing xfailed difftest passes, then wire ref_verified_by"
            res_phase = "Phase 2: Reference-C Bug Fixes & Locked/Name-Only Promotions"
            if m in overnight.DEFAULT_SKIP:
                secondary.append("default_skip_playflic_c")
            if a == 0x231cc:
                secondary.append("shared_epilogue_caller")
            if a == 0x2fcfc:
                secondary.append("large_stack_frame_dbg")
            ev_notes.append(f"Reference C exists ({ref_file}) with t3_blocker, but existing difftest is marked xfail due to genuine C-vs-original divergence")
            unlocked_by.append("targeted ref-C bugfix + difftest green")
        elif not r["named"] and r["c"] in ("T3", "T4"):
            primary = "name_only_placeholder_with_verified_c"
            blocker_origin = "tooling_or_pipeline"
            requires_llm = True
            det_unlock = False
            dep_group = "DG-05-name-only-and-codegen-promo"
            res_strategy = "Assign semantic name from existing evidence + deterministic atomic repo-wide C/test/TOML renamer"
            res_phase = "Phase 2: Reference-C Bug Fixes & Locked/Name-Only Promotions"
            secondary.append("referenced_in_existing_src")
            if ownership == "cross_module":
                secondary.append("cross_toml_ownership")
            if conf == "low":
                secondary.append("low_confidence")
            ev_notes.append(f"Already verified {r['c']} ({src_file or ref_file}) in {ef}; only needs semantic name + rename across {len(ph_src_files)} src / {len(ph_test_files)} test files")
            unlocked_by.append("atomic cross-module symbol renamer")
        elif ef in batch_driver.LOCKED_TOMLS and str(vb or "").startswith("match:"):
            primary = "locked_codegen_promo_matched_t3"
            blocker_origin = "tooling_or_pipeline"
            requires_llm = True
            det_unlock = False
            dep_group = "DG-05-name-only-and-codegen-promo"
            res_strategy = "Assign semantic name + atomic migrate out of codegen_promo.toml + wire src= (a multi-function C file under src/codegen/ needs a one-function-per-file split first)"
            res_phase = "Phase 2: Reference-C Bug Fixes & Locked/Name-Only Promotions"
            secondary.append("locked_toml_codegen_promo")
            secondary.append("referenced_in_existing_src")
            if m in overnight.DEFAULT_SKIP:
                secondary.append(f"default_skip_{m.lower().replace('.', '_')}")
            if matched_unbuilt and matched_unbuilt.startswith("src/codegen/") and sum(
                    1 for x in funcs_db.values() if x.get("src") == matched_unbuilt) > 1:
                secondary.append("multi_function_c_file_needs_split")
            ev_notes.append(f"Byte-matched T3 C already exists ({matched_unbuilt}); blocked by LOCKED_TOMLS + placeholder name ({len(ph_src_files)} src refs)")
            unlocked_by.append("atomic cross-module symbol renamer + codegen_promo unlock")
        elif e is None and not r["named"] and r["c"] == "none":
            # No DB entry and no semantic name: ordinary Wave 3 work. The 10
            # clean BULLET.C functions are the only such rows today; they were
            # blocked solely by the now-removed stale DEFAULT_SKIP entry.
            primary = "wave3_eligible_no_db_entry"
            blocker_origin = "tooling_or_pipeline"
            requires_llm = True
            det_unlock = False
            if m == "BULLET.C":
                dep_group = "DG-06-bullet-c-module"
                res_phase = "Phase 3: BULLET.C & Low-Confidence Named Functions"
            else:
                dep_group = f"DG-08-wave3-{m.lower().replace('.', '_')}"
                res_phase = "Phase 4: Wave 3R Atomic Stub-Upgrade Sweep"
            res_strategy = "Wave 3 (full): reconstruct C/T4 for an unnamed function with no pre-existing DB entry"
            ev_notes.append("No technical blocker: unnamed with no DB entry and eligible for Wave 3 now that the module is not in overnight.DEFAULT_SKIP")
            unlocked_by.append("Wave 3 (already eligible)")
        elif e is not None and not is_ph and conf == "low":
            primary = "existing_low_conf_named_no_c"
            blocker_origin = "tooling_or_pipeline"
            requires_llm = True
            det_unlock = False
            dep_group = "DG-07-low-conf-named-no-c"
            res_strategy = "Wave 3R (upgrade-existing) or Wave 2 extension allowing low-confidence named entries to reconstruct C + upgrade confidence"
            res_phase = "Phase 3: BULLET.C & Low-Confidence Named Functions"
            if ownership == "cross_module":
                secondary.append("cross_toml_ownership")
            if a == 0x1b00c:
                secondary.append("shared_epilogue_caller")
            ev_notes.append(f"Already semantically named '{name}' in {ef} with disassembly evidence, but confidence='low' excludes it from Wave 2")
            unlocked_by.append("Wave 3R / low-conf Wave 2 eligibility")
        else:
            # All remaining 61: existing placeholder fn_* entries without C
            assert e is not None and is_ph and r["c"] == "none", f"Unexpected entry: {hex(a)} {r}"
            if ownership in ("cross_module", "locked_codegen_promo"):
                primary = "cross_toml_placeholder_stub_no_c"
            else:
                primary = "same_toml_placeholder_stub_no_c"
            blocker_origin = "tooling_or_pipeline"
            requires_llm = True
            det_unlock = False
            if m == "BULLET.C":
                dep_group = "DG-06-bullet-c-module"
                res_phase = "Phase 3: BULLET.C & Low-Confidence Named Functions"
                if m in overnight.DEFAULT_SKIP:
                    secondary.append("default_skip_bullet_c")
            elif ef in batch_driver.LOCKED_TOMLS:
                dep_group = "DG-05-name-only-and-codegen-promo"
                res_phase = "Phase 2: Reference-C Bug Fixes & Locked/Name-Only Promotions"
                secondary.append("locked_toml_codegen_promo")
            else:
                dep_group = f"DG-08-stub-area-{m.lower().replace('.', '_')}"
                res_phase = "Phase 4: Wave 3R Atomic Stub-Upgrade Sweep"
            res_strategy = "Wave 3R (upgrade-existing): reconstruct name+C+T4 in module, atomically migrate TOML entry, and deterministically rename callers across src/tests"
            secondary.append("referenced_in_existing_src")
            if conf == "low":
                secondary.append("low_confidence")
            if pre_fn_jts:
                secondary.append("pre_function_jump_table")
            if f["cross"]:
                secondary.append("shared_epilogue_caller")
            if f["ninsns"] >= 200:
                secondary.append("large_function_complexity")
            if _codegen_style(p, f) == "DBG":
                secondary.append("large_stack_frame_dbg")
            ev_notes.append(f"Pre-existing placeholder '{name}' ({conf}) in {ef} referenced in {len(ph_src_files)} src files; excluded from Wave 2 & Wave 3")
            unlocked_by.append("Wave 3R atomic stub-upgrade + cross-module renamer")

        # Data dependencies
        d_addrs = sorted(data_refs[a])
        named_d = [f"{da:#x}:{datas_db[da]['name']}" for da in d_addrs if da in datas_db]
        unnamed_d = [f"{da:#x}" for da in d_addrs if da not in datas_db]

        # Callers / callees
        c_in = sorted(callers[a])
        c_out = sorted(callees[a])
        done_in = [x for x in c_in if x in row_by_addr and row_by_addr[x]["done"]]
        nd_in = [x for x in c_in if x in not_done_addrs]
        nd_out = [x for x in c_out if x in not_done_addrs]

        items.append({
            "addr": a,
            "addr_hex": f"{a:#07x}",
            "end_hex": f"{f['end']:#07x}",
            "limit_hex": f"{f['limit']:#07x}",
            "size_bytes": f["end"] - a,
            "ninsns": f["ninsns"],
            "module": m,
            "kind": r["kind"],
            "subsystem": SUBSYSTEM_MAP.get(m, "other"),
            "codegen_style": _codegen_style(p, f),
            "name": name,
            "is_placeholder": is_ph,
            "confidence": conf,
            "c_status": r["c"],
            "missing": list(r["missing"]),
            "conv": e.get("conv") if e else None,
            "proto": e.get("proto") if e else None,
            "src_file": src_file,
            "ref_file": ref_file,
            "matched_unbuilt_file": matched_unbuilt,
            "verified_by": vb,
            "ref_verified_by": rvb,
            "t3_blocker": t3_blk,
            "toml_file": ef,
            "toml_ownership_class": ownership,
            "in_datas_db": in_datas,
            "datas_db_name": datas_db[a]["name"] if in_datas else None,
            "caller_count": len(c_in),
            "done_caller_count": len(done_in),
            "not_done_caller_count": len(nd_in),
            "callee_count": len(c_out),
            "not_done_callee_count": len(nd_out),
            "data_ptr_ref_count": len(data_ptr_refs[a]),
            "code_ptr_ref_count": len(code_ptr_refs[a]),
            "callers": [f"{x:#x}" for x in c_in],
            "callees": [f"{x:#x}" for x in c_out],
            "not_done_callers": [f"{x:#x}" for x in nd_in],
            "not_done_callees": [f"{x:#x}" for x in nd_out],
            "data_ref_count": len(d_addrs),
            "named_data_refs": named_d,
            "unnamed_data_ref_count": len(unnamed_d),
            "src_placeholder_ref_count": len(ph_src_files),
            "test_placeholder_ref_count": len(ph_test_files),
            "interior_ref_in_count": len(int_refs),
            "outgoing_cross_count": len(f["cross"]),
            "has_pre_function_jump_table": bool(pre_fn_jts),
            "jump_tables": jts_by_fn[a],
            "wave2_eligible": w2_elig,
            "wave3_eligible": w3_elig,
            "wave4a_eligible": w4a_elig,
            "wave4b_eligible": w4b_elig,
            "wave2_exclusion_reason": _w2_reason(),
            "wave3_exclusion_reason": _w3_reason(),
            "wave4a_exclusion_reason": w4_reason,
            "wave4b_exclusion_reason": w4_reason,
            "overnight_default_status": ov_default,
            "overnight_noskip_status": ov_noskip,
            "primary_blocker": primary,
            "secondary_blockers": secondary,
            "blocker_origin": blocker_origin,
            "blocker_evidence": ev_notes,
            "unlocked_by": unlocked_by,
            "dependency_group": dep_group,
            "resolution_phase": res_phase,
            "resolution_strategy": res_strategy,
            "deterministic_unlock": det_unlock,
            "requires_llm": requires_llm,
        })

    # Reconcile totals strictly against wc1.progress
    expected_not_done = summary["in_scope"] - summary["done"]
    assert len(items) == expected_not_done, f"Reconciliation mismatch: {len(items)} != {expected_not_done}"
    assert len({x["addr"] for x in items}) == len(items), "Duplicate addresses in inventory"

    # Build dependency groups summary
    groups_map = collections.defaultdict(list)
    for it in items:
        groups_map[it["dependency_group"]].append(it)

    dep_groups = []
    for gid, members in sorted(groups_map.items()):
        meta = GROUP_META.get(gid)
        if meta is None:
            # DG-08-stub-area-<mod>
            mod_name = members[0]["module"]
            tomls_in = sorted({x["toml_file"] for x in members if x["toml_file"]})
            meta = {
                "priority": 8,
                "title": f"Wave 3R Stub-Upgrade Area: {mod_name}",
                "shared_blocker": f"Pre-existing placeholder fn_* stubs in {', '.join(tomls_in)} referenced by existing src/ callers; excluded from Wave 2/3",
                "mechanism": "Wave 3R (upgrade-existing): module-scoped C+T4 reconstruction + atomic TOML migration + deterministic repo-wide caller rename",
                "estimated_t3_unlocks_beyond_m2": 0,
                "risk": "low_to_medium",
            }
        tot_insns = sum(x["ninsns"] for x in members)
        tot_src_refs = sum(x["src_placeholder_ref_count"] for x in members)
        dep_groups.append({
            "group_id": gid,
            "priority": meta["priority"],
            "title": meta["title"],
            "function_count": len(members),
            "total_insns": tot_insns,
            "avg_insns": round(tot_insns / max(1, len(members)), 1),
            "modules": sorted({x["module"] for x in members}),
            "toml_files": sorted({x["toml_file"] for x in members if x["toml_file"]}),
            "addresses": [x["addr_hex"] for x in members],
            "names": [x["name"] or "-" for x in members],
            "deterministic_unlock_count": sum(1 for x in members if x["deterministic_unlock"]),
            "requires_llm_count": sum(1 for x in members if x["requires_llm"]),
            "total_src_placeholder_refs": tot_src_refs,
            "shared_blocker": meta["shared_blocker"],
            "mechanism": meta["mechanism"],
            "estimated_t3_unlocks_beyond_m2": meta["estimated_t3_unlocks_beyond_m2"],
            "risk": meta["risk"],
        })
    dep_groups.sort(key=lambda g: (g["priority"], -g["function_count"], g["group_id"]))

    # Aggregate statistics
    primary_counts = dict(collections.Counter(x["primary_blocker"] for x in items).most_common())
    secondary_counts = dict(collections.Counter(sb for x in items for sb in x["secondary_blockers"]).most_common())
    origin_counts = dict(collections.Counter(x["blocker_origin"] for x in items).most_common())
    phase_counts = dict(collections.Counter(x["resolution_phase"] for x in items).most_common())

    payload = {
        "meta": {
            "git_head": _git_head(),
            "in_scope": summary["in_scope"],
            "done": summary["done"],
            "not_done": len(items),
            "named": summary["named"],
            "t3": summary["c"]["T3"],
            "t3_by_compiler": summary["T3_by_compiler"],
            "t4": summary["c"]["T4"],
            "ref_unchecked": summary["c"]["ref"],
            "no_c": summary["c"]["none"],
            "unclassified_runtime": summary["unclassified_runtime"],
            "out_of_scope": summary["out_of_scope"],
            "by_kind": summary["by_kind"],
            "reconciled_with_wc1_progress": True,
        },
        "counts": {
            "by_primary_blocker": primary_counts,
            "by_secondary_blocker": secondary_counts,
            "by_blocker_origin": origin_counts,
            "by_resolution_phase": phase_counts,
            "by_codegen_style": dict(collections.Counter(x["codegen_style"] for x in items).most_common()),
            "deterministic_unlock_total": sum(1 for x in items if x["deterministic_unlock"]),
            "requires_llm_total": sum(1 for x in items if x["requires_llm"]),
            "overnight_default_eligible": sum(1 for x in items if x["overnight_default_status"].startswith("eligible:")),
            "overnight_default_skipped": sum(1 for x in items if x["overnight_default_status"].startswith("skipped_default:")),
            "overnight_default_needs_human": sum(1 for x in items if x["overnight_default_status"].startswith("needs_human:")),
        },
        "functions": items,
    }
    return payload, dep_groups


CSV_FIELDS = [
    "addr_hex", "end_hex", "size_bytes", "ninsns", "module", "kind", "subsystem",
    "codegen_style", "name", "is_placeholder", "confidence", "c_status",
    "missing", "conv", "proto", "toml_file", "toml_ownership_class",
    "src_file", "ref_file", "matched_unbuilt_file",
    "caller_count", "done_caller_count", "not_done_caller_count",
    "callee_count", "not_done_callee_count", "data_ptr_ref_count",
    "data_ref_count", "unnamed_data_ref_count",
    "src_placeholder_ref_count", "test_placeholder_ref_count",
    "interior_ref_in_count", "outgoing_cross_count", "has_pre_function_jump_table",
    "wave2_eligible", "wave3_eligible", "wave4a_eligible", "wave4b_eligible",
    "overnight_default_status", "overnight_noskip_status",
    "primary_blocker", "secondary_blockers", "blocker_origin",
    "dependency_group", "resolution_phase", "deterministic_unlock", "requires_llm",
]


def write_outputs(out_dir, payload, dep_groups):
    os.makedirs(out_dir, exist_ok=True)
    inv_json = os.path.join(out_dir, "inventory.json")
    inv_csv = os.path.join(out_dir, "inventory.csv")
    dg_json = os.path.join(out_dir, "dependency-groups.json")

    with open(inv_json, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
        fh.write("\n")

    with open(inv_csv, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        w.writeheader()
        for it in payload["functions"]:
            row = {}
            for k in CSV_FIELDS:
                v = it.get(k)
                if isinstance(v, list):
                    row[k] = ";".join(str(x) for x in v)
                elif v is None:
                    row[k] = ""
                else:
                    row[k] = v
            w.writerow(row)

    dg_payload = {
        "meta": {
            "git_head": payload["meta"]["git_head"],
            "not_done_total": payload["meta"]["not_done"],
            "group_count": len(dep_groups),
            "sum_group_functions": sum(g["function_count"] for g in dep_groups),
        },
        "groups": dep_groups,
    }
    assert dg_payload["meta"]["sum_group_functions"] == payload["meta"]["not_done"]
    with open(dg_json, "w", encoding="utf-8") as fh:
        json.dump(dg_payload, fh, indent=2)
        fh.write("\n")
    return inv_json, inv_csv, dg_json


def main(argv=None):
    ap = argparse.ArgumentParser(prog="wc1.m2_inventory", description=__doc__.split("\n\n")[0])
    ap.add_argument("--out-dir", help="Write inventory.json, inventory.csv, dependency-groups.json here")
    ap.add_argument("--summary", action="store_true", help="Print reconciled summary to stdout")
    a = ap.parse_args(argv)
    payload, dep_groups = build_inventory()
    if a.out_dir:
        paths = write_outputs(a.out_dir, payload, dep_groups)
        print("Wrote:", ", ".join(paths))
    if a.summary or not a.out_dir:
        print(json.dumps({"meta": payload["meta"], "counts": payload["counts"], "group_count": len(dep_groups)}, indent=2))
        print("\nDependency groups:")
        for g in dep_groups:
            print(f"  P{g['priority']:02d} {g['group_id']:42} n={g['function_count']:2d} insns={g['total_insns']:4d} det={g['deterministic_unlock_count']:2d} llm={g['requires_llm_count']:2d} | {g['title']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
