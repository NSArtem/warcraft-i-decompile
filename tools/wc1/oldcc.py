"""The original compiler: Watcom C/C++ 10.0a `wcc386`, run headless under Wine.

war.exe was built with Watcom 10.0a (docs/subsystems/compiler.md).  A C file
selects it with a `codegen-compiler: 10.0a` header line (wc1.match.file_cc);
without one the file is compiled by the Open Watcom 2 `wcc386` of the dev
shell.  This module is the 10.0a side of wc1.match.compile_c.

The compiler is user-supplied like the game CD and never committed: it lives
in original/watcom/10.0a/ (git-ignored; WC1_WATCOM10A overrides) and is
installed and checked by `make toolchain` (install(), below) against
analysis/provenance/watcom10a.sha256.  Files used:

  binnt/wcc386.exe   NT launcher; Wine runs it and it loads ...
  binb/wcc386.exe    ... the bound compiler (DOS/4GW + OS/2 + Win32 PE)
  h/                 the 10.0a system headers (stdio.h, string.h, ...)
  lib386/...         optional: the patched 10.0a runtime libraries, used only
                     by wc1.clib_sig --root (not by compiling)

Wine: one prefix, build/oldcc/wineprefix (WINEPREFIX overrides), created on
first use; DISPLAY/WAYLAND_DISPLAY are removed so no window ever opens, and
Mono/Gecko are disabled so no installer dialog appears.  10.0a spells OW2's
`-q` as `-zq` (normalize_flags).

usage: python3 -m wc1.oldcc --check            the installed compiler is complete
       python3 -m wc1.oldcc --install [SRC]    make toolchain (SRC: wcc10.0a.tar.gz
                                               or a 10.0a installation directory)
       python3 -m wc1.oldcc <file.c> [-o out.obj] [--cflags "..."]
"""
import argparse
import fcntl
import hashlib
import os
import shutil
import subprocess
import sys
import tarfile
import time

from . import omf, path

NAME = "10.0a"
MANIFEST = path("analysis", "provenance", "watcom10a.sha256")
TARBALL = "wcc10.0a.tar.gz"
# archive.org compiler-watcom-watcom-c-c-wcc386-10.0a-win32 (compiler.md)
TARBALL_SHA256 = "920a9674d1b10f227ae65171c187212b06d7fc38b263313922615c4f5e9b24a6"


class OldCCError(Exception):
    pass


class OldCCTimeout(OldCCError):
    """wcc386 under Wine ran past its timeout (a stuck Wine, not a C error)."""


def root():
    return os.path.abspath(os.environ.get("WC1_WATCOM10A") or path("original", "watcom", NAME))


def manifest():
    """[(sha256, relpath, required)] from the provenance file; the entries
    after a '# optional' line are optional (the runtime libraries)."""
    out, required = [], True
    with open(MANIFEST) as fh:
        for line in fh:
            line = line.strip()
            if line.startswith("#"):
                if line.lower().startswith("# optional"):
                    required = False
                continue
            if line:
                h, rel = line.split(None, 1)
                out.append((h, rel.lstrip("*"), required))
    return out


def _sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def check(base=None, optional=False):
    """Problems with the installation at base (default root()): missing or
    altered files.  optional=True also checks the runtime libraries."""
    base = base or root()
    bad = []
    for h, rel, req in manifest():
        if not req and not optional:
            continue
        p = os.path.join(base, rel)
        if not os.path.isfile(p):
            bad.append(f"missing {rel}")
        elif _sha256(p) != h:
            bad.append(f"sha256 mismatch {rel}")
    return bad


def require():
    """Root of the installed compiler, or OldCCError telling how to install it."""
    r = root()
    for rel in ("binnt/wcc386.exe", "binb/wcc386.exe"):
        if not os.path.isfile(os.path.join(r, rel)):
            raise OldCCError(f"Watcom {NAME} not installed ({r}/{rel} missing): run `make toolchain`")
    return r


def find_wine():
    w = os.environ.get("WC1_WINE") or shutil.which("wine")
    if not w:
        raise OldCCError("wine not found (run inside nix develop)")
    return w


def normalize_flags(cflags):
    """10.0a spells quiet -zq; OW2's -q is an invalid option there."""
    return " ".join("-zq" if f == "-q" else f for f in cflags.split())


def win_path(p):
    """Unix path -> Wine's Z: path."""
    p = os.path.abspath(p)
    return "Z:" + p.replace("/", "\\") if p.startswith("/") else p


