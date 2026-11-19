/* codegen-compiler: 10.0a */
/* mod_1b800 (reference C, not T3).  SndEvent 0x1b800: play sound slot id-1 for a
 * unit (only when it is on screen and not hidden/flagged) or, with the sound
 * effects off, show the event's caption in the message strip.
 *
 * T3 blocker (regalloc): the original reads the unit's tile as dword loads at
 * +8/+0xa (sar 16) into edx (x) and edi (y) with the scroll words in esi and ecx
 * (`xor esi,esi; mov si,[map_scroll_x]`); every spelling tried (direct
 * compares, locals for x/y/scroll, one combined condition, reordered
 * conditions, the caption lookup through a pointer local) allocates x to edi and
 * scroll_x to edx (`mov dx,[map_scroll_x]`, reusing the zero upper half) and
 * indexes the caption table with a scaled address instead of the original's
 * `shl eax,2; mov ebx,[eax+0x52028]`.  First difference at +0x19.
 * See docs/subsystems/mod_1b800.md. */
#include "mod_1b800.h"

/* The unit's tile as the original reads it: a dword load at the field - 2,
 * shifted down (code generation only). */
#define TILE_X(u) (*(int *)((char *)&(u)->tx - 2) >> 16)
#define TILE_Y(u) (*(int *)((char *)&(u)->ty - 2) >> 16)

/* @0x1b800 */
void SndEvent(unsigned short id, Unit *u)
{
    if (id == 0x1b)
        u = 0;
    if (id == 0)
        return;
    id--;
    if (opt_sfx_volume != 0) {
        if (u != 0) {
            if (u->flags.w & 0x8)
                return;
            if (u->flags2 & 0x100)
                return;
            if (TILE_X(u) < map_scroll_x || TILE_Y(u) < map_scroll_y)
                return;
            if (TILE_X(u) > map_scroll_x + 15 || TILE_Y(u) > map_scroll_y + 11)
                return;
            if (u->flags.w & 0x4000)
                return;
        }
        SndPlay(id);
    } else {
        const char *text = snd_event_caption[id];

        if (text != 0)
            fn_19edc(text, 0, 0x24);
    }
}
