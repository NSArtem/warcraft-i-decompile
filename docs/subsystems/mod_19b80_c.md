# mod_19b80_c

Module `mod_19b80`, area `mod_19b80_c`.

## Functions

| Addr | Name | Status |
|------|------|--------|
| 0x1a328 | GameScreenInputInit | reference only (not matched) |

`NetPumpEvents` (`net_pump_events.c`) is T3-matched and rechecked by the test.

## GameScreenInputInit (0x1a328)
If `dat_5a7c2 != 0`, clears the word at `status_help_text+0x150` and dwords 0 and 2 of `status_help_text`. It then calls `UiInputInit`. Finally it installs five handlers:
- `event_handlers[0]` = 0x19fd8
- `dialog_left_press` = 0x1a130
- `dialog_right_press` = 0x1a14c
- `dialog_idle` = 0x19f94
- `dialog_pre_event` = 0x1a168

Blocker: the `fn_XXXXX` placeholder externs compile to immediate 0. The first diff is at orig 0x1a350, where the original stores `0x19fd8` and the compiled code stores 0.

## Tests
- T3: `net_pump_events.c` must still match.
- Near-miss guard: the reference file must still fail to match.
- T4: `test_game_screen_input_init` runs a differential test with `UiInputInit` stubbed.
  - The harness resolves the placeholder link names automatically.
  - Buffers are allocated only inside `init_emu`.
