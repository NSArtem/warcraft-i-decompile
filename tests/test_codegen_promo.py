"""Guard for the sample functions staged in analysis/symbols/codegen_promo.toml
(docs/subsystems/codegen.md section 5/7).

The game samples in src/codegen/{bullet,mod_110a0,mod_13e60,mod_13f60,
mod_19470}.c used to match only under `wc1.codegen_sweep` because their own
fn_/dat_ addresses were not in the symbol database.  After the codegen_promo
entries they passed `python3 -m wc1.match` (T3) per function:

    bullet.c     fn_123cc        mod_13e60.c  fn_13e94   mod_13f60.c fn_15558
    mod_110a0.c  fn_1132c        mod_19470.c  fn_19478

mod_12c70.c was the same kind of sample: its only function, fn_12cd4, became
NetNextRecvSlot and moved to src/mod_12c70/net_next_recv_slot.c (2026-11-18,
the link-ring area), so the sample file is gone and the entry lives in
analysis/symbols/net_link.toml.

All seven remaining samples were named and migrated to their module areas on
2026-11-27; their records now live in the area TOMLs named in PROMOTED below
and the sample files are removed.  This test re-checks that every one of them
is still recorded as verified with its src= file and still reported MATCH by
`wc1.match`, and that codegen_promo.toml keeps only the unreconstructed
fn_150f0, the 4 data symbols and the T4-only NetLinkHandshake - so a rename
that drops an entry without renaming the C fails loudly.

fn_15170/0x15170 and fn_15230/0x15230 were the two that needed wc1.match's
extent retry (tools/wc1/match.py, fixed 2026-11-17): the compiled module pads
a function to the end of *its* object, while the original image places the
unnamed neighbours fn_1517c/fn_1518c/fn_1519c/fn_151ac (after 0x15170) and
fn_15244 (after 0x15230) there.  wc1.match retries the comparison with the
extent clamped at the original's flow end when the module only adds alignment
filler past it; test_extent_retry_matches_the_flow_end keeps that guard on the
split single-function files (MapChoiceForest, NetGameHandshakeCallback).
"""
import os
import re

import pytest

from wc1 import analysis, match, path, symbols

HAVE_ORIGINAL = os.path.exists(path("original", "install", "war.exe"))
HAVE_WATCOM = bool(os.environ.get("WATCOM"))
pytestmark = pytest.mark.skipif(not (HAVE_ORIGINAL and HAVE_WATCOM),
                                reason="needs original/ (make extract) and $WATCOM (nix develop)")

# src file -> link names recorded as MATCH under wc1.match
PROMOTED = {
    "src/mod_104b0/attack_fatal_stub.c": {"AttackFatalStub_"},
    "src/mod_104b0/bullet_fatal_stub.c": {"BulletFatalStub_"},
    "src/mod_13e60/demo_idle_timer_reset.c": {"DemoIdleTimerReset_"},
    "src/mod_13f60/map_choice_forest.c": {"MapChoiceForest_"},
    "src/mod_13f60/net_game_handshake_callback.c": {"NetGameHandshakeCallback_"},
    "src/mod_13f60/phone_number_save.c": {"PhoneNumberSave_"},
    "src/mod_19470/game_random.c": {"GameRandom_"},
}

# symbol name -> (area TOML basename, original address, src= file)
MIGRATED = {
    "AttackFatalStub": ("mod_104b0.toml", 0x1132c, "src/mod_104b0/attack_fatal_stub.c"),
    "BulletFatalStub": ("mod_104b0.toml", 0x123cc, "src/mod_104b0/bullet_fatal_stub.c"),
    "DemoIdleTimerReset": ("mod_13e60.toml", 0x13e94, "src/mod_13e60/demo_idle_timer_reset.c"),
    "MapChoiceForest": ("mod_13f60.toml", 0x15170, "src/mod_13f60/map_choice_forest.c"),
    "NetGameHandshakeCallback": ("mod_13f60.toml", 0x15230, "src/mod_13f60/net_game_handshake_callback.c"),
    "PhoneNumberSave": ("mod_13f60.toml", 0x15558, "src/mod_13f60/phone_number_save.c"),
    "GameRandom": ("mod_19470.toml", 0x19478, "src/mod_19470/game_random.c"),
}

