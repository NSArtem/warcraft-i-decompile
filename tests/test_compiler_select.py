"""Per-file compiler selection: the `codegen-compiler:` header.

A C file names the compiler its T3 match is proved with; no header means
Open Watcom 2.  wc1.match, wc1.build (through match.compile_c), wc1.cemu and
wc1.codegen_sweep all follow it.
"""
import os

import pytest

from wc1 import cemu, codegen_sweep, match, oldcc, path

FLAGS = "-q -zl -bt=dos -s -ot -ol -4r -zp2"


def _10a_missing():
    try:
        oldcc.require()
        oldcc.find_wine()
    except oldcc.OldCCError as e:
        return str(e)
    return None


needs_10a = pytest.mark.skipif(_10a_missing() is not None, reason=f"{_10a_missing()}")


def _probe(tmp_path, header):
    src = tmp_path / "probe.c"
    src.write_text(header + "\n" + oldcc.SMOKE_C)
    return str(src)


def test_header_selects_compiler(tmp_path):
    assert match.file_cc(_probe(tmp_path, "")) == "ow2"
    assert match.file_cc(_probe(tmp_path, "/* codegen-compiler: 10.0a */")) == "10.0a"
    assert match.file_cc(_probe(tmp_path, "/* codegen-flags: -s -ot\n * codegen-compiler: ow2\n */")) == "ow2"
    with pytest.raises(SystemExit, match="unknown codegen-compiler"):
        match.file_cc(_probe(tmp_path, "/* codegen-compiler: 11.0 */"))
    assert match.other_cc("ow2") == "10.0a" and match.other_cc("10.0a") == "ow2"


def test_compile_c_dispatches_by_header(tmp_path, monkeypatch):
    seen = []

    def fake(src, cflags, out, includes=()):
        seen.append(src)
        return "MOD"

    monkeypatch.setattr(oldcc, "compile_c", fake)
    src = _probe(tmp_path, "/* codegen-compiler: 10.0a */")
    assert match.compile_c(src, FLAGS, str(tmp_path / "a.obj")) == "MOD"
    assert seen == [src]
    # an explicit cc overrides the header
    mod = match.compile_c(src, FLAGS, str(tmp_path / "b.obj"), cc="ow2")
    assert mod.seg("_TEXT")[1] is not None and len(seen) == 1


def test_ow2_diagnostics_stay_in_the_object_directory(tmp_path):
    """wcc386 writes <name>.err into its working directory; compile_c runs it
    in the object's directory so no stray .err lands in the repo root."""
    src = tmp_path / "warn.c"
    src.write_text("int Warn(void) { int unused; return 0; }\n")
    out = tmp_path / "obj" / "warn.obj"
    out.parent.mkdir()
    match.compile_c(str(src), FLAGS + " -w3", str(out), cc="ow2")
    assert not os.path.exists("warn.err") and not os.path.exists(path("warn.err"))


@needs_10a
def test_declared_10a_file_compiles_with_10a(tmp_path):
    mod = match.compile_c(_probe(tmp_path, "/* codegen-compiler: 10.0a */"), FLAGS,
                          str(tmp_path / "p.obj"))
    code = bytes(mod.seg("_TEXT")[1].data)
    assert oldcc.PROMOTED in code and oldcc.NARROWED not in code


@needs_10a
def test_cemu_and_sweep_follow_the_header(tmp_path):
    src = _probe(tmp_path, "/* codegen-compiler: 10.0a */")
    code = bytes(cemu.compile_module(src, FLAGS).seg("_TEXT")[1].data)
    assert oldcc.PROMOTED in code
    mod, err = codegen_sweep.compile_c(src, "-s -ot -ol -4r -zp2", str(tmp_path / "s.obj"))
    assert err == "" and oldcc.PROMOTED in bytes(mod.seg("_TEXT")[1].data)
    mod, err = codegen_sweep.compile_c(src, "-s -ot -ol -4r -zp2", str(tmp_path / "t.obj"), cc="ow2")
    assert oldcc.NARROWED in bytes(mod.seg("_TEXT")[1].data)


def test_verify_requires_the_toolchain_and_the_compile_check():
    """make verify fails without Watcom 10.0a (toolchain-check) and checks
    that every C file compiles under both compilers (compile-check)."""
    mk = open(path("Makefile")).read()
    verify = next(l for l in mk.splitlines() if l.startswith("verify:"))
    deps = verify.split(":", 1)[1].split()
    assert deps[0] == "toolchain-check" and "compile-check" in deps and "match-all" in deps


def test_compile_check_reports_failures(tmp_path):
    src = tmp_path / "broken.c"
    src.write_text("int Broken(void) { return undeclared_name; }\n")
    bad = match.compile_check([str(src)])
    assert (str(src), "ow2") in bad


def test_progress_reports_t3_per_compiler():
    from wc1 import progress
    rows = [{"scope": "in", "c": "T3", "cc": "10.0a", "out_reason": None, "kind": "game",
             "unclassified": False, "named": True, "blocker": False, "done": True},
            {"scope": "in", "c": "T3", "cc": "ow2", "out_reason": None, "kind": "game",
             "unclassified": False, "named": True, "blocker": False, "done": True}]
    s = progress.summarize(rows)
    assert s["T3_by_compiler"] == {"10.0a": 1, "ow2": 1}
    assert s["c"]["T3"] == 2 and s["done"] == 2
    assert "by compiler: 10.0a 1, ow2 1" in progress.report(s)
