# STATUS.C: the unit status / command panel (0x27b20..0x295d0)

Area = `STATUS.C` **0x27b20..0x295d0** (`analysis/modules.toml`, 81 discovered
functions).  Names, prototypes and per-address evidence:
`analysis/symbols/status.toml`; declarations `src/include/status.h`;
reconstructed C in `src/status/`; tests `tests/test_status.py`.

Two things live here, and the code is interleaved: the **command card** (which
button does what, per unit type) and the **info panel** (portrait, health bar,
name, food usage, gold left).

## 1. The panel

The panel is a 72x128 window at the bottom-left of the screen:

| datum | value | where |
|---|---|---|
| screen rect | `{0, 0x48, 0x47, 0xc7, 0x48, 0x80}` = x 0..71, y 72..199 | `status_panel_rect` 0x53570 |
| offscreen bitmap | 72 x 128, created from the rect by `fn_21d0c` (layer 0x13) | `status_panel_bm` 0x53568 |
| full-panel dirty box | `DirtyRectAddBox(0, 0x48, 0x47, 0xc7)` | 0x2951f |
| info line (screen) | `{3, 0xbc, 0x43, 0xc6, 0x41, 0xa}` = x 3..67, y 188..198 | `status_info_rect` 0x53590 |
| info line (panel) | source rect `{.., w=0x40, h=0xa}`, blitted at (3, 0x74) | `status_info_src_rect` 0x53584 |
| command buttons | 6 slots, two columns x = 2/0x24, rows y = 0x74/0x8b/0xa2, 32x23 | `command_button_rect` 0x514e4 |

Everything the panel draws goes through `cur_bitmap` (0x55438), which is set to
`status_panel_bm` while painting; the blitters use panel-relative coordinates
(the button rects store screen y and the painters subtract the panel origin
0x48, e.g. 0x28510).

The graphics are `DATA.WAR` resources, loaded by `StatusPanelInit` (0x29120)
and freed by `StatusPanelFree` (0x292a4):

| resource | symbol | use |
|---|---|---|
| 0x16b | `unit_icon_grp` 0x53560 | unit heads (frames 0..0x1d) **and** the command symbols |
| 0x169 / 0x16a (`+race`) | `unit_portrait_grp` 0x53564 | the large portraits, per-race frame pairs, plus group frames |
| 0x16c / 0x16d | `status_info_bm_normal/pressed` 0x53528/0x53530 | info-line background |
| 0x16e / 0x16f | `status_button_bm_normal/pressed` 0x53538/0x53540 | button background |
| 0x19a / 0x19b | `status_carry_bm[2]` 0x53550/0x53558 | gold / lumber carry icon |
| 0xe4 + race | `status_panel_art` 0x53548 | the panel artwork, blitted at (0,0) |
| 0x19c | `status_bar_icon_bm` 0x53520 | icon over the construction bar |

## 2. The command card: `unit_panel_table` (0x549c4)

A 14-byte descriptor per unit type **0x00..0x3c** (61 entries; the table ends
exactly where the unit-name strings start, 0x54d1a):

```c
typedef struct UnitPanel {
    unsigned short nbuttons;         /* +0 */
    const CommandButton *buttons;    /* +2 */
    unsigned short (*changed)(void); /* +6 "does the panel need a repaint?" */
    void (*draw)(void);              /* +0xa extra lines, 0 = none */
} UnitPanel;
```

The ids 0x36..0x3c are not unit types: they are the **build menus** a peasant
can switch to (`type_copy`, unit+0x1c, is set to them by the order layer's
0x20c30):

| id | card |
|---|---|
| 0x35 / 0x37 | human / orc basic structures (farm, lumber mill, barracks, cancel) |
| 0x36 / 0x38 | human / orc advanced structures (blacksmith, church/temple, stable/kennel, tower, rebuild town hall, cancel) |
| 0x39 / 0x3a | single cancel-button cards |
| 0x3b / 0x3c | move/stop/attack cards whose attack gate is "no worker selected" |

A button is a 0x14-byte **byte-packed** record (the action pointer sits at
offset 0x0f, unaligned):

