"""wc1.loaded: the analysis cache key names the code this process runs, not the files
on disk, and there is no key when what runs is not what was loaded."""
import copy
import inspect
import os
import pickle
import subprocess
import sys
import types

import pytest
import wc1
from wc1 import analysis, insns, le, loaded, path

MODULES = ("__init__", "le", "insns", "loaded", "analysis")


@pytest.fixture
def tree(tmp_path):
    """A private copy of the tool; tree.run(code, *args) runs `code` in a fresh process on it."""
    d = tmp_path / "tools" / "wc1"
    d.mkdir(parents=True)
    for m in MODULES:
        with open(path("tools", "wc1", m + ".py")) as fh:
            (d / f"{m}.py").write_text(fh.read())
    (tmp_path / "war.exe").write_bytes(b"exe")

    def run(code, *flags, **env):
        r = subprocess.run([sys.executable, *flags, "-c", "import os, sys\n" + code], cwd=tmp_path,
                           capture_output=True, text=True,
                           env=dict(os.environ, WC1_ROOT=str(tmp_path), PYTHONPATH=str(d.parent), **env))
        assert r.returncode == 0, r.stderr
        return r.stdout.strip()

    def edit(module, old, new):
        f = d / f"{module}.py"
        text = f.read_text()
        assert text.count(old) >= 1
        f.write_text(text.replace(old, new, 1))
        edits.append(f)                     # a later mtime: not taken for what the .pyc is of
        os.utime(f, (T0 + len(edits),) * 2)
    edits = []
    return types.SimpleNamespace(root=tmp_path, d=d, run=run, edit=edit)


T0 = 1_000_000_000
KEY = "from wc1 import analysis\nprint(analysis._cache_key('war.exe'))\n"


def test_the_identity_is_the_same_in_every_process(tree, tmp_path):
    """Any hash seed; compiled or from a .pyc; traced; another directory."""
    here = analysis._tool_identity().hex()
    code = "from wc1 import analysis\nprint(analysis._tool_identity().hex())\n"
    trace = "sys.settrace(lambda *a: None)\n"
    monitor = ("m = sys.monitoring\nm.use_tool_id(1, 'x')\n"
               "m.register_callback(1, m.events.LINE, lambda *a: None)\n"
               "m.set_events(1, m.events.LINE | m.events.PY_START)\n")
    got = [tree.run(code, PYTHONHASHSEED="1"),                       # writes the .pyc files
           tree.run(code, PYTHONHASHSEED="2"),                       # loads them
           tree.run(code, "-B", PYTHONHASHSEED="3", PYTHONPYCACHEPREFIX=str(tmp_path / "none")),
           tree.run(trace + code), tree.run(monitor + code),
           tree.run("import wc1.le\n" + code),
           tree.run("from wc1 import insns, le, loaded\n" + code)]
    assert got == [here] * len(got)


def test_using_the_tool_does_not_change_it():
    k = analysis._cache_key(None)
    assert k is not None
    p = analysis.run()
    q = copy.deepcopy(pickle.loads(pickle.dumps(p)))
    i = q.insns[q.le.entry]
    copy.copy(i), pickle.loads(pickle.dumps(copy.copy(q.le.objects[0]))), repr(q.le.fixups[0])
    i.reg_name(19), i.operands, i.id, q.to_json(), q.le.read(q.le.entry, 4)
    for c in (le.LE, le.Obj, le.Fixup, insns.Insn, insns.Operand, insns.OpMem, analysis.Program):
        inspect.get_annotations(c), inspect.signature(c), inspect.getmembers(c), c.__doc__, c.__annotations__
        c.__subclasses__(), isinstance(i, c)
    analysis.Program.insn_at.__annotations__
    assert analysis._cache_key(None) == k


@pytest.mark.parametrize("module, old, new", [
    ("le", "self.raw = data", "self.raw = bytes(data)"),                     # a method
    ("le", "0x1, 0x2, 0x4, 0x2000", "0x1, 0x2, 0x8, 0x2000"),   # a constant
    ("le", "PTR1616: 4", "PTR1616: 5"),                                      # in a generator of a property
    ("le", 'data: bytes = b""', 'data: bytes = b"x"'),                       # a dataclass default
    ("analysis", '"into",', '"intp",'),                                      # in a set
    ("analysis", 'strict=True):', 'strict=False):'),                         # a default argument
    ("analysis", 'm in COND_JUMPS or m == "jmp":', 'm in COND_JUMPS and m == "jmp":'),
    ("insns", '"type size access', '"type  size access'),
    ("insns", "max(which) >= count", "max(which) > count"),
    ("loaded", "if s is None:", "if not s:"),
    ("__init__", '"war.exe"', '"War.exe"'),
])
def test_any_edit_is_another_key(tree, module, old, new):
    before = tree.run(KEY)
    tree.edit(module, old, new)
    after = tree.run(KEY)
    assert len(before) == len(after) == 32 and before != after
    tree.edit(module, new, old)
    assert tree.run(KEY) == before


