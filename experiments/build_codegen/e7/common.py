"""E7 constants and stable, content-based evidence serialization."""
import hashlib
import json
import os
import tempfile
import threading
from pathlib import Path

from wc1 import path

BASELINE = "7c23d2371e95d8de93f0ba1652c8d44b858da273"
RESULTS = Path(path("docs/research/build-codegen/results/e7"))
SCRATCH = Path(path("build/e7"))
STATES = ("matched", "mismatched", "compile_error", "matcher_unsupported", "untested")
CORE_FLAGS = [
    "-s -ot -ol -4r -zp2", "-s -ot -oa -ol -4r -zp2",
    "-s -ot -4r -zp2", "-s -ot -oa -4r -zp2", "-s -os -ol -4r -zp2",
    "-s -ot -ol -5r -zp2", "-s -ot -oa -ol -5r -zp2",
    "-s -ot -5r -zp2", "-s -os -ol -5r -zp2", "-s -ot -ol -3r -zp2",
    "-s -ot -ol -or -4r -zp2", "-s -ot -ol -oi -4r -zp2",
    "-s -ot -ol -om -4r -zp2", "-s -ot -ol -oc -4r -zp2",
    "-s -ot -ol+ -4r -zp2", "-s -ot -ol -4r -zp1",
    "-s -ot -ol -5r -zp1", "-s -ot -ol -4r -d1+ -zp2",
    "-s -ot -ol -5r -d1+ -zp2", "-s -od -4r -zp2",
    "-s -od -4r -d1+ -zp2", "-s -os -4r -zp2",
]


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def file_hash(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# Watcom 10.0a's Win32 wcc386 keeps command-line paths in fixed buffers and
# dies with an access violation past them.  Measured on this toolchain: an
# `-i=` argument fails at 129 bytes (a 124-character unix path plus "Z:" and
# "-i="), and the source operand at 130 characters (132 with "Z:").  A
# checkout root long enough therefore cannot be handed its own absolute
# paths.  Every path this experiment gives the compiler goes through a short
# mirror of the checkout instead; the limit below leaves a wide margin.
COMPILER_PATH_LIMIT = 112
_MIRROR = {}
_MIRROR_LOCK = threading.Lock()


def _short_base():
    """A short, writable directory; /tmp first so the mirror prefix is bounded."""
    for base in ("/tmp", os.environ.get("TMPDIR"), tempfile.gettempdir()):
        if base and os.path.isdir(base) and os.access(base, os.W_OK):
            return Path(base)
    raise RuntimeError("E7 needs a writable temporary directory for the compiler mirror")


def compiler_root():
    """Short absolute path that mirrors the checkout for compiler arguments.

    The returned directory is `<base>/wc1e7-<checkout hash>/repo`, a symlink to
    the checkout, so `compiler_root() / relative_path` names the same file with
    a bounded prefix.  It is created once per checkout and reused across
    processes (the path itself is deterministic).
    """
    with _MIRROR_LOCK:
        if "root" not in _MIRROR:
            repo = Path(os.path.realpath(path()))
            short = _short_base() / ("wc1e7-" + hashlib.sha1(str(repo).encode()).hexdigest()[:8])
            short.mkdir(exist_ok=True)
            root = short / "repo"
            if os.path.islink(root) and Path(os.path.realpath(root)) != repo:
                os.unlink(root)
            if not os.path.lexists(root):
                try:
                    os.symlink(repo, root, target_is_directory=True)
                except FileExistsError:
                    pass
            if Path(os.path.realpath(root)) != repo:
                raise RuntimeError(f"cannot create the short compiler mirror {root} -> {repo}")
            _MIRROR["root"] = root
    return _MIRROR["root"]


def _external(p):
    """Short name for a path outside the checkout (e.g. --scratch elsewhere)."""
    short = compiler_root().parent
    links = short / "ext"
    links.mkdir(exist_ok=True)
    link = links / hashlib.sha1(str(p.parent).encode()).hexdigest()[:16]
    if not os.path.lexists(link):
        try:
            os.symlink(p.parent, link, target_is_directory=True)
        except FileExistsError:
            pass
    return link / p.name


def compiler_path(p):
    """The compiler-facing absolute form of p, bounded by COMPILER_PATH_LIMIT.

    The file is not copied: a path under the checkout maps into the mirror
    root, and anything else gets a short symlink beside it.
    """
    p = Path(os.path.abspath(p))
    root = compiler_root()
    if p.is_relative_to(root):          # already a compiler-facing path
        out = p
    else:
        try:
            out = root / p.relative_to(Path(os.path.abspath(path())))
        except ValueError:
            out = _external(p)
    if len(str(out)) > COMPILER_PATH_LIMIT:
        raise RuntimeError(f"compiler-facing path is {len(str(out))} characters "
                           f"(Watcom 10.0a limit {COMPILER_PATH_LIMIT}): {out}")
    return out


def short_oldcc():
    """Point 10.0a's own fixed `-i=` paths at the short mirror, once.

    `oldcc.compile_c` always adds the repository's src/include and the
    installation's h/ directory to the command line, so a long checkout root
    crashes even when every per-cell path is bounded.  Only the strings handed
    to wcc386 change; they name the same files through the mirror.
    """
    from wc1 import oldcc
    if getattr(oldcc, "_e7_short_paths", False):
        return oldcc
    with _MIRROR_LOCK:
        if not getattr(oldcc, "_e7_short_paths", False):
            real_root = Path(os.path.abspath(oldcc.root()))
            oldcc.root = lambda: str(compiler_path(real_root))
            oldcc.path = lambda *parts: str(compiler_path(Path(path(*parts))))
            oldcc._e7_short_paths = True
    return oldcc


def compile_short(src, cflags=None, out=None, cc=None, includes=(), timeout=None, quiet=False):
    """`wc1.match.compile_c` with every compiler-facing path short and bounded."""
    from wc1 import match
    short_oldcc()
    return match.compile_c(compiler_path(src), cflags, str(compiler_path(out)), cc=cc,
                           includes=tuple(compiler_path(d) for d in includes),
                           timeout=timeout, quiet=quiet)


def dump(p, value, *, compact=False):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(value, sort_keys=True, indent=None if compact else 2,
                              separators=(",", ":") if compact else None) + "\n")
    tmp.replace(p)


def short_flags(full):
    from wc1.match import BASE_CFLAGS
    return " ".join(full.removeprefix(BASE_CFLAGS).split())


def flag_key(flags):
    # Only for deduplicating these independent, non-conflicting header tokens.
    # Actual compiler invocations always preserve the original token order.
    return tuple(sorted(flags.split()))


def configurations(declared=()):
    out, seen = [], set()
    for flags in list(CORE_FLAGS) + sorted(set(declared)):
        key = flag_key(flags)
        if key not in seen:
            out.append(dict(id=f"c{len(out)+1:02d}", flags=flags, compiler="10.0a"))
            seen.add(key)
    return out


def finding_summary(result):
    from collections import Counter
    findings = result["findings"]
    return dict(verdict=result["verdict"], finding_count=len(findings),
                codes=dict(sorted(Counter(f["code"] for f in findings).items())),
                findings_sha256=digest(findings), first_finding=findings[0] if findings else None,
                metrics=result["metrics"], orig_start=result["orig_start"], orig_end=result["orig_end"],
                obligation_count=len(result["obligations"]))


def cell_state(verdict):
    return {"MATCH": "matched", "MISMATCH": "mismatched",
            "UNSUPPORTED": "matcher_unsupported", "ERROR": "matcher_unsupported"}[verdict]
