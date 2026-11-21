# mod_3b3a0: dirty rect / layer table reset

## Functions

| Addr | Name | Status |
|------|------|--------|
| 0x3b3a0 | VidResetLayers | T3 byte-match (src/mod_3b3a0/vid_reset_layers.c) |

## Data
No new data symbols. The layer table (`layers`, 0x5aa90) and the dirty-rect
globals (`dirty_*`, 0x5acd0..0x5acda) are named in other symbol files.

## Notes
- T3: `VidResetLayers` matches the original bytes under Watcom 10.0a. The test is `test_t3_files_match`.
- T4: no reference (near-miss) functions exist, so there are no differential tests.
