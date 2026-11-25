"""tests/conftest.py only reorders: same tests, deterministic, each worker keeps
every module's own order, few pipeline tests at once."""
import pytest

import conftest

PIPE = [f"tests/{conftest.PIPELINES[2]}::test_{i}" for i in range(4)] + \
       [f"tests/{conftest.PIPELINES[3]}::test_{i}" for i in range(6)]
SLOW = [f"tests/{conftest.SLOW[0]}[{i}]" for i in range(2)] + \
       [f"tests/{conftest.SLOW[3]}::test_{i}" for i in range(3)]
IDS = ([f"tests/test_a{m}.py::test_{i}" for m in range(40) for i in range(20)]
       + SLOW + PIPE
       + [f"tests/test_z{m}.py::test_{i}" for m in range(40) for i in range(20)])


@pytest.mark.parametrize("workers", [0, 1, 2, 3, 12, 16, 20, 64, 5000])
@pytest.mark.parametrize("ids", [IDS, IDS[:1], [], IDS[798:818], IDS[::-1], PIPE], ids=range(6))
def test_schedule_is_a_deterministic_permutation(ids, workers):
    order = conftest.schedule(ids, workers)
    assert sorted(order) == list(range(len(ids)))
    assert order == conftest.schedule(list(ids), workers)
    if workers < 2:
        assert order == list(range(len(ids)))


@pytest.mark.parametrize("workers", [2, 8, 12, 16, 20])
def test_slow_tests_start_first_on_bounded_workers(workers):
    order = conftest.schedule(IDS, workers)
    chunk = max(len(IDS) // workers // 4, 2)
    chunks = [order[w * chunk:(w + 1) * chunk] for w in range(workers)]
    few = max(workers * 3 // 10, 1)
    pipe = [sum(IDS[i] in PIPE for i in c) for c in chunks]
    slow = [sum(IDS[i] in SLOW for i in c) for c in chunks]
    # every slow test is in some worker's first chunk, pipelines on `few` workers only
    assert sum(pipe) == len(PIPE) and sum(slow) == len(SLOW)
    assert not any(pipe[few:]) and not any(slow[:few])
    assert max(pipe[:few]) - min(pipe[:few]) <= 1
    for c, n, m in zip(chunks, pipe, slow):
        assert all(IDS[i] in PIPE + SLOW for i in c[:n + m])    # at the front
        assert c[:n + m] == sorted(c[:n + m])                   # in collection order
    # all other tests stay in collection order throughout
    rest = [i for i in order if IDS[i] not in PIPE + SLOW]
    assert rest == sorted(rest)


def test_entries_name_existing_test_files(request):
    for p in conftest.PIPELINES + conftest.SLOW:
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
