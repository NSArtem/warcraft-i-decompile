"""Probe the actual 10.0a compiler; no OW2 option assumptions or LLM calls."""
import re
import subprocess
from pathlib import Path

from wc1 import oldcc, omf
from .common import RESULTS, SCRATCH, compiler_path, digest, dump, file_hash

CANDIDATES = """-3r -4r -5r -6r -ot -os -od -ol -ol+ -oa -or -oi -om -oc
-oe -ou -ox -oz -of -of+ -ob -zp1 -zp2 -zp4 -d1 -d1+ -d2 -j -ri -zc -s""".split()
BASE = "-s -ot -4r -zp2"
PROBE = r'''
typedef unsigned int U;
extern int Sink(int);
extern char *strcpy(char *, const char *);
extern void *memset(void *, int, unsigned);
struct Packed { char c; int n; short s; };
struct Bits { unsigned ready:1; unsigned mode:3; unsigned spare:4; };
volatile int observed;
int Loops(int *a, int n) { int i, sum=0; for(i=0;i<n;i++) sum+=a[i]*12;
    for(i=0;i<16;i++) a[i]=sum+i; return sum; }
int Narrow(unsigned char *p, short *q) { if(*p==12) return *q*7;
    if(*p==14) return *q/3; return p[2]+q[3]; }
int Packing(struct Packed *p) { return sizeof(*p)+p->n+p->s; }
int Bitfields(struct Bits *p) { if(p->ready) p->mode=3; return p->mode; }
int Switch(int x) { switch(x) {case 0:return Sink(19);case 1:return Sink(5);
    case 2:return Sink(17);case 3:return Sink(9);case 4:return Sink(21);
    case 5:return Sink(7);default:return -1;} }
int Multiply(int x, int y) { return x*8+y*12+x/5; }
int Intrinsics(char *p, const char *s) { strcpy(p,s);memset(p+32,0,40);return p[0]; }
int Tail(int x) { return Sink(x+1); }
int Frame(int x) { int a[12]; int i; for(i=0;i<12;i++) a[i]=Sink(x+i);
    for(i=0;i<12;i++) x+=a[i];return x; }
int FloatOps(double x, float y) { return (int)(x*y+3.25); }
int Alias(int *p, int *q) { *p=3;*q=7;return *p+*q; }
int SignedChar(char *p) { return *p; }
int Reuse(int x) { int a=x*17; observed=a;return a*3+Sink(a); }
char ReturnByte(char x) { return x+1; }
short ReturnShort(short x) { return x+1; }
const char *Literal(void) { return "E7 controlled literal"; }
extern double sqrt(double);
double Math(double x) { return sqrt(x); }
int Local(int x) { return x*17+3; }
int InlineUser(int x) { return Local(x)+Local(x+1); }
int SameA(int x) { return x+7; }
int SameB(int x) { return x+7; }
int NullAssumption(int *p) { int x=*p; if(p==0)return 3;return x; }
'''


def diagnostics(text, folder):
    # Remove scratch addresses, not compiler diagnostics or option names.
    for form in (folder, compiler_path(folder)):
        text = text.replace(str(form), "<probe>").replace(oldcc.win_path(form), "<probe>")
    return text.replace("\r", "").strip()


def invoke(args, folder):
    env = oldcc.wine_env()
    oldcc.ensure_prefix(env)
    log = folder / "compiler.log"
    with log.open("w+") as fh:
        # Watcom 10.0a cannot receive long Z:\ paths; run in its short mirror.
        r = subprocess.run([oldcc.find_wine(),
                            str(compiler_path(Path(oldcc.require()) / "binnt/wcc386.exe")), *args],
                           cwd=compiler_path(folder), env=env, stdin=subprocess.DEVNULL, stdout=fh,
                           stderr=subprocess.STDOUT, timeout=30)
        fh.seek(0)
        text = diagnostics(fh.read(), folder)
    return r.returncode, text


