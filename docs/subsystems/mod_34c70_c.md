# mod_34c70 (area mod_34c70_c)

## Functions

| Addr | Name | Status |
|---|---|---|
| 0x34c70 | PaletteLerp | reference only (T4 difftest); not a T3 match |

### PaletteLerp(first, last, step, steps)
Watcall: eax=first, edx=last, ebx=step, ecx=steps. For each palette index i in [first, last] it computes, for each of the three RGB bytes k:
`cur[k] = base[k] + (short)(target[k]-base[k]) * step / steps`.
It then calls `VgaSetPaletteRange(palette_cur + first*3, first, last-first+1)` with 3 register args (eax, edx, ebx).

Blocker: the original prologue is `sub esp, 0x14` at 0x34c75. The reference build emits `sub esp, 0x10`. The original keeps step and steps as stack words that are read back through a dword view (`sar eax, 0x10`). The reference approximates that with the `*(long *)((char *)&x - 2) >> 16` idiom, which gives a different frame size.

## Data
- `palette_base[768]`, `palette_target[768]` and `palette_cur[768]` hold RGB triples, 3 bytes per index.

## Tests
- T3: no files match yet. `assert_t3_matches` is skipped because the list is empty.
- Near-miss guard: `assert_ref_mismatch` checks that `palette_lerp_reference.c` still does not match.
- T4: `test_palette_lerp` runs the original and the compiled reference side by side. It compares palette_cur and the logged `VgaSetPaletteRange` call, and it covers edge and random cases. Steps are never 0, to avoid dividing by zero.
