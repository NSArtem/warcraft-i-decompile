/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* CMD.C 0x12800 - see docs/subsystems/cmd_123f0.md and analysis/symbols/cmd_123f0.toml.
 * Built from C: T3 under Watcom 10.0a (codegen-compiler).  Under OW2 it was reference C: the same loop, `_rotl` call and
 * raw-terminator return; 70 bytes against the original 73 with 22 of them
 * different, because OW2 keeps the input pointer in ecx and the rotating key in
 * ebx (the original the other way round) and duplicates the tail instead of
 * falling into it - codegen.md V3/V10.
 * One function per object: wcc386 aligns each following function to 16 bytes, which
 * would otherwise put the neighbour's padding into the extent wc1.match compares. */
#include "cmd_123f0.h"
unsigned long _rotl(unsigned long value, unsigned shift);

/* @0x12800 */
int CheatCodeMatch(char *text, char *code)
{
    unsigned long key = 0x01010101;

    while (*text) {
        if ((unsigned char)*text++ != ((unsigned char)*code++ ^ (unsigned char)key))
            return 1;
        key = _rotl(key, 1);
    }
    return (unsigned char)*code;
}
