# Setup menu (`mod_2c3f0`)

## Function

| Address | Function | ABI and source |
| --- | --- | --- |
| `0x2c3f0` | `RunSetupMenu` | Watcom register ABI, `void (void)`; `src/mod_2c3f0/run_setup_menu.c` |

The entry address and ABI are recorded in `src/include/mod_2c3f0.h`. The supplied module information does not include an instruction listing or callers, so it does not establish the menu's control flow.

## Data layout

| Address | Symbol | Layout recorded in the header |
| --- | --- | --- |
| `0x55208` | `intro_music_started` | Unsigned 16-bit word |
| `0x5520a` | `setup_menu_top_rect` | `Rect`; fields not exposed by this header |
| `0x55216` | `setup_menu_body_rect` | `Rect`; fields not exposed by this header |
| `0x58f20` | `palette` | 768 unsigned bytes |
| `0x59610` | `slot_file` | 32-bit pointer |
| `0x5aa78` | `cursor_layer_id` | Unsigned byte |
| `0x5aa90` | `layers` | 32 records of `0x12` bytes each; a 16-bit `first_word` at offset zero followed by 16 opaque bytes |

The layer stride accounts for both interior addresses: `0x5aa90 + 0x12 * 0x12 = 0x5abd4` and `0x5aa90 + 0x13 * 0x12 = 0x5abe6`. These are `layers[0x12].first_word` and `layers[0x13].first_word`, not independent globals.

## Regression coverage

`RunSetupMenu` is reported as T3-matched. `tests/test_mod_2c3f0.py::test_t3_matches` guards that match when the original executable and `$WATCOM` are available. There are no reference sources, so this module has no T4 differential cases or near-miss guard.
