"""wc1.roundtrip: the one-pass proof with a converged demotion list, and the
diagnostic convergence loop from any other list."""
import os
import shutil
import struct
import types

import pytest

from wc1 import analysis, emit, le, path, roundtrip

pytestmark = pytest.mark.skipif(
    not (os.path.exists(path("original", "install", "war.exe")) and shutil.which("nasm")),
    reason="needs original/ and nasm (nix develop)")

with open(path("analysis", "raw_insns.txt")) as _fh:
    COMMITTED = _fh.read()
HEADER = [l for l in COMMITTED.splitlines(True) if l.startswith("#")]
ENTRIES = [l for l in COMMITTED.splitlines(True) if not l.startswith("#")]

REAL_EMITTER = emit.Emitter


@pytest.fixture
def rt(tmp_path, monkeypatch):
    """Runs main() on a private build/ and raw_insns.txt; returns (raw list file,
    passes: the force_raw set of every NASM pass)."""
    (tmp_path / "build").mkdir()
    raw = tmp_path / "raw_insns.txt"

    def redirect(*p):
        if p[:1] == ("build",):
            return str(tmp_path.joinpath(*p))
        return str(raw) if p == ("analysis", "raw_insns.txt") else path(*p)

    passes = []
    real = emit.Emitter

    def emitter(*a, **kw):
        passes.append(set(kw["force_raw"]))
        return real(*a, **kw)

    monkeypatch.setattr(roundtrip, "path", redirect)
    monkeypatch.setattr(emit, "Emitter", emitter)
    return raw, passes


def test_converged_list_is_proven_in_one_non_diagnostic_pass(rt, capsys):
    raw, passes = rt
    raw.write_text(COMMITTED)
    os.utime(raw, (1, 1))
    roundtrip.main()
    out = capsys.readouterr().out
    assert "mismatching insns=0 image_identical=True" in out and "[diag]" not in out
    assert f"ROUND-TRIP OK: {len(ENTRIES)} raw instructions of" in out
    # exactly the listed instructions are raw: no branch is hidden from the proof
    assert passes == [{int(l.split()[0], 16) for l in ENTRIES}]
    assert raw.read_text() == COMMITTED and os.stat(raw).st_mtime == 1    # not rewritten
    # the proof is about the image just assembled
    img = raw.parent / "build" / "war_rt.bin"
    assert img.stat().st_size > 0


def test_fallback_converges_to_the_committed_list(rt, capsys):
    """The real image from an incomplete list (three mis-encoded instructions); the
    other ways into the fallback are tried on the tiny program below."""
    raw, passes = rt
    raw.write_text("".join(HEADER + ENTRIES[:50] + ENTRIES[53:]))
    roundtrip.main()
    out = capsys.readouterr().out
    assert "[diag]: mismatching insns=0 image_identical=True" in out
    assert "[full]: mismatching insns=0 image_identical=True" in out
    assert out.splitlines()[-1].startswith("ROUND-TRIP OK:")
    assert raw.read_text() == COMMITTED
    # the last pass is the proof: no branches forced raw
    assert passes[-1] == {int(l.split()[0], 16) for l in ENTRIES}


# ---------------------------------------------------------- tiny real program ---

TINY_CODE = bytes.fromhex(
    "89c8"                  # 10000 mov eax, ecx             as NASM encodes it
    "8bc1"                  # 10002 mov eax, ecx             NASM: 89 c8
    "a110000500"            # 10004 mov eax, [dat_50010]     fixup (BSS)
    "669c"                  # 10009 pushf                    NASM: 9c (shorter)
    "9a785634121000"        # 1000b lcall 0x10:0x12345678    no such NASM instruction
    "75ec"                  # 10012 jne 10000
    "e801000000"            # 10014 call 1001a
    "c3"                    # 10019 ret
    "29d0"                  # 1001a sub eax, edx             as NASM encodes it
    "2bc2"                  # 1001c sub eax, edx             NASM: 29 d0
    "c3")                   # 1001e ret
