/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* CMD.C 0x12b50 - see docs/subsystems/cmd_123f0.md and analysis/symbols/cmd_123f0.toml.
 * Built from C: T3 under Watcom 10.0a (codegen-compiler).  Under OW2 it was reference C: 45/45 bytes with only two exchanged
 * registers - the original keeps the text in ebx and the flag pointer in ecx, OW2 the
 * other way round (5 different bytes) - codegen.md V3.
 * One function per object: wcc386 aligns each following function to 16 bytes, which
 * would otherwise put the neighbour's padding into the extent wc1.match compares. */
#include <string.h>

#include "cmd_123f0.h"
/* @0x12b50 */
short CmdProcessText(char *text, unsigned char *flags)
{
    strlwr(text);
    if (CheatCodeCommand(text, flags))
        return 1;
    if (CheatScenarioCommand(text, flags))
        return 1;
    return 0;
}
