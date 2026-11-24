"""Real end-to-end Wave 4A + Wave 4B integration tests in disposable Git repos.

Uses real Watcom 10.0a, real Open Watcom 2, real war.exe, real `make verify`,
and real Git transactions; mocks ONLY the LLM response in the research/recovery
cases. The mechanical zero-LLM tests have no LLM binary on PATH at all.
"""
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import tomllib

import pytest

from wc1 import oldcc, path
from wave4_repo import seed_analysis_cache


def _require_toolchains():
    if not (Path(path("original/install/war.exe")).is_file() and os.environ.get("WATCOM")
            and all(shutil.which(cmd) for cmd in ("git", "make", "nasm", "wlink", "wine"))):
        pytest.skip("requires original game and Nix dev toolchains")
    try:
        return oldcc.require()
    except oldcc.OldCCError:
        pytest.skip("requires Watcom 10.0a (make toolchain)")


@pytest.fixture
def short_repo():
    base = "/tmp/opencode" if os.path.isdir("/tmp/opencode") else "/tmp"
    with tempfile.TemporaryDirectory(prefix="w4a-", dir=base) as directory:
        yield Path(directory)


def _init_base_repo(repo):
    def write(name, text):
        fn = repo / name
        fn.parent.mkdir(parents=True, exist_ok=True)
        fn.write_text(text)
        return fn

    def git(*args):
        return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()

    for name in ("Makefile", "asm/wc1.inc", "analysis/modules.toml", "analysis/raw_insns.txt",
                 "analysis/provenance/watcom10a.sha256"):
        (repo / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path(name), repo / name)
    original = repo / "original/install/war.exe"
    original.parent.mkdir(parents=True)
    original.symlink_to(path("original", "install", "war.exe"))
    seed_analysis_cache(repo)
    write(".gitignore", "/build/\n/original/\n__pycache__/\n.pytest_cache/\n")
    return write, git


def _commit_fixture(git):
    git("init", "-q")
    git("config", "user.name", "Wave 4A fixture")
    git("config", "user.email", "wave4a@example.test")
    git("config", "commit.gpgsign", "false")
    git("config", "core.hooksPath", ".git/hooks")
    git("add", "--", ".gitignore", "Makefile", "asm", "analysis", "src", "tests")
    git("commit", "-qm", "Wave 4A fixture")
    return git("rev-parse", "HEAD")


def _make_env(repo, watcom, fake_bin=None):
    prefix = repo / "build/wine"
    seed = Path(oldcc.wine_env()["WINEPREFIX"])
    if not (prefix / "system.reg").is_file() and (seed / "system.reg").is_file():
        shutil.copytree(seed, prefix, symlinks=True)
    p_str = f"{fake_bin}{os.pathsep}{os.environ['PATH']}" if fake_bin else os.environ["PATH"]
    env = dict(
        os.environ,
        WC1_ROOT=str(repo),
        WC1_WATCOM10A=watcom,
        WINEPREFIX=str(prefix),
        PYTEST_XDIST_AUTO_NUM_WORKERS="1",
        PATH=p_str,
    )
    for key in ("PYTEST_XDIST_WORKER", "PYTEST_XDIST_WORKER_COUNT", "PYTEST_XDIST_TESTRUNUID"):
        env.pop(key, None)
    return env


