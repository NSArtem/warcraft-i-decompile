"""Match several reconstructed files in one process (NETWORK.C area helper).

    python3 -m wc1.net_match src/network/*.c        # or an explicit list

`wc1.match` loads the whole program for every call (about ten seconds); this
wrapper loads the symbol database and the code discovery once and then runs
match_module() per file, printing one line per function.  Read-only apart from
the object files under build/match/<compiler>/ (same place wc1.match writes).
"""
import os
import sys

from . import analysis, match, path, symbols


def main(argv):
    srcs = argv or sorted(
        os.path.join("src", "network", f) for f in os.listdir(path("src", "network"))
        if f.endswith(".c"))
    funcs, datas, errors = symbols.load()
    if errors:
        raise SystemExit("\n".join(errors))
    by_link = {e["link_name"]: e for t in (funcs, datas) for e in t.values()}
    p = analysis.run()
    bad = 0
    for src in srcs:
        cc = match.file_cc(src)
        d = path("build", "match", cc)
        os.makedirs(d, exist_ok=True)
        out = os.path.join(d, os.path.splitext(os.path.basename(src))[0] + ".obj")
        try:
            mod = match.compile_c(src, None, out, cc=cc)
        except SystemExit as e:
            print(f"COMPILE-FAIL {src}: {e}")
            bad += 1
            continue
        for name, status, problems in match.match_module(p, mod, by_link):
            if status != "MATCH":
                bad += 1
            print(f"{status:9} {name:28s} {src}")
            for pr in problems[:4]:
                print(f"            {pr}")
    print(f"{len(srcs)} files, {bad} not matched")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
