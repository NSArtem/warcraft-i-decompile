"""The content-verified caches behind symbols.load() / t4spec.load_lenient()
(parsed TOML files) and symbols.validate_ref_verified_by_entry() (AST findings of
cited T4 test files) must never be observable: every edit is seen at once, results
are never shared with a caller, and roots do not leak into each other."""
import ast
import glob
import os
import subprocess
import sys
import tomllib

import pytest

from wc1 import path, symbols, t4spec

REF = "src/demo/foo_reference.c"
NODE = "difftest: tests/test_t4.py::test_foo"
HONEST = """import os, pytest
from wc1 import t4spec

def helper(x):
    return x

def test_foo():
    t4spec.run_spec("%s", "Foo_", 0x1000, [])
    #PAD
""" % REF


def entry(addr, name, kind="func", extra=""):
    return f'[[{kind}]]\naddr = {addr:#x}\nname = "{name}"\nconfidence = "high"\nevidence = ["one", "two"]\n{extra}\n'


def overwrite_in_place(fn, text):
    """Same-size in-place overwrite that also restores the mtime: only the content differs."""
    st = os.stat(fn)
    data = text.encode()
    assert len(data) == st.st_size
    with open(fn, "r+b") as fh:
        fh.write(data)
    os.utime(fn, ns=(st.st_atime_ns, st.st_mtime_ns))
    after = os.stat(fn)
    assert (after.st_mtime_ns, after.st_size, after.st_ino) == (st.st_mtime_ns, st.st_size, st.st_ino)


@pytest.fixture
def db(tmp_path, monkeypatch):
    """A private repository root; returns its analysis/symbols directory."""
    d = tmp_path / "analysis" / "symbols"
    d.mkdir(parents=True)
    for mod in (symbols, t4spec):
        monkeypatch.setattr(mod, "path", lambda *p: os.path.join(str(tmp_path), *p))
    return d


def views():
    """{addr: name} of the functions, through both loaders."""
    strict = {a: e["name"] for a, e in symbols.load()[0].items()}
    lenient = {a: e["name"] for a, e in t4spec.load_lenient()[0].items()}
    assert strict == lenient
    return strict


# ------------------------------------------------------------------ TOML ---

def test_toml_add_modify_rename_delete_is_seen_at_once(db):
    (db / "a.toml").write_text(entry(0x100, "Aaa"))
    assert views() == {0x100: "Aaa"}
    (db / "b.toml").write_text(entry(0x200, "Bbb"))
    assert views() == {0x100: "Aaa", 0x200: "Bbb"}
    (db / "a.toml").write_text(entry(0x100, "Aaa") + entry(0x110, "Longer"))
    assert views() == {0x100: "Aaa", 0x110: "Longer", 0x200: "Bbb"}
    os.rename(db / "b.toml", db / "c.toml")
    assert views() == {0x100: "Aaa", 0x110: "Longer", 0x200: "Bbb"}
    assert symbols.load()[0][0x200]["_file"] == "analysis/symbols/c.toml"
    # a path reused by other content
    os.replace(db / "c.toml", db / "a.toml")
    assert views() == {0x200: "Bbb"}
    (db / "a.toml").unlink()
    assert views() == {}


def test_toml_rapid_same_size_overwrites_are_seen(db):
    f = db / "a.toml"
    f.write_text(entry(0x100, "Name000"))
    for i in range(50):
        overwrite_in_place(f, entry(0x100, f"Name{i:03d}"))
        assert views() == {0x100: f"Name{i:03d}"}


def test_returned_entries_are_never_shared(db):
    (db / "a.toml").write_text(
        entry(0x100, "Foo", extra='nested = [["x"], {k = ["y"]}]') + entry(0x900, "bar", "data"))
    pristine = symbols.load(), t4spec.load_lenient(), symbols.read_toml(db / "a.toml")
    for load in (symbols.load, t4spec.load_lenient):
        funcs, datas = load()[:2]
        for e in (funcs[0x100], datas[0x900]):
            e["evidence"].append("poison")
            e["name"] = "Poison"
            e["src"] = "src/poison.c"
        funcs[0x100]["nested"][0].append("poison")
        funcs[0x100]["nested"][1]["k"].clear()
        del funcs[0x100]["confidence"]
        funcs.clear()
    doc = symbols.read_toml(db / "a.toml")
    doc["func"][0]["evidence"].clear()
    doc["func"].clear()
    doc["data"][0]["addr"] = 1
    assert (symbols.load(), t4spec.load_lenient(), symbols.read_toml(db / "a.toml")) == pristine


