# mod_32a80_c: keyboard event / modifier processing

Module `mod_32a80` (area `mod_32a80_c`) turns raw key events into a modifier mask and a character code.

## Functions

| Function | Address | Status |
|---|---|---|
| KeyModClear(mask) | in the 0x32a80 range | T3 |
| KeyModSet(mask) | in the 0x32a80 range | T3 |
| KeyModToggle(mask) | in the 0x32a80 range | T3 |
| EvtProcess(ev) | 0x32b40 | reference only. Blocker: od-frame. The original has `jbe +0x1cc` at 0x32cbf. The reconstruction has `jbe +0x1c0`, so the code size differs. |

## Event layout

- `+0` u16 type. `0x80` is key down and `0x100` is key up. The mask `0x380` filters event types.
- `+8` u8 key (scancode).
- `+9` u8 mods.
- `+10` u16 ch. The low byte is the ASCII code and the high byte is the modifier or scan byte.

## Modifier bits (`key_modifiers`)

- `1`: right shift (scancode 0x36).
- `2`: left shift (0x2a).
- `4`: ctrl (0x1d, 0x71).
- `8`: alt (0x38, 0x74).
- `0x10`: scroll lock (0x46), toggled.
- `0x20`: num lock (0x45), toggled.
- `0x40`: caps lock (0x3a), toggled.
- `0x80`: insert (0x52, 0x7e), toggled.

Ctrl and alt are released only when the paired key state words (`dat_5a90e`/`dat_5a9b6` and `dat_5a944`/`dat_5a9bc`) are both zero.

## Character translation

- If ctrl or alt is held (`key_modifiers & 0xc`), the high byte is the modifier mask and the low byte is the scancode.
- Otherwise the low byte comes from `key_ascii_table`.
  - If the entry is 0, the keypad table is used for keys 0x47-0x53 when num lock is on. Otherwise the result is a scan-only code.
  - Letters a-z are uppercased when shift or caps is active (`key_modifiers & 0x43`).
  - Other keys use `key_shifted_table` when shift is held.

## Tests

- T3: `KeyModClear`, `KeyModSet` and `KeyModToggle` are matched files.
- Near-miss guard: `evt_process_reference.c` must still fail to match.
- T4 difftest: `test_evt_process` runs the reference against the original across event types and keys. The callees are stubbed and their logged calls are compared.
