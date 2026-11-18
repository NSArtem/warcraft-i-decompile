# GAMEDLG.C — the game's modal dialog boxes (0x1a3c0..0x1af20)

Evidence for every name and claim: `analysis/symbols/gamedlg.toml`; the two
helpers outside the range (0x19b80, 0x1a328) are named there too, with their
own code as evidence (they belong to `mod_19b80` and should move when that area
is done).  The generic dialog *runtime* (0x16390..0x19020, `mod_16390`) is
documented by its own area; this page only uses its entry point.

## 1. What a "dialog" is here

Every box in this module is a **page resource** from `DATA.WAR` run by
`DialogRun` (0x180a8, named in `analysis/symbols/mod_16390.toml`):

    unsigned short DialogRun(unsigned int id, short x, short y,
                             unsigned short layer, void **params);

* `id` selects the page (0xff..0x1dc; see the table in section 2).  The page
  carries the frame, the caption(s), the buttons with their **action numbers**
  and the layout; `layer` is the page's text layer (the number of text lines
  the page draws, `0xa` for every message box in this module, `8` for the
  network timeout box).
* `params` is an array of pointers the page substitutes into its widgets: a
  message box passes `&text`, so widget parameter 0 renders the caller's
  string.
* The return value is the **action number** of the button the player pressed
  (0 = the first button).  The box is modal: it saves and replaces the event
  handler block, pumps events until a button is pressed and restores the
  handlers.

`DialogRun` does *not* touch the game's screen state.  This module wraps it:

* `ModalScreen(on, dim)` (0x1a560) brackets a dialog:
  * on the first entry (`dialog_depth` 0 -> 1) it allocates a full-screen
    320x200 copy of the current image (`GdsAlloc(0xfa00)`), installs it as
    **layer 23** (`layers[23]`, 0x5ac2e) with `BitmapBlit` as its draw
    callback, saves the `active` words of layers 13..22 and hides them (that
    is the in-game UI: the status panel is layer 0x13), and - when its second
    argument `dim` is non-zero - tints the screen dark red first
    (`DimScreenImage`);
  * leaving the last nested dialog frees the buffer, restores the layer flags
    and the palette, redraws the whole screen, invalidates the game-speed
    cache and reinstalls the game screen's input handlers
    (`GameScreenInputInit` 0x1a328);
  * nested dialogs only move `dialog_depth`; while `dialog_enabled`
    (0x517cc) is 0 the function returns immediately (the game screen is not
    up yet - `fn_19998` sets the flag at 0x1aae).
* Dialogs that show a *message* pass a text pointer and a page id; the
  per-race id offset selects the human (`scenario_race` 0) or the orc (1)
  variant of the page: every page has both, so `ShowMessageRace(text, id)`
  runs page `id + scenario_race`.

The "dark red wait screen" (`BuildDimPalette` 0x1a3c0 + `DimScreenImage`
0x1a4b8) is a perceptual luminance reduction, not a palette mask: each pixel's
colour is mapped to a brightness (`77*R + 151*G + 28*B >> 8`, the 0.30/0.59/
0.11 weights) masked to 6 bits, `palette_target` becomes a red ramp
`{b,0,0}`, the 64-entry index map is filled with the nearest palette entry for
every brightness and the whole 0xfa00-byte back buffer is remapped in place.
The palette's upper half is restored afterwards (`PaletteSet(0x80,0x80,pal)`),
so only colours 0..0x7f stay red - the colours the remapped image uses.

## 2. The page table

Captions as they appear in the page resource (DATA.WAR id = the number below);
`@1`/`@2` mark the highlighted hotkey letter.  Read with
`python3 -m wc1.resources_war` (see `docs/subsystems/resources.md`).

| Page | Caption / content | Used by |
|---|---|---|
| 0xff | 130-byte page, no caption text; its parameter list names the image resources 0x100 (320x200 picture), 0x102 and 0x103 (17x17 tiles) | HelpScreen 0x1ade4 (palette resource 0x101) |
| 0x170 | "Remote system is not responding!" + `R`etry / `Q`uit | NetTimeoutDialog 0x1a9a4 (game_mode != 3) |
| 0x171 | the same + `S`ave | NetTimeoutDialog (game_mode == 3) |
| 0x172 / 0x173 | "Warcraft": `S`ave Game / `L`oad Game / `O`ptions / `R`estart scenario / `Q`uit / `C`ontinue (actions 0..5) | GameMenuDialog 0x1ae70 |
| 0x174 / 0x175 | "Load Game" + 7 slot lines + `C`ancel | GameLoadDialog 0x1accc |
| 0x176 | `O`k / `C`ancel (the generic message box) | ShowMessage 0x1a894, ShowMessageRace 0x1a720, SaveErrorDialog 0x1aca8, DefeatDialog, GameSaveDialog/VictoryDialog (error text) |
| 0x178 / 0x179 | `O`k / `C`ancel (185-byte page) | GameMenuDialog's "restart?" question (text from the caller) |
| 0x17a / 0x17b | "Options": `G`ame Speed, `M`usic Vol, `S`FX Vol, Mo`u`se Scroll, `K`ey Scroll, `O`k, `C`ancel + the 7 speed labels (Slowest..Fastest) and the volume numbers | OptionsDialog 0x1a800 |
| 0x187 / 0x188 | "Save Game" + 7 slot lines + `1`..`7`, `C`ancel | GameSaveDialog 0x1abc0, VictoryDialog 0x1aa7c |
| 0x189 / 0x18a | "Quit to DOS or Main Menu?" + `D`OS / `C`ancel / `M`enu (actions 0/1/2) | QuitDialog 0x1ab50 |
| 0x1d4 / 0x1d5 | "You are victorious!" + `S`ave / `C`ontinue | VictoryDialog 0x1aa7c |

