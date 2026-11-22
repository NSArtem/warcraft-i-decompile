# Startup (`INIT.C`)

## Function inventory

| Function or source group | Role and test coverage |
| --- | --- |
| `PrintExitBanner` (`0x1d854`) | Tests the status byte in `AL` at `0x1d85a`; nonzero skips the banner. Reference-only, with a T4 differential test. |
| `parse_startup_option.c`, `process_command_line.c`, `print_usage_and_exit.c` | Command-line and usage sources in the T3 regression set. |
| `load_config_file.c`, `load_modem_settings.c`, `load_preferences.c` | Configuration-loading sources in the T3 regression set. |
| `save_file_in_exe_dir.c`, `save_modem_settings.c`, `save_preferences_on_exit.c` | Settings and file-output sources in the T3 regression set. |

The dossier supplies instruction-level evidence for `PrintExitBanner`; the remaining rows are the supplied source inventory, not address or ABI identifications.

## Banner and stream layout

| Address | Layout and evidence |
| --- | --- |
| `0x18260` | Banner byte sequence loaded at `0x1d862`. The loop stops at NUL (`0x1d878`) or the exclusive `NoOp_` address (`0x1d95f`). |
| `0x583d4` | `_IsTable`, a byte classification table. `0x1d8f3–0x1d909` tests bit `0x08` at the wrapped byte index `(c + 1) & 0xff`. The `@` marker bypasses classification and becomes newline (`0x1d88e`, `0x1d8a6`). |
| `0x555de` | Stream base and dword output cursor at offset `+0x00`; `0x1d927–0x1d92d` loads the cursor and stores through it. Calls pass the stream base itself in `EDX` (`0x1d91b`). |
| `0x555e2`, `0x555f2` | Dword used count (`+0x04`) and buffer size (`+0x14`). `0x1d880–0x1d88c` subtracts used from size; the `ja` at `0x1d919` selects inline buffering only when unsigned room exceeds one and flag `0x04` is clear. |
| `0x555eb` | Stream flag byte (`+0x0d`): `0x04` forces delegation to `fputc` (`0x1d911–0x1d914`); successful inline non-newline writes set `0x10` and advance the used count and cursor (`0x1d945–0x1d959`). |

The final newline path begins at `0x1d96b`. With inline space it stores the newline through the cursor before calling `fputc` (`0x1d995–0x1d9ae`); otherwise it calls directly (`0x1d984–0x1d98e`). Neither path normally advances the cursor inline for the newline.

## Regression checks

The T3 check covers the nine listed sources. A separate near-miss guard requires `print_exit_banner_reference.c` to remain unmatched: the reported prologue difference is original `push edi` at `0x1d858` versus reference `push ebp` at `+0x4`.

The T4 test compares the stream bytes, scratch output buffer, and ordered two-argument `fputc` calls at `0x33f90`. It exercises the shipped banner and controlled data prefixes to cover classification, `@`, newlines, and buffer thresholds. The stub records the output boundary but does not model libc flushing or DOS I/O. These checks have not been run here.
