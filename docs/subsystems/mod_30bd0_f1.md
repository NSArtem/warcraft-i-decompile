# mod_30bd0_f1: video backbuffer setup wrapper

## Functions

| Addr | Name | Notes |
|------|------|-------|
| 0x30bd0 | VidSetupBackbuffer | Calls VidAllocBackbuffer (0x3b360) with eax=0, edx=arg (zero-extended 16-bit), then calls 0x3b3a0 with no args. |

## Data layouts
None. No globals are touched.

## T3 / T4 notes
- No T3 (byte-matching) files yet. The reference file `src/mod_30bd0/vid_setup_backbuffer_reference.c` must still fail to match.
- Blocker: the first difference is at 0x30be0, where the original calls 0x3b3a0 and the build emits a call to 0x30be5. All other instructions match, so only the link name for 0x3b3a0 is unresolved. If the DB renames 0x3b3a0, the reference should use that name.
- T4 difftest: `test_vid_setup_backbuffer` stubs both callees. It logs eax and edx for 0x3b360 and nothing for 0x3b3a0. It uses `out_regs=()` and covers edge values for the 16-bit argument, including dirty upper bits in eax.