# the entries that must stay in codegen_promo.toml (locked staging table):
# fn_150f0 is still unreconstructed C; NetLinkHandshake (SAVE.C) is analysed
# but its record has not moved yet.
PROMO_FUNCS = {"fn_150f0", "NetLinkHandshake"}
PROMO_DATA = {"dat_50d7c", "dat_51530", "dat_516ae", "dat_59230"}


@pytest.fixture(scope="module")
def prog():
    return analysis.run()


@pytest.fixture(scope="module")
def by_link():
    funcs, datas, errors = symbols.load()
    assert not errors, errors
    return {e["link_name"]: e for t in (funcs, datas) for e in t.values()}


def _run(src, prog, by_link):
    os.makedirs(path("build", "promo"), exist_ok=True)
    obj = path("build", "promo", os.path.basename(src) + ".obj")
    mod = match.compile_c(path(src), None, obj)
    return match.match_module(prog, mod, by_link)


@pytest.mark.parametrize("src", sorted(PROMOTED))
def test_promoted_functions_still_match(src, prog, by_link):
    res = _run(src, prog, by_link)
    matched = {n for n, st, _ in res if st == "MATCH" and not n.startswith("[")}
    missing = PROMOTED[src] - matched
    assert not missing, (f"{src}: these functions are no longer MATCH under wc1.match "
                         f"(symbol-database entry renamed or removed?): {sorted(missing)}")


@pytest.mark.parametrize("fn_name,src", [
    ("MapChoiceForest_", "src/mod_13f60/map_choice_forest.c"),
    ("NetGameHandshakeCallback_", "src/mod_13f60/net_game_handshake_callback.c"),
])
def test_extent_retry_matches_the_flow_end(fn_name, src, prog, by_link):
    """The two functions that used to fail only on the object-padding byte
    now match through the extent retry: their extent must clamp exactly at
    the original's flow end, with only filler skipped on the module side."""
    f = next(f for f in prog.functions if f["start"] == by_link[fn_name]["addr"])
    res = {n: (st, pr) for n, st, pr in _run(src, prog, by_link)}
    assert fn_name in res, sorted(res)
    status, problems = res[fn_name]
    assert status == "MATCH", problems
    assert f["end"] > f["start"], fn_name
    assert f["limit"] > f["end"], (fn_name, "flow end must not reach the next start")


def test_migrated_entries_are_verified_in_their_area_tomls():
    """Each promoted sample is a verified record with src= in its area TOML."""
    funcs, _, errors = symbols.load()
    assert not errors, errors
    by_name = {e["name"]: e for e in funcs.values()}
    for name, (toml, addr, src) in sorted(MIGRATED.items()):
        e = by_name.get(name)
        assert e is not None, f"{name} missing from the symbol database"
        assert e["_file"].endswith(toml), (name, e["_file"])
        assert e["addr"] == addr, (name, hex(e["addr"]))
        assert e.get("src") == src, (name, e.get("src"))
        assert e["confidence"] == "verified", (name, e["confidence"])
        assert e["verified_by"].startswith("match:"), (name, e["verified_by"])
        assert os.path.exists(path(src)), src


def test_codegen_promo_keeps_only_the_unreconstructed_entry():
    """codegen_promo.toml (LOCKED_TOMLS) still holds fn_150f0 and the T4-only
    NetLinkHandshake, no src=, and the 4 data symbols; the migrated records are
    gone from it."""
    funcs, datas, errors = symbols.load()
    assert not errors, errors
    promo = {e["name"]: e for e in funcs.values() if e["_file"].endswith("codegen_promo.toml")}
    assert set(promo) == PROMO_FUNCS, sorted(promo)
    for e in promo.values():
        assert "src" not in e, f"{e['name']} must not add src= in codegen_promo.toml"
    promo_data = {e["name"] for e in datas.values() if e["_file"].endswith("codegen_promo.toml")}
    assert promo_data == PROMO_DATA, sorted(promo_data)
    for name in MIGRATED:
        assert name not in promo, f"{name} must not remain in codegen_promo.toml"


def test_flags_header_used():
    """wc1.match takes the flags from each file's codegen-flags header (the
    PROMOTED results above are only reproducible with them)."""
    for src in PROMOTED:
        with open(path(src)) as fh:
            assert re.search(r"codegen-flags:", fh.read(2048)), src
