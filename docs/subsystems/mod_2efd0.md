# mod_2efd0: the map selection layer and the mission-end screen

Area = `mod_2efd0` in `analysis/modules.toml`, **0x2efd0..0x3024e**
(26 discovered functions, 0x127e bytes, "OPT" code `-s -ot -ol -4r -zp2`).
Names, addresses and the evidence for every claim:
`analysis/symbols/mod_2efd0.toml`.  Reconstructed C: `src/mod_2efd0/`;
declarations: `src/include/mod_2efd0.h`; tests: `tests/test_mod_2efd0.py`.

The object is **two layers with a visible seam at 0x2f350**:

| part | addresses | what it is | guide candidate [R1] |
|---|---|---|---|
| A | 0x2efd0..0x2f34e | the map selection layer: click-select with the "select all of the same type" modifier, the drag rectangle (marquee), the order packet the command card sends | `SELECT.C`-shaped (unproven) |
| B | 0x2f350..0x30246 | the mission-end layer: the per-mission victory/defeat conditions, the 0x140-tick poll, and the win/lose screen (`win1/win2/lose1/lose2.war`) with the animated 13-line score | `SCORE.C`-shaped (unproven; `SCORE.C` is the in-game panel at 0x24e50) |

Evidence for the split: the module boundary at 0x2efd0 is linker padding
(12 zero bytes, `analysis/modules.toml`); the seam at 0x2f350 is inside the
object (no padding) and is where `SelectionBoxBegin` installs the second
half's callbacks.  No C string survives in v1.22h, so the file names stay
`name_confidence = speculative`.

---

## 1. Selection layer (0x2efd0..0x2f34e)

Four functions, all driven by the map input dispatcher `fn_1a168` and the
viewport layer callback `ViewportLayerCallback` 0x1b00c:

| addr | name | role |
|---|---|---|
| 0x2efd0 | `SelectionClickUnit` | a click on a unit: replace the selection, or - with one of the (always-zero) modifiers - extend the current local creature selection |
| 0x2f0a8 | `IssueOrderAt` | `NetSendOrder(x, y, target)` then, on the machine that owns the order, `fn_1b9b8(SelectionFirst())` (refresh the map cursor) |
| 0x2f0c8 | `SelectionBoxTrack` | mouse-move half of the marquee: min/max the press anchor against the Event position, w/h, `visible = 1` |
| 0x2f350 | `SelectionBoxBegin` | press in the map viewport: guards (`TargetModeIsActive` = a modal owns the input, `PlaceBoxActive` = build placement), `MouseSetRange(0x48,0xc,0x137,0xbb)`, installs `SelectionBoxFrame` as the frame/click callback and `SelectionBoxTrack` as the mouse callback, cursor 6, remembers the anchor pixel |
| 0x2f15c | `SelectionBoxFrame` | per frame: re-track the mouse, hide the box, convert its edges to map pixels (`screen + map_scroll*16 - origin`), collect the local player's live units whose pixel box intersects it, `SelectionSet(count, list)` |
| 0x2f3dc | `SelectionBoxDraw` | viewport layer tail: outline the box in colour 0xdf while `selection_box.visible` |

### The selection box record (0x5a7d0, 9 words)

| off | field | meaning |
|---|---|---|
| +0x0 | `anchor_x` | press x in screen pixels (stored by `SelectionBoxBegin` from the press Event) |
| +0x2 | `anchor_y` | press y |
| +0x4 | `min_x` | box left (`SelectionBoxTrack`) |
| +0x6 | `min_y` | box top |
| +0x8 | `max_x` | box right |
| +0xa | `max_y` | box bottom |
| +0xc | `w` | `max_x - min_x + 1` |
| +0xe | `h` | `max_y - min_y + 1` |
| +0x10 | `visible` | `SelectionBoxDraw` gate (set by the track half, cleared by the frame half) |

