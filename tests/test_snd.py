import os
import re
import struct

import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case, T4Stub

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SND_DIR = path('src/snd')
T3_FILES = ['music_clear.c', 'music_start.c', 'snd_apply_options.c',
            'snd_shutdown.c', 'snd_toggle_music.c', 'snd_toggle_sfx.c']
REF_FILES = ['snd_init_reference.c', 'snd_load_table_reference.c']


def _sym(*names):
    funcs, datas = t4spec.load_lenient()
    for name in names:
        for t in (funcs, datas):
            for e in t.values():
                if e["name"] == name:
                    return e["addr"]
        m = re.fullmatch(r"_?(?:dat|fn)_([0-9a-fA-F]+)", name)
        if m:
            return int(m.group(1), 16)
    raise KeyError(names)


def _w16(emu, name, val):
    emu.write(_sym(name), struct.pack("<H", val & 0xFFFF))


def _w32(emu, name, val):
    emu.write(_sym(name), struct.pack("<I", val & 0xFFFFFFFF))


def test_t3_files_match():
    if T3_FILES:
        t4spec.assert_t3_matches(SND_DIR, T3_FILES)


def test_reference_files_still_mismatch():
    if REF_FILES:
        t4spec.assert_ref_mismatch(SND_DIR, REF_FILES)


# ---------------------------------------------------------------- SndInit

def _init_case(label, dig, mdi, optsfx, optmus):
    def setup(emu):
        _w16(emu, "cfg_dig_driver", dig)
        _w16(emu, "cfg_mdi_driver", mdi)
        for n in ("cfg_dig_io", "cfg_dig_irq", "cfg_dig_dma", "cfg_dig_drq",
                  "cfg_mdi_io", "cfg_mdi_irq", "cfg_mdi_dma", "cfg_mdi_drq"):
            _w16(emu, n, 0x220 + len(n))
        _w32(emu, "opt_sfx_volume", optsfx)
        _w32(emu, "opt_music_volume", optmus)
    return T4Case(setup=setup, label=label)


def _run_init(ret):
    cases = [
        _init_case("none", 0xFFFF, 0xFFFF, 0xFFFFFFFF, 0xFFFFFFFF),
        _init_case("dig_only_unset", 2, 0xFFFF, 0xFFFFFFFF, 0),
        _init_case("dig_only_set", 2, 0xFFFF, 50, 0),
        _init_case("mdi0_unset", 0xFFFF, 0, 0, 0xFFFFFFFF),
        _init_case("mdi3_zero", 0xFFFF, 3, 0, 0),
        _init_case("mdi9_unset", 0xFFFF, 9, 0, 0xFFFFFFFF),
        _init_case("both_unset", 2, 3, 0xFFFFFFFF, 0xFFFFFFFF),
        _init_case("both_set", 2, 9, 50, 40),
    ]
    stubs = [
        T4Stub(_sym("AilInit"), ret=1, log_regs=("eax", "edx")),
        T4Stub(_sym("SndInstallDigital"), ret=ret,
               log_regs=("edx", "ebx", "ecx"), stack_pop=4),
        T4Stub(_sym("SndInstallMidi"), ret=ret,
               log_regs=("edx", "ebx", "ecx"), stack_pop=4),
        T4Stub(_sym("GdsAlloc"), ret=0x123000, log_regs=("eax",)),
        T4Stub(_sym("DpmiLockRegion"), log_regs=("eax", "edx")),
        T4Stub(_sym("_makepath", "makepath"), log_regs=(), stack_pop=4),
        T4Stub(_sym("fputs"), log_regs=("eax", "edx")),
        T4Stub(_sym("exit"), log_regs=("eax",)),
        T4Stub(_sym("FatalError", "_FatalError"), log_regs=()),
    ]
    watch = [(_sym(n), 4) for n in ("opt_sfx_volume", "opt_music_volume")]
    watch += [(_sym(n), 2) for n in ("snd_saved_sfx_pct", "snd_saved_music_pct",
                                     "snd_cur_track", "snd_table_count")]
    watch.append((_sym("snd_music_buffer"), 4))
    t4spec.run_spec(path('src/snd', 'snd_init_reference.c'), "SndInit_", 0x263c0,
                    cases, watch=watch, stubs=stubs, out_regs=())


