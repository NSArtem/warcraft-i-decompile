# mod_1dca0: IPX real-mode wrappers (0x1dca0..0x1de50)

Seven small wrappers around the IPX real-mode API, reached through the DPMI real-mode interrupt helper `fn_23e50(int_no, RealRegs *)`.

Each wrapper does the same four things:

1. It zeroes a 0x32-byte `RealRegs` block on the stack with `memset`.
2. It fills in the registers the IPX call needs.
3. It calls `fn_23e50` (0x23e50).
4. It reads results back from the block.

## RealRegs layout (0x32 bytes, DPMI real-mode call structure)

| Offset | Field |
|---|---|
| 0x00 | edi |
| 0x04 | esi |
| 0x08 | ebp |
| 0x0c | reserved |
| 0x10 | ebx |
| 0x14 | edx |
| 0x18 | ecx |
| 0x1c | eax |
| 0x20 | flags |
| 0x22 | es |
| 0x24 | ds |
| 0x26 | fs |
| 0x28 | gs |
| 0x2a | ip |
| 0x2c | cs |
| 0x2e | sp |
| 0x30 | ss |

## Functions

| Addr | Name | Behaviour |
|---|---|---|
| 0x1dca0 | IpxInstalled | Sets eax=0x7a00 and calls int 0x2f (multiplex). Returns `(al == 0xff)`. |
| 0x1dce0 | IpxOpenSocket | Sets ebx=0, edx=socket (16-bit), then calls int 0x7a. Returns the edx result (the assigned socket). |
| 0x1dd20 | IpxCloseSocket | Sets ebx=1, edx=socket, then calls int 0x7a. |
| 0x1dd5c | IpxGetInternetworkAddress | Sets es=seg, esi=off, ebx=9, then calls int 0x7a. |
| 0x1dda0 | IpxRelinquishControl | Sets ebx=10, then calls int 0x7a. |
| 0x1ddd0 | IpxListen | Sets es=seg, esi=off, ebx=4, then calls int 0x7a. |
| 0x1de14 | IpxSendPacket | Sets es=seg, esi=off, ebx=3, then calls int 0x7a. |

## T3 and T4 notes

- All seven functions only have `*_reference.c` files.
  - Every opcode matches the original.
  - The only difference is the rel32 of the `call 0x23e50`, which is an unresolved extern relocation.
  - So T3 does not report MATCH, and the near-miss guard asserts they still mismatch.
- `tests/test_mod_1dca0.py` runs a T4 differential test for each function.
  - `fn_23e50` (0x23e50) is stubbed.
  - The stub logs the interrupt number (eax) and the full 0x32-byte register block. It does not log the block's stack address.
  - The stub also writes a per-case result into the block (eax at +0x1c, edx at +0x14).
  - The original and the compiled C are compared on the log, the return value and the result handling.
