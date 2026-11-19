# NETWORK.C: the two-player link transport drivers

Code range `0x1f050..0x209e0` (31 discovered starts, all named), between
mod_1eba0 and mod_209e0 (`analysis/modules.toml`).  Names, prototypes and the
per-field evidence: `analysis/symbols/network.toml`.  The layer above it is
documented in `docs/subsystems/net_link.md` (the 0x12c70 ring layer) and
`docs/subsystems/save_score.md` section 1 (SAVE.C/SCORE.C).

This module is the *transport*: two interchangeable drivers behind a six-entry
function table, selected from `connection_type` 0x516ac by the dispatch layer's
`fn_20a80` 0x20a80:

| `connection_type` | driver | range |
|---|---|---|
| 1 (Modem Game) | serial / modem | 0x1f62c..0x209e0 |
| 2 (Network Game) | IPX | 0x1f050..0x1f62c |
| 3 (Direct-Link Game) | serial (null-modem) | 0x1f62c..0x209e0 |
| 0 (Single Player) | none (0x20b27 returns 0) | - |

## 1. The dispatch vtable `net_driver` 0x59b90

`fn_20a80` 0x20a97-0x20b20 stores the six handlers and calls slot 0:

| slot | address | serial/modem (1, 3) | IPX (2) | called by |
|---|---|---|---|---|
| 0 | 0x59b90 | `NetSerialStart` 0x1f854 | `NetIpxStart` 0x1f050 | `fn_20a80` (init), return value = "link up" |
| 1 | 0x59b94 | `NetSerialConnect` 0x1f62c | `NetIpxConnect` 0x1f230 | `fn_20b2c` 0x20b59 (hides the cursor around it) |
| 2 | 0x59b98 | `NetSerialStop` 0x1fb0c | `NetIpxStop` 0x1f3c8 | `fn_20b70` 0x20b7a (then zeroes the table) |
| 3 | 0x59b9c | `NetSerialReceive` 0x1fbc8 | `NetIpxReceive` 0x1f424 | `fn_20ba8` 0x20bae |
| 4 | 0x59ba0 | `NetSerialSend` 0x1fd30 | `NetIpxSend` 0x1f580 | `fn_20bd4` 0x20be7/0x20bfb |
| 5 | 0x59ba4 | `NetSerialDrain` 0x1fb54 | `NetIpxDrain` 0x1f564 | `fn_20c1c` |

The transport contract, from the callers:

* **receive**: `int receive(void __far *dst)` - far pointer (offset in `eax`,
  selector in `edx`); returns the length of one message, 0 when none is ready.
  `fn_20ba8` then compares that length with the record's own length word
  (`dst[2]`) and turns a mismatch into -1.
* **send**: `void send(void __far *msg, unsigned len)` - `eax` = offset,
  `edx` = selector, `ebx` = length.  `fn_20bd4` sends the record once plus
  `net_sync_counter` 0x52a7e extra times (packet duplication, edited by the
  `xtrapkts=` command-line option through `fn_1d61c`).
* `fn_20a50` (module mod_209e0, `NetSendRecord`) checksums the record
  (`fn_209e0`, a rotate-xor over the bytes into record[0]) and stores its
  length in record[2] before calling the send slot.

## 2. The IPX driver (0x1f050..0x1f62c)

The module does not speak IPX itself: `mod_1dca0` (0x1dca0..0x1de60, unnamed)
wraps the driver with the DOS IPX API, reached through DPMI `int 31h` 0x0300
(real-mode interrupt simulation, `fn_23e50`):

| wrapper | API call |
|---|---|
| `fn_1dca0` | `int 2Fh ax=7a00` installation check, returns 1/0 |
| `fn_1dce0` | open socket, `DX` = socket number |
| `fn_1dd20` | close socket, `DX` = socket |
| `fn_1dda0` | relinquish control |
| `fn_1ddd0` | listen for packet, `ES:SI` = ECB |
| `fn_1de14` | send packet, `ES:SI` = ECB |
| `fn_1dd5c` | driver initialisation call (segment + offset of the state) |

The state is one 0x842-byte real-mode block (`NetIpxStart` 0x1f05f), obtained
from the DPMI block allocator `fn_23d10` (module dos_realmode_mem) and kept as
a descriptor in `net_ipx_buf` 0x59a00:

