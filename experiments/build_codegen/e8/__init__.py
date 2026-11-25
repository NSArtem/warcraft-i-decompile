"""E8 — original compilation-unit boundary evidence validation (isolated experiment).

Nothing here is imported by production code (`tools/wc1`, `src`, `tests`).  The
three evidence classes are kept strictly apart (Mandatory Correction R4):

* **Corpus A** (`synthetic_corpus`) — CUs written for this experiment, compiled
  with the original Watcom C/C++ 10.0a `wcc386` and linked with the 10.0a
  `wlink system dos4g`; CU ownership is a fact of the build recipe and the
  linker `.map`, not an inference from any evaluated signal.
* **Corpus B** (`real_corpus`) — boundaries of the real `war.exe` established
  independently: object identity of `clib3r.lib` units matched by
  `wc1.clib_sig` and then verified over the object's whole CODE segment
  (masking relocation fields) with overlapping candidates removed, and
  `setup.exe` shared/unshared provenance transitions.
* **Exploratory game analysis** (`run_e8` / `evaluate_signals`) — the signals
  and E7's `S(f)` applied to the game range of `war.exe`.  Explicitly *not*
  ground truth and never mixed into precision/recall.

Artifacts are deterministic and path-free: JSON is written with `sort_keys`
and CSV with an explicit LF terminator, and no artifact records a checkout,
temporary or build path.
"""
import hashlib
import json
from pathlib import Path

from wc1 import path

RESULTS = Path(path("docs", "research", "build-codegen", "results", "e8"))
SCRATCH = Path(path("build", "e8"))

EXPERIMENT = "E8"
SCHEMA = 1
SPEC_ID = "e8-synthetic-v1"


def abspath(*parts):
    return Path(path(*parts))


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def digest(value):
    """Stable digest of a JSON-serializable value (dict order independent)."""
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def dump_json(p, value):
    """Write JSON deterministically: sorted keys, two-space indent, LF, one newline."""
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, sort_keys=True, indent=2) + "\n"
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    tmp.replace(p)


def write_csv(p, header, rows):
    """Write CSV with an explicit LF terminator and no locale-dependent quoting."""
    import csv
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        for row in rows:
            w.writerow(row)
    tmp.replace(p)


def read_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))
