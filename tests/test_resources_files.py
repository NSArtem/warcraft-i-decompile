"""File/resource layer 0x318f0..0x31bca and the GDS heap 0x32540..0x32800.

Area = the library object's file wrappers (FileClose/Open/Tell/Getc/Seek/
Read/Write, 0x31940..0x31bca), the two header+body resource readers
(0x318f0/0x323e0) and the checked malloc GdsAlloc/GdsFree/GdsOutOfMemory
(0x32540/0x32558/0x32780).  Names/evidence: analysis/symbols/resources.toml
(file layer) and analysis/symbols/graphics.toml (GDS heap); prose:
docs/subsystems/resources.md.

Kinds of test here:
  * T3 re-check of the twelve byte-matched C files: every function must stay
    MATCH under `wc1.match` (Watcom 10.0a).
  * T4 difftest of the one reference function (GdsFree): the original and the
    compiled C run on the same heap block under wc1.emu and must poison the
    same bytes and free the same pointer, both on the healthy block and on a
    corrupted header (the int3 + "GDS heap corrupt" fatal path).
  * structural checks of the claims in docs/subsystems/resources.md: the GDS
    block layout written by the original GdsAlloc, and the file wrappers'
    error behaviour (quiet optional-file probe, retry after the abort/retry
    prompt) run through the original code with stubbed clib calls.
"""
import os
import struct

import pytest

from wc1 import cemu, codegen_sweep, match, path, symbols, t4spec
from wc1.emu import Emu

HAVE = os.path.exists(path("original", "install", "war.exe")) and bool(os.environ.get("WATCOM"))
pytestmark = pytest.mark.skipif(not HAVE, reason="needs original/ and $WATCOM (nix develop)")

AREA = path("src", "resources")
MATCHED = ["res_header_body_at4.c", "res_header_body.c",
           "file_close.c", "file_open.c", "file_tell.c", "file_getc.c",
           "file_seek.c", "file_read.c", "file_write.c",
           "gds_out_of_memory.c", "gds_alloc.c"]
REFERENCE = "gds_free.c"

# addresses (evidence in analysis/symbols/resources.toml / graphics.toml)
FILE_OPEN = 0x31964
GDS_ALLOC, GDS_FREE = 0x32558, 0x32780
CLIB_FOPEN, CLIB_MALLOC, CLIB_FREE = 0x33D2C, 0x3AC5C, 0x3AD3F
FATAL_ERROR = 0x30BF0
CORRUPT_MSG = b"GDS heap corrupt"

CRIT_FLAG = 0x61EA0         # short: set by the DOS critical-error handler
OPEN_NOPROMPT = 0x61EA2     # short: >0 while an optional file is probed
CRIT_PROMPT = 0x33520       # abort/retry message box


def _flags(src):
    full = match.file_cflags(src)
    prefix = match.BASE_CFLAGS + " "
    assert full.startswith(prefix), full
    return full


@pytest.fixture(scope="module")
def prog():
    return codegen_sweep.program()


@pytest.mark.parametrize("name", MATCHED)
def test_matched_c(name, prog):
    """Every T3 file still reproduces the original bytes (wc1.match)."""
    src = os.path.join(AREA, name)
    out = path("build", "resources", "t3_" + name + ".obj")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    mod = match.compile_c(src, _flags(src), out)
    funcs, datas, _ = symbols.load()
    by_link = {e["link_name"]: e for t in (funcs, datas) for e in t.values()}
    res = match.match_module(prog, mod, by_link)
    bad = [(n, s, p) for n, s, p in res if s != "MATCH"]
    assert not bad, bad


def test_reference_c_is_still_a_near_miss(prog):
    """GdsFree stays T4: if the C starts matching it must be promoted."""
    src = os.path.join(AREA, REFERENCE)
    out = path("build", "resources", "t3_" + REFERENCE + ".obj")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    mod = match.compile_c(src, _flags(src), out)
    funcs, datas, _ = symbols.load()
    by_link = {e["link_name"]: e for t in (funcs, datas) for e in t.values()}
    res = match.match_module(prog, mod, by_link)
    rows = [r for r in res if r[0].startswith("GdsFree")]
    assert rows, res
    t4spec.assert_ref_results(src, rows, "GdsFree")


# ---------------------------------------------------------------- GDS heap
def _make_block(emu, size):
    """A valid GDS block as GdsAlloc lays it out: 8-byte header guard, tail
    pointer at +8, the payload, and an 8-byte tail guard."""
    base = emu.alloc(size + 20)
    tail = base + 12 + size
    emu.write(base, b"CHECKSIG")
    emu.put_u32(base + 8, tail)
    emu.write(tail, b"CHECKSIG")
    return base, tail


def test_gds_alloc_block_layout():
    """The original GdsAlloc returns block+12 and writes the header/tail."""
    emu = Emu()
    buf = emu.alloc(64)
    emu.stubs[CLIB_MALLOC] = lambda e: buf
    size = 16
    p = emu.call(GDS_ALLOC, size)
    assert p == buf + 12
    assert emu.read(buf, 8) == b"CHECKSIG"
    assert emu.u32(buf + 8) == buf + 12 + size
    assert emu.read(buf + 12 + size, 8) == b"CHECKSIG"


