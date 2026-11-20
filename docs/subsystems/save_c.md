# SAVE.C (0x23ec0..0x24860) — two-player link half of save/load

Area `save_c`; sources in `src/save/`, shared header `src/include/save_score.h`.

## Reference functions (not byte-matched; verified by T4 difftests)

| Addr | Name | Blocker | Test |
|---|---|---|---|
| 0x23ec0 | NetLinkStart | codegen: orig calls 0x20a80 at 0x23ec0, compiled output is offset by one prologue (IMM/REL diff) | `test_net_link_start` |
| 0x23edc | NetLinkHandshake | regalloc: orig keeps memcpy size 12 in `esi` across the loop (`mov esi,0xc` at 0x23ef6, `mov ebx,esi` at 0x23f63); 156 vs 158 insns | `test_net_link_handshake` |
| 0x2445c | NetLoadSyncMessage | regalloc: zero constant in `eax` (0x244c7) versus `edi` in compiled code; 18 REG diffs | `test_net_load_sync_message` |

## Data layouts

- `NetRecord` (12 bytes): `local_time` +0, `now` +4, `campaign` +8, `cd_present` +9, `version` +0xa (always 0x25), `side_flags` +0xb.
- `NetSync` (18 bytes as used): NetRecord plus `counter` +0xc and `counter_other` +0xe. `NetLoadSyncMessage` range-checks them through `WordInRange` (0x2417c) with a ten-count tolerance.
- Link message at `net_msg` (16 bytes): `{size, type, seq16, payload[12]}`. The handshake sends type 2 with size 0x10, then type 1 with size 4 as the ack.
- Send ring `net_send_ring`: 10 slots of 136 bytes (0x550 bytes), slot selected by `net_send_slot`.

## T4 notes

- Callees are stubbed with logged arguments, and the logs are compared between the original and the compiled C. Stack addresses are never logged. The memcpy stub copies the data and logs only the length.
- The handshake poll stub `0x12f24` writes the address of a reply buffer to `*edx`. That buffer is allocated inside `init_emu`. Cases cover a link failure, a version mismatch, both campaign tie-breaks, the CD-present combinations and the remote-prefs adoption path. The same-campaign, same-time retry is excluded because it never terminates when the time stub is constant.
- `NetLoadSyncMessage` cases cover each early return, each clause of the match condition (including the range edges) and the mismatch path. These cases take `msg` from spare bytes inside `net_send_ring`.
- `GamesDifferDialog` (0x24304) is stubbed.
- T3: no matched C files are currently listed, so `assert_t3_matches` runs with an empty list. The near-miss guard `assert_ref_mismatch` confirms the three reference files still do not match.
