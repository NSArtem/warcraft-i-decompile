# Input subsystem (war.exe 1.22h)

Evidence is in `analysis/symbols/input.toml`.

* `EvtStartup` (0x34260): registers exit handlers, `EvtInit(0x20)` (ring of 12-byte events),
  `EvtHookKeyboard` (DOS 25h/35h on vector 9), `EvtInitMouse` (INT 33h reset, callback mask 0x1f).
* Keyboard: `KeyboardISR` (0x31104) reads port 0x60, handles E0/E1 prefixes, filters typematic repeats
  with `key_down_table`, acknowledges via port 0x61 and 0x20, posts type 0x80 (down) / 0x100 (up).
* Mouse: `MouseCallback` (0x30fe0, far return) halves x (driver is 640 wide), clamps to 320x200 and
  posts move/button events (types 1,2,4,8,0x10). Move events are coalesced in a pending slot.
* Consumers: `EvtGet` (0x31598) returns queued events, then the pending move, then a 0x400 idle event;
  `EvtProcess` (0x32b40) maintains `key_modifiers` and translates scancodes to ASCII.
* ISR code/data (0x30ea0..0x312d8, 0x5a880..+0x1df) are DPMI-locked with `DpmiLockRegion`.
* Timer ISR / PIT code at 0x3846e belongs to the AIL library (audio area).