Pages passed with the `+ scenario_race` offset: 0x172, 0x174, 0x178, 0x17a,
0x187, 0x189, 0x1d4 (each has its human/orc pair, checked in DATA.WAR:
0x172/0x173, 0x174/0x175, 0x178/0x179, 0x17a/0x17b, 0x187/0x188,
0x189/0x18a, 0x1d4/0x1d5).  Pages passed without it: 0x176 (ShowMessage/ShowMessageRace's
caller-provided id), 0xff and 0x170/0x171 (the network boxes are not per-race).

## 3. State

| Address | Name | Meaning |
|---|---|---|
| 0x517cc | `dialog_enabled` | 0 = no modal screens yet (set when the game screen is ready, 0x1aae) |
| 0x51e24 | `dialog_active` | set by ModalScreen; six menu commands are ignored while it is set |
| 0x59620 | `dialog_bitmap` | the modal layer's bitmap header `{0x140, 0xc8, data}` |
| 0x59624 | `dialog_buffer` | = `dialog_bitmap.data`: the `GdsAlloc(0xfa00)` copy of the image |
| 0x59628 | `dialog_layer_state[10]` | saved `active` words of layers 13..22 |
| 0x5963c | `dialog_depth` | nesting counter |
| 0x594f0 | `game_speed_cache` | the game tick's cached speed; -1 forces a recompute (set when the game starts and when the last dialog closes) |
| 0x5aa90 + 23*18 | `layers[23]` | the modal screen layer (data = `&dialog_bitmap`, draw = `BitmapBlit`) |
| 0x532b4 | `prefs_block` | `{game speed 0..6, music vol, sfx vol, mouse scroll, key scroll}` (PREFS.WAR; `LoadPrefs` 0x1d574 clamps it) |

