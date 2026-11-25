"""Recompile controls and the complete dynamic T3 inventory from scratch."""
import argparse
from pathlib import Path
from .controls import run_controls
from .reaudit_t3 import RESULTS, audit, audit_has_errors, dump_json


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--output", type=Path, default=RESULTS)
    args = ap.parse_args()
    if args.jobs < 1:
        ap.error("jobs must be positive")
    controls = run_controls()
    dump_json(args.output / "controls.json", controls)
    print(f"E0 controls: {controls['passed']}/{controls['total']} passed", flush=True)
    # Audit even when a control fails: report every outcome, return failure.
    result = audit(args.jobs, args.output)
    return int(controls["failed"] > 0 or not result["summary"]["count_matches_expectation"] or
               audit_has_errors(result))


if __name__ == "__main__":
    raise SystemExit(main())
