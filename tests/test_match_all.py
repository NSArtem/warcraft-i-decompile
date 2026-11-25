"""wc1.match --all (make match-all): one discovery, parallel workers, every
failure reported."""
import os
import re

import pytest

from wc1 import match, path


def test_all_srcs_are_top_level_and_src_entries():
    srcs = match.all_srcs()
    assert "src/init.c" in srcs and srcs == sorted(set(srcs))
    assert all(s.endswith(".c") and os.path.isfile(path(s)) for s in srcs)
    assert len(srcs) > 200


def test_unique_object_paths():
    srcs = match.all_srcs()
    objs = {match.unique_obj(s, "match", "all", "10.0a") for s in srcs}
    assert len(objs) == len(srcs)          # several files share a basename


def test_match_all_reports_every_failure(tmp_path, capsys):
    good = "src/init.c"
    text = open(path(good)).read()
    bad = tmp_path / "init_bad.c"
    # change the code but keep the file compiling: flip the first decimal literal
    m = re.search(r"\b(\d+)\b", text.split("*/", 1)[1])
    assert m
    head, body = text.split("*/", 1)
    body = body[:m.start()] + str(int(m.group(1)) + 1) + body[m.end():]
    bad.write_text(head + "*/" + body)
    broken = tmp_path / "broken.c"
    broken.write_text("/* codegen-compiler: 10.0a */\nint f(void) { return }\n")
    failed = match.match_all([good, str(bad), str(broken)], jobs=3)
    out = capsys.readouterr().out
    assert failed == [str(bad), str(broken)]
    assert out.index(f"== {good}") < out.index(f"== {bad}") < out.index(f"== {broken}")
    assert "MATCH     InitPaths_" in out and "MISMATCH" in out, out
    assert "match-all: 3 files, 2 failed" in out


def test_makefile_uses_match_all():
    mk = open(path("Makefile")).read()
    rule = mk.split("\nmatch-all:", 1)[1].split("\n\n", 1)[0]
    assert "wc1.match --all" in rule



def test_compile_check_timeout_is_a_toolchain_error(monkeypatch, capsys):
    """A compile timeout is a stuck toolchain, not a C error: compile_check
    raises CompileTimeout and the CLI prints [TOOLCHAIN ERROR] and exits 78."""
    import multiprocessing.dummy
    import sys

    def stuck(src, cflags, out, cc=None, **kw):
        if src.endswith("b.c"):
            raise match.CompileTimeout("error: wcc386 timed out (>180s)")
    # a thread pool: the workers see the monkeypatched compile_c
    monkeypatch.setattr(match, "_pool", lambda jobs, *a, **kw: multiprocessing.dummy.Pool(1))
    monkeypatch.setattr(match, "compile_c", stuck)
    with pytest.raises(match.CompileTimeout, match=r"timed out.*b\.c"):
        match.compile_check(["src/a.c", "src/b.c"])
    monkeypatch.setattr(sys, "argv", ["wc1.match", "--compile-check", "src/a.c", "src/b.c"])
    assert match.main() == 78
    assert "[TOOLCHAIN ERROR]" in capsys.readouterr().err


def test_cli_single_file_and_compile_check(monkeypatch, capsys):
    """`wc1.match <src>` (exit 0 only when everything matches) and --compile-check."""
    import sys

    def cli(*argv):
        monkeypatch.setattr(sys, "argv", ["wc1.match", *argv])
        rc = match.main()
        return rc, capsys.readouterr().out
    rc, out = cli(path("src", "init.c"))
    assert rc == 0 and "MATCH     InitPaths_" in out and "MISMATCH" not in out, out
    rc, out = cli(path("src", "mod_1b800", "snd_event_reference.c"))
    assert rc == 1 and "MISMATCH" in out, out
    rc, out = cli("--compile-check", path("src", "init.c"))
    assert rc == 0 and "compile check: 1 files x 2 compilers, 0 failures" in out, out
