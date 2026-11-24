"""Scheduling only: start the slowest tests first, one per xdist worker.

Nothing is added, dropped, skipped or renamed; without xdist (or with one worker)
the order is untouched.  A slow test that ends up last keeps one worker busy while
the others idle, so the list below should be refreshed from `pytest --durations`
now and then; a stale entry costs time, never correctness."""

# nodeid prefixes (below tests/), longest first
SLOW = (
    "test_wave4a_end_to_end.py",
    "test_wave4_fingerprints_e2e.py",
    "test_wave4_end_to_end.py",
    "test_resources_lzss.py::test_original_decoder_matches_python",
    "test_roundtrip.py",
    "test_overnight.py::test_stall_watchdog",
    "test_analysis_cache.py::test_c",
    "test_tui.py",
    "test_batch_driver.py::test_run_capped",
    "test_batch_driver.py::test_verify_t4_node",
    "test_batch_driver.py::test_build_check",
    "test_t4spec.py::test_t4spec_runtime_audit",
    "test_emit_replaced.py",
    "test_resources_lzss.py",
    "test_mod_2ced0_c6.py",
    "test_mod_1e9a0.py::test_fog_update_tile",
    "test_mod_20c30.py::test_reference_files",
    "test_overnight_wave4.py",
)


def _rank(nodeid):
    name = nodeid.rsplit("tests/", 1)[-1]
    return next((i for i, p in enumerate(SLOW) if name.startswith(p)), None)


def schedule(nodeids, workers):
    """A permutation of range(len(nodeids)).  xdist (--dist=load) first sends each
    worker `chunk` consecutive tests (its LoadScheduling.schedule formula; if that
    ever changes, only the balance suffers).  The slow tests are dealt round-robin
    (back and forth, so the longest pair with the shortest) to the fronts of those
    chunks; everything else follows in collection order."""
    if workers < 2:
        return list(range(len(nodeids)))
    chunk = max(len(nodeids) // workers // 4, 2)
    slow = [(r, i) for i, r in enumerate(map(_rank, nodeids)) if r is not None]
    slow = [i for _, i in sorted(slow)][:workers * chunk]
    hands = [[] for _ in range(workers)]
    for k, i in enumerate(slow):
        turn, w = divmod(k, workers)
        hands[w if turn % 2 == 0 else workers - 1 - w].append(i)
    dealt = set(slow)
    rest = [i for i in range(len(nodeids)) if i not in dealt]
    order = []
    for hand in hands:
        fill = chunk - len(hand)
        order += hand + rest[:fill]
        del rest[:fill]
    return order + rest


def pytest_collection_modifyitems(config, items):
    workers = getattr(config, "workerinput", {}).get("workercount", 1)
    items[:] = [items[i] for i in schedule([it.nodeid for it in items], workers)]
