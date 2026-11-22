"""wc1.oldcc: the original compiler, Watcom C/C++ 10.0a, under Wine.

The first tests need no compiler.  The ones marked needs_10a run the
installed 10.0a (original/watcom/10.0a, git-ignored, `make toolchain`) and
skip with the reason when it or wine is missing; `make verify` itself fails
without the compiler (its toolchain check), so a skip here cannot hide a
missing compiler there.
"""
import io
import os
import tarfile

import pytest

from wc1 import match, oldcc, path


def _missing():
    try:
        oldcc.require()
        oldcc.find_wine()
    except oldcc.OldCCError as e:
        return str(e)
    return None


needs_10a = pytest.mark.skipif(_missing() is not None, reason=f"{_missing()}")


def test_compile_timeout_raises_and_kills_wineserver(tmp_path, monkeypatch):
    """A wine that never returns: OldCCTimeout, wineserver -k, no .log left."""
    wine = tmp_path / "wine"
    wine.write_text("#!/bin/sh\nexec sleep 30\n")
    wine.chmod(0o755)
    killed = []
    monkeypatch.setenv("WC1_WINE", str(wine))
    monkeypatch.setattr(oldcc, "require", lambda: str(tmp_path))
    monkeypatch.setattr(oldcc, "ensure_prefix", lambda *a, **kw: None)
    monkeypatch.setattr(oldcc, "kill_wineserver", lambda env: killed.append(env.get("WINEPREFIX")))
    src = tmp_path / "f.c"
    src.write_text("int f(void) { return 0; }\n")
    out = tmp_path / "obj" / "f.obj"
    with pytest.raises(oldcc.OldCCTimeout):
        oldcc.compile_c(str(src), "-q -s", str(out), timeout=1)
    assert len(killed) == 1
    assert not os.path.exists(str(out) + ".log")


def test_kill_wineserver_runs_wineserver_k(tmp_path):
    mark = tmp_path / "args"
    ws = tmp_path / "wineserver"
    ws.write_text(f"#!/bin/sh\necho \"$@\" > {mark}\n")
    ws.chmod(0o755)
    oldcc.kill_wineserver({"PATH": str(tmp_path)})
    assert mark.read_text().strip() == "-k"


def test_normalize_flags_maps_ow2_quiet():
    got = oldcc.normalize_flags("-q -zl -bt=dos -s -ot -ol -4r -zp2").split()
    assert got[0] == "-zq" and "-q" not in got and "-zl" in got


def test_win_path_is_z_drive():
    assert oldcc.win_path("/tmp/x y/a.c") == "Z:\\tmp\\x y\\a.c"


def test_wine_env_is_headless_with_project_prefix(monkeypatch):
    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-1")
    monkeypatch.delenv("WINEPREFIX", raising=False)
    monkeypatch.delenv("WINEDLLOVERRIDES", raising=False)
    env = oldcc.wine_env()
    assert "DISPLAY" not in env and "WAYLAND_DISPLAY" not in env
    assert env["WINEPREFIX"].endswith(os.path.join("build", "oldcc", "wineprefix"))
    assert env["WINEDLLOVERRIDES"].startswith("mscoree,mshtml=")


def test_manifest_lists_compiler_headers_and_optional_libraries():
    m = {rel: req for _h, rel, req in oldcc.manifest()}
    assert m["binnt/wcc386.exe"] and m["binb/wcc386.exe"]
    assert m["h/string.h"] and m["h/stdlib.h"] and m["h/stdio.h"]
    assert m["lib386/dos/clib3r.lib"] is False
    assert all(len(h) == 64 for h, _r, _q in oldcc.manifest())


def test_check_reports_missing_files(tmp_path):
    bad = oldcc.check(str(tmp_path))
    assert "missing binb/wcc386.exe" in bad
    assert not any("lib386" in b for b in bad)          # libraries are optional
    assert any("lib386" in b for b in oldcc.check(str(tmp_path), optional=True))


def test_require_tells_how_to_install(monkeypatch, tmp_path):
    monkeypatch.setenv("WC1_WATCOM10A", str(tmp_path))
    with pytest.raises(oldcc.OldCCError, match="make toolchain"):
        oldcc.require()


def test_install_rejects_unknown_tarball(monkeypatch, tmp_path):
    tb = tmp_path / "wcc10.0a.tar.gz"
    with tarfile.open(tb, "w:gz") as t:
        data = b"not a compiler"
        ti = tarfile.TarInfo("./binnt/wcc386.exe")
        ti.size = len(data)
        t.addfile(ti, io.BytesIO(data))
    monkeypatch.setenv("WC1_WATCOM10A", str(tmp_path / "inst"))
    with pytest.raises(oldcc.OldCCError, match="sha256"):
        oldcc.install(str(tb))


def test_install_rejects_altered_directory(monkeypatch, tmp_path):
    src = tmp_path / "src"
    for rel in ("binnt/wcc386.exe", "binb/wcc386.exe"):
        (src / rel).parent.mkdir(parents=True, exist_ok=True)
        (src / rel).write_bytes(b"x")
    monkeypatch.setenv("WC1_WATCOM10A", str(tmp_path / "inst"))
    with pytest.raises(oldcc.OldCCError, match="incomplete or altered"):
        oldcc.install(str(src))


@needs_10a
def test_installed_compiler_is_the_verified_one():
    assert oldcc.check() == []


@needs_10a
def test_probe_shows_patch_a_compare_promotion_only_under_10a(tmp_path):
    """The 10.0a code-generator fix (README, patch A): an unsigned char
    compared with a constant is promoted to int (`and eax,0xff; cmp eax,imm`);
    OW2 compares the byte register.  war.exe's game code has only the
    promoted form (docs/subsystems/compiler.md)."""
    assert oldcc.PROMOTED in oldcc.smoke()
    src = tmp_path / "probe.c"
    src.write_text(oldcc.SMOKE_C)
    mod = match.compile_c(str(src), "-q -zl -bt=dos -s -ot -ol -4r -zp2", str(tmp_path / "p.obj"),
                          cc="ow2")
    _i, text = mod.seg("_TEXT")
    assert oldcc.PROMOTED not in bytes(text.data)
    assert oldcc.NARROWED in bytes(text.data)


@needs_10a
def test_compile_reports_diagnostics(tmp_path, capsys):
    src = tmp_path / "bad.c"
    src.write_text("int Bad(void) { return undeclared; }\n")
    with pytest.raises(SystemExit, match="Watcom 10.0a"):
        oldcc.compile_c(str(src), "-q -zl -bt=dos", str(tmp_path / "bad.obj"))
    assert "E1011" in capsys.readouterr().err
