"""Game sound layer, module mod_269f0 (candidate GAMESND.C), 0x269f0..0x27670.

1. T3 re-check: the reconstructions listed in MATCHED must still compile
   byte-identical with wc1.match under Watcom 10.0a with the module's OD flags
   (`-s -od -4r -zp2`), and the database must still carry them (module
   mod_269f0, no `src =` yet - the session owner wires the matched files in).
2. Near-miss guard: every *_reference.c must still NOT match; if one starts
   matching, promote it (T3 entry with src =, owned by the session owner).
3. T4 difftests of the seven reference functions: the compiled C and the
   original run under wc1.emu on identical inputs with the Miles AIL entry
   points stubbed (the real ones would load a driver file, program the PIT or
   call DPMI services).  Every stub records its arguments into a trace buffer
   that `cemu.run_pair` compares as watched memory, so the *call sequence* and
   the IO block contents are compared as well as the state the function
   changes.
4. Naming invariants: the file names, prototypes and calling conventions the
   area established (the two AIL callbacks are cdecl - visible in their
   prologues and in AIL's own call site).

The AIL stubs (all documented at their address in analysis/symbols/audio.toml):

    addr      function                        args    returns
    0x351b8   AIL_startup                     ()      -
    0x34e5b   AIL_set_preference              (n, v)  old value (0)
    0x37400   AIL_set_GTL_filename_prefix     (path)  -
    0x312f0   DpmiLockRegion (input area)     (a, n)  -   (watcall)
    0x37330   AIL_install_MDI_driver_file     (f, io) fake handle
    0x3a000   AIL_install_DIG_driver_file     (f, io) fake handle
    0x37480   AIL_allocate_sequence_handle    (mdi)   fake handle
    0x3a983   AIL_allocate_file_sample        (d, f, b) fake sample
    0x3aaa3   ail_set_file_sample_end_hook    (s, cb) -
    0x3a380   AIL_start_sample                (s)     -
    0x3a440   AIL_end_sample                  (s)     -
    0x3a370   AIL_set_sample_loop_count       (s, n)  -
    0x3a0d0   AIL_active_sample_count         (d)     n (driven by the test)
    0x3a170   AIL_release_sample_handle       (s)     -
"""
import os
import struct

import pytest

from wc1 import analysis, cemu, match, path, symbols

HAVE = os.path.exists(path("original", "install", "war.exe")) and bool(os.environ.get("WATCOM"))
pytestmark = pytest.mark.skipif(not HAVE, reason="needs original/ and $WATCOM (nix develop)")

AREA = path("src", "audio")
FLAGS = "-s -od -4r -zp2"
MODULE = "mod_269f0"

# link name -> file, the T3 reconstructions of this area
MATCHED = {
    "MusicSetData_": "music_set_data.c",
    "MusicIsPlaying_": "music_is_playing.c",
    "MusicPlayTrack_": "music_play_track.c",
    "MusicStop_": "music_stop.c",
    "SndFadeOut_": "snd_fade_out.c",
    "SndFadeOutAndStopAll_": "snd_fade_out_stop_all.c",
    "SndReleaseAll_": "snd_release_all.c",
    "SndActiveCount_": "snd_active_count.c",
    "SndGetSfxVolume_": "snd_get_sfx_volume.c",
    "SndSetSfxVolume_": "snd_set_sfx_volume.c",
    "SndGetMusicVolume_": "snd_get_music_volume.c",
    "SndSetMusicVolume_": "snd_set_music_volume.c",
    "SndLockStart_": "snd_lock_start.c",
    "SndLockEnd_": "snd_lock_end.c",
    "_MusicFadeTimerCallback": "music_fade_timer.c",
    "SndShutdownAil_": "snd_shutdown_ail.c",
}

REFERENCE = [
    "ail_init_reference.c",
    "snd_install_midi_reference.c",
    "snd_install_digital_reference.c",
    "snd_play_data_reference.c",
    "snd_play_data_looped_reference.c",
    "snd_stop_data_reference.c",
    "snd_sample_ended_reference.c",
]

