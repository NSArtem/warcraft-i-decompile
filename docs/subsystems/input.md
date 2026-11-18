# Input subsystem (war.exe 1.22h)

The event queue, keyboard IRQ1 handler and INT 33h mouse callback of
`gfx_evt_vid` (0x30ea0..0x31784, analysis/modules.toml).  Names, addresses and
evidence are in `analysis/symbols/input.toml`; this page records the layout
and the reconstruction notes.

Everything here is "OD" codegen (`-s -od -4r -zp2`, docs/subsystems/codegen.md)
and is reproduced by Watcom 10.0a.

## 1. The event record and the state block

One event is 12 bytes (`Event` in `src/include/input.h`):

| offset | type | meaning |
|---|---|---|
| +0 | word | type: 1 move, 2 L-press, 4 L-release, 8 R-press, 0x10 R-release, 0x80 key-down, 0x100 key-up, 0x400 idle/tick |
| +2 | word | sub-code (move 3, button 4..7, idle 8, key 0 down / 2 up) |
| +4 | word | x (stamped by EvtPost from `mouse_x`) |
| +6 | word | y (stamped by EvtPost from `mouse_y`) |
| +8 | byte | scancode (keyboard events) |
| +9 | byte | modifier bits, filled by EvtProcess (outside this area) |
| +0xa | word | translated key (ascii in the low byte or scancode<<8) |

EvtInit memsets and DPMI-locks **one** state block, 0x5a880..0x5aa5e
(0x1df bytes, `EVT_STATE_SIZE`).  Inside it, in address order:

* 0x5a880 `evt_key` - the keyboard template (type/sub/scan written by
  KeyboardISR);
* 0x5a88c `evt_move` - type 1 / sub 3; MouseCallback fills +4/+6 from the
  cursor and publishes the address in `evt_move_pending`;
* 0x5a898 `evt_button` - the (type, sub) template MouseButtonEvent fills;
* 0x5a8a4 `evt_idle` - type 0x400 / sub 8; EvtGet fills +4/+6 when the idle
  gate opens;
