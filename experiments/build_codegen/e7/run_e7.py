"""Reproduce E7 capability, exhaustive calibration, links and derived results."""
import argparse
from pathlib import Path
import time

from .analyze import summarize, untested_space, write_derived
from .calibrate import calibrate
from .capability_probe import probe
from .common import RESULTS, SCRATCH, dump
from .link_check import representative_links


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--jobs",type=int,default=6)
    ap.add_argument("--output",type=Path,default=RESULTS)
    ap.add_argument("--scratch",type=Path,default=SCRATCH)
    args=ap.parse_args()
    if args.jobs<1:ap.error("--jobs must be positive")
    t0=time.monotonic()
    capability=probe(args.output,args.scratch)
    print(f"E7 capabilities: {sum(r['supported'] for r in capability['flags'])}/{len(capability['flags'])} accepted",flush=True)
    matrix=calibrate(capability,args.jobs,args.output,args.scratch)
    matrix["explored_space"]["untested_combinations"]=untested_space(matrix["configurations"])
    matrix["build_a_links"]=representative_links(matrix,args.scratch)
    matrix["summary"]=summarize(matrix)
    if matrix["provenance"]["production_diff"]:
        raise RuntimeError("Production diff is nonempty")
    dump(args.output/"calibration_matrix.json",matrix,compact=True)
    write_derived(matrix,args.output)
    elapsed=time.monotonic()-t0
    dump(args.scratch/"timing.json",dict(elapsed_seconds=elapsed,jobs=args.jobs))
    print(f"E7 complete in {elapsed:.2f}s: {matrix['summary']['cohorts']}",flush=True)
    print(matrix['summary']['all_tested_t4'],flush=True)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
