import bisect
import os
import sys
import subprocess
import tempfile
from pathlib import Path

MAIN = Path("/mnt/data/projects/warcraft-1-decompile-consilium/runtime/gemini/export-main")
sys.path.insert(0, str(MAIN / "tools"))

# Ensure WC1_ROOT points to MAIN
os.environ["WC1_ROOT"] = str(MAIN)
os.environ["TMPDIR"] = "/tmp/opencode/cn-gemini"
os.environ["WINEPREFIX"] = "/mnt/data/projects/warcraft-1-decompile-wt/cons-c/build/oldcc/wineprefix"

from wc1 import analysis, symbols, cemu, t4spec
from wc1.emu import Emu

print("=== R1-PROBE 1: ALL CROSS-FN REL32 TARGETING INTERIOR IN GAME RANGE ===")
p = analysis.run(cache=True)
by_addr = symbols.load()[0]
sym_name = lambda a: by_addr.get(a, {}).get("name", hex(a))
by_start = {f["start"]: f for f in p.functions}
starts = sorted(by_start)

def owner(a):
    i = bisect.bisect_right(starts, a) - 1
    if i < 0:
        return None
    f = by_start[starts[i]]
    return f if f["start"] <= a < f["end"] else None

import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
code_obj = p.le.objects[0]
code_img = bytes(p.le.loaded_image()[code_obj.index])
for f in p.functions:
    if not (0x104b0 <= f["start"] < 0x3024e):
        continue
    chunk = code_img[f["start"] - code_obj.base : f["end"] - code_obj.base]
    for insn in md.disasm(chunk, f["start"]):
        if not (insn.group(capstone.CS_GRP_JUMP) or insn.group(capstone.CS_GRP_CALL)):
            continue
        if len(insn.operands) != 1 or insn.operands[0].type != capstone.x86.X86_OP_IMM:
            continue
        t = insn.operands[0].imm
        if not (f["start"] <= t < f["end"]):
            tf = owner(t)
            if tf and t != tf["start"]:
                b0 = insn.bytes[0]
                is_rel8 = (0x70 <= b0 <= 0x7f) or b0 in (0xeb, 0xe0, 0xe1, 0xe2, 0xe3)
                if not is_rel8:
                    print(
                        f"  REL32-INTERIOR: {f['start']:#x} {sym_name(f['start'])} "
                        f"@{insn.address:#x} {insn.mnemonic} {insn.op_str} -> {t:#x} "
                        f"(in {tf['start']:#x} {sym_name(tf['start'])}, off=+{t - tf['start']:#x})"
                    )

print("\n=== R1-PROBE 2: Q-B01 — ALL 5 XFAIL T4 TESTS WITH FULL MEMORY SNAPSHOT/RESTORE ===")
# Monkey-patch cemu.run_pair in memory (never touches disk!) to snapshot & restore
# ALL writable LE data + stack + extra mapped pages (from 0x50000..0x900000 or via unicorn mem_regions)
orig_run_pair = cemu.run_pair

def run_pair_full_restore(emu, orig_addr, cmod, name, *args, watch=(), out_regs=("eax",),
                          stack_args=(), regs_in=None, cdecl=False, interrupt=False):
    # Capture all writable/mapped RAM regions outside original code & C code
    c_ranges = getattr(cmod, "_c_ranges", ())
    code_lo, code_hi = emu.proj.code_base, emu.proj.code_base + len(emu.proj.code)
    snapshots = []
    for begin, end, perms in emu.uc.mem_regions():
        # perms & 2 == UC_PROT_WRITE
        if not (perms & 2):
            continue
        size = end - begin + 1
        # Skip huge uninitialized stacks > 2MB or code ranges? No, regions are small in wc1.emu
        if size > 4 * 1024 * 1024:
            continue
        snapshots.append((begin, bytes(emu.uc.mem_read(begin, size))))

    # We want to run original, record outputs + see what changed outside watch, then restore ALL snapshots, then run C!
    orig_watch = list(watch)
    # Run original directly via Emu.call just like run_pair, OR easier:
    # Wrap Emu.write? No, simplest clean check: intercept cemu.run_pair's restore point by
    # calling orig_run_pair? No, orig_run_pair checks type(emu) and shadowing on emu!
    # Instead, let's inspect emu.uc.mem_regions() and pass a custom wrapper that runs BOTH:
    # First run orig_run_pair AS-IS, and second run with FULL snapshot restored before C!
    return orig_run_pair(emu, orig_addr, cmod, name, *args, watch=watch, out_regs=out_regs,
                         stack_args=stack_args, regs_in=regs_in, cdecl=cdecl, interrupt=interrupt)

# Better: copy cemu.run_pair logic into a clean read-only helper that tests ALL 5 xfailed functions!
import importlib.util
def load_mod(path_str, mod_name):
    spec = importlib.util.spec_from_file_location(mod_name, path_str)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

# Let's inspect what pages/bytes actually change in the 5 xfail tests when run!
# We can hook t4spec.run_spec temporarily in memory to intercept calls and compare:
# (a) stock cemu.run_pair (watch-only restore)
# (b) full-RAM restore (all writable regions restored before C run)
orig_run_spec = t4spec.run_spec

