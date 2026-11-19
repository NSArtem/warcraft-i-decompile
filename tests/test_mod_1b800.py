"""mod_1b800: the game-event sound layer (0x1b800..0x1bf80).

* T3: the C files that wc1.match matches byte for byte under Watcom 10.0a are
  re-matched here (with a lenient symbol load, so another area's half-written
  TOML does not break this test; the authoritative command is
  `python3 -m wc1.match <file>`).
* Near-miss guard: the three reference files must still fail to match (a newly
  matching one has to be promoted to src).
* T4: the reference C of SndEvent, UnitAlertSuppressArea and SndEnemyScan is
  compiled and run next to the original under wc1.emu (wc1.cemu.run_pair) on
  the same inputs; the sound back ends (SndPlay, the message-strip function
  0x19edc, SndEvent for the scan) are stubs that log their arguments into
  emulated memory, which is compared as well.
"""
import glob
import os
import random
import struct
import tomllib

import pytest

from wc1 import analysis, cemu, match, path, symbols

pytestmark = pytest.mark.skipif(
    not (os.path.exists(path("original", "install", "war.exe")) and os.environ.get("WATCOM")),
    reason="needs original/ and $WATCOM (nix develop)")

SRC = path("src", "mod_1b800")
T3_FILES = ["snd_events_init.c","snd_building_destroyed.c","snd_unit_death.c","snd_training_complete.c","snd_unit_select.c","snd_bullet_event.c","unit_set_work_sound.c","snd_construction_tick.c","snd_work_complete.c","snd_tick.c","snd_summon_at.c","fn_1b9b8.c","fn_1bb90.c","fn_1bd04.c","fn_1bd54.c"]
REF_FILES = ["snd_event_reference.c", "unit_alert_suppress_area_reference.c",
             "snd_enemy_scan_reference.c"]


def load_lenient():
    funcs, datas = {}, {}
    for f in sorted(glob.glob(path("analysis", "symbols", "*.toml"))):
        try:
            with open(f, "rb") as fh:
                doc = tomllib.load(fh)
        except tomllib.TOMLDecodeError:
            continue
        for kind, table in (("func", funcs), ("data", datas)):
            for e in doc.get(kind, []):
                e = dict(e)
                if not isinstance(e.get("addr"), int) or "name" not in e:
                    continue
                if kind == "func" and e.get("conv", "watcall") not in (
                        "watcall", "cdecl", "asm", "pascal"):
                    continue
                try:
                    e["link_name"] = symbols.link_name(kind, e)
                except KeyError:
                    continue
                e["_kind"] = kind
                table.setdefault(e["addr"], e)
    return funcs, datas


_funcs, _datas = load_lenient()
_BY_LINK = {e["link_name"]: e for t in (_funcs, _datas) for e in t.values()}
cemu._BY_LINK = dict(_BY_LINK)


def _match(name):
    p = analysis.run()
    src = os.path.join(SRC, name)
    out = path("build", "mod_1b800", "match", name[:-2] + ".obj")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    mod = match.compile_c(src, None, out, cc=match.file_cc(src))
    return match.match_module(p, mod, _BY_LINK)


def test_t3_files_still_match():
    bad = []
    for name in T3_FILES:
        for fname, status, problems in _match(name):
            if status != "MATCH":
                bad.append((name, fname, problems[:2]))
    assert not bad, bad


def test_reference_files_still_do_not_match():
    for name in REF_FILES:
        res = _match(name)
        assert res and all(status != "MATCH" for _, status, _ in res), (name, res)


def test_every_c_file_declares_10_0a():
    for f in sorted(glob.glob(os.path.join(SRC, "*.c"))):
        with open(f) as fh:
            head = [fh.readline() for _ in range(2)]
        assert "codegen-compiler: 10.0a" in "".join(head), f


# ---------------------------------------------------------------- the world

UNIT = 0x5c
LOG = 0
SFX = 0x532bc
SCROLL = 0x500d0          # word x, word y
TOWN_HALL = 0x58db0       # dword per player
HOME = 0x50e68            # (word x, word y) per player
OBJMAP = 0x58580
RACE = 0x50088
RACE_ENEMY = 0x5008a
STATE = 0x59680           # 0x59680..0x5968f, the sound-event state block
SNDPLAY = 0x26958
MSG = 0x19edc
SNDEVENT = 0x1b800


def w16(emu, a, v):
    emu.write(a, struct.pack("<H", v & 0xffff))


def w32(emu, a, v):
    emu.write(a, struct.pack("<I", v & 0xffffffff))


def mkunit(emu, tx=10, ty=10, flags=0, flags2=0, owner=0, timer36=0, alert=0, typ=0):
    a = emu.alloc(UNIT)
    emu.write(a, bytes(UNIT))
    w16(emu, a + 0xa, tx)
    w16(emu, a + 0xc, ty)
    w16(emu, a + 0xe, flags2)
    w16(emu, a + 0x10, flags)
    w16(emu, a + 0x18, alert)
    emu.write(a + 0x1b, bytes([typ]))
    emu.write(a + 0x1e, bytes([owner]))
    w16(emu, a + 0x36, timer36)
    return a


