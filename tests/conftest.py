"""Scheduling heuristic only: hand out the slowest tests first, spread over the workers.

Nothing is added, dropped, skipped or renamed; without xdist (or with one worker)
the order is untouched.  A slow test that ends up last keeps one worker busy while
the others idle, so the lists should be refreshed from `pytest --durations` now and
then; a stale entry costs time, never correctness.

The collection order is arranged for the first chunks that pytest-xdist's default
scheduler (--dist=load) deals.  It is a starting point, not a limit: which worker gets
which test after that depends on how fast each one is, and --maxschedchunk, another
--dist mode or another xdist version deal differently.  No test may rely on it, neither
on what runs beside it nor on what ran before it.

Do not list tests that measure wall-clock time (test_overnight's stall watchdog,
test_batch_driver's run_capped, test_tui): they would start beside the heaviest load."""

# Disposable-repository tests (nodeid prefixes below tests/, longest first).  Each is
# a whole pipeline run with its own Wine prefix, so their first chunks go to workers * 3/10
# of the workers: all 12 started together starve everything else.  (Nothing enforces that
# later on; with the default scheduler the rest of a chunk stays with its worker.)
PIPELINES = (
    "test_wave4a_end_to_end.py::test_wave4a_reconciled",
    "test_wave4_fingerprints_e2e.py::test_real_project_wave4a",
    "test_wave4a_end_to_end.py",
    "test_wave4_end_to_end.py",
    "test_wave4_fingerprints_e2e.py",
)
# CPU-bound tests, longest first: one per remaining worker.
SLOW = (
    "test_resources_lzss.py::test_original_decoder_matches_python",
    "test_roundtrip.py::test_fallback",
    "test_analysis_cache.py::test_c",
    "test_emit_replaced.py",
    "test_resources_lzss.py::test_chunked",
    "test_roundtrip.py::test_converged",
)


def _ranked(nodeids, prefixes):
    """Indices of the ids that start with one of `prefixes`, in prefix order."""
    out = []
    for i, nodeid in enumerate(nodeids):
        name = nodeid.rsplit("tests/", 1)[-1]
        r = next((r for r, p in enumerate(prefixes) if name.startswith(p)), None)
        if r is not None:
            out.append((r, i))
    return [i for _, i in sorted(out)]


def _deal(indices, hands):
    """Back and forth over the hands, so the longest pair with the shortest."""
    for k, i in enumerate(indices):
        turn, w = divmod(k, len(hands))
        hands[w if turn % 2 == 0 else -1 - w].append(i)


def schedule(nodeids, workers):
    """A permutation of range(len(nodeids)).  xdist (--dist=load, no --maxschedchunk)
    first sends each worker `chunk` consecutive tests (its LoadScheduling.schedule
    formula; if that ever changes, only the balance suffers): the slow tests are dealt
    to the fronts of those initial chunks, each worker keeping collection order, and
    everything else follows in collection order."""
    if workers < 2:
        return list(range(len(nodeids)))
    chunk = max(len(nodeids) // workers // 4, 2)
    hands = [[] for _ in range(workers)]
    few = max(workers * 3 // 10, 1)
    _deal(_ranked(nodeids, PIPELINES), hands[:few])
    _deal(_ranked(nodeids, SLOW), hands[few:])
    hands = [sorted(h[:chunk]) for h in hands]
    dealt = {i for h in hands for i in h}
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