def test_gds_alloc_null_malloc_calls_the_nomem_hook():
    """A NULL malloc goes through gds_nomem_handler (0x55440), which is
    GdsOutOfMemory by default.  The hook is fatal, so the model returns to
    the emulator's sentinel and records the call."""
    from wc1.emu import SENTINEL
    emu = Emu()
    called = []
    handler = emu.alloc(4)

    def nomem(e):
        called.append(1)
        e.put_u32(e.reg("esp"), SENTINEL)    # never returns
        return 0

    emu.write(0x55440, struct.pack("<I", handler))
    emu.stubs[handler] = nomem
    emu.stubs[CLIB_MALLOC] = lambda e: 0
    emu.call(GDS_ALLOC, 16)
    assert called, "gds_nomem_handler was not called"


def test_gds_free_c_matches_original():
    """T4: GdsFree (0x32780) on a healthy block - both runs poison the two
    guards with 'GISKCEHC' and free the raw block pointer."""
    emu = Emu()
    cm = cemu.load(emu, path(AREA, REFERENCE))
    size = 16
    base, _ = _make_block(emu, size)
    freed = []
    emu.stubs[CLIB_FREE] = lambda e: freed.append(e.reg("eax")) or 0
    diffs = cemu.run_pair(emu, GDS_FREE, cm, "GdsFree_", base + 12,
                          watch=[(base, 12 + size + 8)], out_regs=())
    assert diffs == [], diffs
    assert freed == [base, base], [hex(x) for x in freed]
    assert emu.read(base, 8) == b"GISKCEHC"
    assert emu.read(base + 12 + size, 8) == b"GISKCEHC"


def test_gds_free_corrupt_path_matches_original():
    """T4: a broken header guard traps (int3) and the fatal message is the
    same in both runs; the rest of the poisoning then runs identically."""
    emu = Emu()
    cm = cemu.load(emu, path(AREA, REFERENCE))
    size = 16
    base, _ = _make_block(emu, size)
    emu.write(base, b"XHECKSIG")
    ints, msgs, freed = [], [], []
    emu.on_interrupt = lambda e, n: ints.append(n)
    emu.stubs[FATAL_ERROR] = lambda e: msgs.append(e.cstr(e.u32(e.reg("esp") + 4))) or 0
    emu.stubs[CLIB_FREE] = lambda e: freed.append(e.reg("eax")) or 0
    diffs = cemu.run_pair(emu, GDS_FREE, cm, "GdsFree_", base + 12,
                          watch=[(base, 12 + size + 8)], out_regs=())
    assert diffs == [], diffs
    assert ints == [3, 3], ints
    assert msgs == [CORRUPT_MSG, CORRUPT_MSG], msgs
    assert freed == [base, base], [hex(x) for x in freed]


# ------------------------------------------------------------ file wrappers
def _fopen_model(emu, outcomes, prompts=None):
    """Stub the clib fopen with a sequence of (handle, crit) outcomes: a DOS
    critical error inside the call is modelled by raising crit_error_flag
    (0x61ea0) as the handler 0x336fc does; the prompt stub records the call
    and lets FileOpen retry."""
    state = {"i": 0}

    def fopen(e):
        i = state["i"]
        state["i"] += 1
        handle, crit = outcomes[i] if i < len(outcomes) else (0, 0)
        emu.write(CRIT_FLAG, struct.pack("<H", crit))
        return handle

    def prompt(e):
        if prompts is not None:
            prompts.append(1)

    emu.stubs[CLIB_FOPEN] = fopen
    emu.stubs[CRIT_PROMPT] = prompt
    return state


def test_file_open_probes_optionals_without_prompting():
    """FileOpen (0x31964): with file_open_noprompt != 0 a failed fopen is
    returned quietly, even when the critical-error handler fired."""
    emu = Emu()
    prompts = []
    _fopen_model(emu, [(0, 1)], prompts)
    emu.write(OPEN_NOPROMPT, struct.pack("<H", 1))
    name = emu.alloc(16)
    emu.write(name, b"data.war\x00")
    assert emu.call(FILE_OPEN, name, 0x52500) == 0
    assert prompts == []


def test_file_open_retries_after_the_critical_error_prompt():
    """FileOpen (0x31964): without the flag, an fopen that failed while the
    handler was active shows the prompt and retries; the third open succeeds."""
    emu = Emu()
    prompts = []
    handle = 0x1234
    state = _fopen_model(emu, [(0, 1), (0, 1), (handle, 0)], prompts)
    emu.write(OPEN_NOPROMPT, struct.pack("<H", 0))
    name = emu.alloc(16)
    mode = emu.alloc(8)
    emu.write(name, b"data.war\x00")
    emu.write(mode, b"rb\x00")
    assert emu.call(FILE_OPEN, name, mode) == handle
    assert state["i"] == 3, state["i"]
    assert len(prompts) == 2, prompts


def test_file_open_plain_failure_does_not_prompt():
    """A failed fopen with crit_error_flag == 0 is the ordinary 'not found'
    case: FileOpen returns NULL at once."""
    emu = Emu()
    prompts = []
    state = _fopen_model(emu, [(0, 0)], prompts)
    emu.write(OPEN_NOPROMPT, struct.pack("<H", 0))
    name = emu.alloc(16)
    mode = emu.alloc(8)
    emu.write(name, b"missing.war\x00")
    emu.write(mode, b"rb\x00")
    assert emu.call(FILE_OPEN, name, mode) == 0
    assert state["i"] == 1
    assert prompts == []
