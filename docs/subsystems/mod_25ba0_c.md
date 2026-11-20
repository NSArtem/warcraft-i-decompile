# mod_25ba0_c — selection list helpers (0x25ba0..)

## Functions
| Addr | Name | Status | Notes |
|---|---|---|---|
| 0x25ba0 | SelectionFirst | T3 matched (`selection_first.c`) | resets cursor, returns first entry |
| 0x25c50 | SelectionNext | reference only (`selection_next_reference.c`) | blocker: extra `push ebx` in compiled output [OP/STRUCT] |
| — | SelectionSet | T3 matched (`selection_set.c`) | `(unsigned short count, Unit **list)` |

## Data layout
- `selected_units[2][4]` — `Unit *`, 32 bytes; first index is the player/side (`net_event_pending` is used as the index at 0x25c50).
- `selection_index` — `unsigned short` cursor, 0..4.
- `net_event_pending` — `unsigned short`, used as the row index into `selected_units`.

## SelectionNext semantics
Scans from `selection_index` up to 4, returning the first non-null entry of row `p` and leaving the cursor after it. It returns 0 if none is found, and the cursor is then 4 or more. Both globals are written back on exit.

## Tests
- T3: `selection_first.c` and `selection_set.c` must still match (`assert_t3_matches`).
- Near-miss guard: `selection_next_reference.c` must still NOT match (`assert_ref_mismatch`).
- T4: `test_selection_next` runs the reference C against the original at 0x25c50 in the emulator. Inputs cover the cursor at 0, 2, 4 and 5, both rows, an empty list, gaps, and a last-slot-only list. The watched memory is `selected_units`, `selection_index` and `net_event_pending`, and the return value in eax is compared. There are no callee stubs.
