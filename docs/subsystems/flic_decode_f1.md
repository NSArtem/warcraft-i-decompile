# FLIC chunk decoding

This part of `flic_decode` (`0x19020..0x19470`) reads frame and chunk records, then updates the image or palette. The two reference functions below are tested independently; the chunk test stubs the palette decoder, and the palette test executes it directly.

| Entry | Role and disassembly evidence | Test status |
|---|---|---|
| `0x19020` `FlicReadBytes` | At `0x19177..0x19189` the dispatcher passes a destination in EAX and a six-byte count in EDX, then tests AX. Raw rows use the same call at `0x192a8`. | T3 match guard |
| `0x19048` `FlicSeek` | Type `0x12` passes the full dword chunk size minus six in EAX and `1` in EDX at `0x192cf..0x192dc`. The dispatcher returns one afterward. | T3 match guard |
| `0x19064` `FlicDecodePaletteChunk` | Reads the payload using the low 16 bits of size minus six (`0x19070..0x19090`). Packet decoding adds the skip to the running index and treats count zero as 256 (`0x190aa..0x190bb`). It shifts each RGB component right by two (`0x190c4..0x190ec`), copies the inclusive configured range (`0x1910b..0x1913d`), and conditionally calls the cdecl VGA upload for all 256 entries (`0x1913f..0x1915a`). | T4 reference; original frame allocation is `0x304` at `0x1906a`, reference emits `0x308`. |
| `0x19174` `FlicDecodeChunk` | Reads a six-byte header at `0x19181`. Type 4 calls the palette decoder (`0x191e8`); 7 calls `0x10312` with width in EBX (`0x19237..0x1924b`); 12 calls sparse RLE (`0x19215`); 15 calls RLE with height in EBX and width in ECX (`0x1926d..0x1928a`). Type 16 reads width bytes per row at a `0x140` pitch (`0x1929d..0x192c4`); type 18 seeks. Unsupported types return zero at `0x192ea`. | T4 reference; the dossier reports a call-target mismatch at the type-7 decoder call (`0x1924b`). |
| `0x192f0` `FlicDecodeFrame` | Reads a 16-byte frame header (`0x192f6`), checks its magic (`0x1930d`), and uses the header chunk count as the loop bound (`0x19329`). | T3 match guard |

## Data layouts

- Chunk header at `0x594e4`: little-endian dword size (including the six-byte header), then a word type (`0x1917c`, `0x1918f`, `0x192cf`). Frame header at `0x594c0`: dword size, word magic, word chunk count, then eight reserved bytes (16-byte read at `0x192f6`, field uses at `0x1930d` and `0x19329`).
- Image and payload buffer pointers at `0x594d4` and `0x594d8` are loaded together at `0x1920a..0x19210`. Width and height are words at `0x59448` and `0x5944a`, read by the raw row loop at `0x1929f` and `0x192bb`.
- Palette payload: word packet count (`0x19099`), then byte skip, byte count, and RGB triples per packet (`0x190aa..0x190f0`). The destination at `0x58f20` holds 256 RGB triples (`0x1912b..0x19136`, `0x19149`). Dwords at `0x594d0` and `0x594dc` select the inclusive copy range (`0x1910b..0x19119`); the word at `0x594ea` gates upload, not the copy (`0x1913f`). Valid palette fixtures only copy entries initialized by their packets.

## Test scope

`tests/test_flic_decode_f1.py` compares return registers, watched memory, and stub call logs. It exercises palette skips, full-palette packets and upload gating, plus chunk dispatch, read failures, low-word payload lengths, full-dword seek offsets, and raw row pitch. The near-miss guard requires both reference files to remain nonmatching under T3. These tests require the installed original and `$WATCOM`; no execution result is claimed here.