```c
typedef struct CommandButton {
    unsigned short icon;        /* 0x00 icon slot -> command_button_rect */
    unsigned short face;        /* 0x02 frame in unit_icon_grp */
    unsigned short (*available)(short is_unit); /* 0x04 */
    const char *label;          /* 0x08 info-line text */
    unsigned char key;          /* 0x0c PC scan code */
    unsigned char kind;         /* 0x0d 1 = build/train (arg = unit type) */
    unsigned char arg;          /* 0x0e order argument / research row */
    void (*action)(unsigned char arg);           /* 0x0f */
    unsigned char pad13;
} CommandButton;
```

Examples (the whole set: `python3 -m wc1.status_dump`, which prints every card,
its buttons and the string pool):

| record | slot | face | gate | key | label | action |
|---|---|---|---|---|---|---|
| 0x53b00 | 0 | 0x21 | `ButtonAlwaysAvailable` | 'M' 0x32 | `@1m@2ove` | 0x20ec4 (order 3) |
| 0x53b14…0x53b3c | 1 | 0x4f/0x50/0x51 | `ArmourIs0/1/2` | 'S' 0x1f | `@1s@2top` | 0x20e98 (order 2) |
| 0x53b50…0x53b78 | 2 | 0x3f/0x40/0x41 | `MeleeWeaponIs0/1/2` | 'A' 0x1e | `@1a@2ttack` | 0x21030 (order 4) |
| 0x53e34 | 3 | 0x24 | `CanHarvest` | 'H' 0x23 | `@1h@2arvest lumber/mine gold` | 0x210cc (order 0xa) |
| 0x53e48 | 3 | 0x27 | `CanReturnGoods` | 'T' 0x14 | `return goods to @1t@2own hall` | 0x21130 (order 0xb) |
| 0x53e5c | 4 | 0x25 | `CanBuildBasicStructure` | 'B' 0x30 | `build @1b@2asic structure` | 0x20c30 (menu 0x35/0x37) |
| 0x53f10 | 0 | 0x0e | `CanBuildFarm` | 'F' 0x21 | `build @1f@2arm` | 0x212ac (build 0x20) |

The three icon variants of stop/attack are the **same command with a different
picture**: the gate tests the player's upgrade level (armour for stop, the
weapon for attack), so exactly one variant is available and shows the unit's
current equipment.

### the availability gates

The `available` field is a `unsigned short (*)(short is_unit)` where
`is_unit = unit->type <= 0x1f` (the panel passes that argument at 0x2849c).
The gates read three sources:

* `scenario_unit_mask` (0x50004, a dword of per-scenario availability bits):
  bit 0 footman/grunt, 1 worker, 2 catapult, 3 knight, 4 archer, 5 conjurer,
  6 cleric, 7 farm, 8 barracks, 9 church, 10 tower, 11 rebuild town hall,
  12 lumber mill, 13 stable, 14 blacksmith, 15/16/17/18/19/20 the six spell
  rows, 21 road, 22 wall.  The scenario setup `fn_1e7b0` writes 0x600880
  (farm + rebuild + road + wall) as the always-buildable default.
* the per-player counters `player_mills/blacksmiths/stables/town_hall`
  (0x58e0a/0x58e14/0x58e3c/0x58db0): blacksmith, stable, church, archer,
  catapult and knight need their prerequisite building; "rebuild the town
  hall" needs `player_town_hall[0] == 0`.
* `player_upgrade` (`dat_50008`, 10 rows x 5 players, column 0 is the human):

  | row | meaning | evidence |
  |---|---|---|
  | 0 | ranged weapon level (archer/spearman) | `fn_104b0` adds `0x51098[level&0xf]` for types 8/9 |
  | 1 | melee weapon level | `fn_104b0` for every other type |
  | 2 | speed upgrade (breed faster horses/wolves) | `fn_2ec0c` (the unit tick), gate 0x27da0 |
  | 9 | armour level | `fn_104b0` subtracts `0x5109b[level&0xf]` of the target |
  | 3..8 | the six spells (0 = not researched, 1 = known) | `SetCheatFlags` "eye of newt" sets 1 |

  The two research commands `fn_11910`/`fn_11930` raise rows 0/2 and
  `fn_11950` raises row 1 or 9 (whichever is lower), capped at 2; the cost of
  the next level is `upgrade_level_cost[level]` (75, 150, maxed = 0) times 10
  (`ResearchCost` 0x28c60).

## 3. Panel state

