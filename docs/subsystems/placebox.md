# PLACEBOX.C (0x21df0..0x22c50) — placement box / "Select location"

Flow: a worker starts a build (`PlaceBoxStart` 0x22798), each frame `PlaceBoxUpdate` (0x2261c) draws a coloured box on layer 21 (layers[21] at 0x5ac0a) over the tile under the mouse, a click calls `PlaceBoxConfirm`, and a right click calls `PlaceBoxCancel`. The module also holds order-movement helpers (OrderUpdateMove and related).

## Functions
| Addr | Name | Status |
|---|---|---|
| 0x21e58 | UnitIsPassable | T3 matched |
| 0x222e8 | OrderUpdateMove | T3 matched |
| 0x22464 | UnitOrderTargetFinish | T4 ref (regalloc: u in ebx, order byte in edx) |
| 0x224e0 | PlaceBoxInit | T4 ref (original calls Watcom intrinsic `__STOSB` 0x34390 vs `memset` 0x30c50) |
| 0x22538 | PlaceBoxActive | T3 matched |
| 0x2254c | PlaceBoxShutdown | T3 matched |
| 0x22930 | PlaceBoxCancel | T3 matched |
| 0x229c8 | PlaceBoxCreateBuilding(worker, Point) | T4 ref (xor ecx,ecx vs xor ebx,ebx) |
| 0x22a4c | PlaceBoxRoad(Point) | T4 ref (packed Point split with sar 16) |
| 0x22a98 | PlaceBoxWall(worker, Point) | T4 ref (sar edx,0x10 and `mov eax,[esp-2]; sar eax,0x10`) |
| 0x22ae4 | PlaceBoxConfirm(Point) | T4 ref (regalloc, `xor edx,edx` vs `and edx,0xff`) |

## Data
- 0x5a11a `net_event_pending`: the player index, 0 for the local player. The UI message and the cursor updates run only when it is 0.
- 0x59bd0 `place_type[2]`: unit type per player. 0x34 is road, 0x35 is wall, and types up to 0x32 are buildings.
- 0x59bd2 `place_active[2]`: 1 while placing.
- 0x52b24 `place_box_bm`: 48x48 scratch bitmap. Its pixel buffer is a 0x900-byte GdsAlloc.
- 0x52bc4 `place_error[]`: messages indexed by the PlaceBoxCheck result.
- 0x534f4 `order_props[]`: bit 1 is tested in UnitOrderTargetFinish.
- 0x51dca `owner_block_mask[]`: per-player word passed to TerrainRoadCell.
- 0x5857c `map_flags`: 64x64 words. The unit's tile is at +8/+10 as sar-16 words. Bit 0 of the high byte is toggled around confirm for unit types 2 and 3.
- A Point is passed packed in one register, x in the low word and y in the high word.

## Notes
- T3: the five matched files are checked with `assert_t3_matches`.
- T4: each reference function has a difftest in `tests/test_placebox.py`, which runs it against the original with stubbed callees. The call arities are taken from the register-argument convention. `assert_ref_mismatch` guards that the reference files still fail to match.
- The reference headers disagree with the DB prototypes. The Create, Road, Wall and Confirm references take (worker, Point) or Point rather than `unsigned char`, so the tests follow the reference C and the register layout.
