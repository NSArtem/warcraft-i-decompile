# Save/score: the SAVE.C and SCORE.C modules

Area = `SAVE.C` **0x23ec0..0x24860** and `SCORE.C` **0x24e50..0x25820**
(`analysis/modules.toml` names both; the Insider's Guide module list in
`docs/REFERENCES.md` R1 contains SAVE.C and SCORE.C).  Names, prototypes and
per-address evidence: `analysis/symbols/save_score.toml`; reconstructed C:
`src/save_score/`; declarations: `src/include/save_score.h`; tests:
`tests/test_save_score.py`.

Nothing in SAVE.C opens a file.  The module is the **two-player link half**
of saving and loading: when one player loads a game over a modem/serial
link, both machines exchange identity blocks and the loaded image's header,
and the partner's save/load *events* are transported through the link
message queue while the save/load dialog is up.  The code that actually
reads and writes save files is the neighbouring `mod_24860`
(0x24860..0x24e50: `fn_24900` loader, `fn_24bf0` writer, `fn_249a4` /
`fn_249c8` stream helpers) - outside this area.

SCORE.C is the **per-player score accounting** (the score word array at
0x50e34, the 2500-point pool at 0x5a0ce), the rank titles Slave..Designer,
and the 72x72 score panel.

## 1. The link message

A link message is the 16-byte buffer `net_msg` at **0x5a000**:

| offset | size | meaning |
|---|---|---|
| +0 | u8 | total size (4 for the empty message, 0x10 for a 12-byte payload, `len+4` in NetSendDataMessage) |
| +1 | u8 | type \| flags - receivers mask with 0x3f |
| +2 | u16 | sequence, stamped by the send routine `fn_131d8` (0x131e3) from [0x58d9c] |
| +4 | 12 | payload |

Message types used by this area (verified by
`tests/test_save_score.py::test_save_message_types_are_the_documented_set`):

| type | meaning | sender |
|---|---|---|
| 1 | "nothing" (empty query/ack) | NetQueryRemoteEvent, NetSendLocalEvent, NetSendDataMessage(len=0) |
| 2 | game identity block (12-byte `NetRecord`) | NetLinkHandshake handshake |
| 4 | raw data (payload = size-4 bytes) | NetSendDataMessage, read by NetRecvDataMessage |
| 5 | save/load event (payload = a 12-byte event record) | NetSendLocalEvent, read by NetQueryRemoteEvent |

Two primitives outside this area carry every message:

* **`fn_131d8` (send)** takes the buffer in `eax`, stamps the sequence word
  at +2, sets bit 0x40 (and 0x80 when [0x516ae] and [0x52584] are both set),
  copies `size` bytes into the 10 x 136-byte record ring at 0x58848 and
  hands the record to the dispatch layer.
* **`fn_12f24` (poll)** takes a selector in `eax` (0 = the send-ring
  direction, 1 = the reply direction, sign-extended by the callers with
  `cwde`) and an `unsigned char **out` in `edx`, and returns **0 with the
  record pointer stored at [edx]** when one is available (0x12f78/0x12fa0),
  non-zero when nothing was available.  `fn_12f24` stores the record with a
  4-byte header skipped (record + 4), so the type byte is at [p+1] and the
  payload at p+4.

The link-active word is `net_sync_state[0]` (0x5310c): set by the
NetLinkHandshake handshake (0x240cf), cleared by `NetLinkExit` (0x2416c), and
tested by every sender/receiver here.  The high word is the handshake
phase (compared with 1 by EnemyDidNotLoadDialog 0x24350 and with 2 by
NetLoadSyncMessage 0x24479).

## 2. The two-player save/load flow

### 2.1 The identity handshake: NetLinkHandshake (0x23edc..0x240f8)

`NetLinkHandshake` (named by `analysis/symbols/codegen_promo.toml`, module
SAVE.C; this area deliberately adds no second entry for it) runs when a
two-player game is set up:

1. `fn_20b2c()` must report the link ready, else the function tail-jumps
   into `NetLinkExit` (0x240f0) and returns its result.
2. It builds the 12-byte `NetRecord` on its stack:
   `[0x532b4]` (own game start stamp), `fn_331eb(0)` (a time value),
   byte 8 = `[0x52584]` (campaign), byte 9 = `[0x52518]` (`cd_present`),
   byte 10 = 0x25 (version), byte 11 = `[0x52a5e]` (side flags)
   (0x23f22-0x23f51), sends it as the **type-2** message, delays 0x14 cs
   and polls both directions through `fn_12f24` for the partner's
   type-2 reply.
