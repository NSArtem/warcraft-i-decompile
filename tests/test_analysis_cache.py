"""The analysis.run() result cache (build/cache/analysis-*.pickle) must give
exactly what a fresh discovery gives."""
from array import array
import hashlib
import os
import pickle
import shutil
import subprocess
import sys

import pytest
import wave4_repo
import wc1
from wave4_repo import seed_analysis_cache
from wc1 import analysis, emit, insns, path, symbols


def _fingerprint(p):
    return {
        "func_starts": list(p.func_starts),
        "functions": p.functions,
        "owner": dict(p.owner),
        "table_bytes": set(p.table_bytes),
        "jump_tables": dict(p.jump_tables),
        "call_targets": set(p.call_targets),
        "jump_targets": set(p.jump_targets),
        "ptr_targets": {k: set(v) for k, v in p.ptr_targets.items()},
        "conflicts": list(p.conflicts),
        "seed_kind": dict(p.seed_kind),
        "gaps": p.gaps(),
        "insns": sorted(p.insns),
    }


def _operand(o):
    return (o.type, o.size, o.access, o.avx_bcast, o.avx_zero_opmask, o.reg, o.imm,
            o.value.reg, o.value.imm) + tuple(
        (m.segment, m.base, m.index, m.scale, m.disp) for m in (o.mem, o.value.mem))


def _assert_same_instructions(fresh, cached):
    """Every stored attribute of every instruction (the records against capstone's own)."""
    assert list(cached.insns) == list(fresh.insns)          # the order too
    regs = {0}
    for a, f in fresh.insns.items():
        c = cached.insns[a]
        assert (c.address, c.size, c.bytes, c.mnemonic, c.op_str) == \
               (f.address, f.size, f.bytes, f.mnemonic, f.op_str)
        assert (c.disp_offset, c.disp_size, c.imm_offset, c.imm_size) == \
               (f.disp_offset, f.disp_size, f.imm_offset, f.imm_size), hex(a)
        assert [_operand(o) for o in c.operands] == [_operand(o) for o in f.operands], hex(a)
        for o in f.operands:
            regs |= {o.reg, o.mem.segment, o.mem.base, o.mem.index}
    i, j = cached.insns[fresh.le.entry], fresh.insns[fresh.le.entry]
    for r in regs | set(range(300)):                        # with the union's non-registers
        if r < 1 << 31:
            assert (i.reg_name(r), i.reg_name(r, "x")) == (j.reg_name(r), j.reg_name(r, "x")), r


def _assert_same_emission(fresh, cached, tmp_path):
    """The emitter writes the same bytes from either program."""
    names = symbols.label_map()
    with open(path("analysis", "raw_insns.txt")) as fh:
        force = {int(l.split()[0], 16) for l in fh if not l.startswith("#")}
    code, data = fresh.le.obj(1), fresh.le.obj(2)
    funcs = sorted(fresh.functions, key=lambda f: f["start"])
    starts = {f["start"] for f in funcs}
    cuts = {f["start"]: f["limit"] for f in funcs[40::25]
            if not emit.replaced_interior_refs(fresh, [(f["start"], f["limit"])], starts)}
    assert len(cuts) > 30
    edges = [code.base, *(x for s in sorted(cuts) for x in (s, cuts[s])), code.end]
    pieces = [list(x) if x[0] < x[1] else None for x in zip(edges[::2], edges[1::2])]
    data_pieces = [[data.base, data.end]] + [None] * (len(pieces) - 1)

    def written(p, name):
        d = tmp_path / name
        d.mkdir()
        lines = []

        def emitter(**kw):
            lines.append(emit.Emitter(p, **kw))
            return lines[-1]
        emitter(names=names, force_raw=force).emit(d / "rt.asm")
        emitter().emit(d / "unnamed.asm")                           # no name, nothing raw
        emitter(force_raw=set(p.insns)).emit(d / "raw.asm")         # everything raw
        emitter(names=names, force_raw=force, replaced=sorted(cuts)[:20]).emit(d / "replaced.asm")
        emitter(names=names, force_raw=force, cuts=cuts).emit_pieces(str(d), pieces, data_pieces)
        return {f.name: f.read_bytes() for f in d.iterdir()}, [e.line_addr for e in lines]

    want, lines = written(fresh, "fresh")
    assert len(want) == 4 + len(pieces) and all(lines[:4])
    got, got_lines = written(cached, "cached")
    assert got.keys() == want.keys() and [f for f in want if got[f] != want[f]] == []
    assert got_lines == lines
    every = [(f["start"], f["limit"]) for f in funcs]
    for ranges in (every, every[::7], sorted(every[::150] * 2)):    # the last: overlapping, a linear scan
        for entries in (starts, set()):
            assert emit.replaced_interior_refs(cached, ranges, entries) == \
                emit.replaced_interior_refs(fresh, ranges, entries)
    assert emit.replaced_interior_refs(fresh, every, set())


