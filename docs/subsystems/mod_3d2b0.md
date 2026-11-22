# Critical-error dialog button drawing (`mod_3d2b0`)

| Address | Function | Evidence and confidence |
| --- | --- | --- |
| `0x3d2b0` | `CritErrDrawButtons` | High: called by `CritErrInitDialog` (`0x337d0`); blits each button at `0x3d2e9`, selects the text color at `0x3d32b`–`0x3d33d`, and draws the label at `0x3d350`. |

The Watcom register inputs are the selected index (`AX`, compared via `DI` at `0x3d32b`), the button-array pointer (`EDX`, copied to `ECX` at `0x3d2cc`), the normal color (`BL`), and the selected color (`CL`). The color bytes are saved at `0x3d2ba`–`0x3d2bd`.

## Data layout and behavior

- `default_font` (`0x55444`) and `cur_font` (`0x5acf0`) are 32-bit font pointers: `0x3d2c0`–`0x3d2c5` copies the default to the current font before even testing the first record. `0x3d2fa`–`0x3d2ff` passes the default to `TextWidth`.
- Each button record is `0x14` bytes (`0x3d356`). Offset `+0x00` is the label pointer (`0x3d2ee`); null skips text but still counts toward the selected index (`0x3d2f2`, `0x3d355`). Offset `+0x04` is the bitmap pointer; null ends the array (`0x3d2ce`, `0x3d359`). The routine does not establish a meaning for bytes `+0x08`–`+0x0b`.
- Signed 16-bit bitmap coordinates are at `+0x0c` and `+0x0e` (`0x3d2dd`–`0x3d2e9`). For labeled records, the signed bitmap width at offset zero and the signed low word of `TextWidth` feed the calculation at `0x3d2f4`–`0x3d31c`: `label_x = x + (bitmap_width - text_width) / 2`, with division truncating toward zero. The routine stores `label_x` at `+0x10` and `y + 3` at `+0x12` as words (`0x3d31c`, `0x3d327`), then passes both as sign-extended coordinates to `DrawText` (`0x3d344`–`0x3d350`).

## T3 / T4

There are no T3-matched sources in this module. The reference near-miss guard preserves the known register-allocation mismatch: the original first sentinel comparison at `0x3d2ce` uses `[ecx+4]`, while the reference uses `[edx+4]`. The T4 test compares the current-font pointer, the full button buffer, and the order and arguments of the four drawing-related calls. Cases cover an immediate sentinel, an unlabeled button, selected and normal colors, signed width arithmetic, and coordinate wrap. The tests require the original executable and `$WATCOM`; they were not run for this handoff.
