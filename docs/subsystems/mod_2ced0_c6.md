# mod_2ced0_c6 – UnitRemove / UnitCreate

Module `mod_2ced0` (OPT style, `-s -ot -ol -4r -zp2`, Watcom 10.0a).

| Addr | Name | Signature | Status |
|------|------|-----------|--------|
| 0x2e14c | UnitRemove | `void UnitRemove(Unit *u)` | reference C, T4 difftest |
| 0x2e6f4 | UnitCreate | `Unit *UnitCreate(short px, short py, unsigned char type, unsigned char owner)` | reference C, T4 difftest |

## Unit layout (0x5c bytes, `unit_array` at 0x59640, 200 slots)
- 0x0/0x2 pixel x/y; 0xa/0xc tile x/y; 0xe flagsE; 0x10 flags (bit0 free slot, bit1, bit3, 0x80)
- 0x1b type, 0x1e owner, 0x3e/0x40/0x42/0x44 dest, 0x46 ptr, 0x52 target, 0x54 dword timer.

## UnitRemove
Calls 0x25e58, AiRemoveUnit, UnitSetOrder(u,1), sets flags. Types <= 0x1f (units) go through unit death sound and defeat check (types 0xf/0x12 call MissionDefeat). Types >= 0x20 (buildings) spawn ruins or burst (0x30/0x31), update AI site/helper counters, release training/map flags, and recurse over units whose target (0x52) is `u`.

## UnitCreate
Scans for a free slot (flags bit 0), memset 0x5c, aligns px/py to 16, calls fn_13990 as a placement check, then sets hp from `unit_max_hp`, order 2, and building or unit-specific init.

## Tests
`tests/test_mod_2ced0_c6.py`:
- Near-miss guard: both reference files must still fail T3 matching (blockers: call rel offset in UnitRemove, spill layout in UnitCreate).
- T4: `run_spec` runs the original code against the compiled reference with explicit and seeded random cases. Callees are stubbed with call logs of their register args. The unit array and the globals the functions write are watched.
- The test skips when `original/` or `$WATCOM` is missing.