def test_real_database_survives_a_hostile_caller():
    funcs, datas, errors = symbols.load()
    want = symbols.load()
    for t in (funcs, datas):
        for e in t.values():
            if isinstance(e["evidence"], list):
                e["evidence"].clear()
            e.clear()
    assert symbols.load() == want and not errors
    assert all(e["evidence"] for e in t4spec.load_lenient()[0].values())


def test_strict_and_lenient_semantics_of_a_broken_file(db):
    (db / "a.toml").write_text(entry(0x100, "Foo"))
    (db / "b.toml").write_text(entry(0x200, "Bar"))
    assert views() == {0x100: "Foo", 0x200: "Bar"}          # both files are cached now
    good = (db / "b.toml").read_text()
    broken = good.replace("addr = ", "addr   ")
    overwrite_in_place(db / "b.toml", broken)
    with pytest.raises(tomllib.TOMLDecodeError) as want:
        tomllib.loads(broken)
    for _ in range(2):                                      # errors are not cached away
        with pytest.raises(symbols.SymbolError) as ex:
            symbols.load()
        assert str(ex.value) == f"{db / 'b.toml'}: {want.value}"
        funcs, _, errors = symbols.load(strict=False)
        assert list(funcs) == [0x100] and errors == [f"{db / 'b.toml'}: {want.value}"]
        assert list(t4spec.load_lenient()[0]) == [0x100]
    overwrite_in_place(db / "b.toml", good)
    assert views() == {0x100: "Foo", 0x200: "Bar"}


def test_roots_are_isolated(tmp_path):
    for name in ("x", "y"):
        (tmp_path / name).mkdir()
        (tmp_path / name / "a.toml").write_text(entry(0x100, f"Root_{name}"))
    for _ in range(2):
        for name in ("x", "y"):
            assert symbols.load(root=str(tmp_path / name))[0][0x100]["name"] == f"Root_{name}"


def test_wc1_root_is_honoured(tmp_path):
    d = tmp_path / "analysis" / "symbols"
    d.mkdir(parents=True)
    (d / "a.toml").write_text(entry(0x100, "OtherRoot"))
    code = ("from wc1 import symbols\n"
            "f = symbols.load()[0]\n"
            "print({a: (e['name'], e['_file']) for a, e in f.items()})\n")
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True,
                         cwd=path("tools"), env=dict(os.environ, WC1_ROOT=str(tmp_path))).stdout
    assert ast.literal_eval(out) == {0x100: ("OtherRoot", "analysis/symbols/a.toml")}


def test_modules_file_edits_are_seen(tmp_path):
    f = tmp_path / "modules.toml"
    f.write_text('[[module]]\nstart = 0x100\nend = 0x200\nname = "AAA.C"\n')
    funcs = {0x150: {"_file": "t", "module": "AAA.C"}}
    assert symbols.check_modules(funcs, str(f)) == []
    overwrite_in_place(f, f.read_text().replace("AAA.C", "BBB.C"))
    assert "BBB.C" in symbols.check_modules(funcs, str(f))[0]


@pytest.mark.parametrize("ranges", [
    [(0x100, 0x200), (0x200, 0x300), (0x380, 0x400)],       # sorted, with a hole
    [(0x380, 0x400), (0x100, 0x200), (0x200, 0x300)],       # unsorted
    [(0x100, 0x300), (0x200, 0x400)],                       # overlapping: first in the file wins
    [(0x100, 0x100), (0x100, 0x200)],                       # empty range
    [],
])
def test_check_modules_finds_the_first_containing_range(tmp_path, ranges):
    f = tmp_path / "modules.toml"
    f.write_text("".join(f'[[module]]\nstart = {a}\nend = {b}\nname = "M{i}"\n'
                         for i, (a, b) in enumerate(ranges)))
    for a in (0, 0xFF, 0x100, 0x1FF, 0x200, 0x2FF, 0x300, 0x37F, 0x380, 0x3FF, 0x400):
        want = next((f"M{i}" for i, (lo, hi) in enumerate(ranges) if lo <= a < hi), None)
        errs = symbols.check_modules({a: {"_file": "t", "module": want or "?"}}, str(f))
        assert len(errs) == (want is None) and all("outside" in e for e in errs), (hex(a), errs)
        errs = symbols.check_modules({a: {"_file": "t", "module": "wrong"}}, str(f))
        assert len(errs) == 1 and (repr(want) in errs[0] if want else "outside" in errs[0])


# ------------------------------------------------------------- T4 tests' AST ---

def validate(root, rvb=NODE):
    return symbols.validate_ref_verified_by_entry(rvb, ref_rel=REF, repo_root=str(root))


def make_root(d, text=HONEST):
    (d / "tests").mkdir(parents=True)
    (d / "tests" / "test_t4.py").write_text(text)
    return d / "tests" / "test_t4.py"


