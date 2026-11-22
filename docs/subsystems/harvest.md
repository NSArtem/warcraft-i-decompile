# HARVEST.C — worker harvesting orders

The worker order handlers approach a mine or lumber tile, collect cargo, enter a building to deposit or extract resources, then exit and dispatch the next order.

| Entry | Function | Disassembly evidence | Test track |
|---|---|---|---|
| `0x1cd50` | `HarvestQueueBuildingEntry` | `0x1cde9` calls it with the worker after a valid mine target and a nonzero arrival result. | T3 |
| `0x1cd90` | `OrderUpdateHarvest` | Retaliation is tested at `0x1cd99–0x1cda1`. The mine path checks target state mask `0x207` at `0x1cdba–0x1cdc8`; the lumber path checks the work counter against 50 at `0x1ce60–0x1ce68` and saves the work target before routing to the hall at `0x1ce9b–0x1ced1`. Missing harvest-kind bits reach `FatalError("harvest:7")` at `0x1cf41–0x1cf46`. | T4 reference |
| `0x1cf5c` | `OrderUpdateHarvestReturn` | The module header identifies this entry; the supplied disassembly does not include its body. | T3 |
| `0x1cf94` | `HarvestDepositCargo` | `0x1cf96–0x1cfbc` accepts target types `0x28–0x29` and `0x30–0x31`. `0x1cfd1–0x1d015` credits 100 to the selected resource and harvested-total counters, then increments score; `0x1d01d–0x1d026` clears the cargo-present bit and refreshes graphics. | T4 reference |
| `0x1d034` | `OrderUpdateHarvestEnterBuilding` | `0x1d063–0x1d0af` checks tile occupancy and steps the worker off its tile. Entry sets order `0x0d` and timer `0x50` at `0x1d0ee–0x1d0fa`. `0x1d13a–0x1d1ad` tries cargo deposit first, then caps extraction at 100, or 5 when controller type is 1 and building flag `0x100` is set. `0x1d1b0–0x1d1d2` distinguishes depletion from saving a resumable target. | T4 reference |
| `0x1d1e0` | `OrderUpdateHarvestExitBuilding` | `0x1d1e6–0x1d20b` uses and clears bit `0x04` while selecting size row `0x28` or `0x30`. After a successful exit, `0x1d219–0x1d28e` routes cargo to the hall, gives controller type 1 an AI tick, or consumes the resume bit and dispatches the saved target. | T4 reference |

## Layout and state

- The two-byte-packed `Unit` view stores direction at `+0x08`, packed signed tile coordinates at `+0x0a`, building and state flags at `+0x0e/+0x10`, type at `+0x1b`, and owner at `+0x1e` (`0x1d093–0x1d0af`, `0x1d101`, `0x1d189`, `0x1cf99`, `0x1d012`).
- Saved point/target are at `+0x3e/+0x42`; work ticks and harvest flags are at `+0x48/+0x49`; current point/target are at `+0x4e/+0x52` (`0x1ce60–0x1cea7`). Building accesses reuse byte `+0x4e` as an entry-slot marker and dword `+0x54` as an unsigned resource count (`0x1d112–0x1d121`, `0x1d14b–0x1d159`). Harvest bits `0x80/0x40` select gold/lumber, `0x20` marks cargo, `0x10` marks the step-off phase, and `0x08` marks a saved job to resume.
- Resource balances are five dwords each at `0x50060` (lumber) and `0x50074` (gold); harvested totals are at `0x50dc0` (gold) and `0x50dd4` (lumber). Score is a four-word array at `0x50e34` (`0x1cfd1–0x1d015`). Controller bytes at `0x5008c` are indexed by owner (`0x1d176`, `0x1d24c`).
- `0x58580` holds a pointer to 64×64 tile slots, not the slots themselves (`0x1d063–0x1d07a`). Direction deltas are signed bytes at `0x50f80/0x50f88` (`0x1d096`, `0x1d0a7`). The exit code indexes four-byte size rows at `0x51abc` (`0x1d200–0x1d203`). Town-hall pointers are at `0x58db0` and packed home points at `0x50e68` (`0x1d22f–0x1d240`). The load based at `0x50e66` starts two bytes before each home point so its high word yields the signed x coordinate; it is not a separate coordinate array.

## Test coverage

`tests/test_harvest.py` guards the two T3 sources against codegen regressions and the four references against accidental T3 matches. The T4 cases compare EAX, worker and building memory, applicable counters, and ordered callee arguments. The order-target stub records the fifth Watcom argument and pops its four-byte slot; the clear-tile search stub logs the incoming point rather than a stack-local address. Entry tests stub cargo deposit to isolate the caller's branches; the deposit test runs that routine directly against the original. These are supplied test mappings, not a claim that the suite was executed here.
