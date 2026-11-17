"""wc1.progress (docs/GOAL.md) and the non-matching-C fields of the symbol DB.

1. classify() on synthetic data: scope rules, semantic names, C status, done.
2. symbols.check_c_fields: ref / ref_verified_by / t3_blocker validation.
3. Every function a *_reference.c file defines (and the DB names) carries
   ref = that file, so the progress numbers cannot silently drift.
4. On the real database (needs original/): the counts are consistent.
"""
import glob
import os
import re

import pytest

from wc1 import path, progress, symbols

MODS = [
    {"name": "mod_a", "start": 0x100, "end": 0x200, "kind": "game"},
    {"name": "ail_core", "start": 0x200, "end": 0x300, "kind": "ail"},
    {"name": "int_stub_table", "start": 0x300, "end": 0x400, "kind": "runtime"},
    {"name": "mod_r", "start": 0x400, "end": 0x500, "kind": "runtime"},
]


def _e(name, conf="medium", file="analysis/symbols/game.toml", **kw):
    return dict(name=name, confidence=conf, _file=file, **kw)


def test_classify_scope_names_and_c():
    db = {
        0x100: _e("UnitMove", src="src/x.c", conf="verified"),
        0x110: _e("fn_110"),                                        # placeholder name
        0x120: _e("UnitStop", conf="low"),                          # too weak a name
        0x130: _e("UnitTick", ref="src/r.c"),                       # reference, unchecked
        0x140: _e("UnitPath", ref="src/r.c", ref_verified_by="difftest: t", t3_blocker="regalloc: x"),
        0x150: _e("UnitAi", ref="src/r.c", ref_verified_by="difftest: t"),   # T4, no blocker
        0x160: _e("strlen", file="analysis/symbols/clib.toml"),     # Watcom runtime
        0x410: _e("VidFlip"),
    }
    starts = [0x100, 0x110, 0x120, 0x130, 0x140, 0x150, 0x160, 0x170, 0x210, 0x310, 0x400, 0x410]
    rows = {r["addr"]: r for r in progress.classify(starts, db, MODS)}
    assert rows[0x160]["out_reason"] == "Watcom runtime"
    assert rows[0x210]["out_reason"] == "Miles AIL (third-party)"
    assert rows[0x310]["out_reason"] == "Watcom runtime"
    assert [a for a, r in rows.items() if r["scope"] == "in"] == \
        [0x100, 0x110, 0x120, 0x130, 0x140, 0x150, 0x170, 0x400, 0x410]
    assert [a for a, r in rows.items() if r["named"]] == [0x100, 0x130, 0x140, 0x150, 0x160, 0x410]
    assert {a: r["c"] for a, r in rows.items() if r["c"] != "none"} == \
        {0x100: "T3", 0x130: "ref", 0x140: "T4", 0x150: "T4"}
    assert [a for a, r in rows.items() if r["done"]] == [0x100, 0x140]
    assert rows[0x150]["missing"] == ["t3_blocker"]
    assert rows[0x130]["missing"] == ["C-vs-original difftest", "t3_blocker"]
    assert rows[0x110]["missing"] == ["name", "C"]
    assert rows[0x400]["unclassified"] and not rows[0x410]["unclassified"]
    s = progress.summarize(list(rows.values()))
    assert (s["in_scope"], s["done"], s["c"]["T4"], s["unclassified_runtime"]) == (9, 2, 2, 1)


REF = "src/game_2c4e0/draw_list_reference.c"


@pytest.mark.parametrize("entry, expect", [
    (dict(name="DrawListSort", ref=REF), None),
    (dict(name="DrawListSort", ref=REF, ref_verified_by="difftest: t", t3_blocker="regalloc: ecx vs ebx"), None),
    (dict(name="DrawListSort", ref=REF, src="src/x.c"), "exclusive"),
    (dict(name="DrawListSort", ref="src/nope_reference.c"), "does not exist"),
    (dict(name="DrawListSort", ref="src/x.h"), ".c file"),
    (dict(name="UnitTick", ref=REF), "does not define"),
    (dict(name="DrawListSort", ref_verified_by="difftest: t"), "requires 'ref'"),
    (dict(name="DrawListSort", ref=REF, ref_verified_by="match: x"), "difftest:"),
    (dict(name="DrawListSort", ref=REF, t3_blocker="looks hard"), "category"),
])
def test_c_field_validation(entry, expect):
    errors = symbols.check_c_fields(entry, "t")
    if expect is None:
        assert errors == []
    else:
        assert len(errors) == 1 and expect in errors[0], errors


def test_reference_files_are_recorded_in_the_db():
    funcs, _, _ = symbols.load()
    byname = {e["name"]: e for e in funcs.values()}
    missing = []
    for f in sorted(glob.glob(path("src", "*", "*_reference.c"))):
        rel = os.path.relpath(f, path()).replace(os.sep, "/")
        with open(f, encoding="latin-1") as fh:
            text = fh.read()
        for m in re.finditer(r"^[A-Za-z_][\w \*]*?\b([A-Za-z_]\w*)\s*\([^;]*$", text, re.M):
            n = m.group(1)
            base = n if n in byname else re.sub(r"_[a-z]$", "", n)
            e = byname.get(base)
            if e is not None and not e.get("src") and e.get("ref") != rel:
                missing.append(f"{base} (defined in {rel}, ref = {e.get('ref')!r})")
    assert not missing, "set ref = for: " + "; ".join(missing)


@pytest.mark.skipif(not os.path.exists(path("original", "install", "war.exe")),
                    reason="original files not extracted (make extract)")
def test_progress_on_the_real_database():
    from wc1 import analysis
    funcs, _, _ = symbols.load()
    starts = [f["start"] for f in analysis.run().functions]
    rows = progress.classify(starts, funcs, progress.load_modules())
    assert len(rows) == len(starts)
    inn = [r for r in rows if r["scope"] == "in"]
    # every function built from C is in scope and counts as T3
    assert sum(r["c"] == "T3" for r in inn) == sum(1 for e in funcs.values() if e.get("src"))
    # every clib.toml entry that is a discovered start is out of scope
    by_addr = {r["addr"]: r for r in rows}
    for a, e in funcs.items():
        if e["_file"].endswith("clib.toml") and a in by_addr:
            assert by_addr[a]["scope"] == "out"
    s = progress.summarize(rows)
    assert s["done"] == sum(r["done"] for r in inn) <= s["in_scope"]
    assert sum(s["c"].values()) == s["in_scope"]
    assert progress.main(["--json"]) == 0
