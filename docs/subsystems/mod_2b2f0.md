# mod_2b2f0 (0x2b2f0..0x2b400): per-slot target mode flags

`target_mode_flags` (0x5a350) is `unsigned short[4]`, indexed by `net_event_pending`. `map_aux_handler` is the callback at 0x59514, between `map_press_handler` (0x59510) and `map_release_handler` (0x59518).

| Addr | Name | Role | Status |
|---|---|---|---|
| 0x2b2f0 | TargetModeClear | Zeroes the 4 flags. The original calls the __STOSB helper with ecx=4, edx=0. | Reference only. The memset call compiles differently. |
| 0x2b308 | TargetModeGet | Returns the flag for the current slot. | T3 match (`fn_2b308.c`). |
| 0x2b31c | fn_2b31c | Enter target mode. If the flag is 0, it sets the flag to 1. For slot 0 it also shows the "select target" message, installs the aux, release and press handlers, sets cursor shape 2, and calls fn_25b6c(1) and fn_20c30(0x39). It then calls fn_20cc0. | Reference only. |
| 0x2b390 | fn_2b390 | Leave target mode. The inverse of fn_2b31c. It restores the default handlers, cursor 0, and calls fn_19f70(0,0), fn_25b6c(0), fn_20c4c(0) and fn_20c6c. | Reference only. |

## Blockers
- fn_2b31c: the handler stores at 0x2b350 and 0x2b35a are relocations to fn_ placeholder addresses. The other 23 instructions match. This looks like a link-name resolution gap, not something the C source can change.
- fn_2b390: one relocation differs, at 0x2b3c2 (fn_1efa4).
- TargetModeClear: the original uses the __STOSB helper instead of memset.

## Tests
`tests/test_mod_2b2f0.py` has two groups of tests:
- T3: `fn_2b308.c` must still match.
- T4: differential tests of the reference files against the original code. Callees are stubbed and their calls are logged. The tests compare the flag array, the handler slots and the call log.

The near-miss guard asserts that the reference files still do not match.