@pytest.mark.parametrize("cheat, expect", [
    ("pytest.skip('x')", "pytest.skip() in test_foo"),
    ("pytest.xfail('x')", "pytest.xfail() in test_foo"),
    ("raise pytest.skip.Exception('x')", "forbidden raise"),
    ("t4spec.run_spec = print", "forbidden oracle monkeypatch"),
    ("setattr(t4spec, 'run_spec', print)", "forbidden oracle patch"),
    ("os.environ['WC1_T4_AUDIT_LOG']", "forbidden audit env tampering"),
    ("t4spec.cemu.record_t4_audit({})", "forbidden direct audit forging"),
    ("pytest.raises(AssertionError)", "forbidden pytest.raises"),
])
def test_same_size_test_edit_is_caught_at_once(tmp_path, cheat, expect):
    honest = HONEST.replace("#PAD", "#" + "p" * 60)
    f = make_root(tmp_path, honest)
    cheating = honest.replace("#" + "p" * 60, cheat.ljust(61))
    for _ in range(3):
        assert validate(tmp_path) == []
        overwrite_in_place(f, cheating)
        errs = validate(tmp_path)
        assert len(errs) == 1 and expect in errs[0], errs
        overwrite_in_place(f, honest)
    assert validate(tmp_path) == []


def test_same_size_edit_that_renames_or_breaks_the_node_is_caught(tmp_path):
    f = make_root(tmp_path)
    assert validate(tmp_path) == []
    overwrite_in_place(f, HONEST.replace("def test_foo", "def test_fop"))
    assert "not found" in validate(tmp_path)[0]
    overwrite_in_place(f, HONEST.replace("def test_foo()", "def test_foo(("))
    assert "failed to parse" in validate(tmp_path)[0]
    overwrite_in_place(f, HONEST.replace("foo_reference.c", "bar_reference.c"))
    assert "does not reference" in validate(tmp_path)[0]
    f.unlink()
    assert "does not exist" in validate(tmp_path)[0]
    f.write_text(HONEST)
    assert validate(tmp_path) == []


def test_repo_roots_do_not_share_test_verdicts(tmp_path):
    make_root(tmp_path / "good")
    make_root(tmp_path / "evil", HONEST.replace("#PAD", "pytest.skip('x')"))
    for _ in range(2):
        assert validate(tmp_path / "good") == []
        assert "pytest.skip" in validate(tmp_path / "evil")[0]
    # a reused temp path: same names, other content
    os.rename(tmp_path / "good", tmp_path / "moved")
    os.rename(tmp_path / "evil", tmp_path / "good")
    assert "pytest.skip" in validate(tmp_path / "good")[0]
    assert validate(tmp_path / "moved") == []


def test_returned_error_lists_are_not_shared(tmp_path):
    make_root(tmp_path, HONEST.replace("#PAD", "pytest.skip('x')"))
    first = validate(tmp_path)
    want = list(first)
    first.append("poison")
    assert validate(tmp_path) == want


def test_verdicts_of_different_nodes_of_one_file_are_independent(tmp_path):
    make_root(tmp_path, HONEST + "\ndef test_bad():\n    pytest.skip('x')\n"
                                 "\nclass TestC:\n    def test_m(self):\n        helper(1)\n")
    for _ in range(2):
        assert validate(tmp_path) == []
        assert "pytest.skip() in test_bad" in validate(tmp_path, "difftest: tests/test_t4.py::test_bad")[0]
        assert validate(tmp_path, "difftest: tests/test_t4.py::TestC::test_m") == []
        assert "not found" in validate(tmp_path, "difftest: tests/test_t4.py::TestC::test_foo")[0]


def test_alias_chains_resolve_in_any_order():
    # each alias is bound before the one it depends on: needs the fixed point
    src = ("import pytest, functools\nfrom wc1 import cemu\n"
           "c = b\nb = a\na = pytest.raises\n"
           "go2 = go\ngo = functools.partial(cemu.run_pair, 1)\n"
           "def f():\n    s = pytest.skip\n    t = s\n")
    al = symbols._collect_skip_aliases(ast.parse(src))
    assert al["raises_fns"] == {"a", "b", "c"}
    assert al["oracle_fns"] == {"go", "go2"}
    assert al["skip_fns"] == {"s", "t"}


def test_walk_is_ast_walk_without_context_nodes():
    for f in sorted(glob.glob(path("tests", "*.py")))[::8]:
        with open(f, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        want = [n for n in ast.walk(tree) if not isinstance(n, ast.expr_context)]
        got = symbols._walk(tree)
        assert len(got) == len(want) and all(a is b for a, b in zip(got, want)), f
