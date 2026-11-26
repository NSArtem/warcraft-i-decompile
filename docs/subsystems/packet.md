# PACKET.C: the two-player command layer (0x214b0..0x21cf0)

Area = the object file `PACKET.C` (`analysis/modules.toml`; the guide's
module list in `docs/REFERENCES.md` R1 contains PACKET.C): 23 discovered
functions, 0x840 bytes, 23/23 named.  Names, prototypes and per-address
evidence: `analysis/symbols/packet.toml`.  Reconstructed C: `src/packet/`;
declarations `src/include/packet.h`; tests `tests/test_packet.py`.

This is the layer that keeps two Warcraft games in step: **every player
command is packed into a small packet, sent to the partner, and executed on
both machines by the same dispatcher** (section 3), with a rolling
synchronization check on the shared random-number state (section 4).  The
transport below it is the link-ring layer `mod_12c70` (0x12c70..0x13270,
`docs/subsystems/net_link.md`) and the SAVE.C send/receive helpers
(`docs/subsystems/save_score.md` section 1).

The module's own strings (`analysis/modules.toml` pool slice
0x57278..0x572c1, all four asserted by `test_packet.py::test_module_strings`):

| address | string | used by |
|---|---|---|
| 0x57278 | `A syncing error occurred during gameplay` | PacketCheckSync 0x21554 |
| 0x572a4 | `pktunit: %d %d` | PacketDispatch case 9 (unknown order id) |
| 0x572b4 | `PKT:7 %d %d` | PacketTick 0x21844 (sequence mismatch) |
| 0x572c0 | `message sent to opponent` | NetSendChatText 0x21c68 |

## 1. Framing: four nested layers

```
ring record (136 bytes, net_send_ring/net_recv_ring)
  +0  u16  checksum        fn_20a50/fn_209e0
  +2  u16  length = size+4
  +4  link message:                                  <- what the ring stores
        +0 u8  total size (payload+4)
        +1 u8  link type | side flags 0x40/0x80      NetSendMessage 0x131d8
        +2 u16 sequence                              net_send_state[0]
        +4 ..  command packet:                       <- PACKET.C's buffer
                 +0 u8  packet type (1..0x11)
                 +1 u16 sync id (packet_id)
                 +3 ..  payload
```

`NetSendDataMessage` 0x24780 (SAVE.C) wraps a command packet into the link
message: size = len+4, link type 4 (or the empty type-1 message for len 0),
payload at +4.  `NetSendMessage` stamps the sequence and the side flags and
copies the message into the 10-slot send ring.  The receivers (`fn_12f24`
poll / `NetRecvDataMessage`) hand the *command packet* back, which is what the
dispatcher reads.  The whole chain is exercised end to end in single-player
mode by `test_packet.py::test_sender_framing` and `test_sender_payloads`.

### 1.1 Packet body

| offset | size | field |
|---|---|---|
| +0 | 1 | type (dispatch index) |
| +1 | 2 | sync id (`packet_id`), stamped by `PacketSend`, then cleared |
| +3 | .. | type-specific payload |

Body length = 3 + payload.  The senders build it in a 0x84-byte stack buffer
- the same size the receive side keeps (`sub esp,0x84` in every sender,
0x108 = two buffers in PacketTick, and `NetRecvDataMessage` zeroes 0x80 bytes
of its destination, which is why a type-4 payload is capped at 0x7c bytes).

## 2. Single player is a loopback, two players is a ring

Nothing in the command path branches on "am I the host": the *transport*
decides where the packet goes.

* **No link** (`net_sync_state[0]` 0x5310c == 0, only ever set by a
  successful `NetLinkHandshake` 0x23edc / cleared by `NetLinkExit`
  0x240f8): `NetSendDataMessage` fills the static 16-byte `net_msg` buffer at
  **0x5a000** and does not transmit.  On the next tick `NetRecvDataMessage`
  (0x247d0, "no link" path 0x247f7) reads that same buffer as the incoming
  message, copies its payload into the caller's buffer and clears 0x80 bytes
  of `net_msg`.  So one command per tick travels through a single static
  buffer (`test_no_link_loopback_receive`).
