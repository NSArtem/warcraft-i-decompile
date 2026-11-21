# startup_c1 (INIT.C)

Startup file/path helpers around the data archive (`war.dat`-style archive lookup).

## Functions

| Addr | Name | Proto | Notes |
|---|---|---|---|
| 0x1d330 | LoadFile | `short LoadFile(name, buf, min, max, in_exe_dir)` | Builds path (`_makepath` with `exe_dir`, or `strcpy`), opens with mode string at 0x56c88 under `file_open_noprompt++/--`, seeks to end, `FileTell` for size, rejects size outside [min,max], reads whole file, returns 1/0. 5th arg is on the stack. |
| 0x1d410 | FindDataFile | `FILE *FindDataFile(name)` | `sprintf(fname, fmt@0x56c8c, name)`; tries `exe_dir` then `cd_path`; on success `setvbuf(fp,0,0x100,0x4000)`. |
| 0x1d9d4 | OpenDataArchive | `void OpenDataArchive(void)` | `FindDataFile(str@0x52541)`; success -> `InitResources(fp)`; else `FatalError(fmt@0x56d70, ...)` with `exe_dir`, `cd_path` (or str@0x56d6c if equal), `path_war`. |

## Data
- `exe_dir` 0x59920 (0xb0 bytes), `cd_path` 0x59870 (0x90 bytes).
- Strings: 0x56c88 (fopen mode), 0x56c8c (name format), 0x52541 (archive name), 0x5254a, 0x56d6c, 0x56d70 (error format).
- `file_open_noprompt` (short) is incremented around opens.

## T3 / T4 notes
- All three are reference-only: the near-miss guard asserts they still do not match. Blockers are unresolved `dat_*` relocations (e.g. `mov edx,0x56c88` vs `mov edx,0`), not instruction-selection differences. The instruction counts equal the original's.
- T4 tests in `tests/test_startup_c1.py` stub every callee. Stubs log argument registers or string CRCs. They never log stack pointers. Local path buffers are only observed through string content.
- Buffers are allocated in `init_emu`. Cases and watches are lazy generators, so they are built after allocation.
- Callee stub addresses are resolved from the symbol DB, so the tests skip if a symbol is missing.
