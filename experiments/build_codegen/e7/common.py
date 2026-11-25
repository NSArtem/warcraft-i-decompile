"""E7 constants and stable, content-based evidence serialization."""
import hashlib
import json
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
