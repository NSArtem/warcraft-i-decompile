/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* CMD.C 0x123f0 - see docs/subsystems/cmd_123f0.md and
 * analysis/symbols/cmd_123f0.toml.  One function per object: wcc386 aligns
 * every following function to 16 bytes, so a multi-function file would make
 * wc1.match compare trailing filler against the *next* original function. */
#include "cmd_123f0.h"

/* @0x123f0 */
void MapViewInitLimits(void)
{
    map_scroll_x_max = 0x31;            /* 64 tiles - 15 visible columns */
    map_scroll_y_max = 0x35;            /* 64 tiles - 11 visible rows    */
}