3. The reply's 12 bytes are copied to `net_enemy_record` (0x5a084,
   memcpy at 0x23ff6) and compared field by field: the partner's time
   (0x2402c/0x24032), campaign byte (0x2401d vs [0x52584]), version 0x25
   (0x24001); byte 9 is ORed into `[0x52518]` (0x24093-0x2409b) and when
   the result is 0 the *"At least one player must have a WARCRAFT CD
   present."* dialog (0x578e8) is shown (0x240bb); byte 11 of the reply is
   copied to/from `[0x52a5e]` (0x24065/0x2407f) and adopted as the own
   [0x52a5e] (0x240d1-...).
4. On success the link-active word `[0x5310c]` is set (0x240cf).

`net_enemy_record` (0x5a084) is exactly this block; the save writer
`fn_24bf0` writes it verbatim into save files (count 0xc at 0x24c4c),
which is how the identity survives a save (checked by
`tests/test_save_score.py::test_net_record_layout_matches_the_save_file`).
The placeholder was renamed to `NetLinkHandshake` on 2026-11-17 from this
area's analysis.

### 2.2 The save-stream header: SaveStreamValidate (0x241a4)

The loader (`fn_24900` in mod_24860) GdsAlloc's the loaded image and calls
`SaveStreamValidate(pos)` on it:

* **single player** (`[0x52586]` == 0): `pos == 0` returns 0; the real
  `fn_249a4` (eax=dst, edx=count, ebx=position - it copies `count` bytes
  and subtracts them from the *bytes-left dword* at 0x5a0b0) reads a
  2-byte record type which must be **0x43 ('C')**, else `fn_1a914()`
  (*"Saved game uses old version number!"*) and return 0; two more bytes
  which must be zero, else `fn_1a95c()` and return 0; then `fn_249c8`
  skips 0x566 (1382) bytes and the new position (pos+4+0x566) is
  returned.
* **two player** (`[0x52586]` != 0): the same two reads, then - inverted -
  the second word must be **non-zero**; an 18-byte `NetSync` block
  (`net_sync_msg`, 0x5a090) is read, `fn_21cb8` (PACKET.C) checks it with
  the [0x52a7e] counter raised by 3, and on success
  `net_sync_reply` (0x5310e) = 1, `net_stream_pos` (0x53110) = the
  position; on rejection `fn_21c20(0xc)` and `net_sync_reply` = 2.
  Either way `net_load_state` (0x5a0a2) := 3 and the function *waits*:
  while the game mode ([0x59614] >> 16, `game_mode` in cmd_123f0.toml) is
  3 or 5, call `fn_21844()` (the packet-layer tick); state 0 finishes with
  `net_sync_reply := 0` and returns `net_stream_pos`, state 1 or 2 aborts
  with 0, state 3 keeps waiting, and leaving modes 3/5 aborts with 0.

The single-player paths are difftested with the *real* `fn_249a4`
(`test_save_stream_validate_rejects_bad_header`); the 0x5a0b0
bytes-left semantics is `fn_249a4`'s own `sub dword [0x5a0b0], ebx`
(0x249af), asserted by the same test.

### 2.3 The handshake state machine: net_load_state (0x5a0a2)

| value | set where | meaning |
|---|---|---|
| 3 | 0x2429b (SaveStreamValidate) | stream validated, waiting for the partner |
| 2 | 0x243ae, 0x24445, 0x244c0 (the three dialogs), 0x24292 (rejected sync) | aborted / dialog shown |
| 1 | 0x2460d (NetLoadSyncMessage) | the two games differ |
| 0 | 0x245fc (NetLoadSyncMessage) | done |

`NetLoadSyncMessage` (0x2445c, called by PACKET.C's dispatcher 0x21834
with the partner's sync block) drives the machine to 0: it compares the
partner's block with `net_sync_msg` field by field (two of them through
`WordInRange` with a +/-10 tolerance on the message counters), copies the
first 12 bytes to `net_enemy_record`, reads 0x550 bytes of message ring +
4 bytes of counters from `net_stream_pos`, replays the partner's recorded
messages through the dispatch send, and drops the last ring slot.

