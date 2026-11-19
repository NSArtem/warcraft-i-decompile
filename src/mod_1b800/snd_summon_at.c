/* codegen-compiler: 10.0a */
/* codegen-compiler: 10.0a */
/* mod_1b800.  SndSummonAt 0x1bee4: the on-screen spell cue (id 0x2c) at a
 * pixel position.  Called by the bullet creator 0x11e70 and 0x278ac.  See
 * docs/subsystems/mod_1b800.md. */
#include "mod_1b800.h"

/* @0x1bee4 */
void SndSummonAt(int px, int py)
{
    px = px / 16;
    py = py / 16;
    if (px >= map_scroll_x && py >= map_scroll_y &&
        px <= map_scroll_x + 15 && py <= map_scroll_y + 11)
        SndEvent(0x2c, 0);
}
