import os
import zlib

import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case, T4Stub

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = path('src/init')
EXE_DIR = 0x59920
CD_PATH = 0x59870
FAKE_FP = 0x1234
G = {}


def test_t3_files_match():
    t4spec.assert_t3_matches(path('src/init'), [])


def test_reference_files_still_mismatch():
    t4spec.assert_ref_mismatch(path('src/init'), ['find_data_file_reference.c', 'load_file_reference.c', 'open_data_archive_reference.c'])


def _addr(name, kind=None):
    by = t4spec.by_link_lenient()
    for cand in (name, name + "_", "_" + name):
        if cand in by:
            return by[cand]["addr"]
    pytest.skip("symbol %s not in DB" % name)


def _b(x):
    return x if isinstance(x, (bytes, bytearray)) else x.encode("latin1")


def _cs(e, a):
    if a == 0:
        return b""
    return _b(e.cstr(a, 64))


def _crc(e, a):
    return zlib.crc32(_cs(e, a))


def _u32(e, a):
    return int.from_bytes(bytes(e.read(a, 4)), "little")


def _init(emu):
    G["name"] = emu.alloc(0x100, 16)
    G["buf"] = emu.alloc(0x100, 16)
    G["st"] = {}


def _put(e, a, s):
    e.write(a, _b(s) + b"\0")


def _strs():
    return {EXE_DIR: b"E:\\W\0", CD_PATH: b"C:\\W\0",
            0x56c88: b"rb\0", 0x56c8c: b"%s.dat\0",
            0x52541: b"data.war\0", 0x5254a: b"fmt\0", 0x56d6c: b"x\0",
            0x56d70: b"err\0"}


def _setup(**st):
    def f(e):
        G["st"].clear()
        G["st"].update(st)
    return f


def _open_stub(log_name=True):
    def fn(e, log):
        nm = _cs(e, e.reg("eax"))
        log(zlib.crc32(nm), _crc(e, e.reg("edx")))
        pre = G["st"].get("prefix")
        if pre is None:
            return FAKE_FP if G["st"].get("open") else 0
        return FAKE_FP if nm.startswith(pre) else 0
    return fn


def _makepath_stub(e, log):
    d = _cs(e, e.reg("edx"))
    f = _cs(e, e.reg("ebx"))
    log(zlib.crc32(d), zlib.crc32(f))
    _put(e, e.reg("eax"), d + f)
    return 0


def _strcpy_stub(e, log):
    s = _cs(e, e.reg("edx"))
    log(zlib.crc32(s))
    _put(e, e.reg("eax"), s)
    return e.reg("eax")


def _sprintf_stub(e, log):
    sp = e.reg("esp")
    buf = _u32(e, sp + 4)
    nm = _cs(e, _u32(e, sp + 12))
    log(zlib.crc32(nm))
    _put(e, buf, nm)
    return len(nm)


# ---------------- LoadFile ----------------

def _lf_cases():
    S = _strs()
    out = []
    for lbl, exe, st in (
            ("exe_ok", 1, dict(open=1, size=100, read=100)),
            ("plain_ok", 0, dict(open=1, size=100, read=100)),
            ("open_fail", 1, dict(open=0)),
            ("too_small", 0, dict(open=1, size=5, read=5)),
            ("too_big", 1, dict(open=1, size=900, read=900)),
            ("short_read", 0, dict(open=1, size=100, read=50)),
            ("min_edge", 0, dict(open=1, size=10, read=10)),
            ("max_edge", 1, dict(open=1, size=200, read=200))):
        mem = dict((a, v) for a, v in S.items())
        mem[G["name"]] = b"a.bin\0"
        out.append(T4Case(args=(G["name"], G["buf"], 10, 200),
                          stack_args=(exe,), mem=mem,
                          setup=_setup(**st), label=lbl))
    return out


def test_load_file():
    def tell(e, log):
        log(e.reg("eax"))
        return G["st"].get("size", 0)

    def read(e, log):
        log(e.reg("eax"), e.reg("edx"), e.reg("ebx"), e.reg("ecx"))
        return G["st"].get("read", 0)

    t4spec.run_spec(
        SRC + "/load_file_reference.c", "LoadFile_", 0x1d330,
        (c for _ in [0] for c in _lf_cases()),
        init_emu=_init,
        watch=(w for w in [(G["buf"], 0x40), (_addr("file_open_noprompt"), 2)] if False) if False else [],
        out_regs=("eax",),
        stubs=[
            T4Stub(_addr("FileOpen"), fn=_open_stub()),
            T4Stub(_addr("FileClose"), log_regs=("eax",)),
            T4Stub(_addr("FileTell"), fn=tell),
            T4Stub(_addr("FileSeek"), log_regs=("eax", "edx", "ebx")),
            T4Stub(_addr("FileRead"), fn=read),
            T4Stub(_addr("_makepath"), fn=_makepath_stub, stack_pop=4),
            T4Stub(_addr("strcpy"), fn=_strcpy_stub),
        ])


# ---------------- FindDataFile ----------------

def _fd_cases():
    S = _strs()
    out = []
    for lbl, pre in (("exe_hit", b"E:"), ("cd_hit", b"C:"), ("none", b"ZZ")):
        mem = dict((a, v) for a, v in S.items())
        mem[G["name"]] = b"war\0"
        out.append(T4Case(args=(G["name"],), mem=mem,
                          setup=_setup(prefix=pre), label=lbl))
    return out


def test_find_data_file():
    t4spec.run_spec(
        SRC + "/find_data_file_reference.c", "FindDataFile_", 0x1d410,
        (c for _ in [0] for c in _fd_cases()),
        init_emu=_init,
        out_regs=("eax",),
        stubs=[
            T4Stub(_addr("FileOpen"), fn=_open_stub()),
            T4Stub(_addr("_makepath"), fn=_makepath_stub, stack_pop=4),
            T4Stub(_addr("sprintf"), fn=_sprintf_stub),
            T4Stub(_addr("setvbuf"), log_regs=("eax", "edx", "ebx", "ecx")),
        ])


# ---------------- OpenDataArchive ----------------

def _oda_cases():
    S = _strs()
    out = []
    for lbl, st, cd in (("found", dict(fp=FAKE_FP), b"C:\\W\0"),
                        ("missing_diff", dict(fp=0), b"C:\\W\0"),
                        ("missing_same", dict(fp=0), b"E:\\W\0")):
        mem = dict((a, v) for a, v in S.items())
        mem[CD_PATH] = cd
        out.append(T4Case(mem=mem, setup=_setup(**st), label=lbl))
    return out


def test_open_data_archive():
    def find(e, log):
        log(e.reg("eax"))
        return G["st"].get("fp", 0)

    def strcmp(e, log):
        a = _cs(e, e.reg("eax"))
        b = _cs(e, e.reg("edx"))
        log(zlib.crc32(a), zlib.crc32(b))
        return (a > b) - (a < b)

    def fatal(e, log):
        sp = e.reg("esp")
        log(*[_u32(e, sp + 4 + 4 * i) for i in range(6)])
        return 0

    t4spec.run_spec(
        SRC + "/open_data_archive_reference.c", "OpenDataArchive_", 0x1d9d4,
        (c for c in _oda_cases()),
        init_emu=_init,
        out_regs=(),
        stubs=[
            T4Stub(_addr("FindDataFile"), fn=find),
            T4Stub(_addr("InitResources"), log_regs=("eax",)),
            T4Stub(_addr("strcmp"), fn=strcmp),
            T4Stub(_addr("FatalError"), fn=fatal),
        ])