`SelectionBoxDraw` reads `min_x`/`min_y` **through the dword two bytes before
them** (`mov edx,[0x5a7d4]; sar edx,0x10`), i.e. the source kept a 32-bit
view of the pair - the same idiom as `SndSetSfxVolume` and `game_state`
(docs/subsystems/codegen.md).  The C spells it as
`*(int *)((char *)&selection_box.min_x - 2) >> 16`; with that the file is T3.

### Two modifiers that are dead in v1.22h

`sel_mod_select_all` (0x5a928) and `sel_mod_add` (0x5a940) are read by
`SelectionClickUnit` and `SelectionBoxFrame` and **written nowhere in the
image**, so both are 0 at runtime and the additive / same-type branches are
dead - the same situation as the PLAYFLIC object.  Names state the intended
use only.

### Which units a box selects

`SelectionBoxFrame` scans the 200 unit records (`unit_array` 0x59640, 0x5c
bytes each) and skips a record when

* `flags & 0x207` (dead/gone), `flags & 0x8`, or `flags2 & 0x100`,
* its pixel box (`u->px/u->py`, size `unit_pixel_size[type]` 0x51b9c) does not
  intersect the map-pixel rectangle,
* `add` is set and `flags & 0x40`.

Then: `type_is_creature[type]` (0x51cc0, 1 for 0..0x1f) decides - a
**building** becomes the single "pick" fallback, a **creature** of owner 0
goes into the list (up to 4), and any other owner is also a fallback.  With an
empty list and a fallback, the fallback is selected alone.

`SelectionClickUnit` uses the same two tables for the (dead) same-type mode:
it keeps up to four entries of the current selection, drops the clicked unit
and appends it.

---

## 2. Mission-end layer (0x2f350..0x3024e)

### The condition functions and the poll

`MissionStartCheck` (0x2f788, called once at scenario start from `fn_195ac`
0x19767) installs one condition into `end_screen_action` (0x5a860):

| scenario `objectives` bit (0x50092) | condition |
|---|---|
| `demo_mode` 0x5152c set (the game_mode 9 attract mode) | `EndCheckDemo` 0x2f754 -> `MissionToMenu` (game_mode 4) |
| 0x01 "build up" | `EndCheckSurvive` 0x2f694 |
| 0x20 "destroy the enemy" | `EndCheckElimination` 0x2f4c0 |
| anything else | `EndCheckObjectives` 0x2f540 (the default) |
| 0x80 | also enables the palette cycle (`palette_cycles` 0x628a0 = 1) |

