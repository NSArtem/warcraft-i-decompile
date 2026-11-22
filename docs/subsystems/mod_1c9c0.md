# `mod_1c9c0`: unit graphics indices and session sprite resources

`GameInitSession` calls the graphics loader; `GameShutdownSession` calls the corresponding teardown. Unit creation and death paths also call the unit graphics-index updater.

| Address | Function | Disassembly evidence and confidence |
| --- | --- | --- |
| `0x1c9c0` | `UnitUpdateGraphicsIndex` | **High.** Reads the type at `Unit+0x1b` at `0x1c9c4`; `0x1c9d1–0x1ca0d` selects alternate indices for types 2 and 3 using bits `0x20` and `0x80` at `Unit+0x49`. Other types use the map unless bit `0x80` at `Unit+0x10` is set (`0x1ca0f–0x1ca28`). The result byte at `Unit+0x1d` is doubled and then adjusted based on `Unit+0x1e` and the type (`0x1ca32–0x1ca7b`). |
| `0x1ca84` | `CloneSpriteResource` | **High.** Allocates the supplied size at `0x1ca92`, copies 12 prefix bytes even when the frame count is zero (`0x1caa0–0x1caa2`, `0x1cae6–0x1caf3`), and calls the pixel-copy helper with `width × height` and base-relative source/destination pointers (`0x1cac0–0x1cadb`). Returns the allocation at `0x1caf5`. |
| `0x1cb04` | `IsGraphicsResourceAllowedForScenario` | **Medium.** At `0x1cc32–0x1cc51`, the loader calls this predicate only for an applicable descriptor with bit `0x1000`, passing the low 12-bit resource ID. A zero return skips the entry without clearing either slot. The supplied call site does not establish the predicate's internal scenario rules. |
| `0x1cb90` | `LoadSessionGraphics` | **High.** Loads 12 common resources starting at ID `0x15d` (`0x1cb99–0x1cbca`). Walks 72 descriptors (`0x1ccba–0x1ccc9`), clears both slots for an inapplicable descriptor, and clones a shared resource for the enemy slot while keeping the original for the player slot (`0x1cc1d–0x1cc2d`, `0x1cc73–0x1ccb3`). |
| `0x1ccdc` | `FreeSessionGraphics` | **High.** Frees and clears the non-null entries in the 144 side slots first (`0x1cce6–0x1cd0e`), then does the same for the 12 common slots (`0x1cd14–0x1cd39`). |

## Data layouts

- **`unit_type_graphics_map` (`0x5180e`, high):** `0x1ca28` reads byte 0 of a two-byte row indexed by unit type. The second byte's meaning is not established here.
- **Sprite resource (high):** `0x1cab1` reads a 16-bit count at offset 0. Frame records start at offset 4 and stride 8 (`0x1caa7`, `0x1cae0`). Each record has two leading bytes of unknown meaning here, width and height bytes at `+2` and `+3`, and a 32-bit resource-relative pixel offset at `+4` (`0x1cac0–0x1cad9`).
- **`session_graphics_resource_table` (`0x52214`, high):** two 16-bit race masks followed by 72 16-bit descriptors starting at `0x52218`. The loader indexes the mask words with `scenario_race_enemy` (`0x5008a`) and `scenario_race` (`0x50088`), adding `0x2000` to the enemy mask by OR (`0x1cbce–0x1bf3`). Descriptors carry selection bits, the optional `0x1000` predicate flag, and a low 12-bit resource ID (`0x1cc1d–0x1cc60`).
- **`session_common_graphics` (`0x522a8`, high):** 12 dword pointers (`0x1cbb9–0x1cbca`). **`session_side_graphics` (`0x522d8`, high):** 72 interleaved enemy/player dword pairs, enemy first (`0x1cbfc`, `0x1cc91`, `0x1ccae`, `0x1ccbb`).

## T3 and T4

The T3 assertion covers `is_graphics_resource_allowed_for_scenario.c`. The near-miss guard requires all four `_reference.c` files to remain nonmatches. T4 compares the unit bytes, clone return and buffer contents, and loader/teardown pointer tables plus ordered callee arguments. The loader test stubs the predicate and clone to isolate loader behavior; the clone test exercises the real clone routine separately. These tests were not executed during generation.
