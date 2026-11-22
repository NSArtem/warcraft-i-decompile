# dos_realmode_mem_f1

DPMI real-mode memory and interrupt helpers (0x23d10..0x23e50).

| Addr | Name | Notes |
|---|---|---|
| 0x23d10 | RealModeAlloc | allocates a RealModeBlock (GdsAlloc), DPMI AX=0100h |
| 0x23d88 | RealModeResize | DPMI resize |
| 0x23dd8 | RealModeFree | frees block |
| 0x23e10 | RealModeGetVector | DPMI AX=0200h via int386(0x31): memset 0x1c-byte REGS, ax=0x200, bl=intno. Returns eax=word at +0xc (dx), edx=dword at +8 (ecx). |
| 0x23e50 | RealModeInt | simulate real-mode interrupt |

## Data layouts
RealModeBlock (10 bytes): err +0, sel4 +4, sel +6, seg +8.

## Tests
- T3: alloc/free/int/resize C files match.
- RealModeGetVector reference is a near-miss: the original pushes ebx/ecx and uses
  a 0x1c-byte stack REGS. The reference differs (extra push ebx at +0x0).
  The T4 difftest runs it against the original with memset and int386
  stubs, comparing eax, edx and the logged calls.