The three dialogs show their text with `fn_1a894(text, 0x176, 10)` -
**watcall**, so the 2nd/3rd arguments travel in edx/ebx
(`test_games_differ_dialog_saves_mode`):

* `GamesDifferDialog` (0x24304) - *"The two games did not match."*
  (0x57920); forces the screen-mode word [0x593f6] to the own campaign
  value and restores it after.
* `EnemyDidNotLoadDialog` (0x24344) - *"You tried to load a game, but your
  enemy did not."* (0x57940).
* `NotValidTwoPlayerDialog` (0x243c4) - composes *"You"/"Your enemy"* +
  *" did not load a valid two player game."* in the buffer at 0x59f00.

### 2.4 Event and data transport while the dialog is up

`NetQueryRemoteEvent` (0x2461c) and `NetSendLocalEvent` (0x246b4) are
drop-in replacements for `EvtGet` (0x31598) in the save/load dialog loop
(the callers 0x176fe/0x17709 and 0x18640/0x1864c sit exactly where the
non-link path calls EvtGet): without a link both just call EvtGet; with
the link both delay 0x14 cs, drain two records (`fn_12f24(0,&p)` /
`fn_12f24(1,&p)` - in that order in NetQueryRemoteEvent, reversed in
NetSendLocalEvent; either "nothing" return aborts with 0), send the
appropriate message, and when the reply's type is 5 copy its 12-byte
payload into the caller's event buffer and return 1.

`NetSendDataMessage` (0x24780, **(eax=len, edx=data)** - the length is the
first argument, see the prototype fix in the TOML) wraps up to 12 bytes as
a type-4 message; `NetRecvDataMessage` (0x247d0, (which, dst)) reads one:
a **type-4** record's payload (size-4 bytes) is copied into dst (which the
0x80-byte zeroing in the not-a-data-message path fixes at 128 bytes) and 1
is returned; a poll that finds *nothing* overwrites the stale record's
type byte with 1, which fails the type test and zeroes dst instead; both
behaviours are asserted by `test_net_recv_data_message`.  The callers
0x2188e/0x218a4 in PACKET.C are the poll/re-read pair.

## 3. The score model

`player_score[4]` (0x50e34, words, initialised to 300 each by fn_1e100)
is the per-player score.  Three globals shape its growth:

* `score_pool` (0x5a0ce, word) - 2500 at scenario start (`ScoreInit`
  0x25774); every award is subtracted from it, every claw-back added back.
* `score_cap` (0x5a0d2, word) - the per-player maximum, from
  `score_cap_tbl[level]` (0x5315c, 12 words: 1800, 2600, 3400, 4200, 5000,
  5400, 6200, 7000, 9800, 11800, 11900, 30000).
* `score_rate` (0x5a0cc, word) - the per-tick income, from
  `score_rate_tbl[level]` (0x53174: 50, 50, 50, 300, 50, 50, 55, 500, 50,
  50, 50, 50); the level is `clamp((scenario - 0x77) / 2, 11)` on the
  scenario number [0x50d82].

`ScoreTickIncome` (0x24e90) runs once per game tick (caller 0x30017) and
gives player 0 `score_rate` (+500 in game mode 6) out of the pool, clamped
at `score_cap` (`test_score_tick_income`).

### 3.1 The six adjusters

The unit accounting (0x13b30 men / 0x13b4c buildings) calls one adjuster
per event; the combat code (`fn_10650`) calls the killed pair.  All six
are skipped entirely when `[0x5a7c2] != 0` (checked by
`test_score_suppress_flag_skips_adjustments`), all read the unit's owner
byte at +0x1e, and all use `score_value[...]` (0x51a4c, the per-type point
values 40,40,40,40,90,...) indexed by the *affected* player.  The exact
arithmetic (difftested over 400 random cases per trial plus explicit
corner cases in `test_score_adjust_family` and
`test_score_adjust_forced_and_empty_counters`):