`MissionEndTick` (0x2f7fc) is the poll: it decrements `end_check_timer`
(0x5a868, started at 1), and every 0x140 (320) ticks calls the condition;
`force != 0` (the message path 0x19d33, i.e. the other machine's quit) runs it
immediately.

The conditions write `VictoryDialog` 0x1aa7c / `DefeatDialog` 0x1ab28 (or
`MissionToMenu` 0x2f748, game_mode 4 = main menu) into `end_screen_action`,
except in a link game (`game_mode 3`) where they only send control packet
0x0a.  `MissionDefeat` (0x2f73c) is the small "install DefeatDialog" function
the survive check tail-jumps to (and `UnitRemove` calls).

Cheat bits: 0x100 (`cheat_flags.b[1] & 1`, "yours truly") forces victory,
0x80 (`cheat_flags.b[0] & 0x80`, "crushing defeat") forces defeat.

| condition | victory | defeat |
|---|---|---|
| `EndCheckElimination` | other players have no men (0x58e2a) and no buildings (0x58e20) | this player has neither |
| `EndCheckSurvive` | unit cap >= 6 and two town halls (`player_town_hall_count` 0x58df6) and a town hall | no town hall, no workers, gold < 400; or a town hall but no workers and gold < 400 |
| `EndCheckObjectives` | objectives 0x10 (one enemy building left, no enemy men), 0x02 (every other player wiped out), 0x84 (`ObjectiveUnitCount` >= `scenario_objective_count` 0x50096) | no men and no town hall ever (0x58df6 == 0) or not even 400 gold; or only workers, no town hall and gold+lumber < 400 |
| `EndCheckDemo` | either side wiped out -> back to the menu | same |

`ObjectiveUnitCount` (0x2f428) counts the local player's live units on tiles
whose `map_flags` word has bit 0x20 (an objective/escape zone) and, when
objectives bit 0x04 is set, returns `count >= scenario_objective_count`.

### The win/lose screen (0x2fcfc `EndScreen` + 0x2fac4 `EndScreenMovie`)

`EndScreen` (called from `fn_1e158` for game_mode 6/7):

1. `ResourceBegin(0x19f + scenario_race)` -> palette 0x58f20,
   `GdsAlloc(0x5080)` for the 184x112 panel (0x5a7f0), two 0xfa00 FLIC
   buffers, `FlicOpen(win1|win2|lose1|lose2.war, chunk, image, 1, 0xcf)`; when
   the movie cannot be opened it loads the static panel resources
   0x1a1..0x1a4 and copies 0x26d palette bytes to 0x58f23.
2. Layers: **13** = the panel at (0x75,0xc) 0xb8x0x70 with `BitmapBlit`,
   **14** = the rank name (rectangle 0x10/0x1c/0x5c/0x17 for a victory,
   0x15/0x1c/0x4f/0x13 for a defeat), **15** = the numbers bitmap
   (`end_text_bm` 0x552f8, 290x128, data from `GdsAlloc(0x9100)`).
3. The 13 numbers: three columns of four (x 87/187/285, y 75/85/107/117) plus
   the centred score line at (48,25).  Targets come from the mission counters:

| row | target |
|---|---|
| 0..3 | dead men: others' sum, own, own dead + own alive, others' dead + others' alive |
| 4..7 | dead buildings: the same four |
| 8, 9 | harvested gold (0x50dc0): own, others' sum |
| 10, 11 | harvested lumber (0x50dd4): own, others' sum |
| 12 | `player_score[0]` |

   The count-up steps are `end_value_step` 0x5530c (1 for the unit rows, 500
   for gold, 200/100 for lumber).
4. Music: `SndLoadTable(0x5535a)` + `MusicStart(8..0xb)` chosen by
   game_mode/race, `PaletteFadeIn(0x96)`, `EndScreenMovie`, `PaletteFadeOut`,
   `MusicClear`, then the layers' bitmaps are freed and `CursorLayerShow`.

`EndScreenMovie` runs the animation loop: installs `EndScreenInput` (any mouse
event or a non-ASCII key sends control packet 0x0b = skip) and
`EndScreenTick` as `dialog_idle` (movie_state 0x58da4 = 1 while it owns the
screen), plays one `EndScreenSoundId` (0x2fa30), and then per pass:
`UiEventPump`, `PacketTick` every 0x1e passes, `ScreenUpdate`, the count-up
(`EndScreenAnimate` 0x2f9b4, which redraws via `EndScreenDraw` 0x2f938 and
plays sound 0 while anything moves), the rank name (`RankName` 0x255b8)
centred at (0x30 - width/2, 2) in the text bitmap, and one movie frame per two
`EndScreenTick`s (the second movie of the pair is opened when the first ends).

`EndScreenSoundId` returns `2 + (scenario_race != 0)` for game_mode 7 and
otherwise a random entry of one of the four 6-track tables 0x55370/0x5537c/
0x55388/0x55394, chosen by `(scenario_race == scenario_race_enemy,
scenario_race)`; the LCG is `fn_19478` (0x50d7c).

---

## 3. Verification state

T3 (byte-identical under Watcom 10.0a, `wc1.match`), 10 functions:
`SelectionClickUnit` 0x2efd0, `SelectionBoxTrack` 0x2f0c8 (`-oa`), `SelectionBoxDraw` 0x2f3dc, `EndCheckDemo`
0x2f754, `MissionDefeat` 0x2f73c, `MissionToMenu` 0x2f748, `MissionEndTick`
0x2f7fc, `EndScreenInput` 0x2f90c, `EndScreenTick` 0x2f930, `EndScreenStop`
0x2fa24.

T4 (reference C + `wc1.cemu.run_pair` difftest), 12 functions:
`IssueOrderAt` 0x2f0a8, `SelectionBoxFrame`
0x2f15c, `SelectionBoxBegin` 0x2f350, `EndCheckElimination` 0x2f4c0,
`EndCheckSurvive` 0x2f694, `MissionStartCheck` 0x2f788, `FormatNumber`
0x2f830, `DrawNumberRight` 0x2f878, `DrawNumberCentre` 0x2f8bc,
`EndScreenSoundId` 0x2fa30, `EndScreenAnimate` 0x2f9b4, `EndScreenMovie`
0x2fac4.

Reference C whose T4 difftest is still pending (the emu harness needs the clib
and bitmap setup first; the entries say so): `ObjectiveUnitCount` 0x2f428,
`EndCheckObjectives` 0x2f540, `EndScreenDraw` 0x2f938, `EndScreen` 0x2fcfc.

### Why IssueOrderAt cannot share an object with SelectionClickUnit

The original places `IssueOrderAt` immediately after `SelectionClickUnit`'s
`ret` (0x2f0a7) with no padding, and its `jne` at 0x2f0b9 returns to that
**shared epilogue**.  wcc386 10.0a does merge the epilogue, but it also puts
the second function of an object on a 16-byte boundary: 8 bytes of
`lea eax,[eax]`/`mov ecx,ecx` filler between the two, measured over every
optimization flag set that reproduces `SelectionClickUnit`'s 0xd8 bytes.
Standalone, `IssueOrderAt` gets its own `ret` and the `jne` goes forward.
`-os` gives the right layout (2-byte alignment) but changes
`SelectionClickUnit`'s prologue completely (it emits `enter`).  So the two are
built as two objects (T3 + T4 reference).

### The MissionEndTick argument

`MissionEndTick` takes a `short` `force` argument (`test ax,ax` in the
original; an `int` makes 10.0a emit `test eax,eax`).  The frame loop calls it
with 0 and the message path 0x19d33 with 1.

---

## 4. Data used from other areas

* unit record (0x5c bytes), `unit_array` 0x59640: docs/subsystems/game_2c4e0.md
* `map_flags` 0x5857c, `map_scroll_x/y` 0x500d0/0x500d2: game_2c4e0 / cmd_123f0
* score counters `dead_men` 0x50d8e, `dead_buildings` 0x50da2,
  `player_building_count` 0x58e1e, `player_town_hall_count` 0x58df6,
  `harvested_gold` 0x50dc0, `harvested_lumber` 0x50dd4, `player_score`
  0x50e34: save_score / mod_104b0 (the counters are documented there; the
  names for the two never-named ones are this area's)
* `type_is_creature` 0x51cc0 and `unit_pixel_size` 0x51b9c: this area (the
  "is a unit" predicate and the pixel extent used by the box test)
* cheat bits: cmd_123f0 (`cheat_flags` 0x51214)
* `Event`, `Layer`, `Bitmap`, `Rect`: input / graphics
* `SelectionFirst/Next` 0x25cc4/0x25c50 and `SelectionSet` 0x262a0: status /
  mod_25ba0 (`SelectionSet` is named by this area, see the TOML)

## 5. Open questions

* The two file names.  The object merges a selection layer and the mission-end
  screen, so either `modules.toml` should split the range at 0x2f350 (both
  halves have their own callers) or the original file really held both.
* `sel_mod_select_all`/`sel_mod_add`: the input code that would set them is
  not in v1.22h.
* `end_check_timer` starts at 1 and the code acts when it reaches 0, so the
  first condition check happens on the second poll; whether that is intended
  or an off-by-one in the original is not decidable from the code.
