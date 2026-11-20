# mod_2c4e0_c — pathfinding (0x2c4e0..0x2ced0)

Part of the game-logic range described by `src/include/game_2c4e0.h`. Compiled with `-s -ot -ol -4r -zp2` (10.0a).

## Functions

| Addr | Name | Status | Notes |
|---|---|---|---|
| 0x2c790 | PathCostWalk | reference | Walks the direction map from `path_start` to `to`, shortcutting via `dat_55224[d*8+d2]` until a fixpoint, and returns the step count. Blocker: original loads Point halves with `mov ecx,[esp]; sar ecx,0x10` (dword view), while we emit `movsx ecx, word [esp+2]`. |
| 0x2c8c0 | PathStoreSteps | reference | Copies up to 20 step directions from `map_cost[...*2+dir]` into `path`, then pads with 0xfe. Blocker: orig has an `xor edx,edx` at 0x2c8cd and dword-view loads. |
| 0x2c958 | PathTrace | reference | Traces the route given by fn_1df0c/fn_1df94 (line-stepper callees). Marks `map_flags` (0x2000 on the traced tiles, 0x8000 after the first block), writes `map_cost`, and stops after 20 steps. Blocker: frame is 0x24 vs 0x20 and the register allocation differs. |
| 0x2cb2c | PathBlockArea | reference | ORs 0xc000 into `map_flags` over the unit footprint plus a 1-tile border (3x3 around `path_dest` if the unit is null), then ANDs with `mask`. Blocker: stack slot assignment. |
| 0x2cc54 | PathFind | reference | Top-level pathfinder; builds `path_block_mask`, calls the helpers above and returns `PathPeekStep`. Blocker: `dat_5189c` and `dat_5a474` need resolvable `[[data]]` entries. Otherwise the code is 182/182 instructions. |
| 0x2c?? | PathAdvanceFacing, PathDistance, PathNeedsPath | matched (T3) | `path_advance_facing.c`, `path_distance.c`, `path_needs_path.c`. |

## Data layouts

- `map_flags`: u16 per tile, 64x64. Bit 0x100 means an object is present (`object_map[idx]`), 0x2000 marks the traced route, and 0x4000/0x8000 are the block marks set by PathBlockArea and PathTrace. `path_block_mask` is 0x3cc by default.
- `map_cost`: 2 bytes per tile (direction fields), indexed `(y*64+x)*2`. The byte at `+dir` selects the pass (0 or 1).
- `dir_dx` and `dir_dy` are signed byte tables of 8 entries.
- `path_start`, `path_dest`: `Point`. `dat_5a47e` is the y of `path_dest` (+2).
- Unit fields used: tx/ty +0x0a, type +0x1b, owner +0x1e, order_next2 +0x21, path[20] +0x22 (0xfe terminator), timer36 +0x36, path_idx +0x4c, dest +0x4e, target +0x52.

## Tests

- T3: `path_advance_facing.c`, `path_distance.c` and `path_needs_path.c` must still match.
- Near-miss guard: the five `*_reference.c` files must still NOT match.
- T4 (`tests/test_mod_2c4e0_c.py`): each reference function is run differentially against the original. Buffers are allocated inside `init_emu`. Case args are computed in the case `setup`, after the allocation. The callees fn_1df0c and fn_1df94 (PathTrace), and the Path* helpers (PathFind), are stubbed. Stack-pointer arguments are never logged.
