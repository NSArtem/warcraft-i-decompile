# UI actions and building orders (`mod_20c30_ui_f2`)

These `mod_20c30` routines handle UI action checks and order setup. The UI entry points take a byte-sized order, type, or research row; the building-order handler takes a `Unit *`.

| Entry | Function | Behavior and disassembly evidence |
| --- | --- | --- |
| `0x21238` | `UiActivateSpell` | Loads the mana cost at `0x2124d` and dispatches target mode at `0x21295`. |
| `0x212ac` | `UiStartBuildingPlacement` | Checks cost at `0x212bc` and dispatches placement start at `0x212de`. |
| `0x212e8` | `UiStartResearch` | Checks cost with a stack out-parameter at `0x212fd` and dispatches research start at `0x2131f`. |
| `0x2132c` | `UiStartTraining` | Checks cost at `0x2133c` and dispatches training start at `0x2135e`. |
| `0x21368` | `OrderCreateBuildingAndTarget` | Creates the building at `0x213d9` and assigns it as the unit's target at `0x21417`. |
| `0x21428` | `UiIssueTownSquareOrder` | Checks the home footprint at `0x21471` and sets order `0x1e` at `0x21490`. |

## Data and calling convention

The shared declarations are in `src/include/mod_20c30.h`; it imports the `Unit` layout from `mod_104b0.h`. The target assignment at `0x21417` uses that shared unit record. The stack out-parameter at `0x212fd` belongs to the research cost-check call, not to the public single-byte `UiStartResearch` interface.

## T3/T4 checks

All six sources are already classified as T3. `tests/test_mod_20c30_ui_f2.py::test_t3_matches` checks that they still match under their declared compiler when the original executable and `$WATCOM` are available. There are no T4 reference files or differential-test mappings in this area.
