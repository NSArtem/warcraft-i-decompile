# mod_2b1b0_c

Terrain region walker (module mod_2b1b0).

| Addr | Name | Status |
|---|---|---|
| 0x2b1b0 | TerrainWalkRegion | reference only (register allocation: orig uses edi at 0x2b1bc for `[0x5a340]`, we get ebx) |

## Data layout
Scan state globals (terrain_scan_*): w, h, y, cb, table, x. They are consecutive dwords. The function clips a w×h window centred on (x,y) to a 64×64 map. The 64-wide row stride is `pos += 0x40 - h`. A `ushort` table is walked in parallel with row stride `h`. For each cell it calls `cb(pos)`.

## T4 notes
The test runs the reference C against the original in the emulator. The callback is stubbed and logged (eax = pos). The table buffer is allocated in `init_emu`. The cases cover inside, negative-clip, overflow-clip, zero-size and mixed windows. The near-miss guard asserts the reference still does not match.