def test_snd_init():
    _run_init(0)
    _run_init(1)


# ------------------------------------------------------------ SndLoadTable

_bufs = {}


def _init_emu_table(emu):
    _bufs["base"] = emu.alloc(512, 16)
    emu.write(_bufs["base"], bytes(512))


def _table_gen_factory():
    counter = [0]

    def gen(rng):
        counter[0] += 1
        n = rng.randint(1, 6)
        ids = []
        for _ in range(n):
            v = rng.randint(1, 8)
            if ids and rng.random() < 0.4:
                v = rng.choice(ids) & 0x7FFF
                v |= 0x8000
            ids.append(v)
        ids.append(0)
        cnt = rng.randint(0, 5)
        dig = rng.choice((0xFFFF, 2, 0))
        has_cur = rng.random() < 0.5
        pre = bytes(rng.randrange(1, 9) for _ in range(64))
        ptrs = [rng.randrange(0x1000, 0x90000) for _ in range(60)]
        sizes = [rng.randrange(1, 0x4000) for _ in range(60)]

        def setup(emu):
            base = _bufs["base"]
            emu.write(base, pre)
            emu.write(base + 64, b"".join(struct.pack("<H", x) for x in ids))
            _w16(emu, "snd_table_count", cnt)
            _w16(emu, "cfg_dig_driver", dig)
            _w32(emu, "snd_cur_table", (base + 64) if has_cur else 0)
            emu.write(_sym("snd_data_ptrs"),
                      b"".join(struct.pack("<I", x) for x in ptrs))
            emu.write(_sym("snd_data_sizes"),
                      b"".join(struct.pack("<I", x) for x in sizes))
        return T4Case(args=(_bufs["base"] + 64,), setup=setup)
    return gen


def _null_case(label, has_cur, dig):
    def setup(emu):
        base = _bufs["base"]
        emu.write(base + 64, struct.pack("<HHHH", 3, 0x8003, 4, 0))
        emu.write(base + 128, struct.pack("<HHH", 3, 4, 0))
        _w16(emu, "snd_table_count", 2)
        _w16(emu, "cfg_dig_driver", dig)
        _w32(emu, "snd_cur_table", (base + 64) if has_cur else 0)
        emu.write(_sym("snd_data_ptrs"), struct.pack("<I", 0x4000) * 60)
        emu.write(_sym("snd_data_sizes"), struct.pack("<I", 0x100) * 60)
        case.args = (base + 128,)
    case = T4Case(args=(0,), setup=setup, label=label)
    return case


def test_snd_load_table():
    stubs = [
        T4Stub(_sym("ResourceBegin"), ret=0x1234, log_regs=("eax", "edx")),
        T4Stub(_sym("ResourceRead"), ret=0x5678, log_regs=("eax", "edx")),
        T4Stub(_sym("DpmiLockRegion"), log_regs=("eax", "edx")),
        T4Stub(_sym("DpmiUnlockRegion"), log_regs=("eax", "edx")),
        T4Stub(_sym("GdsFree"), log_regs=("eax",)),
    ]
    watch = [(_sym("snd_data_ptrs"), 240), (_sym("snd_data_sizes"), 240),
             (_sym("snd_cur_table"), 4), (_sym("snd_table_count"), 2)]
    cases = [_null_case("null cur dig", True, 2),
             _null_case("null nocur dig", False, 2),
             _null_case("null cur nodig", True, 0xFFFF)]
    t4spec.run_spec(path('src/snd', 'snd_load_table_reference.c'), "SndLoadTable_",
                    0x267fc, cases, watch=watch, stubs=stubs, out_regs=(),
                    init_emu=_init_emu_table, rand_cases=25,
                    rand_gen=_table_gen_factory())
