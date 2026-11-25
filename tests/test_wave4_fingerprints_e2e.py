"""Real-project end-to-end cache preservation & invalidation tests for Wave 4A and Wave 4B.

Exercises REAL `original/install/war.exe`, REAL Watcom 10.0a, REAL Open Watcom 2,
REAL OMF relocations, REAL `wc1.match`, REAL `make verify` (Build A `IDENTICAL`),
and REAL Git transactions in disposable repositories — mocking ONLY the LLM response.

Demonstrates for BOTH Wave 4B and Wave 4A:
  1. Preservation of a cached miss after a demonstrably unrelated symbol addition & commit
     (0 LLM calls, `preserved_unrelated >= 1` in `build/wave4/metrics.json`).
  2. Invalidation of the cached miss after a demonstrably relevant dependency change & commit
     (LLM invoked again, `invalidated_dep_change >= 1` in `build/wave4/metrics.json`).
"""
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tomllib

import pytest

from wc1 import oldcc, path, wave4_fp
from wave4_repo import disposable_repo, seed_analysis_cache


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
    with disposable_repo("w4fp-") as repo:
        yield repo


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
    git("config", "user.name", "Wave 4 FP fixture")
    git("config", "user.email", "wave4fp@example.test")
    git("config", "commit.gpgsign", "false")
    git("config", "core.hooksPath", ".git/hooks")
    git("add", "--", ".gitignore", "Makefile", "asm", "analysis", "src", "tests")
    git("commit", "-qm", "Wave 4 FP fixture")
    return git("rev-parse", "HEAD")


