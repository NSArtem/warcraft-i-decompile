# Game logic: pathfinding and the unit array (0x2c4e0..0x2efd0)

Two adjacent game objects hold the pathfinder and the unit model.  They are
`mod_2c4e0` (0x2c4e0..0x2ced0, 11 functions) and `mod_2ced0`
(0x2ced0..0x2efd0, 31 functions) in `analysis/modules.toml`; both are "OPT"
code (`-s -ot -ol -4r -zp2`).  Their behaviour matches `PATH.C` and `UNIT.C` of
the Insider's Guide module list [R1] (the guide names exist, this assignment
comes from the code), so the notes below use path/unit terminology while the
module names in the database stay as they are.

Symbols: `analysis/symbols/game_2c4e0.toml`; reconstructed C:
`src/game_2c4e0/`, declarations `src/include/game_2c4e0.h`.

## Unit record

The unit array is 200 records of 0x5c bytes at 0x59640 (`[0x59640]` is the
base pointer; every loop loads it and adds `n * 0x5c`).  Fields established by
the code in this area (offsets are evidence, names descriptive):

| off | type | use |
|---|---|---|
| 0x00 | short x, y | pixel position (tile*16); `+0x1 & 3` is the animation phase in `UnitDrawSprite` |
| 0x04 | word | animation script offset; byte +0x6 timer, +0x7 frame |
| 0x08 | byte | facing/direction (written from the path step in 0x2c538) |
| 0x09 | byte | zeroed when an order starts (0x2e11f) |
| 0x0a/0x0c | short x, y | tile position (0x2c4e0 adds the direction offsets to it) |
| 0x0e | word | secondary flags (bit 0x3 = visibility state in 0x2d66d) |
| 0x10 | word | main flags: 0x207 = "not a normal map unit" for the draw order, 0x205 = kept out of the draw list, 0x80 = dying/dead, 0x400/0x200 death handling, 0x8 = counts as a target |
| 0x11 | byte | high half of the flags; order setters clear bit 7 (`&= 0x7f`), 0x2e115 sets bit 6 |
| 0x16 | word | hit points (0x2d258 compares against the type's max) |
| 0x1a | byte | damage/health fraction (0->0x55->0xaa thresholds pick the frame; set to 0xff at death) |
| 0x1b | byte | unit type (0x00..0x33; >= 0x20 are buildings, 0x20..0x32 counted specially) |
| 0x1c | byte | type copy made at death (0x2d118) |
| 0x1d | byte | sprite set / graphic group |
| 0x1e | byte | owner/player (4 = neutral; tables 0x5008c, 0x5189c, 0x50d98 indexed by it) |
| 0x1f | byte | current order (0xc = special, checked by the order setters) |
| 0x20/0x21 | byte | next order / next order argument (0x1f = none) |
| 0x22..0x35 | byte[20] | path: one direction (0..7) per step, 0xfe = end marker |
| 0x36/0x38 | word | timers |
| 0x4c | byte (word in some states) | path index, compared with 20; a countdown in 0x2d204 |
| 0x4e/0x50 | short x, y | destination tile (or a 32-bit value in the death code) |
| 0x52 | dword | target unit pointer (0x2e126); reused as a pair of words by the death code 0x2d0e0 |
| 0x58 | dword | damage sprite pointer (0x2d262/0x2d280) |

Direction tables: `0x50f80` and `0x50f88` are signed bytes giving the tile
delta for directions 0..7 (`out.x = u->tx + d50f80[d]`, `out.y = u->ty +
d50f88[d]`, 0x2c50b-0x2c52a); `0x2d5c8` and `0x2c790`/`0x2cb2c` use the same
encoding.

## Path object (mod_2c4e0)

`0x2c4e0 PathPeekStep(Unit *u, Point *out)` is the primitive: if
`u->path_idx < 20` and `u->path[u->path_idx] != 0xfe`, it writes
`u->tile + delta(direction)` and returns 1, else 0.  It is used by the
movement code at 0x21f5e, 0x2c53e and 0x2cead and by the path builder itself.

The other functions were identified from their bodies:

* `0x2c538` peeks the next step, calls 0x13348(x, y, 0x3cc) (a tile walkability
  check) and, when free, stores the direction in `u->facing` and advances
  `u->path_idx` - the "take one step" routine.
* `0x2c57c` scans the ring of 8 directions around the current tile, starting
  from `[0x5a484]`, and walks up to 100 steps; it returns the first step that
  leads to the target while respecting the blocked-bit mask `[0x5a480]`,
  writing the found tile to its Point argument.  It consults the object array
  `[0x58580]` and 0x21e58 (a tile-content test).
* `0x2c790` walks the map cost array `[0x58588]` (which is indexed
  `y*64 + x`, word per tile) towards the target, using the 8x8 turn/cost table
  at 0x55224 (index `direction*8 + direction`) and stamping the direction into
  the array; it returns the number of steps.
* `0x2c8c0` copies a direction sequence (the path found by 0x2c790) into
  `u->path`, beginning at `u->path_idx`, and pads with 0xfe up to 20 entries.
* `0x2c958` is the main path builder: snapshots the start/destination
  (`[0x5a478]`, `[0x5a47c]`) with 0x1df0c, marks the start tile in the map,
  then loops calling 0x1df94 (next direction) and storing `dir | dir<<8` in
  the map until the destination or a 20-step budget is reached; it records
  the special direction byte `[0x5a484]`.
* `0x2cb2c` marks a rectangle around a unit (size from the type table at
  0x51abc/0x51abe, +2 cells) or a 3x3 block at the destination as blocked in
  `[0x5857c]` (bits 0x80/0x40).
* `0x2cc04` is the Chebyshev distance `max(|dx|,|dy|)` between two Points;
  `0x2cc2c` returns `distance > [0x5a482] + 8`.
* `0x2cc54` is the orchestration used by the command code at 0x2234a: if the
  unit already has a path step it returns 1; otherwise it sets up the
  start/destination, blocked mask, target, object-size table
  `[0x5a474] = 0x51883 + owner*5`, tries the ring scan and the cost-map walk,
  stores the better path, and marks the destination area.
* `0x2cebc UnitResetPath` writes 20 to `u->path_idx`, i.e. empties the path.

## Unit object (mod_2ced0)

Draw order:

* `0x2ced0 DrawListSort` - bubble sort of the null-terminated `Unit*` array at
  0x5a490 by key `(flags & 0x207) ? 0 : ty`; used after units move.
* `0x2cfa8 DrawListRemove`, `0x2cfd8 DrawListInsert` - remove an entry /
  insert at the first key >= the unit's key.
* `0x2d058 DrawListRebuild` - walk all 200 units, insert those with
  `(flags & 0x205) == 0`, and call 0x13c04 for those with
  `(flags & 0x207) == 0`; 0x13c04 updates the per-owner/type counters and
  runs the per-type callback table at 0x51408.  Called by the map/game init
  0x2d4b8 after it memsets the 201-entry list.

Per-tick update (the tick function 0x2ec0c calls UnitUpdateAll at 0x2ed94,
then 0x2d2e0 at 0x2ed99 and DrawListSort at 0x2ed9e; 0x2edac is the next
function, and the order code calls into the same helpers):

* `0x2d204 UnitUpdateAll` walks the array; for units with `(flags & 0x207)==0`
  and type >= 0x20 it selects the damage sprite by HP against the type's
  maximum (0x51978 table) and stores it in `+0x58`; it runs the death/decay
  timer at `+0x4c` and calls 0x2d0e0 then 0x2d0ac.
* `0x2d0e0` starts the death sequence: sets `path_idx=10`, advances the word
  at +0x52, derives the `+0x1a` fraction from `255 * [0x52] / [0x50]`, sets
  type copy/frame, plays sound 0x26360(u, 2), sets flags 0x80, updates counts
  (0x13c04), decrements the owner's unit counter at 0x50d98, notifies units
  targeting the dying unit (0x1cf94, 0x2e5c8), and then spreads the death to
  the units it was attacking.
* `0x2d0ac UnitUpdateDamageFrame` picks frame 0/1/2 from `+0x1a`
  (<0x55 / <0xaa / else) for non-dead units.
* `0x2d2e0` is the AI/random tick: calls 0x19478 with ids 5..8, adjusts the
  per-player movement counters at 0x55284/0x55285 by -1..+1 and clamps them
  to -2..2.
* `0x2d4b8` is the map/game init for this object: clears draw_list (0x324
  bytes), initializes the unit templates at 0x59640/0x59644, builds the
  0x51abc -> 0x59530 scaled object table, and calls DrawListRebuild.
* `0x2d5c8` tests a rectangle of the fog map `[_fog_map]` (2 bytes per tile)
  against two masks; `0x2d650` uses it to maintain the visibility bits 0x1/0x2
  of `+0x0e` for every unit.
* `0x2d704 UnitDrawSprite` (named in `graphics.toml`) draws one unit;
  `0x2d8c8` is the viewport callback that draws all units/objects.
* Orders: `0x2ee50 UnitSetOrder` sets `+0x1f`, clears the next-order bytes to
  0x1f, drops the target for non-building orders and plays the order sound
  (0x26360); `0x2eeac UnitSetNextOrder` / `0x2eed4 UnitSetNextOrders` only
  set the next-order bytes; `0x2e100` sets an order target from a Point or a
  target unit and invokes the callback passed as 5th argument (39 callers,
  the command handlers); `0x2e96c` is the target-less order handler 0 in the
  table at 0x5158c (index 0: 0x13f60).
* `0x2e9f4` indexes the order property table 0x55264 by `+0x1f`; when the
  "has target" bit is set it returns the owner-relation byte
  `0x51883[owner*5 + target->owner]` (0x2ea1a-0x2ea43).

## Open questions

* The unit record beyond +0x54 (0x54/0x58) is only partly used here; 0x58 is
  a sprite pointer, 0x54 is still unnamed.
* 0x2d0e0 reuses the target pointer word (+0x52) as a counter - a source-level
  union is likely but the exact member layout is unknown.
* 0x50f80/0x50f88 direction tables and the map arrays 0x5857c/0x58588 are not
  in the symbol database yet; they are referenced through raw addresses here.
* Module names: the code supports PATH.C (0x2c4e0) and UNIT.C (0x2ced0), but
  the ranges are still `mod_2c4e0`/`mod_2ced0` in `analysis/modules.toml`.

## Verification status

Reconstructed C that matches (T3, built from `src/`):

| function | file | check |
|---|---|---|
| 0x2cfa8 DrawListRemove | `src/game_2c4e0/draw_list_remove.c` | `python3 -m wc1.match ...` MATCH |
| 0x2cebc UnitResetPath | `src/game_2c4e0/unit_reset_path.c` | MATCH |
| 0x2d0ac UnitUpdateDamageFrame | `src/game_2c4e0/unit_damage_frame.c` | MATCH |
| 0x2eed4 UnitSetNextOrders | `src/game_2c4e0/unit_orders.c` | MATCH |

`make build` links these four in place; the hybrid executable stays
`IDENTICAL` to the original (loaded image, entry, stack, all fixups).

Source idioms needed for the matches (all in the codegen-flags header style):

* the flags word is held in an **unsigned 32-bit local** masked with the flag
  bits (`unsigned f = u->flags.w & 0x80;`); this makes OW2 emit the original's
  `mov dx,[u+0x10]; xor dh,dh; and dl,0x80; and edx,0xffff` instead of
  `test byte [u+0x10],0x80`;
* the order setters **reuse the same local** for the order byte
  (`f = u->order; if (f != 0xc)`), which keeps one register and reproduces the
  original's `and ecx,0xffff; jne; mov cl,[u+0x1f]; cmp ecx,0xc`.

Reference C for the near misses (not built; the control flow matches, the
compiled bytes do not):

* `src/game_2c4e0/draw_list_reference.c` - DrawListSort 0x2ced0,
  DrawListInsert 0x2cfd8. The sort and the insert follow the original
  (same guards, same key rule, same swap and shift loops). The original
  loads the tile as `mov eax,[u+0xa]; sar eax,0x10` and compares 16-bit
  keys; this C reads `ty` as a short, so OW2 emits a different load and
  the function is not T3.
* `src/game_2c4e0/unit_orders_reference.c` - UnitSetNextOrder 0x2eeac (same
  length as the original; OW2 keeps the order byte in dh where the original
  uses bl);
* `src/game_2c4e0/path_reference.c` - PathPeekStep 0x2c4e0, three spellings;
  the original's `mov dl,path[..]; xor ebx,ebx; mov bl,dl` key extraction is
  not reproduced by the OW2 spellings tried so far.

This is the same V1/V2 backend difference documented in
`docs/subsystems/codegen.md` (OW2 is a 11.x descendant; war.exe was built with
Watcom 9.5/10.x), so these functions stay T4 material until either a source
idiom is found or an old compiler is available.