def test_cached_run_equals_fresh_run(tmp_path, monkeypatch):
    # one fresh discovery for all of it (5 s)
    fresh = analysis.run(cache=False)
    cached = analysis.run(cache=True)          # load or create
    again = analysis.run(cache=True)           # certainly a load now
    assert _fingerprint(cached) == _fingerprint(fresh)
    assert _fingerprint(again) == _fingerprint(fresh)
    assert type(next(iter(fresh.insns.values()))).__module__.startswith("capstone")
    assert 0x10000 - 1 not in again.insns and again.insns.get(-1) is None

    # no instruction is decoded again for any of this
    def decode(self, a):
        raise AssertionError(f"{a:#x} decoded")
    monkeypatch.setattr(analysis.Program, "insn_at", decode)
    _assert_same_instructions(fresh, again)
    _assert_same_emission(fresh, again, tmp_path)


def test_each_call_returns_a_fresh_object():
    a, b = analysis.run(), analysis.run()
    assert a is not b and a.functions is not b.functions


def test_key_follows_the_inputs(monkeypatch):
    k = analysis._cache_key(None)
    assert analysis._cache_key(None) == k
    monkeypatch.setattr(analysis, "_CACHE_FORMAT", analysis._CACHE_FORMAT + 1)
    assert analysis._cache_key(None) not in (k, None)


@pytest.fixture(scope="module")
def warm():
    return analysis.run()


@pytest.fixture
def known_tool(monkeypatch):
    """The stubs of a test are not a changed tool (see test_loaded for that)."""
    tool = analysis._tool_identity()
    monkeypatch.setattr(analysis, "_tool_identity", lambda: tool)


@pytest.fixture
def private_root(tmp_path, monkeypatch):
    """WC1_ROOT is a copy with the same modules.toml (so the same key) and its own cache."""
    with open(path("analysis", "modules.toml"), "rb") as fh:
        content = fh.read()
    (tmp_path / "analysis").mkdir()
    (tmp_path / "analysis" / "modules.toml").write_bytes(content)
    monkeypatch.setattr(wc1, "ROOT", str(tmp_path))
    return tmp_path


def test_corrupt_cache_file_is_recomputed(warm, private_root):
    good = warm
    f = private_root / "build" / "cache" / f"analysis-{analysis._cache_key(None)}.pickle"
    f.parent.mkdir(parents=True)
    f.write_bytes(b"not a pickle")
    assert _fingerprint(analysis.run()) == _fingerprint(good)
    assert _fingerprint(analysis._load(f)) == _fingerprint(good)


def _sealed(body):
    return body + hashlib.sha256(body).digest()


def _flip(b, at):
    b = bytearray(b)
    b[at] ^= 1
    return bytes(b)