| global | meaning |
|---|---|
| `status_unit_req` 0x5a2c8 | the unit the selection module wants shown (`StatusPanelSetUnit`) |
| `status_unit` 0x5a2c4 | the unit actually shown |
| `status_unit_type` 0x5a2dc | its `type_copy` (the card id), 0xffff = nothing |
| `status_button` 0x5a2c0, `status_button_rect` 0x5a2cc | the focused button and its rect (or the info-line pseudo button) |
| `status_pressed` 0x5a2e0 | 1 while the focused button is drawn pressed (= armed) |
| `status_visible` 0x5a2da | the panel is open |
| `status_lock` 0x5a2d6 | nesting counter: suppress the panel while a remote dialog is open (`fn_215f0` calls `StatusPanelLockAdjust` 12 times) |
| `status_dirty` 0x5a2d0 | a "repaint now" request (set when the shown unit dies/leaves: 0x2d148, 0x2e251, 0x14352, 0x145b7) |
| `status_sel_count` 0x5a2de | the selection count the panel was last drawn for |
| `status_hp_cache[4]` 0x5a2b8, `status_damage_cache[4]` 0x5a260 | per slot: what was drawn, compared by `UnitPanelStateChanged` |
| `status_men_used` 0x5a2d4, `status_men_grown` 0x5a2d8 | the farm's two numbers |
| `status_flags_cache` 0x5a2e3, `status_progress_cache` 0x5a2e4 | the worker's `+0x49` byte / the gold mine's `+0x54` dword |

`status_text` 0x55148 is the text the panel/message line shows; the info-line
help string for the status chart is a second slot, `status_help_text` 0x59500.

## 4. The frame flow

```
scenario start fn_195ac            -> StatusPanelInit       (0x29120)
selection changed (mod_25ba0)      -> StatusPanelSetUnit    (0x290f8)
mouse over the panel               -> StatusPanelTextRefresh(0x28e88)
                                      + StatusPanelPressUpdate (0x28580)
mouse click / frame callback       -> StatusPanelClick     (0x28600)
every game loop pass fn_197b0      -> UnitPanelUpdate      (0x29450)
  -> StatusPanelCacheUnitState 0x287f0, StatusTextForUnit 0x28d58,
     StatusPanelDraw 0x28894, ScreenUpdate
keyboard (map input fn_19fd8)      -> StatusPanelHandleKey  (0x29354)
teardown fn_19b14                  -> StatusPanelFree      (0x292a4)
```

The three map-view callback slots the panel installs are 0x5940c
(`status_mouse_callback` = `StatusPanelPressUpdate`), 0x59414 and 0x5941c (both
`StatusPanelClick`); `MapInputRestore` (0x1a328) puts the normal handlers back.

## 5. The drawing primitives it calls

`DrawText(x, y, s)`, `TextSetColorBase(c)` with `cur_font`, `FillRect(x, y, w,
h)` with `draw_color`, `BitmapBlit`/`BitmapBlitAll`/`BitmapBlitTransparentAll`,
`GrpFrameBitmap(grp, frame, &out)`, `DirtyRectUnion`, `DirtyRectAddBox`,
`ScreenUpdate`, `LayerInvalidate`; `sprintf` for the numbers
(`src/include/status.h` has the prototypes and the DB addresses).

Bars:

* `HealthBarDraw` (0x2864c) - 27 * hp / max hp wide, 3 high, colour from
  `bar_color_table` (0x5357c = `{75,0xdf},{50,0xdd},{0,0xde}`) picked with
  100 * hp / max.  Drawn at (0x25,0x14) for one unit and at
  (4,0x11)/(0x26,0x11)/(4,0x27)/(0x26,0x27) for up to four group members.
* `HealthBarDrawSingle` (0x28700) - panel state 1: 27 * unit+0x1a / 255 wide at
  (0x25,9), colour 0xdf.
* `ProgressBarDraw` (0x28770) - panel state 2: 62 * unit+0x1a / 255 wide at
  (4,0x25), 5 high, plus the icon `status_bar_icon_bm`.

## 6. Per-function notes

