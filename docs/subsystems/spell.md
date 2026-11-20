# SPELL.C (0x27670..0x27b20)

Spell handlers and dispatch. Handler signature: `int h(Unit *u, short cast)`. With cast==0 it only checks mana and returns 0 if too low. With cast!=0 it performs the spell and deducts mana. Handlers are dispatched through `spell_handler_table` (0x53474, indexed by the unit byte at +0x1f). `spell_invalid_msg` is at 0x57d38 and holds "spell:1". `spell_summon_owner` is at 0x5a7c8.

## Functions
| Addr | Name | Status | Notes |
|---|---|---|---|
| 0x27670 | SpellHeal | reference | Target is at u+0x52. Returns 0 if the target type is in 0x20..0x32. Heals up to 0x28 HP at 3 mana per HP. Type 0x1c takes damage instead of healing. Calls fn_11ec0(t, 8). |
| 0x27740 | SpellHolyVision | reference | Costs 0x32 mana. Calls fn_2e9c4 with the tile x, tile y and owner, then BulletSpawnAt. |
| 0x277a0 | SpellInvisibility | T3 | |
| 0x277d4 | SpellUnholyArmor | reference | Costs 0x7d mana. Sets the target's +0x38 field to 1000 and halves its HP, with a minimum of 1. |
| 0x27824 | SpellPoisonCloud | T3 | |
| 0x2784c | SpellRainOfFire | T3 | |
| 0x278ac | SpellRaiseDead | reference | Costs 0x46 mana. Scans 200 units (0x5c bytes each) for corpses (type 0x33) within squared distance 0x24, then calls UnitCreate for type 0x1a. |
| 0x279c0 | SpellSummon | reference | Selects the unit type and cost from the spell id (0x16, 0x17, 0x19 or other). Makes up to 4 calls to fn_2e650. |
| 0x27a8c | SpellInvalid | T3 | |
| 0x27aa4 | SpellCastOrder | reference | The cheat flag (bit 8) sets mana to 0xff. Calls the handler with cast=0. Sets order 2 if the handler returns 0. |
| 0x27adc | SpellCastNextOrder | reference | Calls the handler with cast=1. Calls UnitSetNextOrder(u, 2) unless the spell id is 0x1a. |

## Unit fields used
- +0x08 and +0x0a: position as a fixed-point dword view
- +0x16: HP (word)
- +0x1a: mana
- +0x1b: type
- +0x1e: owner
- +0x1f: spell id
- +0x38: word set by Unholy Armor
- +0x4c and +0x4e: dword views of the target tile position
- +0x52: target pointer

## Tests
- **T3:** the invalid, invisibility, poison cloud and rain of fire files must match.
- **T4:** each reference function is run against the original with callee stubs, which log only their argument registers.
- **Near-miss guard:** the reference files must still fail to match. Each differs in register allocation, relative-jump offsets, or `xor eax,eax` placement. The SpellHolyVision difference is only a link-resolution artifact.
- **Caveat:** SpellHeal needs the `unit_max_hp` table, which comes from the loaded image. SpellRaiseDead calls UnitCreate and SndSummonAt without stubs, so its tests may need adjusting.
