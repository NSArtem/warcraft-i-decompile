# PLAYFLIC.C: the FLIC movie player and the credits driver

Range 0x22c50..0x23d10 (46 functions, 0x10c0 bytes), the object that
`analysis/modules.toml` names PLAYFLIC.C (guide: "*DFL\* (FLIC) ↔ PLAYFLIC.C,
'flic overrun'*", docs/REFERENCES.md). Evidence is in
`analysis/symbols/playflic.toml`; the C is in `src/playflic/`.

Style: OPT (`-s -ot -ol -4r -zp2`), compiler Watcom 10.0a, like the rest of
the game code (26 of the 46 functions are byte-identical, section 7).

## 1. The object is dead code in v1.22h

Every absolute reference into the range comes from *inside* the range:

* a full scan of the LE fixups finds exactly 28 targets in 0x22c50..0x23d10,
  all of them the script opcode table at 0x52ea8 (data, section 3) plus
  0x52ee0 = op 0x0e → 0x22f48;
* the entry points 0x23ae0, 0x23c74, 0x23c94, 0x23cb4, 0x23cd4, 0x23cf4 and
  0x23668 are not referenced by any fixup, and their object offsets
  (0x13ae0, 0x13c74, 0x13c94, 0x13cb4, 0x13cd4, 0x13cf4, 0x13668) do not
  occur as dwords in the raw data object either;
* the only global the object exports is the animation slot 0x59eb4, which
  nothing outside the object reads or writes.

So the epilogue/finale movie player is linked but unreachable in this build
(an earlier build presumably called `IntroPlay` from the menu code). This is
why the area can be reconstructed without behavioural risk, and why
`FlicOverrun` (the "flic overrun" fatal error of the module record) is an
unreachable stub.

## 2. The FLIC decoder this object drives (module `flic_decode`)

The player does not decode anything itself; it calls the decoder object
0x19020..0x19470, which is analysed separately. The interface and the format
it reads (all from the decoder's own code, needed to read PLAYFLIC.C):

```
int FlicOpen(const char *name, void *chunkbuf, void *image, unsigned first, unsigned last)
void FlicClose(void)         // 0x193dc
short FlicRewind(void)       // 0x193fc: seek 0 + decode, second handle 0x59490
short FlicRestart(void)      // 0x19420: the same on handle 0x59494
short FlicNextFrame(void)    // 0x19450: decode the next frame if open
void FlicPaletteOff(void)    // 0x19444: clear the "upload the palette" flag 0x594ea
```

`FlicOpen` (0x1933c) stores its arguments and reads a 0x80-byte file header
into 0x59440 through the file wrapper 0x31a80 (FileRead).  The header fields
it validates:

| offset | size | field | check in 0x1933c |
|---|---|---|---|
| 0x00 | dword | size | — |
| 0x04 | word | magic | must be 0xaf12 (0x1939c) |
| 0x06 | word | frames | → 0x59446 `flic_frames` |
| 0x08 | word | width | → 0x59448 `flic_width` |
| 0x0a | word | height | → 0x5944a `flic_height` |
| 0x0c | word | depth | must be 8 (0x193b8) |
| 0x0e | word | flags | must be 3 (frame + full frame) (0x193ab) |
| 0x10 | dword | speed | — |
| 0x14 | word | next-frame | must be 0 (0x193c5) |

That is the standard Autodesk FLIC/FLI file header; the game rejects anything
else and leaves the open flag 0x517c8 clear.

Frames (0x192f0 = decode one frame): a 16-byte frame header is read into
0x594c0 — dword size, word magic 0xf1fa (checked at 0x1930d), word chunk
count (0x594c6, the loop bound at 0x1932f) — followed by that many chunks.
Each chunk (0x19174) starts with a **6-byte** header: dword size (`size
includes the header`, the data read is `size - 6`, 0x1907e) and word type at
+4 (0x594e8).  The types the decoder handles:

| type | decoder | behaviour |
|---|---|---|
| 4 | 0x19064 | palette packets `{skip, count, r,g,b}` (skip 0 = 256), values `>>2` into the 6-bit palette at 0x58f20, then `VgaSetPaletteRange` when 0x594ea is set — COLOR_256 |
| 7 | 0x1921e | one plane of `width` bytes to `dest` (0x10312) |
| 12 | 0x191f1 | full copy of the chunk data to `dest` (0x102a4) |
| 15 | 0x19254 | the same with (width, height) and a scaling helper (0x1025c) |
| 16 | 0x19293 | uncompressed frame: `height` rows of `width` bytes, dest stride 0x140 |
| 18 | 0x192cf | postage-stamp chunk: skip 6, then a full frame |

`FlicOpen(name, chunkbuf, image, 1, 0xef)` (the only call in the image) means:
chunk data goes to `frame_chunk`, the decoded 320x200 image to `frame_image`,
and palette entries 1..0xef are loaded from the movie (entry 0 is the
transparent key, never touched).

## 3. The script format (this object)

`IntroRunScript` (0x23668) runs a stream of **little-endian words**:

```
opcode (word, 0x00..0x1b, index into script_ops at 0x52ea8)
arguments (words, as many as the op takes)
```

The dispatch (0x2371f) reads the opcode as a **byte** (`mov dl,[ecx]`, i.e.
the low byte of the word; the high byte is always 0), passes `ecx+2` (the
first argument) to the handler and continues at the handler's return value;
a return of 0 ends the script, as does the abort flag 0x59efa.  After every
op `IntroTick` (0x22c50) runs, which pumps one input event (0x184cc
dispatches it through the handler table 0x51770, where `IntroCheckSkip`
arrives) and then the installed credits tick.

The 28 ops (handler, arguments, effect):

| op | handler | args | effect |
|---|---|---|---|
| 0x00 | 0x22ff4 IntroOpPlayFlic | word movie | select `flic_sel` and open it |
| 0x01 | 0x2300c IntroOpEndFlic | — | close the movie |
| 0x02 | 0x23024 IntroOpQuit | — | `abort_request = 1`, end the script |
| 0x03 | 0x23030 IntroOpFirstFrame | — | rewind, `frame = 1`, show it |
| 0x04 | 0x23054 IntroOpClearScreen | — | `memset(0xa0000, 0, 0xfa00)` |
| 0x05 | 0x23070 IntroOpPlayFrames | word n | play n frames, looping the movie |
| 0x06 | 0x230e8 IntroOpPlayToEnd | — | play to the last frame, fading out over `fade_frames` |
| 0x07 | 0x2315c IntroOpPlaySound | word id | `SndPlay(id)` |
| 0x08 | 0x23170 IntroOpSyncSound | — | play frames while the sound is active |
| 0x09 | 0x231cc IntroOpWaitSound | — | tick while the sound is active |
| 0x0a | 0x231ec IntroOpWaitFrames | word n | tick n frames |
| 0x0b | 0x2322c IntroOpStopTick | — | `intro_tick = 0` |
| 0x0c | 0x23238 IntroOpSlideLayer | — | slide layer 13 up until its bottom edge is `scroll_target` |
| 0x0d | 0x232e8 IntroOpHold | — | stay on this op (returns itself) |
| 0x0e | 0x22f48 IntroBeginFlic | — | open `flic_sel` (the op used by `script_movie`) |
| 0x0f | 0x232ec IntroOpWaitAnim | word n | wait for n animation frames |
| 0x10 | 0x23330 IntroOpSetupFade | word n | prepare a fade over n frames |
| 0x11 | 0x23394 IntroOpWaitSoundB | — | as 0x09, abort tested after the tick |
| 0x12 | 0x233b4 IntroOpPaletteOff | — | stop the decoder's palette upload |
| 0x13 | 0x233c0 IntroOpBlankPalette | — | upload black except colour 0 |
| 0x14 | 0x23410 IntroOpFadeIn | word n | fade black → palette over n frames |
| 0x15 | 0x23458 IntroOpFadeOut | word n | fade palette → black over n frames |
| 0x16 | 0x234a0 IntroOpLoadPalette | word id | read palette resource `id` and set it |
| 0x17 | 0x234d8 IntroOpCreditArea | — | set up the three-line credit area |
| 0x18 | 0x23530 IntroOpStartCredits | — | load the next three credit lines |
| 0x19 | 0x235ec IntroOpScrollCredits | — | play frames while the credits are shown |
| 0x1a | 0x23650 IntroOpSecondPass | — | skip the next movie |
| 0x1b | 0x2365c IntroOpFreeSound | — | `SndReleaseAll()` |

The four scripts in the data object (dumped with `wc1.flic_dump`):

* `script_epilogue` (0x52c7a), used when a digital sound driver is present:
  clear screen, sound 0, movie 0, palette off + blank, first frame, fade in
  36, wait for the sound, sound 1, play to the end, close, movie 1, first
  frame, play for the sound, close, fade out 18, clear, movie 2, ...
* `script_no_dig` (0x52e02), the same without the sound ops, chosen when
  `cfg_dig_driver` (0x59902) is 0xffff (`IntroPlay` 0x23b5a);
* `script_level` (0x52e96) = `{0x0c, 0x02}`: slide the layer, end
  (`IntroPlayLevel`);
* `script_movie` (0x52e9a) = `{0x0e, 0x03, 0x10, 8, 0x06, 0x01, 0x02}`: open,
  first frame, fade over 8 frames, play to the end, close, end
  (`IntroPlayMovieA/B`, which set `flic_sel = index + 9` / `index + 0x15`).

## 4. State (the object's globals)

The player keeps its whole state in the data object; the interesting group is
0x59eb0..0x59efd:

| address | name | meaning |
|---|---|---|
| 0x59eb0 | `intro_dest` | blit destination: `0xa0000 + ((200 - height)/2)*320` |
| 0x59eb4 | `intro_tick` | installed credits tick (`CreditsTickA/B`) or 0 |
| 0x59eb8 | `credit_line[3]` | the three visible credit lines |
| 0x59ecc | `credit_line_x[3]` | their centred x |
| 0x59ec4/0x59ec8 | `frame_image`/`frame_chunk` | the two `GdsAlloc(0xfa00)` buffers |
| 0x59eea | `frame_size` | width*height to blit |
| 0x59ef4 | `line_height` | font rows + 2 |
| 0x59ede | `fade_frames` | fade length, 0xffff = none |
| 0x59ee0 | `scroll_target` | op 0x0c stop position |
| 0x59ee2 | `line_timer` | frames to the next credit scroll |
| 0x59ee4 | `credits_on` | the three-line display is active |
| 0x59ee6 | `abort_request` | op 0x02 asked for a clean end |
| 0x59ee8 | `line_index` | credit table cursor |
| 0x59eec | `sound_timer` | op 0x0c plays sound 0 after 20 ticks |
| 0x59eee | `skip_next_flic` | op 0x1a: open but do not show the next movie |
| 0x59ef0 | `frame` | current frame number (1-based) |
| 0x59ef2 | `line_count` | credit lines on screen |
| 0x59ef6 | `flic_sel` | index into `flic_files` |
| 0x59ef8 | `intro_tick_count` | frames played (the animation clock) |
| 0x59efa | `intro_abort` | leave the script |
| 0x59efc | `frame_ready` | one-frame handshake with the per-frame callback |

Other data: `flic_files` (0x52bdc, 32 name pointers 12 bytes apart, the
strings at 0x57304), `intro_bitmap` (0x52c64 = `{320, 200, frame_image}`, the
descriptor installed as `cur_bitmap` while a script runs), `intro_sounds`
(0x52c6c = 0x224, 0x225, 0x226, 0x227, 0x228, 0x1db, 0 for `SndLoadTable`),
`credit_lines` (0x52d18, 6-byte `{word delay; char *line}` records ending in
a 0xffff delay), `fade_delta` (0x59be0, the 720-byte per-entry fade step) and
the credits animation tables (section 5).

### The credit display

`IntroFrame` (0x22e84) is installed in slot 8 of the UI event table 0x59400
(the idle/frame event, type 0x400/sub 8) by `IntroRunScript`; it bumps
`frame_ready` and `intro_tick_count` once per main-loop frame and, in credit
mode, calls `IntroLoadCreditLines`.  `IntroShowFrame` draws the three lines
`credit_line[i]` with `DrawText` at
`(credit_line_x[i], i*line_height + flic_height + 2)` and then blits
`frame_size` bytes from `frame_image` to `intro_dest`.

The credit table is a scrolling list: each 6-byte record is a text line plus
the number of frames it stays before the next line is loaded; the loader
keeps three lines visible, moving them up one slot at a time, and an empty
line (or the 0xffff delay) ends the display (`credits_on = 0`).

The lines themselves (0x57494...) are the epilogue narration ("In the Age of
Chaos two factions battled for dominance.", "The kingdom of Azeroth was a
prosperous one.", ...).  Several of them are preceded in the string pool by
2-3 stray bytes ("ap", "map", "11.") that the table's pointers skip or
include inconsistently; they look like a compile-time artifact of the
original literal pool and do not affect the code (the strings are used
verbatim).

## 5. The credits animation (CreditsTickA/B)

`CreditsSetAnim(which)` installs `CreditsTickA` (0x237a0) for non-zero and
`CreditsTickB` (0x2393c) for 0 in `intro_tick`, and arms `sound_timer`.

Both ticks run once per intro frame and only when `intro_tick_count` changed.
They advance four independent GRP animations, drawn by four helpers of the
credits module (0x1c1dc/0x1c214/0x1c24c/0x1c284 = layers 14/15/16/17 with
sprite sets 0x59860/0x59858/0x5985c/0x59854):

| state | variant A | variant B |
|---|---|---|
| layer 14 frame | `credit_step_b`, ++, wrap 0x1f | `credit_step_b`, ++, wrap 0x15 |
| layer 15 frame | `credit_frames1[credit_frame_c]` every 2nd frame | the same index as layer 14 |
| layer 16 frame | `credit_frames2[credit_frame_d]` every 2nd frame | `credit_frames3[credit_frame_c]` every 2nd frame |
| layer 17 frame | — | `credit_frames4[credit_frame_d]` every 2nd frame |

The `credit_stepsN` tables (20 words each) are keyframes: every 10 frames the
frame counter is reloaded from them (`credit_frame_c % 10 == 0`), so each
sequence restarts at the next pose every 10 frames.

## 6. Per-function notes

Matching (section 7) is per function.  The 20 that are not byte-identical yet
are kept complete in `src/playflic/player_reference.c`; the first byte
difference (from `wc1.match`) is:

| function | first difference |
|---|---|
| IntroLoadCreditLines 0x22d40 | +0x5: the register save set/order differs (the 10.0a allocator picked 5 registers, mine 6) |
| IntroFadeStep 0x22eac | +0xf: Watcom inserts a one-byte loop-alignment nop that the original does not have; the body is identical |
| IntroFadeFrames 0x22eec | +0x9: 16-bit vs 32-bit loop bound |
| IntroBeginFlic 0x22f48 | +0x42 (0x22f8a): the early-return branch after FlicOpen lands 4 bytes further (the `*5` of `((200-h)/2)*320` is also `lea` here where the original has `shl`) |
| IntroOpPlayFrames 0x23070 | +0x4: register assignment (ebx vs ecx first) |
| IntroOpPlayToEnd 0x230e8 | +0x5: register assignment |
| IntroOpWaitSound 0x231cc | +0xc (0x231d8): the shared epilogue with the op-0x07 handler is targeted through a different displacement |
| IntroOpWaitFrames 0x231ec | +0x3: register assignment |
| IntroOpSlideLayer 0x23238 | +0x6: register assignment of the layer reads |
| IntroOpWaitAnim 0x232ec | +0x4 (0x232f0): register assignment; it shares op 0x05's epilogue |
| IntroOpSetupFade 0x23330 | +0x4: register save set |
| IntroOpFadeIn 0x23410 | +0x4: one extra `mov ecx,eax` in the original prologue |
| IntroOpFadeOut 0x23458 | +0x4 (0x2345c): the same |
| IntroOpCreditArea 0x234d8 | +0x13: the font's row byte is loaded through `al`/`ah` in the original, through `bl`/`bh` in mine |
| IntroOpStartCredits 0x23530 | +0x5: register assignment |
| IntroRunScript 0x23668 | +0x4 (0x2366c): the prologue moves `ecx,eax; esi,edx`, mine swaps them; everything else is identical |
| CreditsTickA 0x237a0 | +0x59: the frame counter arithmetic differs |
| CreditsTickB 0x2393c | as A |
| IntroPlay 0x23ae0 | see below |
| FlicOverrun 0x23cf4 | +0x3 (0x23cf7): the original has `int3` (a debug trap in the source) there, where the `FatalError` push is |

`IntroPlay` (0x23ae0) needs `layers[]` (0x5aa90, mod_16390's entry) and the
shared words 0x55208/0x55558; its first difference is at 0x23ae0 itself - the
original's prologue saves only `edx,edi`, 10.0a's form needs more registers
because of the way the layer stores and the `Bitmap` local are scheduled.

`FlicOverrun` is interesting as a negative result: the function is
`int3` followed by `FatalError("flic overrun")`, i.e. the original source had
an explicit trap.  Nothing calls it, so the string the module record uses as
evidence is dead text.

## 7. Verification status

26 functions are T3 (`python3 -m wc1.match src/playflic/*.c`), one file each
so the owner can add `src =` per function:

    IntroTick 0x22c50, IntroShowFrame 0x22c68, IntroShowFirstFrame 0x22cfc,
    IntroNextFrame 0x22d20, IntroCheckSkip 0x22e60, IntroFrame 0x22e84,
    IntroOpPlayFlic 0x22ff4, IntroOpEndFlic 0x2300c, IntroOpQuit 0x23024,
    IntroOpFirstFrame 0x23030, IntroOpClearScreen 0x23054,
    IntroOpPlaySound 0x2315c, IntroOpSyncSound 0x23170,
    IntroOpStopTick 0x2322c, IntroOpHold 0x232e8, IntroOpWaitSoundB 0x23394,
    IntroOpPaletteOff 0x233b4, IntroOpBlankPalette 0x233c0,
    IntroOpLoadPalette 0x234a0, IntroOpScrollCredits 0x235ec,
    IntroOpSecondPass 0x23650, IntroOpFreeSound 0x2365c,
    CreditsSetAnim 0x23c74, IntroPlayLevel 0x23c94, IntroPlayMovieA 0x23cb4,
    IntroPlayMovieB 0x23cd4.

The 20 functions in section 6 are reference C
(`src/playflic/player_reference.c`) with a `t3_blocker`; they are the player
core's decoder-facing half (the credit loader, the fade helpers,
`IntroBeginFlic`, the frame-play ops, the slide op, the interpreter and the
two credit ticks).  Two of them are T4 (`ref_verified_by`): `IntroOpSetupFade`
0x23330 and `IntroOpCreditArea` 0x234d8 - both are pure arithmetic on real
game memory (the palette, the font header, the intro globals) with no call
that needs a stub, so `wc1.cemu.run_pair` drives them directly over four
input variants each (`tests/test_playflic.py`).  Source idioms that did move the needle (all 10.0a):

* `DrawText` must be declared with `int` parameters, not the library's
  `short` ones: the original's call sites sign-extend (0x22cc0) and its
  unpublished PLAYFLIC.C declaration clearly promoted.
* `SndActiveCount` must be declared 16-bit (`test ax,ax` at 0x2317c).
* `VgaSetPaletteRange` is `__cdecl` (three pushes + `add esp,0xc`).
* the two word reads at 0x22c9f and 0x2323e are `dword[addr-2] >> 16`
  (Watcom 10.0a's word-read idiom) - `I16()` in `src/include/playflic.h`.
* `event_handlers[8]` is the frame callback slot (the idle event's sub code
  is 8), which is why `IntroFrame` is stored there.

## 8. Open questions

* Why the object is dead: the natural caller (`IntroPlay`) has no reference
  anywhere.  Either the CD build plays the epilogue elsewhere or the call was
  removed late.
* The 2-3 stray bytes before some credit lines in the string pool.
* `palette_faded` (0x55558) and `intro_music_started` (0x55208) are shared
  with other areas and only partly understood (low confidence).
* The credit animation tables' exact meaning (which GRP frames are keyframes)
  is documented only as "frame numbers of the corresponding GRP".
