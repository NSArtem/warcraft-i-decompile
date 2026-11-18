# The two-player link ring layer (module `mod_12c70`)

Code range 0x12c70..0x13270, between CMD.C (ends 0x12b80) and the dispatch
module 0x13270.  This is the transport half of the two-player link: two rings
of records, sequence numbers, and the send helper the SAVE.C code calls.
Names and evidence: `analysis/symbols/net_link.toml`; the message format and
the save/load handshake that use it: `docs/subsystems/save_score.md` section 1.

## Record and ring layout

A ring record is 136 (0x88) bytes, exactly two 64-byte cache-line-ish blocks
plus a header:

| offset | size | field |
|---|---|---|
| +0x00 | 2 | checksum, written by `fn_20a50` (`fn_209e0` over the payload) |
| +0x02 | 2 | length (message size + 4), written by `fn_20a50` |
| +0x04 | 1 | message total size (`net_msg[0]`, payload + 4) |
| +0x05 | 1 | message type (1 nothing, 2 identity, 3 ack, 4 data, 5 save event) + side flags 0x40/0x80 |
| +0x06 | 2 | sender sequence number |
| +0x08 | 0x80 | payload |

Two rings of these records:

* `net_send_ring` 0x58848, **10** slots (0x550 bytes), cleared by
  `NetResetLink`.
* `net_recv_ring` 0x58628, **4** slots (0x220 bytes), same clearing.

## State words

| address | name | meaning |
|---|---|---|
| 0x58d98 | `net_ring_state[0]` | receive slot index, 0..3 |
| 0x58d9a | `net_send_slot` | send slot index, 0..9, starts at 9 and is used backwards |
| 0x58d9c | `net_send_state[0]` | outgoing sequence, stamped into every message |
| 0x58d9e | `net_send_state[1]` | sequence the receiver expects next |
| 0x58da0 | `net_send_state[2]` | last consumed outgoing sequence |
| 0x58da2 | `net_reply_pending` | a reply is outstanding; the poll checks the receive ring |
| 0x52b00 | `packet_id` | outgoing packet id (PACKET.C), reset at session start |

`NetResetLink` 0x12c70 sets the three sequence words to 1, the receive slot to
0, the send slot to 9, clears `net_reply_pending` and both rings, and calls
`NetResetPacketId` 0x21974 (a copy of `ResetPacketId` 0x21968 that clears
`packet_id`).  Its two callers start a session: `NetLinkHandshake` 0x23ef1
and `NetLoadSyncMessage` 0x2454e.

## Functions

| address | name | what it does | tier |
|---|---|---|---|
| 0x12c70 | `NetResetLink` | rewind the whole link state | T3 |
| 0x12cd4 | `NetNextRecvSlot` | advance a 0..3 wrapping index | T3 |
| 0x12cec | `NetNextSendSlot` | advance a 0..9 wrapping index | T3 |
| 0x12d04 | `NetPendingMessageCount` | `net_send_state[0] - [2]` when the link mode word 0x516ae is set, else 0; **int** return (callers compare `cmp eax,7; jge`) | T3 |
| 0x12d2c | `NetFindSentRecord` | find a sent record by sequence, rejecting the current and the next sequence (still in flight) | T3 |
| 0x12d7c | `NetFindReceivedRecord` | find a received record by sequence, skipping acks (type 3) | T3 |
| 0x12dec | `fn_12dec` | dispatcher for a polled record (jump table at 0x12dcc) | not yet |
| 0x12f24 | `fn_12f24` | record poll: `which = 0` consumes the oldest send record, `which = 1` polls the packet layer, dispatches and sends acks; a resend/timeout loop around `clock_`/`delay_` | not yet |
| 0x131d8 | `NetSendMessage` | stamp the sequence, take the next send slot, copy the message in, checksum and transmit (`fn_20a50`) | named |

`fn_12f24` is the one the save code polls through (`NetLinkHandshake`,
`NetQueryRemoteEvent`, `NetSendLocalEvent` pass `which = 0`/`1`); it is the
next target in this area.

## Codegen notes (Watcom 10.0a, OPT)

* The ring searches use a `short` index and cast the ring pointer at every
  access.  A `struct NetRingRecord *` local is strength-reduced into a
  pointer walk, which is 5 bytes shorter than the original's `imul` loop.
* `NetPendingMessageCount` returns `int`: the original leaves the subtraction
  in `eax` unmasked, and a caller tests it with a signed `jge`.
* A file holding several of these functions gets its second function 16-byte
  aligned by wcc386, while the original module is not aligned; they are
  therefore one function per object (`src/mod_12c70/*.c`).
* The two slot counters compare the promoted `unsigned short` as an int
  (`cmp edx,4` / `cmp edx,0xa`) - docs/subsystems/codegen.md V4.