### availability gates (T3, one function per file)
`ButtonAlwaysAvailable` 0x27b20, `CanTrainWorker` 0x27bb4, `CanTrainFootman`
0x27be0, `CanBuildRoad` 0x27c40, `CanBuildWall` 0x27c50, `CanTrainConjurer`
0x27c60, `CanTrainCleric` 0x27c70, `CanBuildLumberMill` 0x27c80,
`CanBuildFarm` 0x27cc8, `CanBuildBarracks` 0x27cd8, `CanRebuildTownHall`
0x27b98, `CanTrainArcher` 0x27bc4, `CanBuildCatapult` 0x27bf0,
`CanTrainKnight` 0x27c18, `CanBuildBlacksmith` 0x27c90, `CanBuildStable`
0x27cac, `CanBuildTower` 0x27ce8, `CanBuildChurch` 0x27d04,
`CanResearchMinorSummoning` 0x27ef4 … `CanResearchInvisibility` 0x27f80,
`CanCastMinorSummon` 0x27f9c … `CanCastInvisibility` 0x28050,
`OneUnitSelected` 0x280a4, `OpenGameMenu` 0x281e8 (F10 -> packet 8),
`CanCancelUpgrade` 0x28140.

The eleven upgrade-level tests 0x27d20..0x27ec8 print their row/level in the
name: `RangedWeaponIs0/1/2`, `SpeedIs0/1`, `MeleeWeaponIs0/1/2`,
`ArmourIs0/1/2`.  All take `short is_unit` and mask the level byte with 0x0f
(unit) or 0xff (building).

### reference C (T4)
`CanHarvest`, `CanReturnGoods`, `SelectionHasNoWorkers` (0x27b28/0x27b68/
0x28074, `selection_reference.c`), `UnitPanelStateChanged`, `FarmPanelChanged`
(`panel_state_reference.c`), `FarmPanelDraw`, `GoldMinePanelDraw`,
`ResearchCost`, `StatusTextForUnit` (`panel_text_reference.c`),
`ButtonAvailable`, `ButtonDraw`, `HealthBarDraw`, `HealthBarDrawSingle`,
`ProgressBarDraw`, `UnitPanelDraw`, `StatusPanelDraw` (`draw_reference.c`),
`StatusPanelPressUpdate`, `StatusPanelClick`, `StatusPanelShow`,
`StatusPanelHandleKey` (`input_reference.c`), `StatusPanelSetUnit`,
`StatusPanelInit`, `StatusPanelFree` (`init_reference.c`),
`StatusPanelTextRefresh`, `UnitPanelUpdate` (`update_reference.c`),
`StatusPanelLockClear` 0x29410 and `StatusPanelLockAdjust` 0x29424 (own files),
`CanBuildBasicStructure` 0x280b8, `CanBuildAdvancedStructure` 0x280e8,
`CanCancelTraining` 0x28170, `CanCancelConstruction` 0x281ac.

`SelectionIsWorkersFalse` (0x28090) and `SelectionIsWorkersNext` (0x28093) are
**not functions**: they are the shared `return 0` block and the loop
continuation of `SelectionHasNoWorkers` (0x28074..0x280a2), which code
discovery splits into three starts because of the mid-function return and the
two jumps over it.  `0x28090` is also the `available` field of the
"cancel construction" buttons (0x542ac/0x54374/...), which is why it is
referenced from the data.