def test_a_stale_pyc_has_the_key_of_its_own_code(tree):
    """Python runs the old code for an edit of the same size and mtime."""
    f = tree.d / "le.py"
    os.utime(f, (T0, T0))
    key = tree.run(KEY)
    assert list((tree.d / "__pycache__").glob("le.*.pyc"))
    f.write_text(f.read_text().replace("0x1, 0x2, 0x4, 0x2000", "0x1, 0x2, 0x8, 0x2000"))
    os.utime(f, (T0, T0))
    assert tree.run("from wc1 import le\nprint(le.OBJ_EXEC)") == "4"
    assert tree.run(KEY) == key
    for pyc in (tree.d / "__pycache__").glob("le.*.pyc"):
        pyc.unlink()
    assert tree.run("from wc1 import le\nprint(le.OBJ_EXEC)") == "8"
    assert tree.run(KEY) != key


@pytest.mark.parametrize("module", ["le", "insns", "loaded", "__init__"])
def test_a_module_edited_after_it_was_imported(tree, module):
    """The key is that of the code in memory: the edited file cannot get this process's results."""
    name = "wc1" if module == "__init__" else "wc1." + module
    edit = (f"import {name}\n"
            f"f = {str(tree.d / (module + '.py'))!r}\n"
            "s = open(f).read()\n"
            "open(f, 'w').write('EDITED = 1\\n' + s)\n")
    old = tree.run(KEY)
    assert tree.run(edit + KEY) == old
    new = tree.run(KEY)
    assert len(new) == 32 and new != old


def test_an_edit_between_imports_cannot_pollute_the_cache(tree):
    """import wc1.le, edit le.py, import wc1.analysis, run(): the result is stored under
    the key of the loader that made it, and a process with the new loader does not see it."""
    run = ("from wc1 import analysis\n"
           f"exe = {os.path.abspath(wc1.ORIGINAL_EXE)!r}\n"
           "p = analysis.run(exe)\n"
           "print(analysis._cache_key(exe), p.le.raw[-1])\n")
    # a quick tool: discovery decodes one instruction
    tree.edit("analysis", "    def discover(self):\n", "    def discover(self):\n"
              "        self.insns = {a: self.insn_at(a) for a in [self.le.entry]}\n"
              "        return self\n\n    def _discover(self):\n")
    tree.edit("analysis", "    def partition(self):\n", "    def partition(self):\n        return self\n\n"
              "    def _partition_all(self):\n")
    other = "self.raw = data[:-1] + bytes([data[-1] ^ 0xFF])"
    edit = (f"import wc1.le\nf = {str(tree.d / 'le.py')!r}\n"
            f"s = open(f).read()\nopen(f, 'w').write(s.replace('self.raw = data', {other!r}, 1))\n")
    last = open(wc1.ORIGINAL_EXE, "rb").read()[-1]
    key_old, byte = tree.run(edit + run).split()
    assert int(byte) == last                                                # the loader in memory
    cache = tree.root / "build" / "cache"
    assert os.listdir(cache) == [f"analysis-{key_old}.pickle"]
    for _ in range(2):                                                      # cold, then cached
        key_new, byte = tree.run(run).split()
        assert key_new != key_old and int(byte) == last ^ 0xFF
    assert sorted(os.listdir(cache)) == sorted(f"analysis-{k}.pickle" for k in (key_old, key_new))


PRELOADED = """
import types, wc1
def preload(name, src):
    m = types.ModuleType("wc1." + name)
    m.__package__, m.__file__ = "wc1", f"{wc1.__path__[0]}/{name}.py"
    sys.modules["wc1." + name] = m
    setattr(wc1, name, m)
    exec(compile(src, m.__file__, "exec"), vars(m))
src = open(f"{wc1.__path__[0]}/le.py").read()
"""


def test_a_preloaded_module_that_differs_from_its_file(tree):
    key = tree.run(KEY)
    assert tree.run(PRELOADED + "preload('le', src)\n" + KEY) == key
    other = tree.run(PRELOADED + "preload('le', src.replace('self.raw = data', 'self.raw = data + b\"\"'))\n" + KEY)
    assert len(other) == 32 and other != key
    # not sealed, or sealed and then changed before analysis was imported
    assert tree.run(PRELOADED + "preload('le', src.replace('loaded.seal()', ''))\n" + KEY) == "None"
    assert tree.run("from wc1 import le\nle.LE.read = lambda *a: b''\n" + KEY) == "None"
    assert tree.run("from wc1 import le\nle.OBJ_EXEC = 8\n" + KEY) == "None"
    # a reload runs the new code
    tree.edit("le", "self.raw = data", "self.raw = bytes(data)")
    fresh = tree.run(KEY)
    tree.edit("le", "self.raw = bytes(data)", "self.raw = data")
    reload = ("from wc1 import analysis, le\nimport importlib\n"
              f"f = {str(tree.d / 'le.py')!r}\ns = open(f).read()\n"
              "open(f, 'w').write(s.replace('self.raw = data', 'self.raw = bytes(data)', 1))\n"
              "importlib.invalidate_caches()\nimportlib.reload(le)\n")
    assert tree.run(reload + KEY) == fresh != key


