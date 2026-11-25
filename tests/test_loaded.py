"""wc1.loaded: the analysis cache key names the code this process runs, not the files
on disk, and there is no key when what runs is not what was loaded."""
import copy
import inspect
import os
from pathlib import Path
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

    # Ignore the caller's bytecode settings so each test can choose its cache layout.
    base = {k: v for k, v in os.environ.items() if k not in ("PYTHONPYCACHEPREFIX", "PYTHONDONTWRITEBYTECODE")}

    def run(code, *flags, **env):
        r = subprocess.run([sys.executable, *flags, "-c", "import os, sys\n" + code], cwd=tmp_path,
                           capture_output=True, text=True,
                           env=dict(base, WC1_ROOT=str(tmp_path), PYTHONPATH=str(d.parent), **env))
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
    ("insns", "max(which) < count", "max(which) <= count"),
    ("loaded", "if reloaded:", "if not not reloaded:"),
    ("__init__", '"war.exe"', '"War.exe"'),
])
def test_any_edit_is_another_key(tree, module, old, new):
    before = tree.run(KEY)
    tree.edit(module, old, new)
    after = tree.run(KEY)
    assert len(before) == len(after) == 32 and before != after
    tree.edit(module, new, old)
    assert tree.run(KEY) == before


@pytest.mark.parametrize("use_prefix", [False, True])
def test_a_stale_pyc_has_the_key_of_its_own_code(tree, use_prefix):
    """Python runs the old code for an edit of the same size and mtime."""
    f = tree.d / "le.py"
    prefix = tree.root / "pycache"
    env = {"PYTHONPYCACHEPREFIX": str(prefix)} if use_prefix else {}
    os.utime(f, (T0, T0))
    key = tree.run(KEY, **env)
    where = "import importlib.util\nprint(importlib.util.cache_from_source(%r))" % str(f)
    pyc = Path(tree.run(where, **env))      # as that process names it
    assert pyc.is_relative_to(prefix if use_prefix else tree.d / "__pycache__") and pyc.is_file()
    f.write_text(f.read_text().replace("0x1, 0x2, 0x4, 0x2000", "0x1, 0x2, 0x8, 0x2000"))
    os.utime(f, (T0, T0))
    assert tree.run("from wc1 import le\nprint(le.OBJ_EXEC)", **env) == "4"
    assert tree.run(KEY, **env) == key
    pyc.unlink()
    assert tree.run("from wc1 import le\nprint(le.OBJ_EXEC)", **env) == "8"
    assert tree.run(KEY, **env) != key


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
    for e in QUICK:
        tree.edit(*e)
    other = "self.raw = data[:-1] + bytes([data[-1] ^ 0xFF])"
    edit = (f"import wc1.le\nf = {str(tree.d / 'le.py')!r}\n"
            f"s = open(f).read()\nopen(f, 'w').write(s.replace('self.raw = data', {other!r}, 1))\n")
    last = open(wc1.ORIGINAL_EXE, "rb").read()[-1]
    key_old, byte = tree.run(edit + RUN).split()
    assert int(byte) == last                                                # the loader in memory
    cache = tree.root / "build" / "cache"
    assert os.listdir(cache) == [f"analysis-{key_old}.pickle"]
    for _ in range(2):                                                      # cold, then cached
        key_new, byte = tree.run(RUN).split()
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
    # a namespace with a name that its code does not bind
    shim = "preload('le', src)\ndel m._LOADED\nm.bytes = bytes\nexec(compile(src, m.__file__, 'exec'), vars(m))\n"
    assert tree.run((PRELOADED + shim).replace("m = types", "global m\n    m = types") + KEY) == "None"


# a quick tool: discovery decodes one instruction
QUICK = [("analysis", "    def discover(self):\n", "    def discover(self):\n"
          "        self.insns = {a: self.insn_at(a) for a in [self.le.entry]}\n"
          "        return self\n\n    def _discover(self):\n"),
         ("analysis", "    def partition(self):\n", "    def partition(self):\n        return self\n\n"
          "    def _partition_all(self):\n")]
RUN = ("from wc1 import analysis\n"
       f"exe = {os.path.abspath(wc1.ORIGINAL_EXE)!r}\n"
       "p = analysis.run(exe)\n"
       "print(analysis._cache_key(exe), p.le.raw[-1])\n")