def wine_env():
    env = dict(os.environ)
    env.pop("DISPLAY", None)            # never open a window (X11 or Wayland)
    env.pop("WAYLAND_DISPLAY", None)
    env.setdefault("WINEPREFIX", os.path.abspath(path("build", "oldcc", "wineprefix")))
    env.setdefault("WINEDEBUG", "-all")
    # no Mono/Gecko installer dialogs; no display drivers (saves ~0.2 s a run)
    env.setdefault("WINEDLLOVERRIDES", "mscoree,mshtml=;winex11.drv,winewayland.drv=")
    return env


def ensure_prefix(env=None):
    """Create the Wine prefix once (under a lock, so parallel compiles do not
    race on the first run)."""
    env = env or wine_env()
    pfx = env["WINEPREFIX"]
    if os.path.isfile(os.path.join(pfx, "system.reg")):
        return
    os.makedirs(os.path.dirname(pfx), exist_ok=True)
    with open(pfx + ".lock", "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        if os.path.isfile(os.path.join(pfx, "system.reg")):
            return
        with open(pfx + ".log", "w+") as fh:      # a file, not a pipe (see compile_c)
            r = subprocess.run([find_wine(), "wineboot", "-i"], stdout=fh, stderr=subprocess.STDOUT,
                               stdin=subprocess.DEVNULL, env=env, timeout=600)
            fh.seek(0)
            diag = fh.read()
        if r.returncode != 0 or not os.path.isfile(os.path.join(pfx, "system.reg")):
            raise OldCCError(f"wineboot failed ({r.returncode}): {diag[-400:]}")


def find_wineserver(env):
    """The wineserver of env's PATH, else the one beside wine; None without one."""
    ws = shutil.which("wineserver", path=env.get("PATH"))
    if ws:
        return ws
    try:
        ws = os.path.join(os.path.dirname(os.path.realpath(find_wine())), "wineserver")
    except OldCCError:
        return None
    return ws if os.access(ws, os.X_OK) else None


def kill_wineserver(env):
    """wineserver -k for env's prefix: a timed-out subprocess.run kills only the
    wine launcher, the wcc386 it started and the wineserver live on (that is
    how the 2026-11-22 overnight wedged the machine).  This also ends any other
    compile in the same prefix, which is what a compile timeout wants: the
    callers stop compiling once one times out.  Best effort, never raises."""
    ws = find_wineserver(env)
    if not ws:
        return
    try:
        subprocess.run([ws, "-k"], env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=10)
    except (OSError, subprocess.SubprocessError):
        pass


def compile_c(src, cflags, out, includes=(), timeout=180, quiet=False):
    """Compile src with 10.0a; return its OMF module.

    Same contract as wc1.match.compile_c: `cflags` already includes the
    file's codegen-flags header; `includes` come before src/include and the
    10.0a h/; a failed compile raises SystemExit with the diagnostics (on
    stderr, or in the exception message when `quiet`); a compile that runs
    past `timeout` seconds raises OldCCTimeout.
    """
    r = require()
    env = wine_env()
    ensure_prefix(env)
    argv = [find_wine(), os.path.join(r, "binnt", "wcc386.exe")] + normalize_flags(cflags).split()
    argv += [f"-i={win_path(d)}" for d in includes]
    argv += [f"-i={win_path(path('src', 'include'))}", f"-i={win_path(os.path.join(r, 'h'))}"]
    argv += [f"-fo={win_path(out)}", win_path(src)]
    out_dir = os.path.dirname(os.path.abspath(out))
    os.makedirs(out_dir, exist_ok=True)
    if os.path.exists(out):
        os.unlink(out)
    t0 = time.time()
    # Output goes to a file, not a pipe: the wineserver that wine starts
    # inherits the pipe and holds it open for its linger time (~3 s a run).
    log = os.path.abspath(out) + ".log"
    try:
        with open(log, "w+") as fh:
            # cwd: wcc386 writes <name>.err there on diagnostics
            p = subprocess.run(argv, stdout=fh, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                               env=env, cwd=out_dir, timeout=timeout)
            fh.seek(0)
            diag = fh.read()
    except subprocess.TimeoutExpired as e:
        kill_wineserver(env)
        raise OldCCTimeout(f"wcc386 {NAME} timed out after {timeout}s: {src}") from e
    finally:
        try:
            os.unlink(log)
        except OSError:
            pass
    if p.returncode != 0 or not os.path.isfile(out):
        msg = (f"compile failed (Watcom {NAME}, rc={p.returncode}, "
               f"{time.time() - t0:.1f}s): {src}")
        if quiet:
            raise SystemExit(f"{msg}\n{diag}".rstrip())
        sys.stderr.write(diag)
        raise SystemExit(msg)
    return omf.parse_object(out)


# --- make toolchain -------------------------------------------------------

def _from_tarball(tb, dst, rels):
    if _sha256(tb) != TARBALL_SHA256:
        raise OldCCError(f"{tb}: sha256 is not the known {TARBALL} ({TARBALL_SHA256[:16]}...)")
    want = set(rels)
    with tarfile.open(tb) as t:
        for m in t.getmembers():
            rel = os.path.normpath(m.name)
            if rel in want and m.isfile():
                p = os.path.join(dst, rel)
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with t.extractfile(m) as fi, open(p, "wb") as fo:
                    shutil.copyfileobj(fi, fo)


def _from_dir(src, dst, rels):
    for rel in rels:
        s = os.path.join(src, rel)
        if os.path.isfile(s):
            p = os.path.join(dst, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            shutil.copyfile(s, p)


SMOKE_C = ("int Probe(unsigned char *p) { unsigned char c = *p; "
           "if (c == 12) return 1; if (c == 14) return 3; return 2; }\n")


def smoke():
    """Compile a probe with 10.0a; its patch-A compare promotion (`and eax,0xff;
    cmp eax,imm` where OW2 writes `cmp al,imm`) shows the right compiler ran."""
    d = os.path.abspath(path("build", "oldcc", "smoke"))
    os.makedirs(d, exist_ok=True)
    src = os.path.join(d, "probe.c")
    with open(src, "w") as fh:
        fh.write(SMOKE_C)
    mod = compile_c(src, "-q -zl -bt=dos -s -ot -ol -4r -zp2", os.path.join(d, "probe.obj"))
    _i, text = mod.seg("_TEXT")
    return bytes(text.data)


PROMOTED = bytes.fromhex("25ff00000083f80c")     # and eax,0xff; cmp eax,0xc
NARROWED = bytes.fromhex("3c0c")                 # cmp al,0xc (pre-A 10.0, 10.5+, OW2)


def install(src=None):
    """make toolchain: copy the manifest's files from SRC (a 10.0a directory or
    wcc10.0a.tar.gz) into root(), verify every hash, create the Wine prefix
    and run the smoke compile.  Without SRC, $WATCOM10A or ./wcc10.0a.tar.gz
    is used when present, else the existing installation is only checked."""
    dst = root()
    src = src or os.environ.get("WATCOM10A") or (TARBALL if os.path.isfile(TARBALL) else None)
    rels = [rel for _h, rel, _r in manifest()]
    if src:
        os.makedirs(dst, exist_ok=True)
        if os.path.isdir(src):
            if os.path.abspath(src) != dst:
                _from_dir(src, dst, rels)
        elif os.path.isfile(src):
            _from_tarball(src, dst, rels)
        else:
            raise OldCCError(f"{src}: no such file or directory")
    bad = check(dst)
    if bad:
        raise OldCCError(f"Watcom {NAME} in {dst} is incomplete or altered: " + "; ".join(bad[:6])
                         + ("" if src else f" (give WATCOM10A=<dir> or put {TARBALL} in the repo root)"))
    libs = check(dst, optional=True)
    code = smoke()
    if PROMOTED not in code:
        raise OldCCError(f"smoke compile did not show the 10.0a compare promotion: {code.hex()}")
    print(f"OK: Watcom {NAME} wcc386 in {dst} (sha256 verified, Wine prefix ready, smoke compile ok)")
    print("    runtime libraries: " + ("verified" if not libs else
          f"not installed ({len(libs)} files; needed only by wc1.clib_sig --root)"))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", nargs="?")
    ap.add_argument("-o", dest="out")
    ap.add_argument("--cflags")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--install", action="store_true")
    a = ap.parse_args()
    try:
        if a.install:
            return install(a.src)
        if a.check:
            bad = check()
            if bad:
                print(f"Watcom {NAME}: " + "; ".join(bad[:6]) + " - run `make toolchain`",
                      file=sys.stderr)
                return 1
            find_wine()
            return 0
        if not a.src:
            ap.error("a C file, --check or --install")
        from . import match
        out = a.out or os.path.splitext(os.path.basename(a.src))[0] + ".obj"
        compile_c(a.src, a.cflags or match.file_cflags(a.src), out)
        print(out)
        return 0
    except OldCCError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