def runtime_segments(mod):
    return {s.name: dict(length=s.length, data=bytes(s.data).hex(),
                        fixups=[vars(f) for f in s.fixups])
            for s in mod.segments if s.cls not in ("DEBSYM", "DEBTYP") and s.length}


def compile_probe(folder, flags):
    src, obj = folder / "probe.c", folder / "probe.obj"
    src.write_text(PROBE)
    obj.unlink(missing_ok=True)
    args = ["-zq", "-zl", "-bt=dos", *flags.split(),
            f"-fo={oldcc.win_path(compiler_path(obj))}", oldcc.win_path(compiler_path(src))]
    rc, diag = invoke(args, folder)
    accepted = rc == 0 and obj.exists() and not re.search(r"invalid option|unknown option|ignored", diag, re.I)
    return accepted, rc, diag, runtime_segments(omf.parse_object(str(obj))) if accepted else None


def probe(output=RESULTS, scratch=SCRATCH):
    folder = Path(scratch) / "capability"
    folder.mkdir(parents=True, exist_ok=True)
    usage_rc, usage = invoke([], folder)
    ok, _, diag, baseline = compile_probe(folder, BASE)
    if not ok:
        raise RuntimeError(f"synthetic baseline failed: {diag}")
    rows = []
    for flag in CANDIDATES:
        tokens = BASE.split()
        if re.fullmatch(r"-[3456]r", flag):
            tokens.remove("-4r")
        elif flag.startswith("-zp"):
            tokens.remove("-zp2")
        elif flag in ("-os", "-od", "-ot"):
            tokens.remove("-ot")
        tokens.append(flag)
        flags = " ".join(dict.fromkeys(tokens))
        supported, rc, diag, got = compile_probe(folder, flags)
        changes = []
        if supported:
            for name in sorted(set(baseline) | set(got)):
                a, b = baseline.get(name), got.get(name)
                if a != b:
                    ad, bd = bytes.fromhex(a["data"]) if a else b"", bytes.fromhex(b["data"]) if b else b""
                    first = next((i for i, (x, y) in enumerate(zip(ad, bd)) if x != y), min(len(ad), len(bd)))
                    lo,hi=max(0,first-4),first+12
                    relocation_changes=(a or {}).get("fixups") != (b or {}).get("fixups")
                    changes.append(dict(segment=name, baseline_length=a["length"] if a else 0,
                                        variant_length=b["length"] if b else 0,
                                        first_byte_difference=first if ad != bd else None,
                                        description=f"{name}: stored bytes {len(ad)} -> {len(bd)}; first byte difference {hex(first) if ad != bd else 'none'}; relocation changes {relocation_changes}",
                                        window_start=lo,baseline_window_hex=ad[lo:hi].hex(),variant_window_hex=bd[lo:hi].hex(),
                                        baseline_sha256=digest(a), variant_sha256=digest(b),
                                        relocation_changes=relocation_changes))
        rows.append(dict(flag=flag, flags=flags, supported=supported,
                         observed_codegen_effect=bool(changes), diff=changes,
                         warnings_or_errors=diag, returncode=rc))
    data = dict(schema=1, compiler="Watcom C/C++ 10.0a", baseline_flags=BASE,
                compiler_hashes={p: file_hash(Path(oldcc.require()) / p)
                                 for p in ("binnt/wcc386.exe", "binb/wcc386.exe")},
                probe_sha256=digest(PROBE), usage_output=usage, usage_returncode=usage_rc,
                effect_scope="Runtime segments, bytes and relocations; excludes debug metadata. No observed effect is probe-local, not a universal no-op claim.",
                flags=rows)
    # These are research controls: fail loudly if the actual compiler contradicts them.
    assert all(not next(r for r in rows if r["flag"] == f)["supported"] for f in ("-6r", "-ob"))
    dump(Path(output) / "capability_db.json", data)
    return data


if __name__ == "__main__":
    probe()
