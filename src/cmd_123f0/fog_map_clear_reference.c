/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -oa -4r -zp2 */
/* CMD.C 0x12404 - see docs/subsystems/cmd_123f0.md and analysis/symbols/cmd_123f0.toml.
 * T3 under Watcom 10.0a (built, `src =`); recovered by wc1.wave4 (2026-11-23) from the
 * former OW2 reference C: declaring `i` first and `p` as `register` gives the
 * original's register roles (fog_map in eax, counter in edx).  The file name is kept:
 * the T4 difftest still loads it.  Under OW2 the original's pre-tested loop with a
 * duplicated exit epilogue and *promoted* `unsigned short` counter compare
 * (`xor ebx,ebx; mov bx,dx; cmp ebx,0x1000; jl`) is narrowed to `cmp dx,0x1000; jb`
 * - codegen.md V4/V5/V10 cite this very function.
 * One function per object: wcc386 aligns each following function to 16 bytes, which
 * would otherwise put the neighbour's padding into the extent wc1.match compares. */
#include "cmd_123f0.h"
/* @0x12404 - no reference to it anywhere in v1.22h */
void FogMapClear(void)
{
    unsigned short i;
    register unsigned short *p = fog_map;

    for (i = 0; i < 0x1000; i++)
        *p++ = 0;
}