def logger(emu, log, regs):
    """Stub that appends the values of `regs` to the log at `log` (a dword
    counter followed by the entries); returns 0."""
    def stub(e):
        n = struct.unpack("<I", e.read(log, 4))[0]
        for i, r in enumerate(regs):
            w32(e, log + 4 + (n * len(regs) + i) * 4, e.reg(r))
        w32(e, log, n + 1)
        return 0
    return stub


@pytest.fixture(scope="module")
def emu():
    from wc1.emu import Emu
    e = Emu()
    try:
        e.uc.mem_map(0, 0x1000)
    except Exception:
        pass
    return e


def snapshot(emu):
    return None


# ---------------------------------------------------------------- T4: SndEvent

def _event_case(emu, log, cm, id_, unit, sfx, scroll):
    w32(emu, SFX, sfx)
    w16(emu, SCROLL, scroll[0])
    w16(emu, SCROLL + 2, scroll[1])
    emu.write(log, bytes(0x200))
    return cemu.run_pair(emu, SNDEVENT, cm, "SndEvent_", id_, unit, out_regs=(),
                         watch=[(log, 0x200)])


def test_t4_snd_event(emu):
    log = emu.alloc(0x200)
    emu.stubs[SNDPLAY] = logger(emu, log, ["eax"])
    emu.stubs[MSG] = logger(emu, log, ["eax", "edx", "ebx"])
    cm = cemu.load(emu, os.path.join(SRC, "snd_event_reference.c"))
    scroll = (20, 30)
    cases = []
    # ids: none, the global one (0x1b ignores the unit), captioned ids, plain ids
    for id_ in (0, 1, 2, 0x10, 0x11, 0x12, 0x14, 0x18, 0x1b, 0x2c, 0x2f, 0x30):
        cases.append(("noun", id_, 0))
    ok = dict(tx=25, ty=35)
    units = {
        "ok": ok,
        "hidden8": dict(ok, flags=0x8),
        "flag4000": dict(ok, flags=0x4000),
        "flag0207": dict(ok, flags=0x207),
        "flags2": dict(ok, flags2=0x100),
        "flags2other": dict(ok, flags2=0xfeff),
        "left": dict(tx=19, ty=35),
        "right_edge": dict(tx=35, ty=35),
        "right_out": dict(tx=36, ty=35),
        "top": dict(tx=25, ty=29),
        "bottom_edge": dict(tx=25, ty=41),
        "bottom_out": dict(tx=25, ty=42),
        "negative": dict(tx=0xfffe, ty=35),
        "left_edge": dict(tx=20, ty=30),
    }
    for k, kw in units.items():
        for id_ in (3, 0x10, 0x1b, 0x2b):
            cases.append((k, id_, kw))
    n = 0
    for sfx in (0x4e, 0):
        for k, id_, kw in cases:
            unit = 0 if kw == 0 else mkunit(emu, **kw)
            diffs = _event_case(emu, log, cm, id_, unit, sfx, scroll)
            assert diffs == [], (sfx, k, id_, diffs)
            n += 1
    # the logs differ between the cases (so the comparison is not vacuous)
    w32(emu, SFX, 0x4e)
    emu.write(log, bytes(0x200))
    emu.call(SNDEVENT, 5, 0)
    assert struct.unpack("<II", emu.read(log, 8)) == (1, 4)
    w32(emu, SFX, 0)
    emu.write(log, bytes(0x200))
    emu.call(SNDEVENT, 0x10, 0)
    cnt, text, flag, mode = struct.unpack("<IIII", emu.read(log, 16))
    assert (cnt, flag, mode) == (1, 0, 0x24)
    assert emu.read(text, 14).startswith(b"work complete")
    assert n > 100


# ------------------------------------------------- T4: UnitAlertSuppressArea

def test_t4_unit_alert_suppress_area(emu):
    cm = cemu.load(emu, os.path.join(SRC, "unit_alert_suppress_area_reference.c"))
    rng = random.Random(0x1b800)
    centres = [(32, 32), (0, 0), (63, 63), (0, 63), (63, 0), (4, 4), (5, 5), (58, 58),
               (59, 59), (5, 58), (58, 5), (1, 40), (40, 62), (32, 0), (63, 32)]
    centres += [(rng.randrange(64), rng.randrange(64)) for _ in range(25)]
    grid = emu.alloc(0x4000)
    units = emu.alloc(UNIT * 140)
    for cx, cy in centres:
        emu.write(grid, bytes(0x4000))
        emu.write(units, bytes(UNIT * 140))
        k = 0
        cells = {(cx, cy)}
        for _ in range(120):
            cells.add((max(0, min(63, cx + rng.randrange(-8, 9))),
                       max(0, min(63, cy + rng.randrange(-8, 9)))))
        for (x, y) in sorted(cells):
            u = units + k * UNIT
            w16(emu, u + 0xa, x)
            w16(emu, u + 0xc, y)
            w16(emu, u + 0x18, rng.choice([0, 0, 7, 0xfa0]))
            w32(emu, grid + (y * 64 + x) * 4, u)
            k += 1
        w32(emu, OBJMAP, grid)
        centre_unit = units + sorted(cells).index((cx, cy)) * UNIT
        diffs = cemu.run_pair(emu, 0x1bc60, cm, "UnitAlertSuppressArea_", centre_unit,
                              out_regs=(), watch=[(units, UNIT * 140)])
        assert diffs == [], ((cx, cy), diffs)
    # the cool-down really is set in the window (not a vacuous comparison)
    w32(emu, OBJMAP, grid)
    emu.call(0x1bc60, centre_unit)
    assert struct.unpack("<H", emu.read(centre_unit + 0x18, 2))[0] == 0xfa0


