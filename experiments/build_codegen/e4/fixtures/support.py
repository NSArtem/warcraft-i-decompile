"""Fixture support for E4: compile, assemble, link and synthetic programs.

Every generated file lives under `build/e4/`.  Nothing here modifies the
production tree or the game data; the original program is only read.
"""
from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
from types import SimpleNamespace

import capstone
from wc1 import le, omf, path
from experiments.build_codegen.e0.matcher_proto import OriginalIndex
from experiments.build_codegen.e4 import omf_extract as x
from experiments.build_codegen.e5 import build_e5 as b
from . import builder

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUT = Path(path("build", "e4"))
OBJ = OUT / "obj"
LINK = OUT / "link"
FLAGS = "-s -ot -ol -4r -zp2"


def _run(argv, **kwargs):
    r = subprocess.run([str(a) for a in argv], capture_output=True, text=True,
                       timeout=180, **kwargs)
    if r.returncode:
        raise RuntimeError(f"{argv}: {r.stdout}\n{r.stderr}")
    return r.stdout


def compile_controlled():
    """Compile the controlled three-function TU with real Watcom 10.0a."""
    OBJ.mkdir(parents=True, exist_ok=True)
    out = OBJ / "controlled_tu.obj"
    b.compile_10a(HERE / "controlled_tu.c", out, FLAGS)
    return out


def assemble(source, name):
    OBJ.mkdir(parents=True, exist_ok=True)
    obj = OBJ / (name + ".obj")
    _run(["nasm", "-O0", "-f", "obj", "-I", str(ROOT / "asm") + "/",
          "-w-number-overflow", "-o", obj, source])
    return obj


def write_obj(name, data):
    OBJ.mkdir(parents=True, exist_ok=True)
    obj = OBJ / (name + ".obj")
    obj.write_bytes(bytes(data))
    return obj


def runtime_object():
    return assemble(HERE / "runtime.asm", "e4_runtime")


def mini_link(objects, name):
    """Link the given OMF objects into a DOS/4GW LE executable."""
    LINK.mkdir(parents=True, exist_ok=True)
    exe = LINK / (name + ".exe")
    lnk = LINK / (name + ".lnk")
    lnk.write_text("system dos4g\noption quiet\nname " + str(exe) + "\n" +
                   "".join("file " + str(Path(o)) + "\n" for o in objects))
    _run(["wlink", "@" + str(lnk)])
    return exe, le.LE(exe.read_bytes())


def compare(a, b):
    r = subprocess.run([sys.executable, "-m", "wc1.compare", str(a), str(b)],
                       capture_output=True, text=True, timeout=60)
    return r.returncode == 0, r.stdout.strip()


def text_bytes(obj):
    mod = omf.parse_object(obj)
    return bytes(mod.seg("_TEXT")[1].data)


def body_ends(text, starts):
    """End (exclusive) of each function body: the first top-level terminating
    instruction.  Compiler/padding bytes after it belong to the next start."""
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    out = []
    for start in starts:
        pos = start
        while pos < len(text):
            insn = next(md.disasm(text[pos:], pos, 1), None)
            if insn is None:
                break
            pos += len(insn.bytes)
            if insn.mnemonic in ("ret", "retf", "iret", "iretd", "jmp"):
                break
        out.append(min(pos, len(text)))
    return out


def program_from_le(image, functions):
    """A minimal read-only `Program` view of a linked oracle executable."""
    code = next(o for o in image.objects if o.is_code)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    insns = {i.address: i for i in md.disasm(bytes(image.loaded_image()[code.index]), code.base)}
    fix_at = {}
    for f in image.fixups_unique:
        addr = image.obj(f.obj).base + f.src_off
        target = image.obj(f.target_obj).base + f.target_off
        fix_at[addr] = (f, target)
    return SimpleNamespace(code=code, cbytes=bytes(image.loaded_image()[code.index]),
                           image=image.loaded_image(), le=image, fix_at=fix_at,
                           insns=insns, functions=functions, jump_tables={}, owner={})


def function_table(image, ranges, db):
    """Program function records for [(name, start, end)]."""
    return [dict(start=start, end=end, name=name, limit=end) for name, start, end in ranges]


# ------------------------------------------------------------------ remainder
def remainder_object(obj, keep_from, extra_publics=()):
    """Rebuild `obj` as a standalone provider of the bytes at [keep_from, end).

    This is the oracle-side counterpart of an extraction: `_TEXT` starts at the
    first byte after the extracted slice, every other segment keeps its bytes,
    and extra publics define the anchor labels the slice references.
    """
    raw = Path(obj).read_bytes()
    mod = omf.parse_module(raw)[0]
    recs = x.read_records(raw)
    raw_by_seg = x.raw_fixups(recs)
    ti, tseg = mod.seg("_TEXT")
    segments = []
    for si, s in enumerate(mod.segments, 1):
        data = bytes(s.data)
        fixups = []
        if si == ti:
            data = data[keep_from:]
        base = keep_from if si == ti else 0
        for fu, fix in zip(s.fixups, raw_by_seg.get(si, [])):
            if base <= fu.offset:
                fixups.append(dict(offset=fu.offset - base, loc=fix.loc,
                                   self_rel=fix.self_rel, fm=fix.fm, fi=fix.fi,
                                   tm=fix.tm, ti=fix.ti, disp=fix.disp))
        # Build A places the _TEXT continuation with BYTE alignment (the pieces
        # carry the original padding bytes themselves); local data keeps the
        # compiled alignment so the oracle layout is reproduced exactly.
        segments.append(dict(name=s.name, cls=s.cls,
                             align=1 if si == ti else s.align,
                             data=data, fixups=fixups))
    publics = [(n, si, off - keep_from) for n, (si, off) in mod.publics.items()
               if si == ti and off >= keep_from]
    statics = [(n, si, off - keep_from) for n, (si, off) in mod.statics.items()
               if si == ti and off >= keep_from]
    publics += [tuple(p) for p in extra_publics]
    return builder.build(segments=segments, publics=publics, statics=statics,
                         externs=mod.externs,
                         groups=[(n, []) for _, n in sorted(mod.groups.items())])


def loadable_sha256(data):
    if isinstance(data, (bytes, bytearray)):
        return x.loadable_digest(omf.parse_module(bytes(data))[0])
    return x.loadable_digest(data)