| offset | contents |
|---|---|
| +0x00 | socket number (`0x40`, opened by `NetIpxStart`) |
| +0x02 | session dword, copied into the transmit ECB |
| +0x06 | own node address, compared against a received packet's source node |
| +0x0e | 12-byte header of the last received packet |
| +0x1a | command word stamped into every packet (`0xa`/`0xb`/`0xc` in the handshake) |
| +0x1c | command word of the last received packet |
| +0x1e | packet id counter, starts at `0xffffffff` and counts down |
| +0x22 | ten IPX ECBs of 0xd0 bytes (slot 0 = transmit, 1..9 = receive) |

The ECB is the standard 0x2a-byte IPX ECB (link +0, ESR +4, in-use +8,
completion +9, socket +0xa, workspace, immediate address +0x1c, fragment count
+0x22, fragment offset/segment +0x24/+0x26, fragment size +0x28) followed by
this module's packet area at +0x2a (0xa6 bytes):

| packet offset | contents |
|---|---|
| +0x12 | 12-byte header (copied to `state+0xe` on receive; never filled on send in this build) |
| +0x1e | packet id (dword) - the receive path keeps the *largest* id, i.e. the oldest packet: FIFO |
| +0x22 | command word |
| +0x24 | payload length |
| +0x26 | payload, 0x80 bytes |