# ------------------------------------------------------ T4: SndEnemyScan

def test_t4_snd_enemy_scan(emu):
    cm = cemu.load(emu, os.path.join(SRC, "snd_enemy_scan_reference.c"))
    log = emu.alloc(0x200)
    emu.stubs[SNDEVENT] = logger(emu, log, ["eax", "edx"])
    rng = random.Random(0x1bd64)
    hostility = emu.read(0x51883, 25)
    assert hostility[:5] == bytes([0, 1, 1, 1, 0])      # owner 0 vs 0..4

    grid = emu.alloc(0x4000)
    units = emu.alloc(UNIT * 8)

    def case(home, enemies, hall=1, near=0, alt=0, races=(0, 1), timer=7):
        emu.write(grid, bytes(0x4000))
        emu.write(units, bytes(UNIT * 8))
        for i, (x, y, kw) in enumerate(enemies):
            u = units + i * UNIT
            w16(emu, u + 0x10, kw.get("flags", 0))
            emu.write(u + 0x1e, bytes([kw.get("owner", 1)]))
            w16(emu, u + 0x36, kw.get("timer36", 0))
            w32(emu, grid + (y * 64 + x) * 4, u)
        w32(emu, OBJMAP, grid)
        w32(emu, TOWN_HALL, hall)
        w16(emu, HOME, home[0])
        w16(emu, HOME + 2, home[1])
        w16(emu, RACE, races[0])
        w16(emu, RACE_ENEMY, races[1])
        w16(emu, 0x59688, near)
        w16(emu, 0x5968c, alt)
        w32(emu, 0x59684, timer)
        emu.write(log, bytes(0x200))
        return cemu.run_pair(emu, 0x1bd64, cm, "SndEnemyScan_", out_regs=(),
                             watch=[(STATE, 16), (log, 0x200)])

    homes = [(32, 32), (0, 0), (63, 63), (3, 60), (60, 3), (8, 8), (9, 9), (55, 55),
             (56, 40), (7, 20)]
    for home in homes:
        hx, hy = home
        spots = [(hx, hy), (hx - 8, hy - 8), (hx + 8, hy + 8), (hx - 9, hy), (hx, hy + 9),
                 (hx + 9, hy + 9), (hx + 8, hy - 8), (hx - 8, hy + 8)]
        spots = [(x, y) for x, y in spots if 0 <= x < 64 and 0 <= y < 64]
        # none, every spot alone, the variants that must not count
        assert case(home, []) == []
        for s in spots:
            for kw in ({}, {"owner": 0}, {"owner": 4}, {"owner": 2}, {"flags": 0x200},
                       {"flags": 0x4}, {"flags": 0x1}, {"flags": 0x80}, {"timer36": 3}):
                d = case(home, [(s[0], s[1], kw)])
                assert d == [], (home, s, kw, d)
        for near in (0, 1):
            for alt in (0, 1):
                for races in ((0, 1), (1, 1), (0, 0)):
                    s = spots[rng.randrange(len(spots))]
                    d = case(home, [(s[0], s[1], {})], near=near, alt=alt, races=races)
                    assert d == [], (home, near, alt, races, d)
    assert case((32, 32), [(32, 32, {})], hall=0) == []
    assert case((32, 32), [(33, 32, {})], hall=0, near=1) == []
    # randomised crowds
    for _ in range(60):
        home = (rng.randrange(64), rng.randrange(64))
        en = [(max(0, min(63, home[0] + rng.randrange(-12, 13))),
               max(0, min(63, home[1] + rng.randrange(-12, 13))),
               {"owner": rng.randrange(5), "flags": rng.choice([0, 0, 0x200, 0x80]),
                "timer36": rng.choice([0, 0, 2])}) for _ in range(rng.randrange(0, 8))]
        d = case(home, en, near=rng.randrange(2), alt=rng.randrange(2),
                 races=rng.choice([(0, 1), (1, 1)]))
        assert d == [], (home, en, d)
    # non-vacuous: an enemy next to the town hall plays id 0x14 or 0x15 and sets 1000
    case((32, 32), [(33, 33, {})])           # leaves the world set up; rerun the original
    w16(emu, 0x59688, 0)
    w32(emu, 0x59684, 0)
    emu.write(log, bytes(0x200))
    emu.call(0x1bd64)
    cnt, eax, edx = struct.unpack("<III", emu.read(log, 12))
    assert cnt == 1 and eax in (0x14, 0x15) and edx == 0
    assert struct.unpack("<I", emu.read(0x59684, 4))[0] == 1000
