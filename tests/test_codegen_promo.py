"""Promotion guard for analysis/symbols/codegen_promo.toml (AGENTS.md step 1
tail, docs/subsystems/codegen.md section 5/7).

The game samples in src/codegen/{bullet,mod_110a0,mod_13e60,mod_13f60,
mod_19470}.c used to match only under `wc1.codegen_sweep` because their own
fn_/dat_ addresses were not in the symbol database.  After the codegen_promo
entries they pass `python3 -m wc1.match` (T3) per function:

    bullet.c     fn_123cc        mod_13e60.c  fn_13e94   mod_13f60.c fn_15558
    mod_110a0.c  fn_1132c        mod_19470.c  fn_19478

mod_12c70.c was the same kind of sample: its only function, fn_12cd4, became
NetNextRecvSlot and moved to src/mod_12c70/net_next_recv_slot.c (2026-11-18,
the link-ring area), so the sample file is gone and the entry lives in
analysis/symbols/net_link.toml.

This test re-checks exactly that: every function recorded here must still be
reported MATCH by wc1.match (a superset is fine - promoting more functions
later must not break this), so a rename that removes a codegen_promo entry
without renaming the C fails loudly.

fn_15170 and fn_15230 of mod_13f60.c joined them on 2026-11-17, when
wc1.match's extent model was fixed (tools/wc1/match.py): the compiled module
pads a function to the next public of *its* object, while the original image
places the unnamed neighbours fn_1517c/fn_1518c/fn_1519c/fn_151ac (after
fn_15170) and fn_15244 (after fn_15230) there.  wc1.match now retries the
comparison with the extent clamped at the original's flow end (code
discovery) when the module only adds alignment filler past it (see the
evidence in codegen_promo.toml).
"""
import os
import re

import pytest

from wc1 import analysis, match, path, symbols

HAVE_ORIGINAL = os.path.exists(path("original", "install", "war.exe"))
HAVE_WATCOM = bool(os.environ.get("WATCOM"))
pytestmark = pytest.mark.skipif(not (HAVE_ORIGINAL and HAVE_WATCOM),
                                reason="needs original/ (make extract) and $WATCOM (nix develop)")

# link names recorded as MATCH under wc1.match (fn_15170_/fn_15230_ since the
# 2026-11-17 extent fix, previously MISMATCH on the padding byte only)
PROMOTED = {
    "bullet.c": {"fn_123cc_"},
    "mod_110a0.c": {"fn_1132c_"},
    "mod_13e60.c": {"fn_13e94_"},
    "mod_13f60.c": {"fn_15170_", "fn_15230_", "fn_15558_"},
    "mod_19470.c": {"fn_19478_"},
}


@pytest.fixture(scope="module")
def prog():
    return analysis.run()


@pytest.fixture(scope="module")
def by_link():
    funcs, datas, errors = symbols.load()
    assert not errors, errors
    return {e["link_name"]: e for t in (funcs, datas) for e in t.values()}


def _run(name, prog, by_link):
    src = path("src", "codegen", name)
    os.makedirs(path("build", "codegen"), exist_ok=True)
    mod = match.compile_c(src, None, path("build", "codegen", "promo_" + name + ".obj"))
    return match.match_module(prog, mod, by_link)


@pytest.mark.parametrize("name", sorted(PROMOTED))
def test_promoted_functions_still_match(name, prog, by_link):
    res = _run(name, prog, by_link)
    matched = {n for n, st, _ in res if st == "MATCH" and not n.startswith("[")}
    missing = PROMOTED[name] - matched
    assert not missing, (f"{name}: these functions are no longer MATCH under wc1.match "
                         f"(symbol-database entry renamed or removed?): {sorted(missing)}")


@pytest.mark.parametrize("fn_name", ["fn_15170_", "fn_15230_"])
def test_extent_retry_matches_the_flow_end(fn_name, prog, by_link):
    """The two functions that used to fail only on the object-padding byte
    now match through the extent retry: their extent must clamp exactly at
    the original's flow end, with only filler skipped on the module side."""
    f = next(f for f in prog.functions if f["start"] == by_link[fn_name]["addr"])
    res = {n: (st, pr) for n, st, pr in _run("mod_13f60.c", prog, by_link)}
    assert fn_name in res, sorted(res)
    status, problems = res[fn_name]
    assert status == "MATCH", problems
    assert f["end"] > f["start"], fn_name
    assert f["limit"] > f["end"], (fn_name, "flow end must not reach the next start")


def test_codegen_promo_entries_exist():
    """Every PROMOTED/EXTENT_FAILS link name resolves in the database, with the
    placeholder-name policy: confidence medium at most unless mechanically
    checked, and no src= line (the build must keep taking these bytes from asm)."""
    funcs, _, errors = symbols.load()
    assert not errors, errors
    promo = {e["name"]: e for e in funcs.values() if e["_file"].endswith("codegen_promo.toml")}
    wanted = {n.rstrip("_") for s in PROMOTED.values() for n in s}
    for n in sorted(wanted):
        assert n in promo, f"{n} missing from codegen_promo.toml"
    assert promo, "codegen_promo.toml has no functions"
    for e in promo.values():
        assert "src" not in e, f"{e['name']} must not add src= (AGENTS task)"
        if e["confidence"] == "verified":
            assert e["verified_by"].startswith("match: python3 -m wc1.match src/codegen/"), e


def test_flags_header_used():
    """wc1.match takes the flags from each file's codegen-flags header (the
    PROMOTED results above are only reproducible with them)."""
    for name in PROMOTED:
        with open(path("src", "codegen", name)) as fh:
            assert re.search(r"codegen-flags:", fh.read(2048)), name