* 0x5a8b0/0x5a8b2 `mouse_raw_x`/`mouse_raw_y` - the driver's clamped position;
* 0x5a8b4 `evt_mask` - accepted type bits;
* 0x5a8ba `evt_move_pending` - `Event *`, the coalescing slot for move events;
* 0x5a8be `evt_queue` - `Event *` (GdsAlloc'd ring), 0x5a8c2 `evt_tail`,
  0x5a8c4 `evt_head`, 0x5a8c6 `evt_queue_size`, 0x5a8c8 `evt_count` (volatile);
* 0x5a8ca/0x5a8cc `mouse_x`/`mouse_y` - where the cursor layer draws;
* 0x5a8d4 `key_down_table[128]` - the typematic filter (word per scancode);
* 0x5a9d5 `kbd_e0_prefix`, 0x5a9d7 `kbd_e1_count` (volatile),
  0x5a9be `kbd_pause_flag` (read only), 0x5a9d9 `old_int9` (far pointer:
  dword offset at +0, word segment at +4);
* 0x5a9df `scancode_fixup_table[0x80]` - the copy of 0x553b4 that the ISR
  indexes for 0xE0-prefixed codes.  The source table remaps the extended
  scancodes into 0x70..0x7f (keypad Enter 0x1C→0x70, right Ctrl 0x1D→0x71,
  keypad / 0x35→0x72, PrintScreen 0x37→0x73, right Alt 0x38→0x74, the
  Home/arrow/Ins/Del/Page group 0x47..0x53→0x76..0x7f), so an extended key
  never collides with a plain one.

`EvtInit(0x20)` (`EvtStartup` 0x34260, called from 0x1da34) allocates the ring
of 0x20 events and locks the block and the ISR code.  `evt_last_idle` (0x55434)
sits outside the block: it is the clock tick of the last synthetic 0x400 event.

## 2. Producers

* **KeyboardISR** (0x31104) - IRQ1.  `inp(0x60)`; 0xE0 sets `kbd_e0_prefix`
  and the next byte is remapped through `scancode_fixup_table` (the 0x80 bit
  is preserved); 0xE1 starts the 6-byte pause sequence counted by
  `kbd_e1_count`, whose completion posts scancode 0x75 (or 0xF5 when the
  never-written `kbd_pause_flag` is set).  A break byte (bit 7) posts type
  0x100/sub 2 and clears `key_down_table[scan]`; a make byte posts
  0x80/sub 0 only when the table entry was clear (typematic filter), else the
  event is dropped.  `evt_key.scan` is always written before EvtPost.  The
  controller is acknowledged by pulsing port 0x61 bit 7 (read, or 0x80, out;
  read, and 0x7F, out) and the PIC with `outp(0x20, 0x20)`.
* **MouseCallback** (0x30fe0) - the INT 33h user callback, installed by
  EvtInitMouse with mask 0x1F.  The driver passes the condition mask in EAX,
  x in ECX and y in EDX with a far call: the source uses
  `#pragma aux MouseCallback parm [eax] [ecx] [edx]`, `__far` and `__loadds`
  (the DS reload shows as `push ds; call __GETDS` / `pop ds; retf`).  x is
  the driver's 640-wide coordinate, halved (`sar`) and clamped to 0..0x13F,
  y clamped to 0..0xC7; the result goes to `mouse_raw_x/y`.  Bit 0 with
  `evt_mask & 1` fills `evt_move` and sets `evt_move_pending`; bits 1..4 call
  MouseButtonEvent with (2,4) (4,5) (8,6) (0x10,7).  The first parameter must
  be `volatile`: the original tests it with the 7-byte
  `test dword [ebp-0xc],1`.
* **MouseButtonEvent** (0x30fa8) - fills `evt_button` and posts it.
* **EvtPost** (0x30eb8) - the queue insert: reject when `ev == 0` or
  `(ev->type & evt_mask) == 0`, `cli`, drop when `evt_count ==
  evt_queue_size`, else `evt_count++`, stamp `mouse_x/y` into +4/+6,
  `memcpy(&evt_queue[evt_head], ev, 12)`, advance and wrap `evt_head`, `sti`
  only if the caller's IF was set (`pushf; pop ax` → `test ah,2`).

## 3. Consumer

`EvtGet` (0x31598) pops the ring, then (if empty) the coalesced move event,
then - when `clock() - evt_last_idle >= 5` - a synthetic 0x400 idle event with
the current cursor position, else returns 0.  `evt_last_idle` is updated only
when an idle event is emitted.  cli/sti as in EvtPost.  `EvtPump` (0x31568)
drains it into EvtProcess (0x32b40, another area).

## 4. DPMI locking

`DpmiLockRegion` (0x312f0) / `DpmiUnlockRegion` (0x31360) wrap `int 31h`
ax=600h/601h (bx:cx = linear address, si:di = size) through the Watcom
`int386` library call; a set carry is fatal ("evt lock" 0x57e54 / "evt unlock"
0x57e60).  The register block is filled through the **word** view
(`r.w.ax/bx/cx/si/di` → word stores at the DWORDREGS offsets
+0/+4/+8/+0x10/+0x14); the address is latched in one local declared before the
union so the frame is REGS, size, addr, lin.  The two DPMI-locked regions are
the state block (0x5a880, 0x1df) and the ISR code
`[IsrRegionStart, IsrRegionEnd]`, locked with the size
`IsrRegionEnd - IsrRegionStart + 1`; the +1 includes the end marker's first
byte.  `fn_1f854` locks its own code the same way (0x202bc), which is the
strongest evidence that the two empty functions are marker pairs.

## 5. Keyboard vector

`EvtHookKeyboard` (0x313d0) uses int 21h ax=3509h/2509h with `segread` +
`int386x`; the saved vector is a single far pointer at 0x5a9d9
(`old_int9 = MK_FP(s.es, r.x.ebx)`), which is why the original evaluates BX
and ES before writing the segment and the offset.  The install side writes
`r.x.edx = FP_OFF(KeyboardISR)` (a dword store; the source uses the `.x` view
here and `.w` for the ax function number) and `s.ds = FP_SEG(KeyboardISR)`.
`EvtUnhookKeyboard` (0x31450) restores it and is registered as an exit
handler by EvtStartup.  EvtInitMouse (0x314a4) is the same pattern with
`MouseCallback` and returns 0 when the reset does not report a driver
(ax != 0xFFFF).

## 6. Per-function reconstruction status

`T3` = byte-identical under Watcom 10.0a (`wc1.match`); `T4` = reference C
with a difftest against the original.  The T3 entries carry
`verified_by = "match: ..."` but no `src =` yet: the matched files are listed
here (and in `tests/test_input_evt.py::MATCHED`) for the session owner to wire
into the build, which `src =` would change.

| function | addr | status | file |
|---|---|---|---|
| IsrRegionStart | 0x30ea0 | T3 | `isr_region_start.c` |
| IsrRegionEnd | 0x312d8 | T3 | `isr_region_end.c` |
| EvtPost | 0x30eb8 | T4 | `evt_post_reference.c` |
| MouseButtonEvent | 0x30fa8 | T3 | `mouse_button_event.c` |
| MouseCallback | 0x30fe0 | T3 | `mouse_callback.c` |
| KeyboardISR | 0x31104 | T3 | `keyboard_isr.c` |
| DpmiLockRegion | 0x312f0 | T3 | `dpmi_lock_region.c` |
| DpmiUnlockRegion | 0x31360 | T3 | `dpmi_unlock_region.c` |
| EvtHookKeyboard | 0x313d0 | T3 | `evt_keyboard_vector.c` |
| EvtUnhookKeyboard | 0x31450 | T3 | `evt_keyboard_vector.c` |
| EvtInitMouse | 0x314a4 | T3 | `evt_init_mouse.c` |
| EvtShutdownMouse | 0x31538 | T3 | `evt_shutdown_mouse.c` |
| EvtPump | 0x31568 | T3 | `evt_pump.c` |
| EvtGet | 0x31598 | T4 | `evt_get_reference.c` |
| EvtInit | 0x316a0 | T3 | `evt_init.c` |
| EvtShutdown | 0x31764 | T3 | `evt_shutdown.c` |

Source idioms that the OD match depends on (each one is the difference
between MATCH and a near miss):

* `post` is a **short** (`cmp word [post],0` vs the dword stores of 0/1);
  `ok`, `now` and the Dpmi locals are ints.
* two event-state words are **volatile**: `evt_count` and `kbd_e1_count`
  (declared in `src/include/input.h`).  `evt_count++` on a volatile word leaves the
  original's dead `mov ax,[x]` load in front of `inc word [x]`; `++x` does
  not, which tells the two KeyboardISR increments apart.
* KeyboardISR's two "no event" branches jump **past** the `if (post)` test
  (an explicit `goto ack` in the source); without it 10.0a jumps to the test.
* the flag capture is a `#pragma aux` function
  (`"pushf" "pop ax" value [ax]`, `short` return) and the test is
  `(unsigned)flags & 0x200` - that gives the original's
  `movsx eax,word [flags]; test ah,2`; a plain `flags & 0x200` gives the
  `and eax,0x200; cwde` form.
* `__interrupt` reproduces the KeyboardISR prologue/epilogue exactly
  (pushal, ds/es/fs/gs, `cld`, `__GETDS`, iretd).
* `__far __loadds` + `parm [eax] [ecx] [edx]` reproduce MouseCallback.
* inter-function names without a leading underscore (KeyboardISR,
  MouseCallback) need `#pragma aux <name> "<name>"`; the TOML has
  `conv = "asm"` for both.

## 7. Open items (T3 blockers)

* **EvtPost 0x30eb8** (`codegen`): 10.0a evaluates `ev->type` before
  `evt_mask` (`mov eax,[ev]; mov ax,[eax]; and eax,0xffff`, then
  `xor eax,eax; mov ax,[evt_mask]`), the original loads the mask into edx
  first.  The flags/return locals also land in a different order (original
  ev, ok, flags, ret; 10.0a ev, flags, ok, ret).  Tried: both operand orders,
  `unsigned`/`unsigned short` casts, volatile mask, `!`/`!= 0` spellings,
  separate `if`s, every declaration order, `short`/`int` ok and flags - the
  evaluation order does not move.
* **EvtGet 0x31598** (`regalloc`): only the stack-slot allocation of the
  `flags` local differs - the original frame is out -0x14, now -0x10,
  flags -0xc, ok -8, return -4; 10.0a produces out -0x14, ret -0x10,
  now -0xc, ok -8, flags -4.  Every declaration order and every
  short/int/long/volatile combination tried leaves the same one-byte
  difference at +0x1e.
* Both are T4 with difftests (`tests/test_input_evt.py::test_t4_evt_post`,
  `::test_t4_evt_get`); a compiler-configuration difference (Watcom 10.0 vs
  10.0a) would explain both, but only 10.0a is available.