def _run_cli(cmd, repo, env, timeout=240):
    try:
        with subprocess.Popen(cmd, cwd=repo, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              text=True, start_new_session=True) as proc:
            try:
                out, _ = proc.communicate(timeout=timeout)
                return proc.returncode, out
            except subprocess.TimeoutExpired:
                rows = [tuple(map(int, line.split())) for line in
                        subprocess.check_output(["ps", "-eo", "pid=,ppid=,pgid="], text=True).splitlines()]
                descendants = {proc.pid}
                while True:
                    found = {pid for pid, ppid, _ in rows if ppid in descendants} - descendants
                    if not found:
                        break
                    descendants.update(found)
                groups = {pgid for pid, _, pgid in rows if pid == pgid and pid in descendants}
                for group in groups | {proc.pid}:
                    try:
                        os.killpg(group, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                oldcc.kill_wineserver(env)
                out, _ = proc.communicate(timeout=10)
                pytest.fail(f"Wave 4A fixture timed out:\n{out}")
    finally:
        if (repo / "build/wine/system.reg").exists():
            oldcc.kill_wineserver(env)


# ---------------------------------------------------------------------------
# 1. Zero-LLM mechanical reconciliation -> T3 promotion + Build A IDENTICAL
# ---------------------------------------------------------------------------

def test_wave4a_mechanical_zero_llm_promotion_end_to_end(short_repo):
    watcom = _require_toolchains()
    repo = short_repo
    write, git = _init_base_repo(repo)
    ref = "src/mod_19470/game_set_random_seed_reference.c"
    toml = "analysis/symbols/mod_19470.toml"
    write(ref, """/* codegen-compiler: 10.0a */
extern long game_rng_seed;

void GameSetRandomSeed(long seed)
{
    game_rng_seed = seed;
}
""")
    write(toml, f"""[[func]]
addr = 0x19470
name = "GameSetRandomSeed"
conv = "watcall"
proto = "void GameSetRandomSeed(long seed)"
module = "mod_19470"
confidence = "high"
ref = "{ref}"
ref_verified_by = "difftest: tests/test_fixture.py::test_seed"
t3_blocker = "codegen: unresolved _game_rng_seed"
evidence = ["0x19470 stores EAX into 0x50d7c"]

[[data]]
addr = 0x50d7c
name = "dat_50d7c"
type = "long"
confidence = "high"
evidence = ["RNG seed dword at 0x50d7c"]
""")
    write("tests/test_fixture.py", f"""from wc1 import cemu, path
from wc1.emu import Emu

EXTRA = {{"_game_rng_seed": 0x50d7c}}


def test_seed():
    emu = Emu()
    mod = cemu.load(emu, path("{ref}"), extra=EXTRA)
    emu.put_u32(0x50d7c, 0)
    assert not cemu.run_pair(emu, 0x19470, mod, "GameSetRandomSeed_", 0x12345678, watch=[(0x50d7c, 4)], out_regs=())
""")
    head = _commit_fixture(git)
    env = _make_env(repo, watcom)

    rc, out = _run_cli(
        [sys.executable, "-m", "wc1.overnight", "--headless", "--wave", "wave4a",
         "--wave4a-max-calls", "0", "--max-modules", "1", "--window-budget", "1", "--no-sleep"],
        repo, env,
    )
    assert rc == 0, out
    assert "[COMMITTED " in out and "IDENTICAL (loaded image, entry, stack, fixups)" in out, out
    assert git("rev-parse", "HEAD^") == head
    assert not git("status", "--porcelain"), out
    receipt = json.loads((repo / "build/wave4/reconcile_outcomes/data_50d7c.json").read_text())
    assert receipt["outcome"] == "PROMOTED"
    assert receipt["method"] == "mechanical" and receipt["llm_calls"] == 0
    assert receipt["promoted"] == ["0x19470"]
    assert "dat_50d7c = seed;" in (repo / ref).read_text()
    func = tomllib.loads((repo / toml).read_text())["func"][0]
    assert func["src"] == ref and func["confidence"] == "verified" and "ref" not in func
    mappings = json.loads((repo / "build/wave4/mappings.json").read_text())["mappings"]
    assert mappings["_game_rng_seed"]["canonical_name"] == "dat_50d7c"
    metrics = json.loads((repo / "build/wave4/metrics.json").read_text())
    assert metrics["wave4a"]["t3_promotions"] == 1
    assert metrics["wave4a"]["zero_llm_t3_promotions"] == 1
    assert metrics["wave4a"]["llm_calls"] == 0


# ---------------------------------------------------------------------------
# 2. Bounded LLM research adding missing [[data]] + verify rollback gate
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("gate", [None, "verify"])
def test_wave4a_research_missing_data_and_rollback_end_to_end(short_repo, gate):
    watcom = _require_toolchains()
    repo = short_repo
    write, git = _init_base_repo(repo)
    ref = "src/mod_13f60/dispatch_fatal_reference.c"
    toml = "analysis/symbols/mod_13f60.toml"
    orig_c = """/* codegen-compiler: 10.0a */
extern void __cdecl FatalError(const char *fmt, ...);
extern const char str_56b10[11];

int DispatchFatal(void *u)
{
    FatalError(str_56b10);
    return 0;
}
"""
    orig_t = f"""[[func]]
addr = 0x30bf0
name = "FatalError"
conv = "cdecl"
proto = "void FatalError(const char *fmt, ...)"
confidence = "high"
evidence = ["fatal error at 0x30bf0"]

[[func]]
addr = 0x145d0
name = "DispatchFatal"
conv = "watcall"
proto = "int DispatchFatal(void *u)"
module = "mod_13f60"
confidence = "high"
ref = "{ref}"
ref_verified_by = "difftest: tests/test_fixture.py::test_dispatch_fatal"
t3_blocker = "codegen: missing [[data]] 0x56b10"
evidence = ["0x145d0 calls FatalError with 0x56b10"]
"""
    write(ref, orig_c)
    write(toml, orig_t)
    test_extra = (
        '\n\ndef test_full_gate():\n'
        '    with open("stray_verify.txt", "w") as fh:\n'
        '        fh.write("stray")\n'
        '    assert False, "controlled wave4a verify failure"\n'
    ) if gate == "verify" else ""
    write("tests/test_fixture.py", f"""from wc1 import cemu, path
from wc1.emu import Emu

EXTRA = {{"_str_56b10": 0x56b10}}


def test_dispatch_fatal():
    emu = Emu()
    mod = cemu.load(emu, path("{ref}"), extra=EXTRA)
    calls = []
    emu.stubs[0x30bf0] = lambda e: (calls.append(e.read(e.u32(e.reg("esp") + 4), 10)), 0)[1]
    assert not cemu.run_pair(emu, 0x145d0, mod, "DispatchFatal_", 0, out_regs=("eax",))
    assert calls == [b"dispatch:5", b"dispatch:5"]
""" + test_extra)
    head = _commit_fixture(git)

    payload = {
        "type": "result",
        "structured_output": {
            "decision": "apply",
            "summary": "Add order_dispatch_error at 0x56b10 and reference it in DispatchFatal",
            "uncertainties": [],
            "toml_entries": [{
                "toml_file": toml,
                "toml_block": (
                    '[[data]]\naddr = 0x56b10\nname = "order_dispatch_error"\n'
                    'type = "const char[11]"\nconfidence = "high"\n'
                    'evidence = ["NUL-terminated string dispatch:5 at 0x56b10"]\n'
                ),
            }],
            "file_patches": [{
                "path": ref,
                "old": "extern const char str_56b10[11];\n\nint DispatchFatal(void *u)\n{\n    FatalError(str_56b10);",
                "new": "extern const char order_dispatch_error[11];\n\nint DispatchFatal(void *u)\n{\n    FatalError(order_dispatch_error);",
            }],
        },
    }
    model = write("build/fake-bin/claude", f"""#!/usr/bin/env python3
import sys
from pathlib import Path
Path("build/w4a.prompt").write_text(sys.stdin.read())
print({json.dumps(payload)!r})
""")
    model.chmod(0o755)
    env = _make_env(repo, watcom, fake_bin=model.parent)

    rc, out = _run_cli(
        [sys.executable, "-m", "wc1.overnight", "--headless", "--wave", "wave4a",
         "--wave4a-max-calls", "1", "--max-modules", "1", "--window-budget", "1", "--no-sleep"],
        repo, env,
    )
    assert rc == 0, out
    assert not git("status", "--porcelain"), out
    assert "0x56b10" in (repo / "build/w4a.prompt").read_text()
    if gate is None:
        assert git("rev-parse", "HEAD^") == head and "[COMMITTED " in out
        assert "IDENTICAL (loaded image, entry, stack, fixups)" in out
        doc = tomllib.loads((repo / toml).read_text())
        fn = next(f for f in doc["func"] if f["addr"] == 0x145d0)
        dt = next(d for d in doc["data"] if d["addr"] == 0x56b10)
        assert fn["src"] == ref and fn["confidence"] == "verified"
        assert dt["name"] == "order_dispatch_error"
    else:
        assert git("rev-parse", "HEAD") == head and "[ROLLED BACK]" in out
        assert (repo / ref).read_text() == orig_c
        assert (repo / toml).read_text() == orig_t
        assert not (repo / "stray_verify.txt").exists()
        archived, = (repo / "build/failed").glob("*_w4a_data_56b10")
        assert (archived / "stray_verify.txt").is_file()


# ---------------------------------------------------------------------------
# 3. Verified intermediate RECONCILED (no immediate T3) -> Wave 4B handoff
# ---------------------------------------------------------------------------

def test_wave4a_reconciled_intermediate_then_wave4b_end_to_end(short_repo):
    watcom = _require_toolchains()
    repo = short_repo
    write, git = _init_base_repo(repo)
    ref = "src/cmd_123f0/fog_map_clear_reference.c"
    toml = "analysis/symbols/cmd.toml"
    before_body = "    unsigned short *p = fog_map;\n    unsigned short i;"
    after_body = "    unsigned short i;\n    register unsigned short *p = fog_map;"
    write(ref, """/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -oa -4r -zp2 */
extern unsigned short *stale_fog_map;
void FogMapClear(void)
{
    unsigned short *p = stale_fog_map;
    unsigned short i;
    for (i = 0; i < 0x1000; i++)
        *p++ = 0;
}
""")
    write(toml, f"""[[func]]
addr = 0x12404
name = "FogMapClear"
conv = "watcall"
proto = "void FogMapClear(void)"
module = "CMD.C"
confidence = "high"
ref = "{ref}"
ref_verified_by = "difftest: tests/test_fixture.py::test_fog"
t3_blocker = "regalloc: loop keeps fog_map in wrong register plus stale _stale_fog_map"
evidence = ["original function at 0x12404"]

[[data]]
addr = 0x58578
name = "fog_map"
type = "unsigned short *"
confidence = "high"
evidence = ["original fog_map at 0x58578"]
""")
    write("tests/test_fixture.py", f"""from wc1 import cemu, path
from wc1.emu import Emu

EXTRA = {{"_stale_fog_map": 0x58578}}


def test_fog():
    emu = Emu()
    mod = cemu.load(emu, path("{ref}"), extra=EXTRA)
    buf = emu.alloc(0x2008)
    emu.write(buf, b"\\xff" * 0x2008)
    emu.put_u32(0x58578, buf)
    assert not cemu.run_pair(emu, 0x12404, mod, "FogMapClear_", watch=[(buf, 0x2008)], out_regs=())
""")
    head0 = _commit_fixture(git)
    payload_4b = {"type": "result", "structured_output": {
        "diagnosis": "recover register allocation", "patches": [{"old": before_body, "new": after_body}],
    }}
    model = write("build/fake-bin/claude", f"""#!/usr/bin/env python3
import sys
sys.stdin.read()
print({json.dumps(payload_4b)!r})
""")
    model.chmod(0o755)
    env = _make_env(repo, watcom, fake_bin=model.parent)

    # Step 1: Wave 4A mechanical-only fixes stale_fog_map -> fog_map (0 LLM), commits RECONCILED (still T4!)
    rc1, out1 = _run_cli(
        [sys.executable, "-m", "wc1.overnight", "--headless", "--wave", "wave4a",
         "--wave4a-max-calls", "0", "--max-modules", "1", "--window-budget", "1", "--no-sleep"],
        repo, env,
    )
    assert rc1 == 0, out1
    assert "[COMMITTED " in out1 and "wave4a: reconcile data_58578" in out1, out1
    head1 = git("rev-parse", "HEAD")
    assert git("rev-parse", "HEAD^") == head0
    rec1 = json.loads((repo / "build/wave4/reconcile_outcomes/data_58578.json").read_text())
    assert rec1["outcome"] == "RECONCILED" and rec1["llm_calls"] == 0
    assert rec1["unresolved_before"] == 1 and rec1["unresolved_after"] == 0
    assert "stale_fog_map" not in (repo / ref).read_text()
    # Still T4 after Wave 4A (genuine regalloc codegen blocker remains)
    assert "ref" in tomllib.loads((repo / toml).read_text())["func"][0]

    # Step 2: Wave 4B picks up the now dependency-clean 0x12404 and promotes it to T3!
    rc2, out2 = _run_cli(
        [sys.executable, "-m", "wc1.overnight", "--headless", "--wave", "wave4b",
         "--max-modules", "1", "--wave4-max-calls", "1", "--window-budget", "1", "--no-sleep"],
        repo, env,
    )
    assert rc2 == 0, out2
    assert "[COMMITTED " in out2 and "IDENTICAL (loaded image, entry, stack, fixups)" in out2, out2
    assert git("rev-parse", "HEAD^") == head1
    func = tomllib.loads((repo / toml).read_text())["func"][0]
    assert func["src"] == ref and func["confidence"] == "verified"