Handshake (`NetIpxConnect` 0x1f230): both sides send a 12-byte identity - the
10 bytes at `net_signature` 0x52984 (`"WARCRAFT"` + two zero bytes) followed by
`net_node_number` 0x52a7c - once a second, and require the partner's 12 bytes
to be equal (`fmemcmp` at 0x1f313).  On a match they exchange the 10 bytes at
`state+0x52` and the 6 bytes at `state+0x12`, send the message again with
command `0xb` (twice unless the partner's command word already reads `0xb`),
drain and finish with command `0xc`.

## 3. The serial/modem driver (0x1f62c..0x209e0)

### 3.1 The UART state (`net_uart` 0x59a70, 0x1076 bytes)

`NetSerialStart` 0x1f854 allocates it with `fn_23d10(0x1076)`, derives the
linear base from the block's real-mode segment (`seg << 4`) and DPMI-locks it
(`DpmiLockRegion(net_uart, 4)`) plus one byte at `NetSerialIsrAnchor` 0x202bc
so the interrupt handlers' page stays resident.

| offset | field | notes |
|---|---|---|
| +0x0000 | io base | 0xffff until `NetSerialFixPort` resolves it |
| +0x0002 | IRQ | 0xffff until resolved |
| +0x0004 | COM port number 1..4 | |
| +0x0006 | baud rate | |
| +0x000a/+0x000c/+0x000e | rx head / tail / count | 0x800-byte ring at +0x10 |
| +0x0810/+0x0812/+0x0814 | tx head / tail / count | 0x800-byte ring at +0x816 |
| +0x1016 | last MSR value | |
| +0x1018 | last LSR value | |
| +0x101a..+0x1072 | 23 statistics dwords | cts/dcd/ri/dsr counts, tx/rx interrupts, tx overflow, rx bytes/frames/max/min/overrun/total/too-long/longest/run, tx frames/max/min/total/too-long/longest |

Settings: modem mode (`net_modem_link` 0x52a5a, set by `SelectGameTypeDialog`
0x156e4 for "Modem Game") reads `modem_irq`/`modem_port`/`modem_baud`
0x52996/0x52994/0x52990, else `serial_irq`/`serial_port`/`serial_baud`
0x52a58/0x52a56/0x52a52 (the values the two setup dialogs edit).

`NetSerialFixPort` 0x1fe04 maps a COM port number to the standard I/O base and
IRQ through two tables: `net_port_base` 0x52a62 = {0xffff, 0x3f8, 0x2f8, 0x3e8,
0x2e8} and `net_port_irq` 0x52a6c = {4, 3, 4, 3}.  Quirk: the `xtrapkts=` option
writes the port table's unused element 0, which `NetSerialStart`/`Stop` use as
their "not configured" sentinel (element 0 is never a valid port).

`NetSerialStart` also picks the link speed class `net_link_speed` 0x52a5e
unless the `pktspeed=` option set it: 0 for a serial link above 9600 baud, 3
otherwise, 4 at 2400 baud; and it enables one duplicate packet
(`net_sync_counter` 0x52a7e = 1) when no FIFO is present and the speed is not
2400.  That byte is also the identity record's "side flags" byte and is swapped
between the players by `NetLinkHandshake` 0x23edc (`save_score.md` 2.1).

### 3.2 UART programming and the interrupt vectors

`NetSerialUartInit` 0x1fe48 programs a 16550: divisor `0x1c2000/baud` (with
3840 remapped to 19200), 8N1, FIFO enable, then a FIFO probe (`IIR & 0xf8 ==
0xc0`), MCR = DTR|RTS|OUT2 and dummy reads.  It saves the previous handlers
through DPMI `int 31h` 0x0204 (protected mode: `net_old_isr_sel` 0x59a76,
`net_old_isr_off` 0x59a68) and 0x0200 (real mode: `net_old_vector_seg` 0x59a74,
`net_old_vector_off` 0x59a7a), then installs `NetSerialIsrFifo` 0x20448 when
the FIFO probe succeeded, else `NetSerialIsr` 0x202c0, at vector
`net_irq_vector` 0x59a78 = IRQ + 8 (DPMI 0x0205).  The matching *real-mode*
vector (DPMI 0x0201) points at a stub loaded from resource 0xd9 into
`net_irq_buf` 0x59a64 / `net_vector_table` 0x59a6c: the stub's first two words
select the FIFO and non-FIFO entry.  Finally it unmasks the IRQ in the 8259
(port 0x21), enables the UART's RX and modem-status interrupts (`outp(io+1,
7)`) and sends the specific EOI for the cascade (`outp(0x20, 0xc2)`).
`NetSerialUartStop` 0x200e8 is the exact inverse.

The two handlers differ only in how much data they move per interrupt:
`NetSerialIsr` one received byte and one transmitted byte, `NetSerialIsrFifo`
drains the FIFO (`LSR & 1`) and writes up to 16 bytes.  Both dispatch on
`IIR & 7` (4 = received data, 2 = transmitter empty, 6 = line/modem status,
anything else = end of interrupt), count the MSR bits into +0x1026 (ΔDSR),
+0x1022 (ΔRI), +0x101e (ΔDCD) and +0x101a (CTS), and share the EOI tail at
0x20494 - `NetSerialIsr` jumps into `NetSerialIsrFifo`'s exit block, which is
why the two functions must be reconstructed in one object.

### 3.3 The byte rings and the frame format

`NetSerialGetByte` 0x201c0 / `NetSerialPutByte` 0x2020c pop and push one byte
of the rings; `NetSerialPushBytes` 0x20258 copies a block or falls back to the
byte path at a ring wrap; `NetSerialQueueBytes` 0x1fb60 throws the transmit
ring away when it would overflow (`tx_overflow` 0x1032) and, when the
transmitter is idle (LSR THRE), writes the first byte with `NetSerialKickTx`
0x2061c (which also unmasks the IRQ in direct-link mode, `net_direct_link`
0x52a5c = the `dlink` option).

Messages are framed with 0x70 as the escape/delimiter byte
(`NetSerialSend` 0x1fd30 / `NetSerialReceive` 0x1fbc8):

* every 0x70 in the payload is sent twice;
* a frame ends with 0x70 followed by any non-0x70 byte (the encoder appends
  0x70, 0x00);
* the receiver keeps `net_rx_escape` 0x52a76; a second 0x70 is data, any other
  byte completes the frame (`net_rx_frame_done` 0x52a78, length
  `net_rx_length` 0x52a74);
* frames longer than `0x88` bytes are dropped and counted (0x104e/0x1052);
* the encoder buffer is `net_tx_frame` 0x59a7d, `0x113` bytes (0x88 payload,
  worst case all escaped, plus the terminator).

### 3.4 The modem (Hayes) layer

`NetModemCommand` 0x206c8 sends an AT line one frame per character, 0x14 ms
apart, then a CR (`net_cr` 0x570f4).  `NetModemWaitResponse` 0x20900 collects
response lines (terminated by LF or a full 0x4f-byte line, control bytes below
0x20 skipped) into `net_response` 0x59a10 and compares them with the five
result strings `net_result_table` 0x1f618 - "BUSY", "ERROR", "NO CARRIER",
"NO DIALTONE", "NO ANSWER" (the last three are copied to `net_error_text`
0x59ba8 and all five return 0), otherwise with the expected string (1 = match).

`NetModemInit` 0x207c0 sends `modem_init1` 0x52998 ("ATZ") and
`modem_init2` 0x529c8 and stores "Error resetting modem." / "Error in modem
init string." when the answer starts with "ERROR".  `NetModemDial` 0x20884
builds `ATDP%s`/`ATDT%s` with `phone_number` 0x52a28 (`dial_pulse` 0x52a51
selects pulse) and waits for "CONNECT"; `NetModemAnswer` 0x208d4 waits for
"RING", sends "ATA" and waits for "CONNECT"; `NetModemHangup` 0x2094c drops
DTR, sends "+++", `modem_hangup` 0x529f8 ("AT H0") and drains the receiver.

`NetSerialConnect` 0x1f62c is the serial handshake, a four-word text protocol
over the same framing: "listen" (0x1f600), "talk" (0x1f607), "waiting"
(0x1f60c), "ack" (0x1f614).  In modem mode the dialler retries while the answer
is "BUSY" and the answering side fails when "RING"/"CONNECT" never come.  Then,
with `clock() + 0x64` as a deadline: "listen" answers "talk" plus three
"listen" and finishes, "talk" finishes, "waiting" answers "ack", "ack" answers
three "ack" and finishes; every pass sends "waiting" until a command completed.
Pressing Esc aborts (the abort test reads `key_down_table[1]`, i.e. 0x5a8d6,
and 0x5a930 = index 46; the same test guards the IPX handshake and SAVE.C's
`NetLinkHandshake`).  A failed handshake leaves "Connection aborted." in
`net_error_text`.

## 4. Statistics and diagnostics

Both drivers keep counters the game never displays but that the handshake and
the pacing use indirectly: the UART block's 23 dwords (section 3.1) and
`net_link_speed`/`net_sync_counter`.  Nothing else in the image reads them, so
they are documented rather than modelled further.

## 5. Reconstruction status

`analysis/symbols/network.toml`: 31 functions, all named.

* **T3 (5)** - `NetIpxDrain` 0x1f564, `NetSerialDrain` 0x1fb54,
  `NetSerialFixPort` 0x1fe04, `NetSerialIsrAnchor` 0x202bc,
  `NetSerialPortIrq` 0x209d4 (sources in `src/network/`, one function per
  object; not built until the owner adds `src =`).  `NetSerialFixPort` needed
  the two codegen idioms the module is full of: the dword view of a word
  field (`*(int *)&u->io_base >> 16`) and a fresh `net_uart` load per test.
* **T4 (4)** - `NetSerialQueueBytes` 0x1fb60, `NetSerialGetByte` 0x201c0,
  `NetSerialPutByte` 0x2020c, `NetSerialKickTx` 0x2061c run against the
  original under `wc1.cemu` (`tests/test_network.py`).
* **Reference C (22)** - one file per function with a `t3_blocker` naming the
  first byte difference.  Most are 1-2 byte register-allocation differences
  (the save set, the register holding a block pointer); `NetSerialFixPort`
  and `NetSerialReceive` are codegen differences (the original re-loads
  `net_uart`; it increments the ring index in memory) and
  `NetModemWaitResponse`/`NetModemWaitResponse_tail` cannot match at all
  because the original compiles one function into two blocks that code
  discovery reports as separate starts.
* The T4 harness for the rest is written but skipped (each skip names the
  first failure): the IPX descriptor model trips `lgs` on a modelled selector,
  the interrupt handlers need an `iretd` frame the emulator does not build,
  and the modem path needs the exact stack-table frame of
  `NetModemWaitResponse`.

## 6. Open questions

1. **0x2070e is not a function.**  It has no prologue, reads the caller's
   frame and its `ret` pops that frame; it is the byte-reading block of
   `NetModemWaitResponse` 0x20900, entered by the conditional jump at 0x20930
   and left into the loop head at 0x2091e.  Code discovery split it because a
   backward conditional jump that leaves a function's extent promotes its
   target (the 2026-11-18 conditional-tail-target rule).  Proposal: veto starts
   whose own flow pops below their frame - the stack-balance veto that already
   protects the other seeds, applied here with the entry exemption removed for
   *jump-target* promotions.
2. **The IPX handshake's three command values** (0xa/0xb/0xc in `state+0x1a`)
   are not anchored to the partner side: the reply path sends `0xb`, checks
   the received command word and ends with `0xc`.  A two-sided trace (or the
   DOSBox-X link test) would settle who sends what first.
3. **The 12-byte packet header** at `packet+0x12` is copied out on receive but
   never filled by this module's send path (it stays zero); the field is
   probably reserved by the original protocol.
4. **0x59a04..0x59a0f** (12 bytes between `net_ipx_buf` and `net_response`)
   are never referenced; unexplained.