def _rewrite(module, f, old, new, reload_call="importlib.reload"):
    """Code that edits the source of a module and reloads it."""
    return (f"from wc1 import analysis, {module}\nimport importlib\n"
            f"f = {str(f)!r}\ns = open(f).read()\nassert s.count({old!r}) == 1\n"
            f"open(f, 'w').write(s.replace({old!r}, {new!r}))\n"
            f"importlib.invalidate_caches()\n{reload_call}({module})\n")


def test_a_reloaded_module_has_no_key(tree):
    """A name that its new code does not bind any more is still in its namespace: not
    what a process that loads the new code runs.  Such a run neither writes the cache
    nor reads what the other process wrote."""
    for e in QUICK:
        tree.edit(*e)
    shim = "def bytes(x):\n    b = type(b'')(x)\n    return b if type(x) is int else b[:-1] + b'\\xff'\n\n\n"
    tree.edit("le", "self.raw = data", "self.raw = bytes(data)")
    tree.edit("le", "class LE", shim + "class LE")
    with open(wc1.ORIGINAL_EXE, "rb") as fh:
        last = fh.read()[-1]
    assert last != 255
    cache = tree.root / "build" / "cache"
    key, byte = tree.run(RUN).split()
    assert len(key) == 32 and byte == "255" and os.listdir(cache) == [f"analysis-{key}.pickle"]
    reloaded = _rewrite("le", tree.d / "le.py", shim, "") + RUN
    assert tree.run(reloaded) == "None 255"                         # the shim is still in le
    assert os.listdir(cache) == [f"analysis-{key}.pickle"]          # nothing written
    for _ in range(2):                                              # a clean process: cold, then cached
        clean, byte = tree.run(RUN).split()
        assert len(clean) == 32 and clean != key and int(byte) == last
    stored = cache / f"analysis-{clean}.pickle"
    content = stored.read_bytes()
    tree.edit("le", "class LE", shim + "class LE")
    assert tree.run(reloaded) == "None 255"                         # nothing read
    assert stored.read_bytes() == content
    assert sorted(os.listdir(cache)) == sorted(f"analysis-{k}.pickle" for k in (key, clean))


@pytest.mark.parametrize("module", ["le", "insns", "loaded", "analysis", "__init__"])
def test_no_reload_of_any_module_has_a_key(tree, module):
    """Not even of unchanged code, nor after a second one."""
    name = "wc1" if module == "__init__" else "wc1." + module
    reload = f"import importlib, sys, wc1.analysis\nm = importlib.reload(sys.modules[{name!r}])\n"
    assert len(tree.run(KEY)) == 32
    assert tree.run(reload + KEY) == tree.run(reload * 2 + KEY) == "None"


def test_names_left_by_unsealed_code(tree):
    """le had no seal when it was first imported (and its _LOADED is not there to tell)."""
    f = tree.d / "le.py"
    src = f.read_text()
    f.write_text(src.replace("loaded.seal()", "bytes = bytes  # and no seal"))
    reload = f"from wc1 import le\nimport importlib\nopen({str(f)!r}, 'w').write({src!r})\nimportlib.reload(le)\n"
    assert tree.run(reload + KEY) == "None"
    assert len(tree.run(KEY)) == 32


@pytest.mark.parametrize("public_reload", ["original", "replaced_after_import", "replaced_before_import"])
def test_reload_of_unsealed_code_that_rebinds_all_names(tree, public_reload):
    for edit in QUICK:
        tree.edit(*edit)
    tree.edit("le", "self.raw = data", "self.raw = data[:-1] + bytes([MARKER])")
    unsealed = "SCALE = 2\nMARKER = 4\n"
    sealed = "MARKER = 4 * globals().get('SCALE', 1)\nSCALE = 1\nloaded.seal()\n"
    tree.edit("le", "loaded.seal()\n", unsealed)
    setup, reload_call = "", "importlib.reload"
    if public_reload != "original":
        setup = """
import importlib
from functools import partial
orig_reload = importlib.reload
"""
        if public_reload == "replaced_after_import":
            setup += "from wc1 import loaded\nimportlib.reload = lambda module: module\n"
        else:
            setup += "importlib.reload = partial(orig_reload)\n"
        reload_call = "orig_reload"
    reloaded = setup + _rewrite("le", tree.d / "le.py", unsealed, sealed, reload_call) + """
from wc1 import loaded
assert le._LOADED.bindings.keys() <= loaded._bound(le._LOADED.code)
try:
    loaded.identity(vars(le))
except loaded.Uncertain:
    pass
else:
    raise AssertionError("the unsealed namespace was reused")
""" + RUN
    cache = tree.root / "build" / "cache"
    assert tree.run(reloaded) == "None 8"
    assert not cache.exists()

    key, byte = tree.run(RUN).split()
    assert len(key) == 32 and byte == "4"
    stored = cache / f"analysis-{key}.pickle"
    content = stored.read_bytes()
    tree.edit("le", sealed, unsealed)
    assert tree.run(reloaded) == "None 8"
    assert list(cache.iterdir()) == [stored] and stored.read_bytes() == content


