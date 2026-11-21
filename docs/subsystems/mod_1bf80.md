# mod_1bf80 (0x1bf80..0x1c020): modal wait-for-input-or-timeout

Small modal loop: waits until a click/key sets a done flag, or a tick countdown expires.

## Functions
| Addr | Name | Notes |
|---|---|---|
| 0x1bf80 | WaitTickDown | idle callback that decrements `wait_ticks_left` (T3 matched, wait_tick_down.c) |
| 0x1bf88 | WaitSetDone | callback that sets `wait_done_flag` (T3 matched, wait_set_done.c) |
| 0x1bf94 | WaitInputOrTimeout(short ticks) | reference only (wait_input_or_timeout_reference.c); returns done flag |

## Data
| Addr | Name | Type |
|---|---|---|
| 0x59690 | wait_done_flag | short |
| 0x59692 | wait_ticks_left | short |

## WaitInputOrTimeout flow
Calls UiInputInit, EvtPump. Installs WaitSetDone in event_handlers[0], status_frame_callback and status_click_callback. If ticks != 0, sets dialog_idle = WaitTickDown and wait_ticks_left = ticks; otherwise wait_ticks_left = 1. Clears the done flag, then loops UiEventPump, ScreenUpdate until the done flag is nonzero or equals wait_ticks_left. Returns wait_done_flag.

## Status
- T3: wait_set_done.c and wait_tick_down.c match byte-for-byte.
- Reference: the compiled version lacks the `push ebx` at 0x1bf94 (OP/STRUCT mismatch), so it is kept as a reference and guarded by assert_ref_mismatch.
- T4: tests/test_mod_1bf80.py::test_wait_input_or_timeout differentially tests the reference against the original with stubbed callees.