`StatusPanelDraw` (0x28894) draws one of three layouts from the "state":
0/1 = one unit (portrait frame 0 or the type's flag), 2 = a building under
construction, 3..5 = a group of 2..4 units (group portrait frame `state`,
`state+3` for the roster, the members' head icons and health bars).  The state
is `player_selection_count+1` for a group, 0 for a foreign owner, 2 for a busy
or dead building, else `unit_names[type].flags`.

### the info line
`StatusTextForUnit` (0x28d58) picks the text: a carrying worker shows "carrying
gold"/"carrying lumber" (`unit+0x49` bits 0x80/0x20), a busy building with
order 0xf shows "training a<suffix>" (the suffix table 0x5506c) or "building a
wall" for the construction menu 0x35, order 0x10 shows the research text
(0x550f8); otherwise a damaged unit shows "full repairs will cost %d gold &
lumber" with `missing/8 + 1`.  Only the local player's units (owner 0) get a
text.

`StatusPanelTextRefresh` (0x28e88) is the mouse-over: over the info line it
shows "menu (@1F10@2)" and focuses the pseudo button at 0x53aec; over a command
button it shows the button's label and fills the tooltip numbers: kind 1
(build/train) gold = `score_value[type]*10`, lumber =
`unit_lumber_cost[type]*10`; kind 2 (research) gold =
`ResearchCost(owner, row, &level)`; the chart `fn_1a168` renders them.

## 7. Discovery / data notes

* `status_unused_d2` (0x5a2d2) is written once (0 = `StatusPanelInit`) and
  never read: dead state from an older panel revision.
* `status_work_state` (0x5a2e2) copies `unit+0x4e` for a building and is never
  read either.
* `unit_panel_table` entries 0x0e/0x10/0x32/0x33/0x34 have no button block
  (0x0e is Medivh, 0x10 "Wounded", 0x33/0x34 the unused types) - the panel
  shows the portrait only; 0x39/0x3a are single-cancel cards.
* The unit record's `+0x46` dword (work/progress) and `+0x49` byte (the
  carrying/loaded state bits 0x20/0x80) overlap: the union in `status.h`
  models both views, as the original does.

## 8. Verification status

> **Watcom 10.0a (2026-11-18).**  With the original compiler
> (docs/subsystems/compiler.md) every built file of the area carries
> `codegen-compiler: 10.0a`, and four former reference functions are T3 and
> built from C: ButtonAvailable 0x28434 (split out of `draw_reference.c` into
> `button_available.c`), CanCancelTraining 0x28170, CanCancelConstruction 0x281ac
> and StatusPanelLockClear 0x29410 (their own files).  Their T4 tests still run.
> The OW2 near-miss notes below are history.

48 of the 81 functions are T3 (`src =`, `wc1.match`, each in its own object so
the build can link them in place):

* the 24 availability gates that need nothing but a mask/level/counter test,
  including all eleven upgrade-level tests;
* `ButtonAlwaysAvailable`, `OpenGameMenu`, `OneUnitSelected`,
  `StatusPanelLockGet`;
* `GoldMinePanelChanged` 0x28360, `WorkerPanelChanged` 0x28400,
  `StatusPanelCacheUnitState` 0x287f0, `CanCancelUpgrade` 0x28140,
  `CanResearch*`/`CanCast*` (the twelve spell gates).

31 functions are reference C (T4 or not yet difftested, see each entry): the
ones that draw, the iterators over the selection, the state machine and the
init/free pair.

T4 difftests (`tests/test_status.py`, `wc1.cemu.run_pair`, compiled C vs the
original on identical inputs): `test_t4_can_harvest`,
`test_t4_can_return_goods`, `test_t4_selection_is_workers`,
`test_t4_unit_panel_state_changed`, `test_t4_farm_panel_changed`,
`test_t4_farm_panel_draw`, `test_t4_gold_mine_panel_draw`,
`test_t4_research_cost`, `test_t4_health_bar_draw`,
`test_t4_health_bar_draw_single`, `test_t4_progress_bar_draw`,
`test_t4_status_text_for_unit`, `test_t4_button_available`,
`test_t4_status_panel_press_update`, `test_t4_status_panel_lock_adjust`,
`test_t4_status_panel_lock_clear`, `test_t4_status_panel_set_unit`,
`test_t4_status_panel_handle_key`, `test_t4_can_cancel_training`,
`test_t4_can_cancel_construction`, `test_t4_can_build_basic_structure`,
`test_t4_can_build_advanced_structure`.

Structural tests: `test_status_string_pool` (the 0x57d50..0x57dd9 pool),
`test_footman_command_card` (the card of type 0, the farm/gold-mine painters,
the six button rects), `test_panel_rect_and_module_boundary`.

## 9. Open questions

* `unit_names[type].flags` (the second word of the 8-byte name record, 1 for
  the spellcasters and several monsters) is only read as the initial panel
  state; its meaning is unclear (it never reaches the >= 3 branch).
* The constants 0x62/0x63 that `CanCancelUpgrade/Training/Construction` pass to
  `SelectionFirst` (0x25cc4 ignores the register) are still unexplained.
* `CanCancelUpgrade` requires `unit+0x46 != 0`, while the training/construction
  gates require `== 0` - read from the code, not explained.
* The text at 0x57de8 "Select target" is in the module's string slice but no
  function of the range references it.
* The info-line pseudo button 0x53aec holds `kind = 0xff`, `arg = 0xff`: `StatusPanelTextRefresh`
  would treat it as neither build nor research, which is what the info line
  wants.