* **Link up**: `NetSendMessage` queues the message in the send ring, the
  partner's transport fills the receive ring, and the same
  `NetRecvDataMessage`/`fn_12f24` poll hands the packet over.

Either way the *execution* of a command happens only in `PacketDispatch`,
which is why a sender never executes anything itself (the card actions even
pay-then-refund the cost so the payment happens once, in the executor, on
both machines).

The receive/direction constants: `which = 0` is the local (loopback / own
send-ring) direction, `which = 1` the partner's.

## 3. The tick: PacketTick 0x21844

`PacketTick` is called once per game loop pass (callers: fn_197b0 0x197d1,
fn_19908 0x1990d, fn_1e158 0x1e230/0x1e242, SaveStreamValidate 0x242b4,
fn_2fac4 0x2fb7d) and does:

1. **sequence sanity** (two-player only): `net_send_state[2]` (0x58da0, last
   consumed outgoing sequence) must equal `net_send_state[1]` (0x58d9e, the
   sequence the receiver expects next), else `FatalError("PKT:7 %d %d")`.
2. **receive**: `NetRecvDataMessage(0, buf1)`, and `(1, buf0)` when
   `net_play_flag` (0x52586) is set.
3. **sync id**: when two-player, the game screen is up (`dialog_enabled`
   0x517cc) and no message is outstanding (`NetPendingMessageCount() == 0`),
   `PacketGenerateId()` (0x214b0) folds the shared LCG state into
   `packet_id`.
4. **idle packet**: `PacketSendIdle()` (0x2150c) - two-player: the 3-byte
   type-1 packet that carries the id just generated; otherwise the empty
   link message (the keep-alive).
5. **execute**, in an order that depends on `own_campaign` (0x52584) - the
   two machines are on different sides, so one starts with its own packet and
   the other with the partner's, and both end up executing player 0's command
   before player 1's:
   * own side: `PacketDispatch(buf1)` with `net_event_pending` = 0, then
     `PacketDispatch(buf0)` with `net_event_pending` = 1;
   * other side: the remote one first (`net_event_pending` = 1), then the
     local one with 0.
   `net_event_pending` (0x5a11a) is the **player slot whose command is being
   executed**: the executors index all shared per-player state with it
   (selections, placement box, target mode, status-panel lock).
6. `dialog_active` (0x51e24) = 0, then `PacketCheckSync(buf1, buf0)`.

`PacketDispatch` and `PacketTick` are reference C (section 7): the logic is
proved by `test_t4_packet_dispatch` / `test_t4_packet_tick_loopback`, which
run the compiled C and the original side by side with every executor
replaced by a recording stub.

## 4. The synchronization check

`packet_id` (0x52b00) is not a counter - it is a **hash of the shared
deterministic state**:

* `PacketGenerateId` 0x214b0: `id = (dat_50d7c >> 16) ^ dat_50d7c`, forced to
  1 when the low word is zero.  `dat_50d7c` is the LCG state of the game
  (`codegen_promo.toml`): seeded identically on both machines by the
  handshake (`NetLinkHandshake` 0x24089) and saved with the game.
* It is generated only when the outgoing queue is empty, so both peers attach
  it to the packet at the same position of the command stream - normally the
  idle packet of that tick.
* `PacketSend` 0x214d4 stamps it into the next packet of length >= 3 (word at
  +1) and clears it, so exactly one packet carries each id.
* `PacketCheckSync` 0x21554 (called at the end of the tick) compares the ids
  of the two packets executed this tick: if both exist, both ids are non-zero
  and they differ, the simulations diverged -> `packet_sync_error` (0x52b02)
  latches and `FatalError("A syncing error occurred during gameplay")`.
  Single player never checks (`net_play_flag` gate).
  `test_sync_check_latches` covers every branch, `test_sync_id_is_the_folded_rng_state`
  the hash.

## 5. The dispatch table (types)

