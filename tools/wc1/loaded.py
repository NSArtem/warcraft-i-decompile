"""Identity of the tool code this process runs, for the keys of persistent caches.

A source file on disk says nothing certain about the module in memory: it can be
edited after (or while) the module is imported, and a stale .pyc can stand in for it.
So each module that takes part calls seal() at its end.  That keeps the code object
Python executed for the module - every function, class body and literal of it is in
there - and what its names were bound to.  identity() is a digest of those code
objects, the same in every process that runs the same code.  It is refused
(Uncertain) when a module was not sealed, no longer is what its code made it (e.g.
after a monkeypatch) or never was that alone: a reload runs the new code in the old
namespace, where every name that code does not bind stays.  No cache then.
"""
from dataclasses import dataclass
import hashlib
import importlib
import inspect
import opcode
import sys
import types
from weakref import WeakSet


# Keep the code even if the public callable is replaced. CPython's reload uses
# _exec; fresh imports use _load_unlocked.
_RELOAD_CODE = getattr(importlib.reload, "__code__", None)
_BOOTSTRAP_EXEC_CODE = getattr(getattr(importlib._bootstrap, "_exec", None), "__code__", None)


class Uncertain(Exception):
    """What this process runs cannot be told from the code it loaded."""


@dataclass(frozen=True, slots=True)
class _Seal:
    code: types.CodeType
    free: tuple[str, ...] | None
    bindings: types.MappingProxyType | None
    digest: bytes | None
    reloaded: bool


# Keep the record through a reload of this module, without keeping old modules alive.
if "_SEALED" not in globals():
    _SEALED = WeakSet()


# everything about a code object but the path of its file
_CODE = ("co_name", "co_qualname", "co_flags", "co_argcount", "co_posonlyargcount", "co_kwonlyargcount",
         "co_nlocals", "co_stacksize", "co_code", "co_consts", "co_names", "co_varnames", "co_freevars",
         "co_cellvars", "co_exceptiontable", "co_firstlineno", "co_linetable")


def _digest(v):
    """sha256 of a code object or of a constant in one.  (marshal and repr will not do:
    they depend on reference counts and on the order of sets.)"""
    t = type(v)
    if t is types.CodeType:
        parts = [_digest(getattr(v, a)) for a in _CODE]
    elif t is tuple:
        parts = [_digest(x) for x in v]
    elif t is frozenset:
        parts = sorted(_digest(x) for x in v)
    elif t is slice:
        parts = [_digest(x) for x in (v.start, v.stop, v.step)]
    elif v is None or v is ... or t in (bool, int, float, complex, str, bytes):
        parts = [repr(v).encode()]
    else:
        raise Uncertain(f"constant of type {t}")
    return hashlib.sha256(b"\0".join([t.__name__.encode(), *parts])).digest()


def _bound(code):
    """The names the code of a module binds in its namespace (its functions: none)."""
    out, arg = set(), 0
    for op, low in zip(code.co_code[::2], code.co_code[1::2]):
        arg = arg << 8 | low
        if op == opcode.EXTENDED_ARG:
            continue
        if op == opcode.opmap["STORE_NAME"]:
            out.add(code.co_names[arg])
        arg = 0
    return out


# what Python itself adds to a class later (annotations, copy and pickle)
_LAZY = {"__annotations__", "__annotations_cache__", "__annotate_func__", "__slotnames__"}


def _state(v, module):
    """Comparable state of one binding: the object itself, and what can be changed in it."""
    t = type(v)
    if t is types.FunctionType:
        inner = v.__code__, v.__defaults__, v.__kwdefaults__ and dict(v.__kwdefaults__)
    elif t in (staticmethod, classmethod):
        inner = _state(v.__func__, module)
    elif t is property:
        inner = [_state(f, module) for f in (v.fget, v.fset, v.fdel)]
    elif t in (list, dict, set, bytearray):
        inner = t(v)
    elif isinstance(v, type) and v.__module__ == module:
        inner = v.__bases__, [_state(b, module) for b in v.__bases__], \
            {k: _state(x, module) for k, x in vars(v).items() if k not in _LAZY}
    else:
        inner = None
    return id(v), v, inner              # id first: never compares two objects by ==


def _bindings(ns, free):
    return {k: _state(v, ns["__name__"]) for k, v in list(ns.items())
            if not (k.startswith("__") and k.endswith("__")) and k not in free and k != "_LOADED"}


def _record(frame, free, bindings):
    ns, code = frame.f_globals, frame.f_code
    module = sys.modules.get(ns["__name__"])
    registered = getattr(module, "__dict__", None) is ns
    reloaded = ("_LOADED" in ns or registered and module in _SEALED
                or bindings is not None and not bindings.keys() <= _bound(code))
    # reload can reuse old values before rebinding all the same names, even if
    # the previous code never sealed the namespace.
    current_reload_code = getattr(importlib.reload, "__code__", None)
    caller = inspect.currentframe()
    try:
        while caller is not None:
            code_in_stack = caller.f_code
            if (code_in_stack is _RELOAD_CODE or code_in_stack is _BOOTSTRAP_EXEC_CODE
                    or code_in_stack is current_reload_code):
                reloaded = True
                break
            caller = caller.f_back
    finally:
        del caller

    if registered:
        _SEALED.add(module)
    try:
        digest = _digest(code)
    except Uncertain:
        digest = None
    if bindings is not None:
        bindings = types.MappingProxyType(bindings)
    ns["_LOADED"] = _Seal(code, free, bindings, digest, reloaded)


def seal(*free):
    """Call at the end of a module.  free: names that may be rebound or changed later,
    as they do not affect a cached result or are part of its key."""
    frame = sys._getframe(1)
    _record(frame, free, _bindings(frame.f_globals, free))


def seal_package():
    """seal() for a package: its code only.  (Its namespace changes with every submodule
    import, and wc1 itself just says where the files are.)"""
    _record(sys._getframe(1), None, None)


def identity(*namespaces):
    """Digest of the code the modules with these namespaces (their vars()) run; Uncertain
    if that is not certain."""
    h = hashlib.sha256()
    for ns in namespaces:
        name, s = ns.get("__name__"), ns.get("_LOADED")
        if type(name) is not str or type(s) is not _Seal:
            raise Uncertain(f"{name!r}: not sealed")   # also if wc1.loaded was reloaded since
        try:
            code, free, bindings, digest, reloaded = s.code, s.free, s.bindings, s.digest, s.reloaded
        except AttributeError as exc:
            raise Uncertain(f"{name}: incomplete seal") from exc
        if (type(code) is not types.CodeType or code.co_name != "<module>"
                or type(reloaded) is not bool or type(digest) is not bytes or len(digest) != 32
                or (free is None) != (bindings is None)
                or free is None and "__path__" not in ns
                or free is not None and (type(free) is not tuple or any(type(k) is not str for k in free)
                                         or type(bindings) is not types.MappingProxyType)):
            raise Uncertain(f"{name}: invalid seal")
        if reloaded:
            raise Uncertain(f"{name}: loaded into a namespace that was not new")
        if getattr(sys.modules.get(name), "__dict__", None) is not ns:
            raise Uncertain(f"{name}: another module has its name")     # and pickle would use that
        if bindings is not None and _bindings(ns, free) != bindings:
            raise Uncertain(f"{name}: changed since it was loaded")
        h.update(name.encode() + b"\0" + digest)
    return h.digest()


seal()