def test_fresh_import_with_a_partial_reload_can_seal(tree):
    key = tree.run(KEY)
    assert len(key) == 32
    assert tree.run("""
import importlib
from functools import partial
importlib.reload = partial(importlib.reload)
""" + KEY) == key


def test_reexecuting_a_previously_sealed_module_without_its_seal(tree):
    assert tree.run(PRELOADED + """
from wc1 import le
del le._LOADED
exec(compile(src, le.__file__, "exec"), vars(le))
""" + KEY) == "None"


@pytest.mark.parametrize("seal", ["False", "None", "0", "123", "object()", "{}", "'x'", "()", "loaded._Seal",
                                  "object.__new__(loaded._Seal)", "types.SimpleNamespace(reloaded=False)",
                                  "type('S', (loaded._Seal,), {})"])
@pytest.mark.parametrize("module", ["le", "wc1"])
def test_an_invalid_seal_is_no_key(tmp_path, monkeypatch, module, seal):
    (tmp_path / "analysis").mkdir()
    (tmp_path / "analysis" / "modules.toml").write_bytes(b"")
    monkeypatch.setattr(wc1, "ROOT", str(tmp_path))
    monkeypatch.setattr({"le": le, "wc1": wc1}[module], "_LOADED", eval(seal))
    with pytest.raises(loaded.Uncertain):
        analysis._tool_identity()
    assert analysis._cache_key(None) is None
    monkeypatch.setattr(analysis.Program, "discover", lambda self: self)
    monkeypatch.setattr(analysis.Program, "partition", lambda self: self)
    monkeypatch.setattr(analysis, "_load", lambda f: pytest.fail("read"))
    assert type(analysis.run()) is analysis.Program
    assert not (tmp_path / "build").exists()


def test_seal_is_read_only():
    with pytest.raises(AttributeError):
        le._LOADED.digest = b""
    with pytest.raises(AttributeError):
        del le._LOADED.digest
    with pytest.raises(TypeError):
        le._LOADED.bindings["new"] = ()


@pytest.mark.parametrize("field, value", [
    ("digest", 1), ("digest", b"bad"), ("digest", bytearray(32)),
    ("reloaded", 0), ("reloaded", True),
    ("code", None), ("code", (lambda: None).__code__),
    ("free", None), ("free", []), ("free", (1,)),
    ("bindings", None), ("bindings", {}), ("bindings", types.MappingProxyType({})),
])
def test_a_corrupted_seal_has_no_key(monkeypatch, field, value):
    seal = copy.copy(le._LOADED)
    object.__setattr__(seal, field, value)
    monkeypatch.setattr(le, "_LOADED", seal)
    with pytest.raises(loaded.Uncertain):
        loaded.identity(vars(le))
    assert analysis._cache_key(None) is None


def test_names_bound_by_code():
    src = ("import a.b, c as d\nfrom e import f\ng: int = 1\nh = i = print\nclass j: k = 1\ndef l(m): n = m\n"
           "for o in (): pass\nwith p as q: pass\n[r for r in s]\ntry: t\nexcept u as v: pass\n"
           + "".join(f"w{i} = {i}\n" for i in range(300)))
    names = loaded._bound(compile(src, "x", "exec"))
    assert {n for n in names if not n.startswith("__")} == {
        "a", "d", "f", "g", "h", "i", "j", "l", "o", "q", "v", *(f"w{i}" for i in range(300))}


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
