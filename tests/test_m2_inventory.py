"""Tests for wc1.m2_inventory: narrative GROUP_META text and live reconciliation.

The pure test needs no original/install/war.exe; the integration test builds the
inventory from the live binary/symbol database (the same build_inventory() that
`python3 -m wc1.m2_inventory` uses) and re-checks its per-function overnight
classification against wc1.overnight.build_queue_with_needs_human(wave="all").
Counts and group membership are deliberately not pinned: they change as work
lands.
"""
import os
import re

import pytest

from wc1 import m2_inventory, overnight, path

HAVE_ORIGINAL = os.path.exists(path("original", "install", "war.exe"))
HAVE_WATCOM = bool(os.environ.get("WATCOM"))


def _group_text(group_id):
    meta = m2_inventory.GROUP_META[group_id]
    return "\n".join(str(v) for v in meta.values())


def test_group_meta_repository_paths_exist():
    """Every src/tools/analysis path named in GROUP_META still exists."""
    pat = re.compile(r"(?:src|tools|analysis)/[A-Za-z0-9_./-]+")
    missing = set()
    for group_id in m2_inventory.GROUP_META:
        for raw in pat.findall(_group_text(group_id)):
            # Trim sentence punctuation; a trailing slash is a directory.
            rel = raw.rstrip(".,;:")
            if not os.path.exists(path(rel)):
                missing.add((group_id, rel))
    assert not missing, sorted(missing)


def test_dg01_text_does_not_offer_a_wiring_candidate():
    """DG-01 is empty history: both members are resolved/reclassified."""
    text = _group_text("DG-01-immediate-zero-llm-wiring")
    assert "IntroOpSyncSound" in text
    assert "reclassified" in text.lower()
    assert "buildable" not in text.lower()
    assert "WaitInputOrTimeout" in text


def test_dg03_text_covers_both_shared_epilogue_variants():
    text = _group_text("DG-03-build-shared-epilogue-interior-jumps")
    assert "IntroOpSyncSound" in text
    assert "0x23170" in text


@pytest.mark.skipif(not (HAVE_ORIGINAL and HAVE_WATCOM),
                    reason="needs original/ (make extract) and $WATCOM (nix develop)")
def test_inventory_reconciles_with_overnight_classification():
    payload, _ = m2_inventory.build_inventory()
    items = payload["functions"]

    queue, needs_human = overnight.build_queue_with_needs_human(wave="all")
    queued = {a for it in queue for a in it["addrs"]}
    needs_human_addrs = {nh["addr"] for nh in needs_human}
    skip = set(overnight.DEFAULT_SKIP)

    for it in items:
        st = it["overnight_default_status"]
        a = it["addr"]
        if st.startswith("eligible:"):
            assert a in queued, (it["addr_hex"], st, "not in the overnight queue")
            assert a not in needs_human_addrs, (it["addr_hex"], "eligible but needs_human")
        elif st.startswith("needs_human:"):
            assert a in needs_human_addrs, (it["addr_hex"], st, "not in needs_human")
            assert a not in queued, (it["addr_hex"], "needs_human but queued")
        elif st.startswith("skipped_default:"):
            assert it["module"] in skip, (it["addr_hex"], st)
            assert a not in queued
            assert a not in needs_human_addrs
        else:
            pytest.fail(f"{it['addr_hex']}: unexpected overnight status {st!r}")

    # Every C file the inventory names still exists.
    for it in items:
        for key in ("src_file", "ref_file", "matched_unbuilt_file"):
            rel = it.get(key)
            if rel:
                assert os.path.exists(path(rel)), (it["addr_hex"], key, rel)
