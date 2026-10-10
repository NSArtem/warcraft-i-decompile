"""Build war.exe from the generated asm plus reconstructed C.

usage: python3 -m wc1.build [--out build/war.exe]

1. functions whose symbol entry has `src = "src/<file>.c"` are omitted from the
   generated asm (declared extern) and compiled from C with wcc386;
2. the rest of the program is emitted as NASM (OMF) and assembled;
3. everything is linked with wlink (system dos4g, original stub);
4. the result is compared with the original at the loaded-image level.
   With no C replacements it must be IDENTICAL; with replacements, the layout
   shifts and equivalence is established per function (wc1.match) and by
   behavioural tests.
"""
import argparse
import os
import subprocess
import sys

from . import analysis, emit, le, match, path, symbols


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        sys.stderr.write(r.stdout + r.stderr)
        raise SystemExit(f"failed: {' '.join(cmd)}")
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=path("build", "war.exe"))
    ap.add_argument("--cflags", default=os.environ.get("WC1_CFLAGS", match.DEFAULT_CFLAGS))
    a = ap.parse_args()
    bdir = path("build")
    os.makedirs(os.path.join(bdir, "obj"), exist_ok=True)

    funcs, datas, _ = symbols.load()
    names = {e["addr"]: e["link_name"] for t in (datas, funcs) for e in t.values()}
    replaced = {e["addr"]: e["src"] for e in funcs.values() if e.get("src")}
    rawfile = path("analysis", "raw_insns.txt")
    force = {int(l.split()[0], 16) for l in open(rawfile) if l.strip() and not l.startswith("#")}

    p = analysis.run()
    e = emit.Emitter(p, names=names, force_raw=force, replaced=replaced)
    asm = os.path.join(bdir, "war.asm")
    e.emit(asm)
    run(["nasm", "-O0", "-f", "obj", "-I", path("asm") + "/", "-w-number-overflow",
         "-w+error=label-orphan", "-o", os.path.join(bdir, "obj", "war_asm.obj"), asm])
    objs = [os.path.join(bdir, "obj", "war_asm.obj")]
    for src in sorted(set(replaced.values())):
        o = os.path.join(bdir, "obj", os.path.splitext(os.path.basename(src))[0] + ".obj")
        match.compile_c(path(src), a.cflags, o)
        objs.append(o)

    stub = os.path.join(bdir, "stub.exe")
    orig = le.load()
    with open(stub, "wb") as f:
        f.write(orig.stub)
    lnk = os.path.join(bdir, "war.lnk")
    with open(lnk, "w") as f:
        f.write("system dos4g\n")
        f.write(f"name {a.out}\n")
        for o in objs:
            f.write(f"file {o}\n")
        f.write(f"option stub={stub}\noption map={os.path.join(bdir, 'war.map')}\noption quiet\n")
    run(["wlink", f"@{lnk}"])
    print(f"built {a.out} ({len(replaced)} functions from C: {sorted(set(replaced.values()))})")
    r = subprocess.run([sys.executable, "-m", "wc1.compare", le.ORIGINAL_EXE if hasattr(le, 'ORIGINAL_EXE') else path("original", "install", "war.exe"), a.out],
                       capture_output=True, text=True)
    print(r.stdout.strip().splitlines()[-1])
    if not replaced and r.returncode != 0:
        print(r.stdout)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
