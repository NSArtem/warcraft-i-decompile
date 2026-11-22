# Minimap terrain, overlays, and input coordinates (`mod_1eba0_f2`)

This slice covers painting the minimap terrain, gating and drawing its overlays, and converting screen coordinates for minimap input.

| Address | Function | Disassembly evidence |
| --- | --- | --- |
| `0x1ec6c` | `MinimapDrawTerrain` | Tests cheat bit 0 at `0x1ec74–0x1ec79`; uses fog mask `0x1f` and obscured color `0x60` at `0x1eca6–0x1ecba`; otherwise samples minitile pixels at `0x1ecbe–0x1ecef`. Both loop bounds are 64 (`0x1ecfa`, `0x1ed16`). |
| `0x1ed2c` | `MinimapRedraw` | Tests force in AX, decrements the countdown for unforced calls, and checks cached scroll at `0x1ed34–0x1ed6e`. Refresh requires state ≥4 (`0x1ed73–0x1ed7e`), resets the countdown to 40 and selects the minimap bitmap before calling terrain (`0x1ed8b–0x1edb6`). Draws unit markers via `FillRect` at `0x1ee71` and the 15×11 viewport via `RectOutline` at `0x1eeb3`. |
| `0x1eec8` | `MinimapScreenToTile` | Subtracts panel origin and clamps X at `0x1eecb–0x1ef00`, then does the same for Y at `0x1ef03–0x1ef38`. Both deltas are stored and tested as signed 16-bit values before the upper clamp. |

## Layouts

- **Terrain output:** The bitmap starts at `0x5297c`. The destination is the pixel pointer at `0x52980` plus the unsigned word at `0x599f8` (`0x1ec81–0x1ec8f`). The signed pitch is the high word of the dword read at `0x5297a` (`0x1ed00–0x1ed0b`). Each row writes 64 bytes; pitch determines where the next row starts.
- **Terrain inputs:** Fog and tile maps are row-major word arrays, advanced by two bytes per cell (`0x1ecf5`). The tile's low 11 bits select an eight-byte cell-table entry, and its first word supplies the byte index `2 * (word & 0xffe0) + 0x3f` (`0x1ecc3–0x1ecef`).
- **Refresh and markers:** The countdown and cached scroll Y/X are consecutive words at `0x599fa–0x599fe` (`0x1ed39–0x1ed67`). The renderer scans 200 records of stride `0x5c` (`0x1edbb–0x1edc6`, `0x1ee76–0x1ee7e`). It skips records with flags `0x020f` at `+0x10`, flag `0x0100` at `+0x0e`, or both nonzero state at `+0x36` and nonzero owner at `+0x1e` (`0x1edcb–0x1ee11`). The local town hall gets color `0xdd`; other eligible records use the owner palette (`0x1ee13–0x1ee2f`). Coordinates at `+0x0a/+0x0c` receive the draw origin from `0x599e0/0x599e2`; type at `+0x1b` indexes word pairs beginning at `0x51abc` (`0x1ee34–0x1ee70`).
- **Input bounds:** Screen origin words are at `0x599ec/0x599ee`; input width and height are at `0x599f4/0x599f6`. The dword loads at `0x1eee6` and `0x1ef1f` obtain signed bounds from their high words. For positive dimensions, the corresponding output range is zero through dimension minus one.

## T3 and T4

The T3 regression check covers begin/end scroll input, issue order, panel free/init, and scroll from mouse. The three functions in the table remain reference C: the near-miss guard requires them not to match. The reported first blockers are branch encoding/displacement at `0x1ecbc` and `0x1ed37`, and the saved-register choice at `0x1eeca`.

T4 compares terrain output including row padding and surrounding bytes, redraw return/state and ordered calls (including colors at rectangle calls), and the two in-place coordinate outputs. Redraw stubs terrain and the rectangle routines to isolate overlay dispatch; terrain is exercised directly by its own test. The unchanged-scroll return is a short: at `0x1ed6c` the low halves cancel, but the upper half of EAX can depend on the incoming ESI, so the test controls that register for its full-EAX comparison. These checks require the original executable and `$WATCOM`; no run result is claimed here.