| function | counts read | ratio (when) | post-div | clamps in order | applies |
|---|---|---|---|---|---|
| 0x24ee0 ScoreAddForMen | men | value*others/mine (mine > others) | /4 | pool, cap | += score, -= pool |
| 0x24fa0 ScoreAddForBuildings | buildings | value*others/mine (mine > others) | /2 | pool, cap | += score, -= pool |
| 0x2505c ScoreSubForMen | men | value*mine/others (others > mine) | /4 | own score | -= score, += pool |
| 0x250fc ScoreSubForBuildings | **men** (!) | value*mine/others (others > mine) | /2 | own score | -= score, += pool |
| 0x25198 ScoreOnMenKilled, self | - | - | value/2 | victim's score | -= score, pool untouched |
| 0x25198 ScoreOnMenKilled, other | killer's men | value*others/mine (mine > others) | **/8** | pool, cap | += victim's score, -= pool |
| 0x2529c ScoreOnBuildingKilled, self | - | - | **none** (full value) | victim's score | -= score, pool untouched |
| 0x2529c ScoreOnBuildingKilled, other | killer's buildings | value*others/mine (mine > others) | /4 | pool, cap | += victim's score, -= pool |

Details that matter (all verified from the disassembly and covered by the
model):

* All products are signed 32-bit `imul`, all divisions are *truncating*
  signed: the `idiv` for the ratio, and the
  `mov eax,x; mov edx,x; sar edx,31; shl edx,n; sbb eax,edx; sar eax,n`
  idiom (n = 1, 2 or 3) for the /2, /4 and /8 steps - which computes
  `trunc(x / 2^n)` for both signs (the /2 form uses `sub eax,edx` with
  `edx = x>>31` instead of the `shl`/`sbb` pair).
* The **add** pair forces `mine >= 1` then `others >= 1`.  The
  **claw-back** pair is different and asymmetric: when `mine == 0` it sets
  **others = 1** (0x25088-0x2508c writes the *others* register), and when
  `others == 0` also `others = 1` - `mine` itself is never forced, so an
  owner with no men left loses nothing (the ratio computes value*0/1).
  The **killed** pair (both branches) forces the killer's `mine` and
  `others` like the add pair.
* The clamps are signed comparisons against zero-extended 16-bit
  globals, pool first then cap for the award branches; the claw-back
  pair has no pool term (the delta is capped by the player's own score,
  and the pool gets it back).
* **0x250fc reads the MEN counters** (`call TotalActiveMen_` at 0x25102,
  `mov dx,[edx*2+0x58e28]` at 0x2510c) although its caller is the
  *buildings* accounting fn_13b4c - the original's own inconsistency
  (most likely a copy-paste in the original SCORE.C); the name keeps the
  call-site semantics.
* The killed pair's "other" branch awards the score to the *victim's*
  owner (with `score_value[victim->owner]` and the *killer's* force
  ratio) - the direction is not explained by anything in the code; both
  branches are difftested as found.

**0x24ee0** is named `ScoreAddForMen` (entry restored 2026-11-18, see
section 6).

## 4. Rank titles

`RankName` (0x255b8) walks `rank_thresholds` (0x5318c, 18 words: 200, 300,
400, 800, 1600, 2400, 3200, 4000, 4800, 5200, 5600, 6000, 6400, 6800,
7200, 9600, 11400, 11880; a 12000 entry follows but the walk stops at
offset 0x24) while `player_score[0] > threshold[i]`, and indexes the
side-specific name table: `rank_names_human` (0x531b4) for
`scenario_race` != 1, `rank_names_orc` (0x53200) for == 1:

| i | human | orc |
|---|---|---|
| 0..4 | Slave, Peasant, Squire, Footman, Corporal | Slave, Peon, Rogue, Grunt, Slasher |
| 5..9 | Sergeant, Lieutenant, Captain, Major, Knight | Sergeant, Commander, Captain, Major, Raider |
| 10..14 | General, Brigadier, Marshall, Lord, Duke | General, Master, Marshall, Slayer, Dictator |
| 15..18 | War Leader, Demigod, God, Designer | War Chief, Demigod, God, Designer |

Callers: `ScorePageScore` 0x2562f and the status line fn_2fcfc at
0x2faf8.  Difftested over both sides and the full score range
(`test_rank_name`).

## 5. The score panel

`ScoreInit` (0x25718, called from the scenario start 0x19785) loads the
72x72 panel bitmap (resource 0xe6 + side) into `score_panel_bm`
(0x5314c, rectangle `score_panel_rect` 0x53140 = {0,0,71,71,72,72}),
keeps a pristine copy via `BitmapCloneAlloc(&score_panel_clean,
&score_panel_bm)`, resets `score_page`/`score_page_shown` to 0, sets the
pool to 2500 and loads cap/rate from the level tables.
`ScoreFreePanels` (0x257dc) frees both bitmaps in the game-teardown path.

