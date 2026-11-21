# snd_f1 (SND.C)

Animation-table helpers living next to the audio layer (0x26360..0x263b0).

| Addr | Name | Proto | Status |
|---|---|---|---|
| 0x26360 | fn_26360 | `void fn_26360(Unit *u, unsigned short sound)` | reference only; near-miss on register allocation (orig `mov ebx,eax` at 0x26362, ours `mov ecx,edx`) |
| 0x26390 | BulletStartAnim | `void BulletStartAnim(Bullet *b, unsigned short anim)` | reference only; same REG blocker at 0x26392 |
| - | anim_table_free / anim_table_load | | T3 matched |

## Data
`anim_table` is a pointer to an array of u16. The first entries are byte offsets, so `>>1` gives a word index.
- fn_26360: `base = anim_table[u->byte1b] >> 1; u->word4 = anim_table[base + sound]; u->byte6 = 1`.
- BulletStartAnim: `base = anim_table[0x34 + b->byte0] >> 1; b->word0a = anim_table[base + anim]; b->byte0c = 1`.

## Tests
- T3: `assert_t3_matches` on the matched files.
- Near-miss: `assert_ref_mismatch` confirms the reference files still fail to match.
- T4: difftests of both functions against the original, with the object and table allocated in `init_emu`.

Caveat: the T4 tests use placeholder object and table buffers that may need rework. The `anim_table` pointer global is not yet wired into the emulated memory.