def inspect_t4_test(test_fn, label):
    print(f"\n--- Testing {label} ---")
    captured = []
    def spy_run_spec(*a, **kw):
        captured.append((a, kw))
    t4spec.run_spec = spy_run_spec
    try:
        # Remove xfail mark if any, call underlying function
        fn = getattr(test_fn, "__wrapped__", test_fn)
        fn()
    except Exception as e:
        print(f"  spy capture error: {e}")
    finally:
        t4spec.run_spec = orig_run_spec

    print(f"  Captured {len(captured)} run_spec calls")
    for idx, (a, kw) in enumerate(captured):
        # Run stock first
        try:
            orig_run_spec(*a, **kw)
            print(f"  call[{idx}] STOCK: PASS")
        except AssertionError as e:
            msg = str(e).splitlines()[0] if str(e) else ""
            print(f"  call[{idx}] STOCK: FAIL ({msg[:140]})")

        # Now run with FULL memory restore inside run_pair!
        # We patch Emu.write? No, run_pair checks vars(emu) not Emu class? No, we can patch cemu.run_pair
        # directly since t4spec calls cemu.run_pair!
        def patched_run_pair(emu, orig_addr, cmod, name, *pargs, watch=(), out_regs=("eax",),
                             stack_args=(), regs_in=None, cdecl=False, interrupt=False):
            # Snapshot EVERY writable RAM region (skip original code 0x10000..0x4ffff and stub traps 0xffe0000+)
            snaps = []
            for begin, end, perms in emu.uc.mem_regions():
                if not (perms & 2):
                    continue
                if begin == 0x10000 or begin >= 0xffe0000:
                    continue
                sz = end - begin + 1
                if sz <= 16 * 1024 * 1024:
                    snaps.append((begin, bytes(emu.uc.mem_read(begin, sz))))
            # Run original
            c_addr = cemu.CModule.fn(cmod, name)
            kw_call = dict(stack_args=stack_args, regs=regs_in, cdecl=cdecl, interrupt=interrupt)
            Emu.call(emu, orig_addr, *pargs, **kw_call)
            ro = {n: Emu.reg(emu, n) for n in out_regs}
            mo = [(wa, Emu.read(emu, wa, wn)) for wa, wn in watch]
            # Find bytes mutated outside watch (and outside stack 0xef00000..0xeffffff)!
            watch_set = set()
            for wa, wn in watch:
                for x in range(wa, wa + wn):
                    watch_set.add(x)
            mutated_unwatched = []
            for begin, old in snaps:
                cur = bytes(emu.uc.mem_read(begin, len(old)))
                if cur != old:
                    if begin != 0xef00000:
                        for off in range(len(old)):
                            if cur[off] != old[off]:
                                addr = begin + off
                                if addr not in watch_set:
                                    mutated_unwatched.append((addr, old[off], cur[off]))
                                    if len(mutated_unwatched) >= 8:
                                        break
                    # Restore ALL writable memory (data, heap, stack) except cmod._c_ranges!
                    emu.uc.mem_write(begin, old)
            # Run C
            Emu.call(emu, c_addr, *pargs, **kw_call)
            rc = {n: Emu.reg(emu, n) for n in out_regs}
            mc = [(wa, Emu.read(emu, wa, wn)) for wa, wn in watch]
            diffs = []
            for r in out_regs:
                if ro[r] != rc[r]:
                    diffs.append(f"{r}: original {ro[r]:#x} != C {rc[r]:#x}")
            for (wa, _), (_, x), (_, y) in zip(watch, mo, mc):
                if x != y:
                    for k in range(len(x)):
                        if x[k] != y[k]:
                            diffs.append(f"memory {wa + k:#x}: original {x[k]:02x} != C {y[k]:02x}")
                            break
            if mutated_unwatched and not getattr(patched_run_pair, "_printed", False):
                sample = [(hex(x), hex(o), hex(n)) for x, o, n in mutated_unwatched[:5]]
                print(f"    unwatched mutations sample: {sample}")
                patched_run_pair._printed = True
            return diffs

        cemu.run_pair = patched_run_pair
        try:
            orig_run_spec(*a, **kw)
            print(f"  call[{idx}] FULL-RESTORE: PASS (!!! HARNESS STATE ASYMMETRY !!!)")
        except AssertionError as e:
            msg = str(e).splitlines()[0] if str(e) else ""
            print(f"  call[{idx}] FULL-RESTORE: FAIL (REAL C DIVERGENCE: {msg[:140]})")
        finally:
            cemu.run_pair = orig_run_pair

pf = load_mod(str(MAIN / "tests" / "test_playflic_t4.py"), "test_playflic_t4")
m2 = load_mod(str(MAIN / "tests" / "test_mod_2efd0_t4.py"), "test_mod_2efd0_t4")

for fn_name in ("test_intro_op_wait_sound", "test_intro_op_start_credits", "test_intro_run_script", "test_intro_play"):
    if hasattr(pf, fn_name):
        inspect_t4_test(getattr(pf, fn_name), f"playflic::{fn_name}")
    else:
        print(f"Missing {fn_name}")

for fn_name in ("test_end_screen",):
    if hasattr(m2, fn_name):
        inspect_t4_test(getattr(m2, fn_name), f"mod_2efd0::{fn_name}")
    else:
        print(f"Missing {fn_name}")