`ScoreUpdate` (0x25684, called every game loop pass from 0x197e0) calls
the page handler from `score_page_fns` (0x5324c) =
[fn_1ed2c, ScorePageMen, ScorePageHarvest, ScorePageScore] with
`page_changed = (score_page != score_page_shown)`, and repaints the panel
rectangle around ScreenUpdate.  `ScoreSetPage` (0x257f8) selects the page
(a low word of 4 wraps to 0 through the 32-bit xor, > 4 clamps to 3 -
`test_score_set_page`).

`ScorePanelText` (0x253cc) restores the panel from the clean copy
(memcpy 0x1440 = 72*72), installs `cur_bitmap = &score_panel_bm`,
`cur_font = &score_font` (0x59228), sets the colour base 0xf3 and
`text_line_gap = 1`, draws the string at (6, 6) and resets the gap.  The
three page renderers sprintf into a 0x100-byte stack buffer and call it:
page 1 (ScorePageMen 0x25428) the six unit counters, page 2
(ScorePageHarvest 0x2553c) the harvested gold/lumber dwords, page 3
(ScorePageScore 0x25600) score, rank name and the scenario name at
[0x50098].

## 6. What is byte-matched (T3) and what is a near miss

Reconstruction state, per function (`docs/METHODOLOGY.md` T3/T4):

### Built from C (T3, `src =` in the TOML)

| function | address | file |
|---|---|---|
| WordInRange | 0x2417c | `src/save_score/save.c` |
| ScoreSetUncapped | 0x257c0 | `src/save_score/score.c` |

WordInRange's source *shape* is what makes it match: each positive branch
test returns 1 in place while every failure falls or jumps to the single
shared `xor eax,eax; ret` at 0x241a1 - the inverted spelling (the
`return 0`s in the branches) makes OW2 share the *return 1* blocks
instead and misses by one byte at +0x8.
ScoreSetUncapped is dead code (no caller in the image); its compiled
object covers exactly 0x257c0..0x257d9 and the following `lea eax,[eax]`
filler stays with the asm.

### Reference C (near misses, `src/save_score/{save,score}_reference.c`)

Same logic, verified differentially (T4), but OW2 allocates one register
differently per function - the V2/V3 backend differences of
`docs/subsystems/codegen.md` section 4, which no source idiom steers
(all spellings tried are recorded in the area report):

| function | address | the remaining diff |
|---|---|---|
| TotalActiveMen / TotalActiveBuildings | 0x24e50/0x24e70 | the zero-extended word temp is ecx (original: ebx) - 5 bytes |
| ScoreTickIncome | 0x24e90 | sum in ebx / cap in ecx (original: ecx / ebx) - 6 bytes |
| BitmapCloneAlloc | 0x25390 | dst stays in ecx, src never leaves edx, size in ebx (original: dst in ebx, src saved to ecx, size in edx) - 45 bytes, ours shorter |
| ScorePanelText | 0x253cc | the final `text_line_gap = 0` zeroes edx (original: ebx) - 2 bytes |
| RankName | 0x255b8 | the table index lives in ecx (original: edx) - 50 bytes |
| ScoreSetPage | 0x257f8 | v in eax with page evicted to edx via `mov edx,eax; xor eax,eax; mov ax,dx` (original: v in edx, `xor edx,edx; mov dx,ax`, page keeps eax) - 24 bytes |
| SaveStreamValidate | 0x241a4 | +0x1 pushes edx where the original pushes ecx (the header-word temp); the single-player half is the one difftested |
| NetQueryRemoteEvent | 0x2461c | codegen (store forwarding): OW2 merges `net_msg[0]=4; net_msg[1]=1` into `mov word [net_msg],0x104` and reuses the eax=0 proved by the first poll |
| NetSendLocalEvent | 0x246b4 | same merged constant stores, plus the second poll reuses eax=0 instead of the original's `xor eax,eax` |
| NetSendDataMessage | 0x24780 | same merged empty-message stores; OW2 materialises the net_msg address with `mov eax,imm32` |
| NetRecvDataMessage | 0x247d0 | codegen: OW2 keeps `msg[1] & 0x3f` in al and compares a zero-extended eax, and stores the net_msg base as a constant dword |