def _make_env(repo, watcom, fake_bin):
    prefix = repo / "build/wine"
    seed = Path(oldcc.wine_env()["WINEPREFIX"])
    if not (prefix / "system.reg").is_file() and (seed / "system.reg").is_file():
        shutil.copytree(seed, prefix, symlinks=True, ignore=shutil.ignore_patterns("*.tmp"))
    env = dict(
        os.environ,
        WC1_ROOT=str(repo),
        WC1_WATCOM10A=watcom,
        WINEPREFIX=str(prefix),
        PYTEST_XDIST_AUTO_NUM_WORKERS="1",
        PATH=f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
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
                pytest.fail(f"Wave 4 FP fixture timed out:\n{out}")
    finally:
        if (repo / "build/wine/system.reg").exists():
            oldcc.kill_wineserver(env)


def test_real_project_wave4b_cache_preservation_and_invalidation(short_repo):
    """Real `FogMapClear` (0x12404) under Watcom 10.0a:
      1. Clean NO_IMPROVEMENT cached with real OMF relocations (`_fog_map`).
      2. Unrelated symbol added + committed -> cache HIT preserved (0 LLM calls).
      3. Relevant symbol (`fog_map` at 0x58578) changed + committed -> cache INVALIDATED (LLM called).
    """
    watcom = _require_toolchains()
    repo = short_repo
    write, git = _init_base_repo(repo)
    ref = "src/cmd_123f0/fog_map_clear_reference.c"
    toml = "analysis/symbols/cmd.toml"
    write(ref, """/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -oa -4r -zp2 */
extern unsigned short *fog_map;
void FogMapClear(void)
{
    unsigned short *p = fog_map;
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
t3_blocker = "regalloc: loop keeps fog_map in different register"
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


def test_fog():
    emu = Emu()
    mod = cemu.load(emu, path("{ref}"))
    buf = emu.alloc(0x2008)
    emu.write(buf, b"\\xff" * 0x2008)
    emu.put_u32(0x58578, buf)
    assert not cemu.run_pair(emu, 0x12404, mod, "FogMapClear_", watch=[(buf, 0x2008)], out_regs=())
""")
    _commit_fixture(git)

    # Mock LLM returns a valid structured no-op diagnosis (clean NO_IMPROVEMENT) and counts calls
    count_file = repo / "build/llm_call_count.txt"
    payload = {"type": "result", "structured_output": {"diagnosis": "no patch", "patches": []}}
    model = write("build/fake-bin/claude", f"""#!/usr/bin/env python3
import sys
from pathlib import Path
sys.stdin.read()
cf = Path({str(count_file)!r})
n = int(cf.read_text()) if cf.is_file() else 0
cf.write_text(str(n + 1))
print({json.dumps(payload)!r})
""")
    model.chmod(0o755)
    env = _make_env(repo, watcom, model.parent)
    cmd = [
        sys.executable, "-m", "wc1.overnight", "--headless", "--wave", "wave4b",
        "--only", "0x12404", "--max-modules", "1", "--wave4-max-calls", "1",
        "--window-budget", "1", "--no-sleep",
    ]

    # Step 1: Cold miss -> compiles with real Watcom 10.0a, runs 1 LLM call, writes v2 cache entry
    rc1, out1 = _run_cli(cmd, repo, env)
    assert rc1 == 0, out1
    assert int(count_file.read_text()) == 1
    cache_files = list((repo / "build/wave4/retry/12404").glob("*.json"))
    assert len(cache_files) == 1
    rec1 = json.loads(cache_files[0].read_text())
    assert rec1["cache_schema"] == wave4_fp.CACHE_SCHEMA_VERSION
    assert rec1["fingerprint_mode"] == "dependency_scoped"

    # Step 2: Add demonstrably UNRELATED function & data symbols and commit in Git
    write("analysis/symbols/unrelated.toml", """[[func]]
addr = 0x19470
name = "UnrelatedRngSeed"
conv = "watcall"
proto = "void UnrelatedRngSeed(long seed)"
confidence = "high"
evidence = ["0x19470 unrelated to 0x12404"]

[[data]]
addr = 0x50d7c
name = "unrelated_rng_seed"
type = "long"
confidence = "high"
evidence = ["0x50d7c unrelated to 0x12404"]
""")
    git("add", "analysis/symbols/unrelated.toml")
    git("commit", "-qm", "Add unrelated symbols")

    rc2, out2 = _run_cli(cmd, repo, env)
    assert rc2 == 0, out2
    assert int(count_file.read_text()) == 1, f"LLM should NOT have been called on unrelated symbol change:\n{out2}"
    assert "HIT preserved across unrelated repo change" in out2, out2
    m2 = json.loads((repo / "build/wave4/metrics.json").read_text())
    assert m2["wave4b"]["cache_hits_skipped"] == 1
    assert m2["wave4b"]["cache"]["preserved_unrelated"] == 1

    # Step 3: Change a RELEVANT dependency (`fog_map` type/ABI in cmd.toml) and commit
    write(toml, (repo / toml).read_text().replace('type = "unsigned short *"', 'type = "volatile unsigned short *"'))
    git("add", toml)
    git("commit", "-qm", "Update relevant fog_map type")

    rc3, out3 = _run_cli(cmd, repo, env)
    assert rc3 == 0, out3
    assert int(count_file.read_text()) == 2, f"LLM MUST be called after relevant dependency change:\n{out3}"
    assert "INVALIDATED relevant dependency change" in out3, out3
    m3 = json.loads((repo / "build/wave4/metrics.json").read_text())
    assert m3["wave4b"]["cache"]["invalidated_dep_change"] == 1


def test_real_project_wave4a_cache_preservation_and_invalidation(short_repo):
    """Real `DispatchFatal` (0x145d0) with unresolved `_str_56b10` -> 0x56b10 under Watcom 10.0a + OW2:
      1. Clean AMBIGUOUS cached under schema v2.
      2. Unrelated data symbol added far from 0x56b10 + committed -> cache HIT preserved (0 LLM calls).
      3. Relevant nearby data symbol (within ±0x60 of 0x56b10) added + committed -> cache INVALIDATED,
         LLM now resolves & promotes to T3 with Build A `IDENTICAL`!
    """
    watcom = _require_toolchains()
    repo = short_repo
    write, git = _init_base_repo(repo)
    ref = "src/mod_13f60/dispatch_fatal_reference.c"
    toml = "analysis/symbols/mod_13f60.toml"
    write(ref, """/* codegen-compiler: 10.0a */
extern void __cdecl FatalError(const char *fmt, ...);
extern const char str_56b10[11];

int DispatchFatal(void *u)
{
    FatalError(str_56b10);
    return 0;
}
""")
    write(toml, f"""[[func]]
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
""")
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
""")
    _commit_fixture(git)

    count_file = repo / "build/w4a_llm_calls.txt"
    ambig_payload = {
        "type": "result",
        "structured_output": {
            "decision": "ambiguous",
            "summary": "need neighbor context around 0x56b10",
            "uncertainties": ["nearby string table boundary unclear"],
            "toml_entries": [],
            "file_patches": [],
        },
    }
    apply_payload = {
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
    # First call returns ambiguous; second call (after relevant invalidation) resolves & promotes to T3!
    model = write("build/fake-bin/claude", f"""#!/usr/bin/env python3
import sys
from pathlib import Path
sys.stdin.read()
cf = Path({str(count_file)!r})
n = int(cf.read_text()) if cf.is_file() else 0
cf.write_text(str(n + 1))
print({json.dumps(ambig_payload)!r} if n == 0 else {json.dumps(apply_payload)!r})
""")
    model.chmod(0o755)
    env = _make_env(repo, watcom, model.parent)
    cmd = [
        sys.executable, "-m", "wc1.overnight", "--headless", "--wave", "wave4a",
        "--wave4a-max-calls", "1", "--max-modules", "1", "--window-budget", "1", "--no-sleep",
    ]

    # Step 1: Cold miss -> AMBIGUOUS cached under v2 dependency-scoped fingerprint
    rc1, out1 = _run_cli(cmd, repo, env)
    assert rc1 == 0, out1
    assert int(count_file.read_text()) == 1
    cfiles = list((repo / "build/wave4/reconcile_cache/data_56b10").glob("*.json"))
    assert len(cfiles) == 1
    rec1 = json.loads(cfiles[0].read_text())
    assert rec1["cache_schema"] == wave4_fp.CACHE_SCHEMA_VERSION
    assert rec1["fingerprint_mode"] == "dependency_scoped"

    # Step 2: Add demonstrably UNRELATED data symbol (0x59990, far outside ±0x60) & commit
    write("analysis/symbols/unrelated.toml", """[[data]]
addr = 0x59990
name = "unrelated_far_data"
type = "unsigned long"
confidence = "high"
evidence = ["0x59990 unrelated to 0x56b10"]
""")
    git("add", "analysis/symbols/unrelated.toml")
    git("commit", "-qm", "Add unrelated data symbol")

    rc2, out2 = _run_cli(cmd, repo, env)
    assert rc2 == 0, out2
    assert int(count_file.read_text()) == 1, f"Wave 4A cache should be preserved on unrelated symbol:\n{out2}"
    assert "HIT preserved across unrelated repo change" in out2, out2
    m2 = json.loads((repo / "build/wave4/metrics.json").read_text())
    assert m2["wave4a"]["cache_hits_skipped"] == 1
    assert m2["wave4a"]["cache"]["preserved_unrelated"] == 1

    # Step 3: Add a RELEVANT neighbor data symbol at 0x56b20 (within ±0x60 of 0x56b10) & commit
    write(toml, (repo / toml).read_text() + """
[[data]]
addr = 0x56b20
name = "nearby_dispatch_str"
type = "const char[8]"
confidence = "high"
evidence = ["nearby string at 0x56b20 within +-0x60 of 0x56b10"]
""")
    git("add", toml)
    git("commit", "-qm", "Add nearby data symbol within +-0x60 of 0x56b10")

    rc3, out3 = _run_cli(cmd, repo, env)
    assert rc3 == 0, out3
    assert int(count_file.read_text()) == 2, f"Wave 4A cache MUST invalidate on nearby data symbol:\n{out3}"
    assert "INVALIDATED relevant dependency change" in out3, out3
    assert "[COMMITTED " in out3 and "IDENTICAL (loaded image, entry, stack, fixups)" in out3, out3
    m3 = json.loads((repo / "build/wave4/metrics.json").read_text())
    assert m3["wave4a"]["cache"]["invalidated_dep_change"] == 1
    assert m3["wave4a"]["t3_promotions"] == 1
    doc = tomllib.loads((repo / toml).read_text())
    fn = next(f for f in doc["func"] if f["addr"] == 0x145d0)
    assert fn["src"] == ref and fn["confidence"] == "verified"