# the 23 functions of the module (analysis/modules.toml 0x269f0..0x27670)
ALL = {
    0x269F0: "AilInit", 0x26B18: "SndShutdownAil", 0x26B3C: "SndInstallMidi",
    0x26C10: "MusicSetData", 0x26C70: "MusicIsPlaying", 0x26CC8: "MusicPlayTrack",
    0x26D60: "MusicStop", 0x26D98: "SndFadeOut", 0x26E3C: "SndFadeOutAndStopAll",
    0x26F1C: "SndInstallDigital", 0x26FD4: "SndPlayData", 0x270DC: "SndPlayDataLooped",
    0x271F4: "SndReleaseAll", 0x27278: "SndStopData", 0x27320: "SndActiveCount",
    0x27360: "SndGetSfxVolume", 0x27384: "SndSetSfxVolume", 0x2743C: "SndGetMusicVolume",
    0x27460: "SndSetMusicVolume", 0x2753C: "SndLockStart", 0x27554: "SndSampleEndedCallback",
    0x275A8: "MusicFadeTimerCallback", 0x2764C: "SndLockEnd",
}

# AIL entry points (audio.toml) and the game state this area touches
AIL_STARTUP = 0x351B8
AIL_SET_PREFERENCE = 0x34E5B
AIL_SET_GTL_PREFIX = 0x37400
DPNI_LOCK_REGION = 0x312F0
AIL_INSTALL_MDI = 0x37330
AIL_INSTALL_DIG = 0x3A000
AIL_ALLOC_SEQUENCE = 0x37480
AIL_ALLOC_FILE_SAMPLE = 0x3A983
AIL_SET_FILE_SAMPLE_END_HOOK = 0x3AAA3
AIL_START_SAMPLE = 0x3A380
AIL_END_SAMPLE = 0x3A440
AIL_SET_LOOP_COUNT = 0x3A370
AIL_ACTIVE_SAMPLE_COUNT = 0x3A0D0
AIL_RELEASE_SAMPLE = 0x3A170

SND_DIG_ACTIVE = 0x53414
SND_MDI_ACTIVE = 0x53415
SND_FADE_TIMER = 0x53418
SND_HDIG = 0x5A240
SND_HMDI = 0x5A248
SND_MUSIC_DATA = 0x5A244
SND_CHANNELS = 0x5A220
SND_SEQUENCES = 0x5A24C
SND_SFX_VOL = 0x5A252
SND_MUSIC_VOL = 0x5A254
SND_EVICT_NEXT = 0x5342E
SND_EVICT_LOOPED = 0x53430

FAKE_MDI = 0x0012_3400
FAKE_HANDLE = 0x0012_3404
FAKE_SAMPLE = 0x0012_3408


class Trace:
    """Stub argument trace in the emulator heap: a count word then 12-byte
    records (stub address, then its arguments).  Watched by run_pair, so the
    original's and the compiled C's call sequences are compared."""

    def __init__(self, emu, size=768):
        self.emu = emu
        self.addr = emu.alloc(size, 16)
        self.size = size
        self.reset()

    def reset(self):
        self.emu.write(self.addr, b"\0" * self.size)

    def add(self, *vals):
        n = struct.unpack("<I", self.emu.read(self.addr, 4))[0]
        self.emu.write(self.addr + 4 + n * 12,
                       struct.pack("<" + "I" * len(vals), *vals))
        self.emu.write(self.addr, struct.pack("<I", n + 1))


def stub_cdecl(emu, trace, addr, nargs, ret=0, hook=None):
    """Model a cdecl AIL entry point: record (addr, arg1, arg2) and pop the
    stack arguments.  `hook(emu, trace, args)` runs before the record for
    stubs that must capture more (e.g. the IO block words)."""
    def fn(e):
        esp = e.reg("esp")
        args = [e.u32(esp + 4 + 4 * i) for i in range(nargs)]
        # cdecl: the *caller* pops the arguments (the stub only returns), so
        # stub_pops stays 0 - popping here would over-pop the caller's stack.
        if hook:
            hook(e, trace, args)
        trace.add(addr, args[0] if args else 0, args[1] if len(args) > 1 else 0)
        return ret
    emu.stubs[addr] = fn


