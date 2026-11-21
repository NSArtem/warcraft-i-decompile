# snd_f1 (SND.C)

Animation-table helpers at the start of `SND.C` (`0x26320..0x263bf`), immediately before `SndInit` (`0x263c0`).

| Addr | Name | Proto | Status |
|---|---|---|---|
| 0x26320 | AnimTableLoad | `void AnimTableLoad(void)` | T3 matched (`src/snd/anim_table_load.c`) |
| 0x26340 | AnimTableFree | `void AnimTableFree(void)` | T3 matched (`src/snd/anim_table_free.c`) |
| 0x26360 | fn_26360 | `void fn_26360(Unit *u, unsigned sound)` | T4 reference (`src/snd/fn_26360_reference.c`); unit animation start (codegen blocker under Watcom 10.0a) |
| 0x26390 | BulletStartAnim | `void BulletStartAnim(Bullet *b, unsigned anim)` | T4 reference (`src/snd/bullet_start_anim_reference.c`); bullet animation start (same codegen blocker) |

## Data
`anim_table` (`0x53288`) is a pointer to an array of `unsigned short` loaded from resource `0xd6`. The header entries store byte offsets into the table, so `>> 1` converts them to word indices. Both `0x26360` and `0x26390` mask their 2nd argument (`dl`) to 8 bits (`mov cl, dl; xor ch, ch`):
- `fn_26360` (`0x26360`, unit animation start): `base = anim_table[u->byte1b] >> 1; u->word4 = anim_table[(unsigned short)(base + (unsigned char)anim)]; u->byte6 = 1`.
- `BulletStartAnim` (`0x26390`, bullet animation start): `base = anim_table[0x34 + b->byte0] >> 1; b->word0a = anim_table[(unsigned short)(base + (unsigned char)anim)]; b->byte0c = 1`.

## Tests
- T3: `tests/test_snd_f1.py::test_t3_files_match` (`anim_table_free.c`, `anim_table_load.c`).
- Near-miss: `tests/test_snd_f1.py::test_ref_mismatch` confirms both reference files still fail to match.
- T4: `tests/test_snd_f1.py::test_fn_26360` and `test_bullet_start_anim` wire `anim_table` (`0x53288`) to a full `0x10200`-byte table (covering even, odd, and `0xfffe` byte offsets), pass 8-bit and upper-bit-dirty anim arguments (`0..0x12345678`), and compare the full `0x60`-byte object buffer and callee-saved registers against the original.