TINY_DATA = struct.pack("<I", 0x1001A) + b"text\x01\x02\x03\x04"
TINY_RAW = {0x10002, 0x10009, 0x1000B, 0x1001C}


class TinyLE:
    """Two objects and three fixups, with the interface of le.LE that the tools use."""
    entry, initial_esp = 0x10000, 0x50100

    def __init__(self, *_):
        code = le.Obj(1, len(TINY_CODE), 0x10000, le.OBJ_EXEC, 1, 1, TINY_CODE)
        data = le.Obj(2, 0x100, 0x50000, 0, 2, 1, TINY_DATA.ljust(0x100, b"\0"))
        code.file_size, data.file_size = len(TINY_CODE), len(TINY_DATA)
        self.objects = [code, data]
        self.fixups_unique = [le.Fixup(1, 5, le.SRC_OFF32, 2, 0x10), le.Fixup(2, 0, le.SRC_OFF32, 1, 0x1A)]

    def obj(self, k):
        return self.objects[k - 1]

    def loaded_image(self):
        return {o.index: bytearray(o.data) for o in self.objects}


@pytest.fixture
def tiny(rt, monkeypatch):
    """rt on the tiny program, through the real discovery, emitter and NASM."""
    monkeypatch.setattr(analysis.lefmt, "load", TinyLE)
    prog = analysis.Program(modules=b"").discover().partition()
    assert sorted(prog.insns)[-1] == 0x1001E and not prog.gaps()
    monkeypatch.setattr(roundtrip.analysis, "run", lambda: prog)
    monkeypatch.setattr(roundtrip.symbols, "label_map", lambda: {})
    return rt


def listed(text):
    return {int(l.split()[0], 16) for l in text.splitlines() if not l.startswith("#")}


@pytest.mark.parametrize("start", [
    None,                                   # no list at all
    "",                                     # an empty one: the assembler stops at the lcall
    "1000b x\n10009 x\n",                   # assembles, two wrong encodings
    "10002 x\n1000b x\n1001c x\n",          # assembles, one wrong size: everything after it moves
], ids=["missing", "empty", "encodings", "size"])
def test_tiny_fallback_converges(tiny, capsys, start):
    raw, passes = tiny
    if start is not None:
        raw.write_text(start)
    roundtrip.main()
    out = capsys.readouterr().out
    first = out.splitlines()[0]
    if start is not None:
        assert first == "recorded list [full]: " + \
            ("assembler errors" if not start else
             "mismatching insns=%d image_identical=False" % (2 if "1001c" not in start else 1))
        assert passes[0] == listed(start)
    if not start:
        assert "[diag]: assembler errors, demoting 1" in out
    assert "[full]: mismatching insns=0 image_identical=True" in out
    assert out.splitlines()[-1] == "ROUND-TRIP OK: 4 raw instructions of 11"
    assert listed(raw.read_text()) == TINY_RAW and passes[-1] == TINY_RAW
    img = (raw.parent / "build" / "war_rt.bin").read_bytes()
    assert img == TINY_CODE + TINY_DATA

    del passes[:]                           # and the list it wrote is proven in one pass
    roundtrip.main()
    assert passes == [TINY_RAW] and "[diag]" not in capsys.readouterr().out


def test_tiny_image_difference_is_fatal(tiny, monkeypatch, capsys):
    """A wrong data byte shows in no instruction: only the image comparison finds it."""
    raw, passes = tiny
    text = "".join(f"{a:05x} x\n" for a in sorted(TINY_RAW))
    raw.write_text(text)
    real = REAL_EMITTER._emit_bytes
    monkeypatch.setattr(REAL_EMITTER, "_emit_bytes", staticmethod(lambda w, bs: real(w, bs.replace(b"\x03", b"\x13"))))
    with pytest.raises(SystemExit) as ex:
        roundtrip.main()
    assert ex.value.code == 1
    out = capsys.readouterr().out
    assert "recorded list [full]: mismatching insns=0 image_identical=False" in out
    off = len(TINY_CODE) + TINY_DATA.index(b"\x03")
    assert f"image differs at offset {off} (len 43 vs 43)" in out and "ROUND-TRIP OK" not in out
    assert raw.read_text() == text