def stub_watcall(emu, trace, addr, nargs, ret=0):
    def fn(e):
        args = [e.reg(r) for r in ("eax", "edx", "ebx", "ecx")][:nargs]
        trace.add(addr, args[0] if args else 0, args[1] if len(args) > 1 else 0)
        return ret
    emu.stubs[addr] = fn


def base_stubs(emu, trace):
    """The stubs every test needs (startup/shutdown/volume/lock plumbing)."""
    stub_cdecl(emu, trace, AIL_STARTUP, 0)
    stub_cdecl(emu, trace, AIL_SET_PREFERENCE, 2)
    stub_cdecl(emu, trace, AIL_SET_GTL_PREFIX, 1)
    stub_watcall(emu, trace, DPNI_LOCK_REGION, 2)
    return trace


def run_pair(emu, trace, addr, cmod, name, *args, watch=(), out_regs=("eax",),
             stack_args=(), cdecl=False):
    """cemu.run_pair with the stub trace as an extra watched range."""
    diffs = cemu.run_pair(emu, addr, cmod, name, *args,
                          watch=[(trace.addr, trace.size)] + list(watch),
                          out_regs=out_regs, stack_args=stack_args, cdecl=cdecl)
    return diffs


def load(src):
    from wc1.emu import Emu
    emu = Emu()
    trace = Trace(emu)
    base_stubs(emu, trace)
    return emu, trace, cemu.load(emu, os.path.join(AREA, src))


# ---------------------------------------------------------------- T3 re-check
@pytest.mark.parametrize("link_name,name", sorted(MATCHED.items()))
def test_matched_c_still_matches(link_name, name, prog):
    src = os.path.join(AREA, name)
    assert match.file_cflags(src) == f"{match.BASE_CFLAGS} {FLAGS}", name
    assert match.file_cc(src) == "10.0a", name
    out = path("build", "audio_snd", "t3_" + name + ".obj")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    mod = match.compile_c(src, None, out)
    funcs, datas, _ = symbols.load()
    by_link = {e["link_name"]: e for t in (funcs, datas) for e in t.values()}
    res = match.match_module(prog, mod, by_link)
    bad = [(n, s, p) for n, s, p in res if s != "MATCH"]
    assert not bad, bad
    assert link_name in [n for n, _, _ in res], [n for n, _, _ in res]


# ------------------------------------------------------- near-miss guard (T4)
@pytest.mark.parametrize("name", REFERENCE)
def test_reference_c_is_still_a_near_miss(name, prog):
    src = os.path.join(AREA, name)
    out = path("build", "audio_snd", "ref_" + name + ".obj")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    mod = match.compile_c(src, None, out)
    funcs, datas, _ = symbols.load()
    by_link = {e["link_name"]: e for t in (funcs, datas) for e in t.values()}
    res = match.match_module(prog, mod, by_link)
    assert res, name
    assert all(status != "MATCH" for _, status, _ in res), \
        f"{name} now matches - promote it to T3 (session owner adds src =)"


# --------------------------------------------------------------- T4 difftests
def test_ail_init_t4():
    """AilInit (0x269f0): same AIL call sequence (startup, prefix with the
    _makepath result, the six preferences), same locked ranges and volumes."""
    emu, trace, cm = load("ail_init_reference.c")
    watch = [(SND_SFX_VOL, 2), (SND_MUSIC_VOL, 2)]
    diffs = run_pair(emu, trace, 0x269F0, cm, "AilInit_", 70, 90, watch=watch)
    assert diffs == [], diffs[:4]
    # the locks AilInit performs: 1,1,1,6,0x20,4 and the callback range
    locks = []
    n = struct.unpack("<I", emu.read(trace.addr, 4))[0]
    for k in range(n):
        a, b, c = struct.unpack_from("<III", emu.read(trace.addr + 4 + 12 * k, 12))
        if a == DPNI_LOCK_REGION:
            locks.append(b)
    assert len(locks) == 7, locks