The Options page edits a *copy* of `prefs_block` plus three extra words
(`OptionsParams`): +0x14 `OptionsRefresh` 0x1a79c, +0x18 `OptionsApplyTimer`
0x1a778 and +0x1c the next apply tick.  The page's callback widgets call the
first two (the dialog runtime's `[params+0x14]`/`[params+0x18]` hooks), which
is how a dragged volume slider is applied every 25 ticks while the box is
open.

## 4. The functions

`T3` = byte-identical C under Watcom 10.0a (`python3 -m wc1.match`), `T4` =
reference C verified against the original under `wc1.cemu`.

| Address | Name | Status | Notes |
|---|---|---|---|
| 0x1a3c0 | BuildDimPalette | T3 | the 64-entry red luminance map (section 1); `memset(map,0xff,0x40)` then one pass over the 256 colours, then a fixpoint that fills the map's holes from the neighbouring entries |
| 0x1a4b8 | DimScreenImage | T4 | remap the back buffer, mark the whole screen dirty, present, restore the palette's upper half; T3 blocked by the loop's register allocation (`regalloc`) |
| 0x1a560 | ModalScreen | T4 | the modal screen bracket (section 1); T3 blocked by `regalloc` |
| 0x1a714 | ModalDepthReset | T3 | `dialog_depth = 0`, called once from the game start-up (0x1976c) |
| 0x1a720 | ShowMessageRace | T3 | `DialogRun(id + scenario_race, 0x11, 0x46, 0xa, &text)`, returns "dismissed" |
| 0x1a778 | OptionsApplyTimer | T3 | the Options page's timer: `if (clock() > p->next_apply) { SndApplyOptions(p); p->next_apply = t + 0x19; }`, returns 0 |
| 0x1a79c | OptionsRefresh | T3 | in a linked game copy `opt_music_volume`/`opt_sfx_volume`/`opt_mouse_scroll`/`opt_key_scroll` into the block; force 0 where the MIDI/DIG driver is 0xffff |
| 0x1a800 | OptionsDialog | T4 | page 0x17a+race at (0x54,0x14); Ok copies the block back and `SndApplyOptions` runs unconditionally; T3 blocked by `codegen` (20-byte copy) |
| 0x1a894 | ShowMessage | T3 | page `width` (0x176) at (0x11,0x46) for `height` lines, caller's text; returns "dismissed" |
| 0x1a8e4 | VersionMismatchDialog | T3 | "Warcraft version numbers are different." (0x51e26) during the link handshake (0x24007); no modal screen yet |
| 0x1a914 | SaveVersionDialog | T3 | "Saved game uses old version number!" (0x51e4e) when the save stream's version word is not 0x43 (0x241d2) |
| 0x1a95c | TwoPlayerComputerDialog | T3 | "Cannot play a two player game\nagainst the computer." (0x51e72) when the save is flagged as a computer two-player game (0x241f4) |
| 0x1a9a4 | NetTimeoutDialog | T4 | page 0x170 (+1 while game_mode 3): Retry restores `screen_mode`/`net_play_flag`/`layers[0].active`, Quit does `NetLinkExit` + `setup_quit` + game_mode 4, Save runs GameSaveDialog first; called by the reply timeout of the network wait loop 0x131ba |
| 0x1aa7c | VictoryDialog | T3 | game_mode 6; the "You are victorious!" box; Save -> `SaveSlotCreate(0xa, 0x187+race)` + `SaveWriteImage`, an error repeats the box; linked games return at once.  Installed as the mission-end action (0x5a860) by fn_2f540 |
| 0x1ab28 | DefeatDialog | T3 | game_mode 7; "You failed to achieve victory..." (0x56c0c) in a single-player game (fn_2f540's defeat path) |
| 0x1ab50 | QuitDialog | T3 | page 0x189+race: action 0 -> game_mode 2 (exit), 2 -> game_mode 4 (main menu), 1 = cancel; returns "leaving" |
| 0x1abc0 | GameSaveDialog | T3 | page 0x187+race; a linked game runs the list once per side (`screen_mode` flip), then `SaveWriteImage`; a NULL handle shows "Error saving game!" (0x56bf8) |
| 0x1aca8 | SaveErrorDialog | T4 | "Disk Error!  Unable to save game!" (0x51ea6) or "Remote system failed to save game!" (0x51ec8) by `net_event_pending`; T3 blocked by `codegen` (CONST pool spacing) |
| 0x1accc | GameLoadDialog | T4 | page 0x174+race; a stream in `slot_file` sets game_mode 5 (the main loop's "start the loaded game"); linked games run it per side |
| 0x1ade4 | HelpScreen | T3 | the full-screen info page: clear 0xa0000, palette resource 0x101, page 0xff; reached by F1 / Ctrl+H (game command 9) |
| 0x1ae70 | GameMenuDialog | T4 | the in-game menu loop over page 0x172+race: Save/Load/Options/Restart/Quit/Continue, exits when an action reports done, stores the load result in `load_not_cancelled` (0x516b0) |

Non-function data in the range: the six-entry switch table at 0x1ae58
(GameMenuDialog's cases).

## 5. Behaviour notes and oddities

* `ModalScreen`'s second argument is the *red tint switch*, not an unused
  parameter: the callee (`NetPumpEvents` 0x19b80) preserves `edx`, so the
  original compares the still-live argument (`test dx,dx` at 0x1a5a5).  All
  callers in this module pass 1 except `HelpScreen`, which passes 0 (its page
  has its own palette).
* `NetTimeoutDialog` saves and restores `layers[0].active` (0x5aa90) although
  nothing in between touches layer 0; it is kept as recorded because the
  reference C must reproduce it.
* The victory box's Save button loops: a cancelled slot list or a failed
  create (with the error message) returns to the same box until the player
  continues or the file is written.
* `GameSaveDialog`'s "keep the second handle" branch (`if (screen_mode)`)
  reads `screen_mode` *after* the second slot list, i.e. it keeps the handle
  of the side it flipped to; the loader does the same with `slot_file`.

## 6. Verification

* `python3 -m wc1.match src/gamedlg/<file>.c` for the 14 T3 files (Watcom
  10.0a, `-s -ot -ol -4r -zp2`; `net_timeout_dialog` is the one DBG function
  of the module, `-d1+`).
* `tests/test_gamedlg.py`: the T3 re-checks, the seven T4 difftests (stubbed
  callees, watched globals), the 21-starts check, the page-caption table read
  from DATA.WAR and the module's string pool.

## 7. Open questions

* The help page's *content* is not provable from the binary: page 0xff has no
  caption strings and its picture (resource 0x100) is a rendered page.  The
  name follows the F1 / Ctrl+H command; a screenshot from T5 would settle it.
* Why `ModalScreen` restores only the palette's upper half
  (`PaletteSet(0x80,0x80,palette)`) is unexplained by the code; the remapped
  image only uses colours 0..0x7f, so the effect is that the tint stays.
* `0x532c0`/`0x532c4` are named `opt_mouse_scroll`/`opt_key_scroll` from the
  Options page's row order and `LoadPrefs`' clamp sites (medium confidence);
  the sound area owns `opt_music_volume`/`opt_sfx_volume` and may want them.
* `NetPumpEvents` (0x19b80) and `GameScreenInputInit` (0x1a328) are named in
  this area's TOML only because no area owns 0x19b80..0x1a3c0 yet; move them
  when it is analysed.