def test_tiny_without_convergence_fails(tiny, monkeypatch, capsys):
    raw, passes = tiny
    real = roundtrip.parse_listing

    def listing(lst):                       # some instruction is always wrong
        out = real(lst)
        out[min(out)] = b"\xcc\xcc"
        return out
    monkeypatch.setattr(roundtrip, "parse_listing", listing)
    raw.write_text("")
    with pytest.raises(SystemExit) as ex:
        roundtrip.main()
    assert ex.value.code == 1
    out = capsys.readouterr().out
    assert out.splitlines()[-1] == "did not converge" and len(passes) == 1 + 20
    assert raw.read_text() == ""


def test_tiny_unexplained_assembler_error_fails(tiny, monkeypatch, capsys):
    """An error on a line that is no instruction demotes nothing: give up at once."""
    raw, passes = tiny
    real = REAL_EMITTER.emit

    def emit_bad(self, src):
        real(self, src)
        with open(src, "a") as fh:
            fh.write("    no_such_instruction eax, eax\n")
    monkeypatch.setattr(REAL_EMITTER, "emit", emit_bad)
    raw.write_text("".join(f"{a:05x} x\n" for a in sorted(TINY_RAW)))
    with pytest.raises(SystemExit) as ex:
        roundtrip.main()
    assert ex.value.code == 1 and len(passes) == 2
    assert "demoting 0" in capsys.readouterr().out


# ------------------------------------------------------------- control flow ---

@pytest.fixture
def scripted(rt, monkeypatch):
    """main() with attempt() replaced by scripted results (control flow only, no NASM).
    run(results) -> the force_raw set of each attempt."""
    raw, _ = rt

    def run(results):
        forced, left = [], list(results)

        def attempt(p, names, force_raw, src, out, want):
            forced.append(set(force_raw))
            stderr, bad, ok = left.pop(0)
            with open(out, "wb") as fh:
                fh.write(want if ok else b"?")
            return types.SimpleNamespace(line_addr={}), stderr, set(bad), ok

        monkeypatch.setattr(roundtrip, "attempt", attempt)
        roundtrip.main()
        assert not left, "not every scripted pass was run"
        return forced
    return raw, run


GOOD = (None, (), True)
LISTED = {int(l.split()[0], 16) for l in ENTRIES}


@pytest.mark.parametrize("defect", [
    (None, (), False),                         # only the image differs
    (None, (0x10000,), True),                  # only one instruction differs
    (None, (0x10000,), False),
    ("war_rt.asm:1: error: x", (), False),     # NASM fails
])
def test_fast_pass_defect_is_never_accepted(scripted, capsys, defect):
    """Whatever is wrong with the first pass, main() goes through the full loop;
    the first pass's own report demotes nothing."""
    raw, run = scripted
    raw.write_text(COMMITTED)
    fast, diag, full = run([defect, GOOD, GOOD])
    assert fast == full == LISTED and diag > LISTED     # diag: the branches too
    out = capsys.readouterr().out
    assert "iter 0 [diag]" in out and "iter 1 [full]" in out
    assert raw.read_text() == COMMITTED


def test_without_a_list_the_diagnostic_loop_runs_first(scripted, capsys):
    raw, run = scripted
    bad = sorted(LISTED)[:2]
    diag, diag2, full = run([(None, bad, False), GOOD, GOOD])
    assert diag and not diag & set(bad) and diag2 == diag | set(bad) and full == set(bad)
    assert "recorded list" not in capsys.readouterr().out
    assert raw.read_text() == "".join(HEADER + [l for l in ENTRIES if int(l.split()[0], 16) in bad])


def test_persistent_image_difference_fails(scripted, capsys):
    raw, run = scripted
    raw.write_text(COMMITTED)
    with pytest.raises(SystemExit) as ex:
        run([(None, (), False)] * 3)
    assert ex.value.code == 1
    out = capsys.readouterr().out
    assert "image differs at offset 0" in out and "ROUND-TRIP OK" not in out
    assert raw.read_text() == COMMITTED