`PacketDispatch` 0x215f0 switches on `pkt[0]` through the 18-dword jump table
at **0x215a8** (`jmp dword [cs:edx*4+0x215a8]`; the table sits in the code
segment between fn_21554 and fn_215f0).  The table is asserted by
`test_dispatch_jump_table_matches_the_documented_types`.

| type | payload | executor on the receiving side | sender (and its caller) |
|---|---|---|---|
| 0,1,2 | - | nothing (the link layer's nothing/identity/ack types never reach this layer) | - |
| 3 | u16 count, count × u16 unit index | `fn_25f9c(count, units)` - writes `selected_units[player*16]` | NetSendSelection 0x219d8 (fn_262a0: selection changed) |
| 4 | u8 building type | `PlaceBoxStart(type)` 0x22798 ("Select location") | NetSendPlaceStart 0x21ac8 (build cards, fn_212ac) |
| 5 | - | `PlaceBoxCancel()` 0x22930 | PlaceBoxPress 0x21af8 (the box's map press handler) |
| 6 | u32 cell (x, y) | `PlaceBoxConfirm(cell)` 0x22ae4 (pays, creates) | NetSendPlaceConfirm 0x21b24 (PlaceBoxRelease 0x1b4dc) |
| 7 | - | `fn_2b31c()` target mode on | NetSendTargetMode 0x21980 (Move/Attack/Harvest/Repair/targeted spells) |
| 8 | - | `fn_2b390()` target mode off | NetSendTargetCancel 0x219ac (Escape fn_1b5e8, and the mode's cancel callback) |
| 9 | Point cell, u16 unit index, u16 order id | `fn_260c8(x, y, target, order_handlers[order])` | NetSendOrder 0x21a58 (fn_2f0a8, the target click / non-targeted orders) |
| 0xa | u16 unit index | `fn_2e384(unit)` - refund + detach + remove | NetSendCancelConstruction 0x21b54 (the "cancel construction" card fn_20e78) |
| 0xb | u8 research row | `UnitStartResearch(SelectionFirst(), row)` | NetSendStartResearch 0x21b94 ("research ..." cards, fn_212e8) |
| 0xc | u8 unit type | `UnitStartTraining(SelectionFirst(), type)` | NetSendStartTraining 0x21bc4 ("train ..." cards, fn_2132c) |
| 0xd | - | `UnitCancelProduction(SelectionFirst())` | NetSendCancelProduction 0x21bf4 (the "cancel unit training" card fn_20e70) |
| 0xe | u16 command id | `fn_19c14(command)` - menu/dialog dispatcher | NetSendControlPacket 0x21c20 (OpenGameMenu sends 8, SaveStreamValidate 0xc) |
| 0xf | text (NUL-terminated) | `fn_19edc(text, net_event_pending, 0x48)` - in-game message window; only when `net_event_pending == 1` | NetSendChatText 0x21c68 (the message window fn_1b690) |
| 0x10 | u32 cheat flags | `SetCheatFlags(flags)` | NetSendCheatFlags 0x21c44 (the message window, after a cheat matched) |
| 0x11 | 18-byte sync block | `NetLoadSyncMessage(pkt+3)` (SAVE.C) | NetSendSyncMessage 0x21cb8 (SaveStreamValidate 0x2426a) |

Every command row except the last three starts with
`StatusPanelLockAdjust(0)`, the mirror of the sender's
`StatusPanelLockAdjust(1)`: the sender takes one status-panel lock while its
modal action is up and the receiver releases one.  The lock is only touched
while `net_event_pending == 0` (`StatusPanelLockAdjust` 0x29424 itself), i.e.
the *remote* player's lock, never the local one.

The order id in type 9 indexes `order_handlers` at **0x52a80** (4-byte
executors; 2 stop, 3 move, 4 attack, 0xa harvest, 0xb return-goods, 0xe
repair, ...); a zero entry is a fatal error (`pktunit: %d %d`).  The order
layer itself is ORDER.C (`mod_20c30`), not this area.

## 6. The senders and their callers

All senders share the same shape: build the body in a stack buffer, call
`PacketSend`, and (except for chat/cheat/control) take a status-panel lock.
The *command card* table of STATUS.C (`docs/subsystems/status.md` section 2,
`python3 -m wc1.status_dump`) supplies the callers, which is how the card
actions were identified: `move` (0x20ec4), `attack` (0x21030), `harvest`
(0x210cc), `repair` (0x2110c) enter target mode with `pending_order` set;
`stop` (0x20e98), `return goods` (0x21130) and every spell that needs no
target issue an order packet directly; `build ...` (0x212ac) starts
placement; `train ...` (0x2132c) / `research ...` (0x212e8) / `cancel ...`
(0x20e70, 0x20e78) send their command; the spells (0x21238) pick target mode
or a direct order from `order_props` 0x534f4 bit 0 (`mov al,[eax+0x534f4]; and al,1`).

`pending_order` (0x5a7c4, next to `spell_order` 0x5a7c0) holds the order id
between the card press and the target click; `NetSendOrder` copies it into
the packet and clears it, so a click without a pending order sends nothing.

The card actions *validate* the cost and then refund it - `fn_20d74(player,
1, type)` pays, `fn_20d74(player, 0, type)` gives it back - because the real
payment happens inside the receiver's executor (`UnitStartTraining` /
`UnitStartResearch` / `PlaceBoxConfirm`).  That is what makes the two
machines' economies stay identical.

## 7. What is byte-matched (T3) and what is reference C

**Built from C (T3, Watcom 10.0a, `-s -ot -ol -4r -zp2`)** - 20 functions:

| function | addr | file |
|---|---|---|
| PacketGenerateId | 0x214b0 | `src/packet/packet_generate_id.c` |
| PacketSend | 0x214d4 | `src/packet/packet_send.c` |
| PacketSendIdle | 0x2150c | `src/packet/net_send_idle.c` |
| PacketCheckSync | 0x21554 | `src/packet/packet_check_sync.c` |
| PacketTick | 0x21844 | `src/packet/packet_tick.c` |
| NetSendTargetMode | 0x21980 | `src/packet/net_send_target_mode.c` |
| NetSendTargetCancel | 0x219ac | `src/packet/net_send_target_cancel.c` |
| NetSendOrder | 0x21a58 | `src/packet/net_send_order.c` |
| NetSendPlaceStart | 0x21ac8 | `src/packet/net_send_place_start.c` |
| PlaceBoxPress | 0x21af8 | `src/packet/place_box_press.c` |
| NetSendPlaceConfirm | 0x21b24 | `src/packet/net_send_place_confirm.c` |
| NetSendCancelConstruction | 0x21b54 | `src/packet/net_send_cancel_construction.c` |
| NetSendStartResearch | 0x21b94 | `src/packet/net_send_start_research.c` |
| NetSendStartTraining | 0x21bc4 | `src/packet/net_send_start_training.c` |
| NetSendCancelProduction | 0x21bf4 | `src/packet/net_send_cancel_production.c` |
| NetSendControlPacket | 0x21c20 | `src/packet/net_send_control_packet.c` |
| NetSendCheatFlags | 0x21c44 | `src/packet/net_send_cheat_flags.c` |
| NetSendChatText | 0x21c68 | `src/packet/net_send_chat_text.c` |
| ResetPacketId | 0x21968 | `src/packet/reset_packet_id.c` |
| NetResetPacketId | 0x21974 | `src/packet/net_reset_packet_id.c` |

Four of these were already named by neighbouring areas (PlaceBoxPress in
`mod_20c30.toml`, NetSendControlPacket in `status.toml`, the two resetters in
`net_link.toml`) and three more by the same `mod_20c30.toml` block
(NetSendCheatFlags, NetSendChatText, NetSendSyncMessage) - this area keeps
those names (no duplicate address) and only adds the C.  The linker symbols
they need (`fn_25f9c`, `fn_260c8`, `fn_2b31c`, `fn_2b390`, `fn_2e384`,
`fn_19c14`, `order_handlers` 0x52a80) are placeholders in `packet.toml` with
one line of evidence each, like `mod_20c30.toml`'s collaborators block.

**Reference C (T4, difftested) - 3 functions:**

| function | addr | file | blocker |
|---|---|---|---|
| PacketDispatch | 0x215f0 | `src/packet/packet_dispatch_reference.c` | codegen: the switch's index/jump-table sequence differs at 0x21604 (the original `xor edx,edx; mov dl,al; jmp cs:[edx*4+0x215a8]` vs `and eax,0xff; lea edx,[eax*4+t]; jmp [edx]`); all 15 case bodies, the frame (0x10 for `Unit *units[4]`) and the case order are byte-identical - `test_t4_packet_dispatch` |
| NetSendSelection | 0x219d8 | `src/packet/net_send_selection_reference.c` | regalloc: the original spills the count to the frame and uses no ebp, 10.0a keeps it in edi and pushes ebp - `test_t4_net_send_selection` |
| NetSendSyncMessage | 0x21cb8 | `src/mod_20c30/net_send_sync_message_reference.c` (the address is owned by `mod_20c30.toml`) | codegen: the original ends `mov eax,eax; ret` (the only such epilogue in the program), 10.0a emits a plain `ret` - `test_t4_net_send_sync_message`; the TOML entry is in `mod_20c30.toml` (see the change requests) |

A fourth caveat: even if PacketDispatch matched, its object could not be
placed in sequence - the compiler puts the 18-entry jump table *before* the
function (0x50 bytes in the object, 0x48 in the original, where the table sits
in the asm gap after fn_21554), so `wc1.build`'s placement check
(`base = first public`) would fail.  The compile-alone form of the same
switch was tested both alone and after another module function: the
index/jump-table sequence does not change, so the table's position is not the
trigger.

## 8. Codegen notes (Watcom 10.0a, OPT)

* The module is OPT style (`-s -ot -ol -4r -zp2`): no ebp frame, `push
  ebx/ecx/edx` prologues, `sub esp,0x84` scratch buffers.
* A 16-bit payload word is read as `*(int *)(pkt + k - 2) >> 16` - the
  `mov eax,[edi+k-2]; sar eax,0x10` idiom.  Writing `*(short *)(pkt + k)`
  gives `movsx` and does not match (`packet_dispatch_reference.c` documents
  the two read styles; the same idiom appears in the 0x25xxx and 0x26xxx
  order code).
* `NetSendOrder`'s two payload words must be stored through a `Point *`
  into the buffer: two separate `short` stores give the other register
  assignment (`esi`/`ecx` swapped, 0x21a60).
* `PacketSend`'s length check needs an unsigned literal (`len >= 3u`): a plain
  `len >= 3` promotes the `unsigned short` to `int` and 10.0a emits
  `cmp eax,3; jl` where the original has `jb`.
* `PacketGenerateId` needs the hash in a `long` temporary before the
  `unsigned short` narrowing, otherwise 10.0a keeps everything in eax and
  never pushes edx.
* `PacketCheckSync` compares the two ids as direct memory expressions; a
  pair of `unsigned short` locals gives `bx`/`ax` instead of the original's
  `si`/`di` (and 16-bit `push si`).

## 9. Open questions / change requests

* `NetSendSyncMessage`'s `ref`/`t3_blocker`/`ref_verified_by` cannot be
  recorded here because the address is owned by `mod_20c30.toml` (its
  reference C already is, so only the `ref_verified_by = "difftest:
  tests/test_packet.py::test_t4_net_send_sync_message"` and the return type of
  the prototype are missing).
* The 18-byte sync block is `save_score.h`'s `NetSync` *plus a third
  counter word*: `NetSendSyncMessage` copies 0x12 bytes (4 movsd + 1 movsw)
  and `SaveStreamValidate` reads 0x12, while `typedef struct NetSync` in
  `src/include/save_score.h` is 0x10 bytes.  The sender here declares its own
  opaque 18-byte layout; the SAVE.C header should be extended.
