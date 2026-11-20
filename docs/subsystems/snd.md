# snd (SND.C)

Game-level sound setup/option layer on top of the Miles AIL wrapper in `audio.h` (see audio.md).

## Functions

| Addr | Name | Status | Notes |
|---|---|---|---|
| 0x263c0 | SndInit | reference (T4) | Derives default SFX/music volumes from the cfg_dig_*/cfg_mdi_* driver ids and opt_* volumes, calls AilInit, builds driver paths with `_makepath(exe_dir, dig/mdi_driver_files[id])`, installs digital and MIDI drivers, allocates and DPMI-locks a 30000-byte music buffer, and on failure prints a message with fputs and calls exit(1). |
| 0x267fc | SndLoadTable | reference (T4) | Loads (or, with a NULL list, frees) a zero-terminated list of resource ids into `snd_data_ptrs[60]`/`snd_data_sizes[60]`. An id with bit 0x8000 duplicates an earlier entry with the same key. |
| — | music_clear, music_start, snd_apply_options, snd_shutdown, snd_toggle_music, snd_toggle_sfx | T3 | Byte-matched, in `src/snd/`. |

## Data

- `opt_sfx_volume`, `opt_music_volume`: unsigned int percent, with -1 meaning unset.
- `cfg_dig_driver`, `cfg_mdi_driver`: unsigned short driver ids, with 0xffff meaning none. The limits are 7 digital drivers and 10 MIDI drivers.
- `snd_data_ptrs[60]` and `snd_data_sizes[60]`: the loaded sample table.
- `snd_cur_table`: pointer to the active id list.
- `snd_table_count`: current index into the table.

## Blockers

- SndInit: the first difference is at 0x26416, where the original has `je +0xdd` and our build has `je +0x56`. The branch layout differs, which is a codegen problem.
- SndLoadTable: this is a register allocation problem. The original keeps the id in ebx in a bottom-tested loop and has `xor edx,edx` at 0x2680c.

## Tests

- T3: `assert_t3_matches` runs over the six matched files.
- Near-miss guard: `assert_ref_mismatch` checks that both reference files still fail to match.
- T4: `tests/test_snd.py` runs the reference C against the original code in the emulator. Callees are stubbed and their register arguments are logged. Stack pointers are never logged.
  - SndInit is run over a grid of driver ids and volumes, with install return values 0 and 1.
  - SndLoadTable uses explicit NULL-list cases plus 25 random cases. Their buffers are allocated inside `init_emu`.