def _patched_function_code(m):
    f = le.load
    m.setattr(f, "__code__", (lambda path=None: None).__code__)


CHANGES = {
    "method": lambda m: m.setattr(le.LE, "read", lambda *a: b""),
    "new method": lambda m: m.setattr(le.LE, "__getattr__", lambda *a: 0, raising=False),
    "property": lambda m: m.setattr(le.Obj, "is_code", property(lambda self: True)),
    "dataclass default": lambda m: m.setattr(le.Obj, "data", b"x"),
    "generated method": lambda m: m.setattr(le.Fixup, "__init__", lambda *a: None),
    "function": lambda m: m.setattr(insns, "pack", lambda i: ()),
    "function code": _patched_function_code,
    "function defaults": lambda m: m.setattr(analysis.Program._closure, "__defaults__", (False,)),
    "constant": lambda m: m.setattr(le, "HDR_FMT", "<"),
    "dict": lambda m: m.setitem(le.SRC_NAMES, 7, "x"),
    "list": lambda m: m.setattr(le, "HDR_NAMES", le.HDR_NAMES[:]),
    "set": lambda m: m.setattr(analysis, "IMPLAUSIBLE", set()),
    "class": lambda m: m.setattr(analysis, "Program", type("Program", (analysis.Program,), {})),
    "class constant": lambda m: m.setattr(analysis.Program, "FILLERS", ()),
    "imported module": lambda m: m.setattr(analysis, "lefmt", types.SimpleNamespace(LE=None, load=None)),
    "third-party module": lambda m: m.setattr(analysis, "capstone", types.ModuleType("capstone")),
    "shadowed builtin": lambda m: m.setattr(analysis, "open", open, raising=False),
    "base class": lambda m: m.setattr(insns._Fields, "__init__", lambda *a: None),
    "module table": lambda m: m.setitem(sys.modules, "wc1.le", types.ModuleType("wc1.le")),
    "the check itself": lambda m: m.setattr(loaded, "_LAZY", set()),
    "no seal": lambda m: m.delattr(le, "_LOADED"),
}


@pytest.mark.parametrize("change", CHANGES.values(), ids=CHANGES)
def test_a_changed_tool_has_no_key(monkeypatch, change):
    k = analysis._cache_key(None)
    with monkeypatch.context() as m:
        change(m)
        assert analysis._cache_key(None) is None
    assert analysis._cache_key(None) == k is not None


def test_in_place_changes_of_containers_are_seen():
    k = analysis._cache_key(None)
    for container, change, undo in (
            (analysis.COND_JUMPS, lambda: analysis.COND_JUMPS.remove("jo"), lambda: analysis.COND_JUMPS.add("jo")),
            (le.HDR_NAMES, lambda: le.HDR_NAMES.append("x"), lambda: le.HDR_NAMES.pop())):
        change()
        try:
            assert analysis._cache_key(None) is None
        finally:
            undo()
        assert analysis._cache_key(None) == k


def test_without_a_key_the_cache_is_neither_read_nor_written(tmp_path, monkeypatch):
    """run() then discovers, from the inputs it read."""
    (tmp_path / "analysis").mkdir()
    (tmp_path / "analysis" / "modules.toml").write_bytes(b"[[module]]\nstart = 1\nend = 9\nkind = 'ail'\n")
    monkeypatch.setattr(wc1, "ROOT", str(tmp_path))
    monkeypatch.setattr(analysis.Program, "discover", lambda self: self)
    monkeypatch.setattr(analysis.Program, "partition", lambda self: self)
    monkeypatch.setattr(analysis, "_load", lambda f: pytest.fail("read"))
    p = analysis.run()
    assert type(p) is analysis.Program and p.module_kinds == [(1, 9, "ail")]
    assert not (tmp_path / "build").exists()
    with pytest.raises(FileNotFoundError):
        analysis.run(str(tmp_path / "no.exe"))


def test_digest_of_constants():
    def code(src, name="f.py"):
        return loaded._digest(compile(src, name, "exec"))
    assert code("x = 1") == code("x = 1", "elsewhere/g.py")
    different = ["x = 1", "x = 2", "x = 1.0", "x = True", "x = '1'", "x = b'1'", "x = 1j", "x = -0.0", "x = 0.0",
                 "x = ...", "x = None", "y = 1", "x = (1, 2)", "x = ((1,), 2)", "x = (1, (2,))", "x = y in {1, 2}",
                 "x = y in {1, 3}", "x = y[1:2]", "x = y[1:3]", "def f(a): return 1", "def f(a): return 2",
                 "def f(b): return 1", "def f(a, /): return 1", "def f(*, a): return 1", "x = 'a\\0b'",
                 "x = ('a', 'b')", "x = 'ab', ''"]
    assert len({code(s) for s in different}) == len(different)
    a, b = frozenset(["a", "b", "c"]), frozenset(["c", "b", "a"])
    assert loaded._digest(a) == loaded._digest(b) != loaded._digest(("a", "b", "c"))
    with pytest.raises(loaded.Uncertain):
        loaded._digest(object())