def test_snd_install_midi_t4():
    """SndInstallMidi (0x26b3c): the 24-byte IO block the original builds, the
    driver/sequence handles stored, snd_mdi_active and the return value."""
    emu, trace, cm = load("snd_install_midi_reference.c")

    def capture_io(e, tr, args):
        # io block pointer as the second argument; record the four words
        blk = args[1]
        words = struct.unpack("<4H", e.read(blk, 8)) if blk else (0, 0, 0, 0)
        tr.add(0x3733F, words[0] | (words[1] << 16), words[2] | (words[3] << 16))

    stub_cdecl(emu, trace, AIL_INSTALL_MDI, 2, ret=FAKE_MDI, hook=capture_io)
    stub_cdecl(emu, trace, AIL_ALLOC_SEQUENCE, 1, ret=FAKE_HANDLE)
    pathbuf = emu.alloc(32)
    emu.write(pathbuf, b"drivers\\sblaster.mdi\0")
    watch = [(SND_HMDI, 4), (SND_MDI_ACTIVE, 1),
             (SND_SEQUENCES, 4)]
    for io, irq, dma, drq in ((0, 0, 0, 0), (0x220, 5, 1, 3), (0xFFFF, 0xFFFF, 0xFF, 0xFF)):
        diffs = run_pair(emu, trace, 0x26B3C, cm, "SndInstallMidi_", pathbuf,
                         io, irq, dma, drq, stack_args=(drq,), watch=watch)
        assert diffs == [], (io, irq, dma, drq, diffs[:4])


def test_snd_install_digital_t4():
    """SndInstallDigital (0x26f1c): same IO block, the four channel slots are
    cleared, snd_dig_active is set and the return value is 0/1."""
    emu, trace, cm = load("snd_install_digital_reference.c")

    def capture_io(e, tr, args):
        blk = args[1]
        words = struct.unpack("<4H", e.read(blk, 8)) if blk else (0, 0, 0, 0)
        tr.add(0x3A00F, words[0] | (words[1] << 16), words[2] | (words[3] << 16))

    stub_cdecl(emu, trace, AIL_INSTALL_DIG, 2, ret=0, hook=capture_io)
    pathbuf = emu.alloc(32)
    emu.write(pathbuf, b"drivers\\sblaster.dig\0")
    watch = [(SND_HDIG, 4), (SND_DIG_ACTIVE, 1), (SND_CHANNELS, 0x20)]
    emu.write(SND_CHANNELS, struct.pack("<4I", 1, 2, 3, 4) * 2)
    diffs = run_pair(emu, trace, 0x26F1C, cm, "SndInstallDigital_", pathbuf,
                     0x220, 5, 1, 3, stack_args=(3,), watch=watch)
    assert diffs == [], diffs[:4]


def _play_data_setup(emu, trace, looped):
    emu.write(SND_DIG_ACTIVE, b"\x01")
    emu.write(SND_CHANNELS, b"\0" * 0x20)
    emu.write(SND_EVICT_NEXT, b"\0\0")
    emu.write(SND_EVICT_LOOPED, b"\0\0")
    stub_cdecl(emu, trace, AIL_ALLOC_FILE_SAMPLE, 3, ret=FAKE_SAMPLE)
    stub_cdecl(emu, trace, AIL_SET_FILE_SAMPLE_END_HOOK, 2)
    stub_cdecl(emu, trace, AIL_START_SAMPLE, 1)
    stub_cdecl(emu, trace, AIL_END_SAMPLE, 1)
    stub_cdecl(emu, trace, AIL_SET_LOOP_COUNT, 2)
    watch = [(SND_CHANNELS, 0x20), (SND_EVICT_NEXT, 2), (SND_EVICT_LOOPED, 2)]
    return watch


