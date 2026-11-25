# Status text and resource counters (`mod_2b400_c`)

| Entry | Behavior and disassembly evidence | Confidence |
| --- | --- | --- |
| `StatusBarDrawText` (`0x2b67c`) | `0x2b688` gates on demo mode; `0x2b69a` loads the fallback pointer. `0x2b6b2` and `0x2b6c6` compare and copy the cached string. A change redraws the background; only nonempty text is drawn, and the saved DL at `0x2b727` controls the cost overlay. `0x2b7b2–0x2b7b7` dirties layer `0xf`. | high |
| `ResourceCountersUpdate` (`0x2b824`) | `0x2b828` gates on demo mode; `0x2b836–0x2b84e` returns early if both displayed counts match their targets. Otherwise `0x2b89e` and `0x2b8bd` call the counter helper for lumber and gold, respectively, even if only one count changed. `0x2b8c2–0x2b8c7` dirties layer `0xe`. | medium |

## Data and draw state

- `demo_mode` (`0x5152c`) is tested as a 16-bit word at `0x2b688` and `0x2b828`. The status fallback `status_text` (`0x55148`) is a 32-bit string pointer; if both input pointers are null, `0x2b6a4–0x2b6a8` supplies a local empty string. `dat_5a380` is the NUL-terminated cache used by `strcmp` and `strcpy`; those calls do not establish its capacity.
- The status background blit uses destination `0x5a408` and source `0x5a378` (`0x2b6cb–0x2b6e9`). It restores `cur_bitmap` (`0x55438`) immediately afterward; a nonempty redraw then selects that destination again and installs `score_font` (`0x59228`) in `cur_font` (`0x5acf0`) at `0x2b6f8–0x2b702`. The cost overlay blits icons at `(163,3)` and `(200,5)` from `0x5a410` and `0x5a370`, then draws the corresponding numbers at `(179,5)` and `(218,5)`. The loads at `0x2b746–0x2b74f` and `0x2b786–0x2b78f` zero-extend the lumber and gold words at `0x5a424` and `0x5a422` for the `%d` format at `0x57df8`.
- The counters compare 32-bit displayed slots at `0x5a418` (lumber) and `0x5a41c` (gold) with element zero of the arrays at `0x50060` and `0x50074`. The redraw uses destination `0x5a360`, background source `0x5a368`, and the same score font and color `0xf3` (`0x2b850–0x2b87e`). Calls at `0x2b89e` and `0x2b8bd` pass the format pointers (`lumber:%6ld ` at `0x57dfc`, `gold:%6ld ` at `0x57e0c`), positions `(23,2)` and `(135,2)`, and displayed-slot pointers in Watcom argument registers, with the target count on the stack.

## T3/T4 coverage

Neither file is listed as T3 in this scope. The per-function codegen guard checks both references remain near misses; the dossier reports unresolved `_dat_5a380` and `_dat_5a418` fixups, respectively. The proposed T4 tests compare global writes and stubbed draw calls, not rendered pixels or the counter helper's animation. Text passed through temporary buffers is compared by content rather than stack address. The tests require the original executable and `$WATCOM` and were not run here.