def _repacked(change):
    """A cache file with a changed instruction state: valid otherwise."""
    def damage(body, p, m):
        pack = insns.pack
        m.setattr(insns, "pack", lambda i: change(*pack(i)))
        return _sealed(pickle.dumps(p, protocol=pickle.HIGHEST_PROTOCOL))
    return damage


def _redigested(**change):
    """The same with one part of the state changed; both checksums fit."""
    names = ("addrs", "which", "numbers", "text", "refs", "operands")

    def repacked(*state):
        parts = dict(zip(names, state))
        parts |= {k: f(parts[k]) for k, f in change.items()}
        return *parts.values(), insns._digest(*parts.values())
    return _repacked(repacked)


def _items(damage):
    """`damage` applied to the raw bytes of an array."""
    def f(a):
        raw = damage(a.tobytes())
        return array(a.typecode, raw[:len(raw) // a.itemsize * a.itemsize])
    return f


def _garbage(raw):
    return b"not a table " * (len(raw) // 12)


def _format_4(addrs, which, *tables):
    """The format before: the tables as a nested pickle, which a hit did not look into."""
    payload = b"not a pickle"
    h = hashlib.sha256(f"{len(addrs)} {len(which)} {max(which) + 1} {len(payload)} ".encode())
    for part in (addrs, which, payload):
        h.update(part)
    return addrs, which, max(which) + 1, payload, h.digest()


DAMAGE = {
    "empty": lambda body, p, m: b"",
    "truncated": lambda body, p, m: _sealed(body)[:-100],
    "no checksum": lambda body, p, m: body,
    "flipped bit": lambda body, p, m: _flip(_sealed(body), len(body) // 2),
    "flipped checksum": lambda body, p, m: _flip(_sealed(body), -1),
    # the checksum of the file fits
    "garbage": lambda body, p, m: _sealed(b"not a pickle"),
    "short": lambda body, p, m: _sealed(body[:-100]),
    "unsupported protocol": lambda body, p, m: _sealed(b"\x80\xff" + body[2:]),           # ValueError
    "missing class": lambda body, p, m: _sealed(body.replace(b"Program", b"Prograd", 1)),
    "missing module": lambda body, p, m: _sealed(body.replace(b"wc1.analysis", b"wc1.analysid", 1)),
    "other object": lambda body, p, m: _sealed(pickle.dumps({"functions": []})),
    "no instructions": lambda body, p, m: _sealed(pickle.dumps(p).replace(b"\x8c\x05insns", b"\x8c\x05insnz", 1)),    # KeyError
    "no state": _repacked(lambda *s: None),
    "old state": _repacked(_format_4),
    "fewer parts": _repacked(lambda *s: s[:2] + s[3:]),
    "numbers": _repacked(lambda *s: (*s[:2], _flip(s[2], len(s[2]) // 2), *s[3:])),
    # the checksum of the state fits too
    "numbers garbage": _redigested(numbers=_garbage),
    "numbers short": _redigested(numbers=lambda n: n[:-1]),
    "numbers of one shape less": _redigested(numbers=lambda n: n[:-insns.SHAPE]),
    "text garbage": _redigested(text=lambda t: "not a table"),
    "text of one shape less": _redigested(text=lambda t: t.rsplit("\n", 2)[0]),
    "one shape less": _redigested(numbers=lambda n: n[:-insns.SHAPE], text=lambda t: t.rsplit("\n", 2)[0]),
    "refs garbage": _redigested(refs=_items(_garbage)),
    "one ref less": _redigested(refs=lambda r: r[:-1]),
    "operands garbage": _redigested(operands=_items(_garbage)),
    "one operand less": _redigested(operands=lambda o: o[:-insns.OPERAND]),
    "fewer shape indices": _redigested(which=lambda w: w[:-1]),
    "shape index garbage": _redigested(which=_items(_garbage)),
    "fewer addresses": _redigested(addrs=lambda a: a[:-1]),
    "no addresses": _redigested(addrs=lambda a: a[:0], which=lambda w: w[:0]),
    "addresses garbage": _redigested(addrs=_items(_garbage)),
    "shape out of range": _redigested(which=lambda w: w[:-1] + array("I", [max(w) + 1])),
}


@pytest.mark.parametrize("damage", DAMAGE.values(), ids=DAMAGE)
def test_damage_is_a_miss(warm, private_root, known_tool, monkeypatch, damage):
    """Whatever the file holds: run() discovers again and replaces it."""
    good = warm
    f = private_root / "build" / "cache" / f"analysis-{analysis._cache_key(None)}.pickle"
    body = pickle.dumps(good, protocol=pickle.HIGHEST_PROTOCOL)
    f.parent.mkdir(parents=True)
    with monkeypatch.context() as m:
        bad = damage(body, good, m)
    f.write_bytes(bad)
    with pytest.raises(Exception):
        analysis._load(f)
    discoveries = []
    monkeypatch.setattr(analysis.Program, "discover", lambda self: discoveries.append(1) or good)
    monkeypatch.setattr(analysis.Program, "partition", lambda self: self)
    p = analysis.run()
    assert p is good and discoveries == [1]
    assert f.read_bytes() == _sealed(body) != bad and os.listdir(f.parent) == [f.name]
    again = analysis.run()
    assert discoveries == [1] and again.insns[again.le.entry].mnemonic == good.insns[good.le.entry].mnemonic


def test_modules_edit_in_one_process_equals_fresh_discovery(tmp_path, known_tool, monkeypatch):
    """The module kinds come from the bytes the key was computed from: a run without
    modules.toml leaves nothing behind for a run with it (or the other way round)."""
    # decoding depends on the executable only: share it between the discoveries
    real, memo = analysis.Program.insn_at, {}

    def insn_at(self, a):
        if a not in memo:
            memo[a] = real(self, a)
        return memo[a]
    monkeypatch.setattr(analysis.Program, "insn_at", insn_at)
    want = analysis.run(cache=False)
    with open(path("analysis", "modules.toml"), "rb") as fh:
        content = fh.read()
    monkeypatch.setattr(wc1, "ROOT", str(tmp_path))
    modules = tmp_path / "analysis" / "modules.toml"
    modules.parent.mkdir()

    absent_key = analysis._cache_key(None)
    absent = analysis.run()                         # cold, and cached under absent_key
    assert {0x38AA8, 0x38ADE} & set(absent.func_starts) == set()
    assert absent.module_kind(0x38AA8) == "game"

    modules.write_bytes(content)
    assert analysis._cache_key(None) != absent_key
    present = analysis.run()                        # cold again
    assert {0x38AA8, 0x38ADE} <= set(present.func_starts)
    assert len(present.func_starts) == len(absent.func_starts) + 2
    assert _fingerprint(present) == _fingerprint(want)
    assert _fingerprint(analysis.run()) == _fingerprint(want)      # what was written to the cache

    modules.unlink()
    assert analysis._cache_key(None) == absent_key
    assert _fingerprint(analysis.run()) == _fingerprint(absent)
    assert len(os.listdir(tmp_path / "build" / "cache")) == 2


def test_inputs_are_read_once_per_run(tmp_path, known_tool, monkeypatch):
    """An edit between the key and discovery cannot split them."""
    root = tmp_path
    f = _inputs(root, b"[[module]]\nstart = 1\nend = 9\nkind = 'ail'\n", b"exe")
    monkeypatch.setattr(wc1, "ROOT", str(root))
    key, seen = analysis._cache_key(f), []

    class Prog:
        def __init__(self, exe, modules, raw):
            (root / "analysis" / "modules.toml").write_bytes(b"")     # too late
            (root / "war.exe").write_bytes(b"")
            seen.append((analysis._module_kinds(modules), raw))

        def discover(self):
            return self

        def partition(self):
            return {"func_starts": []}
    real = analysis._cache_key

    def key_then_edit(*a):
        k = real(*a)
        (root / "analysis" / "modules.toml").write_bytes(b"# edited\n")
        (root / "war.exe").write_bytes(b"another")
        return k
    monkeypatch.setattr(analysis, "Program", Prog)
    monkeypatch.setattr(analysis, "_cache_key", key_then_edit)
    analysis.run(f)
    assert seen == [([(1, 9, "ail")], b"exe")]
    assert os.listdir(root / "build" / "cache") == [f"analysis-{key}.pickle"]


@pytest.mark.parametrize("when", ["before the key", "after the key", "in discovery"])
def test_the_cached_program_is_that_of_the_hashed_executable(private_root, known_tool, monkeypatch, when):
    """The executable is replaced (a data byte changes) at any time during a cold run."""
    with open(wc1.ORIGINAL_EXE, "rb") as fh:
        a = fh.read()
    b = bytearray(a)
    b[-1000] ^= 1                                   # the same code, other data
    exe, b = private_root / "war.exe", bytes(b)
    exe.write_bytes(a)
    key_a, key_b = analysis._cache_key(str(exe), raw=a), analysis._cache_key(str(exe), raw=b)
    assert key_a == analysis._cache_key(str(exe)) != key_b
    real_key, real_open, opened = analysis._cache_key, open, []

    def swap_at(moment):
        if moment == when:
            exe.write_bytes(b)

    def cache_key(*args):
        swap_at("before the key")
        k = real_key(*args)
        swap_at("after the key")
        return k

    def discover(self):                             # enough of one
        swap_at("in discovery")
        self.insns = {self.le.entry: self.insn_at(self.le.entry)}
        return self
    monkeypatch.setattr(analysis, "_cache_key", cache_key)
    monkeypatch.setattr(analysis.Program, "discover", discover)
    monkeypatch.setattr(analysis.Program, "partition", lambda self: self)

    def counting(f, *args, **kw):
        if str(f) == str(exe):
            opened.append(f)
        return real_open(f, *args, **kw)
    monkeypatch.setattr("builtins.open", counting)
    p = analysis.run(str(exe))
    assert len(opened) == 1
    monkeypatch.setattr("builtins.open", real_open)
    assert exe.read_bytes() == b
    cache = private_root / "build" / "cache"
    assert os.listdir(cache) == [f"analysis-{key_a}.pickle"]
    stored = analysis._load(cache / f"analysis-{key_a}.pickle")
    for q in (p, stored):
        assert q.le.raw == a and q.data.data == analysis.lefmt.LE(a).obj(2).data
    q = analysis.run(str(exe))                      # now it is the other one
    assert q.le.raw == b and sorted(os.listdir(cache)) == sorted(f"analysis-{k}.pickle" for k in (key_a, key_b))


@pytest.mark.parametrize("content, kinds", [
    (b"", []),
    (b"not toml [", []),
    (b"[[module]]\nstart = 5\nend = 6\n[[module]]\nstart = 1\nend = 5\nkind = 'asm'\n",
     [(1, 5, "asm"), (5, 6, "game")]),
])
def test_module_kinds_of_content(content, kinds):
    assert analysis._module_kinds(content) == kinds


def _inputs(root, modules, exe):
    (root / "analysis").mkdir(parents=True)
    (root / "analysis" / "modules.toml").write_bytes(modules)
    (root / "war.exe").write_bytes(exe)
    return str(root / "war.exe")


def test_key_is_content_addressed(tmp_path, monkeypatch):
    """Same inputs at two paths: one key; any changed input: another key."""
    def key(name, modules, exe):
        root = tmp_path / name
        f = _inputs(root, modules, exe)
        with monkeypatch.context() as m:
            m.setattr(wc1, "ROOT", str(root))
            return analysis._cache_key(f)

    k = key("a", b"modules", b"exe")
    assert key("a_much_longer_name", b"modules", b"exe") == k
    assert len({k, key("c", b"modulez", b"exe"), key("d", b"modules", b"exf"),
                key("e", b"exe", b"modules"), key("f", b"", b"exe")}) == 5
    # the tool and the runtime versions are inputs too
    with monkeypatch.context() as m:
        m.setattr(analysis.capstone, "__version__", "0")
        assert key("g", b"modules", b"exe") != k
    monkeypatch.setattr(analysis, "_tool_identity", lambda: b"another version")
    assert key("h", b"modules", b"exe") not in (k, None)


def test_real_key_does_not_depend_on_where_the_inputs_are(tmp_path, monkeypatch):
    k = analysis._cache_key(None)
    with open(path("analysis", "modules.toml"), "rb") as m, open(wc1.ORIGINAL_EXE, "rb") as e:
        f = _inputs(tmp_path / "copy", m.read(), e.read())
    monkeypatch.setattr(wc1, "ROOT", str(tmp_path / "copy"))
    assert analysis._cache_key(f) == k
    with open(f, "ab") as fh:
        fh.write(b"\0")
    assert analysis._cache_key(f) != k


def test_seeded_cache_file_is_used_only_for_identical_inputs(tmp_path):
    analysis.run()                             # makes sure the parent has the file
    repo = tmp_path / "repo"
    _inputs(repo, b"", b"")
    (repo / "original" / "install").mkdir(parents=True)
    (repo / "original" / "install" / "war.exe").symlink_to(wc1.ORIGINAL_EXE)
    modules = repo / "analysis" / "modules.toml"
    assert not seed_analysis_cache(repo) and not (repo / "build").exists()   # other modules.toml
    with open(path("analysis", "modules.toml"), "rb") as fh:
        modules.write_bytes(fh.read())
    assert seed_analysis_cache(repo)

    code = ("import sys\nfrom wc1 import analysis\n"
            "def cold(*a): raise SystemExit('cold discovery')\n"
            "analysis.capstone.Cs.disasm = cold\n"     # not a part of the tool: the key stays
            "print(len(analysis.run().functions))\n")

    def child():
        return subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                              env=dict(os.environ, WC1_ROOT=str(repo)), cwd=path("tools"))
    r = child()
    assert r.returncode == 0 and int(r.stdout) == len(analysis.run().functions), r.stderr
    with open(modules, "ab") as fh:            # the child's own inputs changed
        fh.write(b"\n# edited\n")
    r = child()
    assert r.returncode != 0 and "cold discovery" in r.stderr, r.stdout + r.stderr


def test_repo_base_is_a_writable_exec_directory_with_room(tmp_path, monkeypatch):
    old = "/tmp/opencode" if os.path.isdir("/tmp/opencode") else "/tmp"
    assert wave4_repo.repo_base(str(tmp_path / "missing")) == old
    assert os.access(wave4_repo.repo_base(), os.W_OK | os.X_OK)
    monkeypatch.setattr(wave4_repo, "NEED", 0)
    assert wave4_repo.repo_base(str(tmp_path)) == str(tmp_path)
    monkeypatch.setattr(wave4_repo, "NEED", 1 << 60)         # no room
    assert wave4_repo.repo_base(str(tmp_path)) == old


def test_disposable_repo_survives_a_late_writer(monkeypatch):
    """A process that still writes while the repository is removed (a wineserver
    flushing its registry) only delays the removal."""
    real, calls = shutil.rmtree, []

    def rmtree(d):
        calls.append(d)
        if len(calls) == 1:
            raise OSError(39, "Directory not empty")
        real(d)
    monkeypatch.setattr(wave4_repo.shutil, "rmtree", rmtree)
    with pytest.raises(ZeroDivisionError):         # also when the test failed
        with wave4_repo.disposable_repo("w4t-") as repo:
            (repo / "build/wine").mkdir(parents=True)
            1 / 0
    assert len(calls) == 2 and not repo.exists()