@pytest.mark.parametrize("looped,name,addr,func", [
    (False, "snd_play_data_reference.c", 0x26FD4, "SndPlayData_"),
    (True, "snd_play_data_looped_reference.c", 0x270DC, "SndPlayDataLooped_"),
])
def test_snd_play_data_t4(looped, name, addr, func):
    """SndPlayData / SndPlayDataLooped: free-slot pick, round-robin eviction
    (including the wrap the dword-view counter test performs), the end-hook
    install, the loop count for the looped variant, and the recorded
    {hsample,data} slot."""
    emu, trace, cm = load(name)
    watch = _play_data_setup(emu, trace, looped)
    voc = emu.alloc(64)
    emu.write(voc, b"Creative Voice File\0")
    # 1) all slots free; 2) two busy; 3) all busy, evict slot 0;
    # 4) all busy with the round-robin counter at 3 (the wrap case)
    for slots, evict in (((0, 0, 0, 0), 0),
                         ((0x111, 0, 0x333, 0), 1),
                         ((0x111, 0x222, 0x333, 0x444), 2),
                         ((0x111, 0x222, 0x333, 0x444), 3)):
        for k in range(4):
            emu.write(SND_CHANNELS + 8 * k, struct.pack("<2I", slots[k], 0xA0 + k))
        emu.write(SND_EVICT_NEXT, struct.pack("<H", evict))
        emu.write(SND_EVICT_LOOPED, struct.pack("<H", evict))
        diffs = run_pair(emu, trace, addr, cm, func, voc, watch=watch, out_regs=())
        assert diffs == [], (slots, evict, diffs[:4])


def test_snd_stop_data_t4():
    """SndStopData (0x27278): releases only the channel whose recorded data
    pointer matches (and only while a sample is active)."""
    emu, trace, cm = load("snd_stop_data_reference.c")
    emu.write(SND_DIG_ACTIVE, b"\x01")
    for count in (0, 3):
        stub_cdecl(emu, trace, AIL_ACTIVE_SAMPLE_COUNT, 1, ret=count)
        stub_cdecl(emu, trace, AIL_RELEASE_SAMPLE, 1)
        voc = emu.alloc(32)
        for k in range(4):
            emu.write(SND_CHANNELS + 8 * k, struct.pack("<2I", 0x500 + k, voc + 4 * k))
        diffs = run_pair(emu, trace, 0x27278, cm, "SndStopData_", voc + 8,
                         watch=[(SND_CHANNELS, 0x20)], out_regs=())
        assert diffs == [], (count, diffs[:4])


def test_snd_sample_ended_callback_t4():
    """SndSampleEndedCallback (0x27554) is cdecl (AIL's sample end hook is a
    stack-argument call): the slot whose handle matches is cleared."""
    emu, trace, cm = load("snd_sample_ended_reference.c")
    for slots in ((0x10, 0x20, 0x30, 0x40), (0, 0x20, 0, 0), (0, 0, 0, 0)):
        emu.write(SND_CHANNELS, struct.pack("<4I", *slots))
        emu.write(SND_CHANNELS + 4, b"\0" * 0x10)
        for handle in (0x20, 0x99):
            diffs = run_pair(emu, trace, 0x27554, cm, "_SndSampleEndedCallback",
                             handle, watch=[(SND_CHANNELS, 0x20)], out_regs=(),
                             cdecl=True)
            assert diffs == [], (slots, handle, diffs[:4])


# ------------------------------------------------------------------- database
def test_module_symbols_are_named():
    """All 23 functions of the module are named, in the module range, with the
    calling conventions the prologues show (the two AIL callbacks are cdecl)."""
    funcs, datas, _ = symbols.load()
    for addr, name in ALL.items():
        e = funcs.get(addr)
        assert e is not None, f"{name} ({addr:#x}) missing"
        assert e["name"] == name, (addr, e["name"], name)
        assert e.get("module") == MODULE, (name, e.get("module"))
        if addr != 0x26B18:      # SndShutdownAil was wired in earlier
            if "src" in e:      # wired by the session owner after the T3 report
                assert e["confidence"] == "verified" and e["verified_by"].startswith("match:"), name
    assert funcs[0x27554]["conv"] == "cdecl", "SndSampleEndedCallback is cdecl"
    assert funcs[0x275A8]["conv"] == "cdecl", "MusicFadeTimerCallback is cdecl"
    assert funcs[0x27554]["link_name"] == "_SndSampleEndedCallback"
    assert funcs[0x275A8]["link_name"] == "_MusicFadeTimerCallback"
    assert funcs[0x26B3C]["proto"].startswith(
        "int SndInstallMidi(const char *path, unsigned short io")
    assert funcs[0x27460]["proto"] == "void SndSetMusicVolume(int vol)"


@pytest.fixture(scope="module")
def prog():
    return analysis.run()
