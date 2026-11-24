"""tests/conftest.py only reorders: same tests, deterministic, each worker keeps
every module's own order."""
import itertools

import pytest

import conftest

SLOW_MODULE = conftest.SLOW[0]
IDS = ([f"tests/test_a{m}.py::test_{i}" for m in range(40) for i in range(20)]
       + [f"tests/{SLOW_MODULE}::test_{i}" for i in range(6)]
       + [f"tests/{conftest.SLOW[2]}::test_{i}" for i in range(6)]
       + [f"tests/test_z{m}.py::test_{i}" for m in range(40) for i in range(20)])


@pytest.mark.parametrize("workers", [0, 1, 2, 3, 12, 16, 20, 64, 5000])
@pytest.mark.parametrize("ids", [IDS, IDS[:1], [], IDS[798:815], IDS[::-1]], ids=range(5))
def test_schedule_is_a_deterministic_permutation(ids, workers):
    order = conftest.schedule(ids, workers)
    assert sorted(order) == list(range(len(ids)))
    assert order == conftest.schedule(list(ids), workers)
    if workers < 2:
        assert order == list(range(len(ids)))


@pytest.mark.parametrize("workers", [2, 8, 12, 20])
def test_slow_tests_start_first_on_distinct_workers(workers):
    order = [IDS[i] for i in conftest.schedule(IDS, workers)]
    chunk = max(len(IDS) // workers // 4, 2)
    chunks = [order[w * chunk:(w + 1) * chunk] for w in range(workers)]
    slow = [i for i in IDS if conftest._rank(i) is not None]
    heads = [c[0] for c in chunks[:len(slow)]]
    assert heads == sorted(slow, key=conftest._rank)[:workers]
    # inside a worker's chunk every module keeps its collection order
    for c in chunks:
        for _, g in itertools.groupby(sorted(c, key=lambda n: n.split("::")[0]), lambda n: n.split("::")[0]):
            pos = [IDS.index(n) for n in g]
            assert pos == sorted(pos)
    # and the tests that are not slow stay in collection order throughout
    rest = [IDS.index(n) for n in order if conftest._rank(n) is None]
    assert rest == sorted(rest)


def test_entries_name_existing_test_files(request):
    for p in conftest.SLOW:
        assert (request.path.parent / p.split("::")[0]).is_file(), p


def test_the_hook_keeps_the_collection():
    class Item:
        def __init__(self, nodeid):
            self.nodeid = nodeid

    class Config:
        workerinput = {"workercount": 20}

    items = [Item(i) for i in IDS]
    before = list(items)
    conftest.pytest_collection_modifyitems(Config, items)
    assert len(items) == len(before) and {id(i) for i in items} == {id(i) for i in before}
    assert items != before
    items = list(before)
    conftest.pytest_collection_modifyitems(object(), items)        # no xdist: untouched
    assert items == before
