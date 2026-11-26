# mod_2b2f0 (0x2b2f0..0x2b400): per-slot target mode flags

`target_mode_flags` (0x5a350) is `unsigned short[4]`, indexed by `net_event_pending`. `map_aux_handler` is the callback at 0x59514, between `map_press_handler` (0x59510) and `map_release_handler` (0x59518).

| Addr | Name | Role | Status |
|---|---|---|---|
| 0x2b2f0 | TargetModeClear | Zeroes the 4 flags. The original calls the __STOSB helper with ecx=4, edx=0. | Reference only. The memset call compiles differently. |
| 0x2b308 | TargetModeIsActive | Returns the flag for the current slot. | T3 match (`target_mode_is_active.c`). |
| 0x2b31c | TargetModeEnter | Enter target mode. If the flag is 0, it sets the flag to 1. For slot 0 it also shows the "select target" message, installs the aux, release and press handlers, sets cursor shape 2, and calls fn_25b6c(1) and fn_20c30(0x39). It then calls fn_20cc0. | T3 match (`target_mode_enter_reference.c`). |
| 0x2b390 | TargetModeExit | Leave target mode. The inverse of TargetModeEnter. It restores the default handlers, cursor 0, and calls fn_19f70(0,0), fn_25b6c(0), fn_20c4c(0) and fn_20c6c. | T3 match (`target_mode_exit_reference.c`). |

## Blockers
- TargetModeClear: the original uses the __STOSB helper instead of memset.

## Tests
`tests/test_mod_2b2f0.py` has three groups of tests:
- T3: `target_mode_is_active.c` must still match.
- T4: differential tests of the reference files against the original code. Callees are stubbed and their calls are logged. The tests compare the flag array, the handler slots and the call log.
- The near-miss guard asserts that the two target-mode reference files and `target_mode_clear_reference.c` still do not match.