T4 evidence (the compiled reference C and the original on the same
inputs under `wc1.emu`, `ref_verified_by` in the TOML):
`test_t4_score_adjusters` (the six adjusters of section 3.1, 120 random
cases each with both counter arrays, the score values, pool/cap, owner and
suppress flag varied), `test_t4_link_dialogs` (GamesDifferDialog and
EnemyDidNotLoadDialog: the screen-mode save/restore, the message arguments
and all the state words), `test_t4_total_active_sums`, `test_t4_score_tick_income`,
`test_t4_rank_name`, `test_t4_score_set_page`, `test_t4_bitmap_clone_alloc`,
`test_t4_score_panel_text`, `test_t4_save_stream_validate_single_player`,
`test_t4_net_query_remote_event`, `test_t4_net_send_local_event`,
`test_t4_net_send_data_message`, `test_t4_net_recv_data_message` in
`tests/test_save_score.py`.  They use `wc1.cemu.run_pair`: the original runs
first, the watched memory is restored, the compiled C runs with the same
arguments, and return registers plus watched memory (and, where the effect is
a call, the recorded stub arguments) must be identical.

`tests/test_save_score.py::test_reference_c_stays_a_near_miss` guards
both files: their functions must *not* match under the codegen sweep; if
one starts matching (a future toolchain), it must be promoted into
`save.c`/`score.c` with a `src =` entry.

### Difftest-only (T4, no C at all)

`NetLinkHandshake` (the identity handshake, section 2.1), `NetLinkStart`,
`NetLinkExit`, the three dialogs, `NetLoadSyncMessage`, the three page
renderers, `ScoreUpdate`, `ScoreInit`, `ScoreFreePanels` and the tail
entries 0x24ee0/0x2505c are documented from the disassembly and (where a
test exists) difftested; writing reference C for them adds little until
their callees are named.

### The formerly deferred 0x24ee0 entry

`ScoreAddForMen` (0x24ee0) is a real function - a well-formed watcall
body ending in `ret` at 0x24f9f, reached only by the *conditional* tail
jump `jg near 0x24ee0` at 0x13b33 from the men accounting fn_13b30.
From 2026-11-17 to 2026-11-18 it had no database entry: the discovery's
partition promoted tail-jump targets only for *unconditional* `jmp`, so
0x24ee0 stayed cross-flow out of fn_13b30 and a hole between the
functions 0x24e90 and 0x24fa0, while the shared pipeline tests require
every entry to sit at a discovered start.

`tools/wc1/analysis.py` now promotes conditional tail-jump targets too
(the `tails` scan accepts the COND_JUMPS mnemonics as well as `jmp`; the
fall-through guard is unchanged - 0x24ee0 passes it because its preceding
`lea eax,[eax+0]` filler at 0x24edd is *undecoded*, so no instruction
ends at 0x24ee0).  The change promotes 10 starts program-wide, all
entered only by (conditional) jumps and preceded by terminators or
undecoded filler, and the partition's own validity metric improved
(functions with crossing flow: 33 -> 29).  A tempting extension - also
accepting targets preceded by *decoded* no-op filler - was tried and
rejected: the `mov eax,eax` at 0x2c226 is reachable in-function code in
front of a mid-function spill block, and promoting 0x2c228 split the
genuine function 0x2c208.  The `ScoreAddForMen` entry (verified by the
two adjuster difftests) is in `analysis/symbols/save_score.toml`;
`test_discovery_merges_the_tail_jump_entries` pins the new partition
state for this area.

## 7. Emulator notes

The clib `memcpy` at 0x31789 begins `push ecx; push esi; push edi; mov
edi,eax; mov esi,edx; mov ecx,ebx; push es; mov eax,ds ...` - a
segmented ES:EDI copy that Unicorn cannot execute.  `wc1/emu.py` ships a
built-in flat model for it (`self.stubs.setdefault(0x31789, _memcpy)` in
`Emu.__init__`, override-able per test; guarded by
`tests/test_emu.py::test_memcpy_stub_is_builtin`); the per-test
`stub_memcpy` installs in tests/test_save_score.py predate it and are
kept as explicit overrides.  memset 0x30c50 runs fine natively.
`fn_249a4` and `fn_249c8` (mod_24860) are pure enough to run
for real under the emulator, which is what
`test_save_stream_validate_rejects_bad_header` does.
