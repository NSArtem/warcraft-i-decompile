/* codegen-flags: -s -od -4r -zp2
 * codegen-compiler: 10.0a
 * MouseCallback (0x30fe0): the INT 33h user callback (mask in AX, x in CX,
 * y in DX, far return).  Halves and clamps the driver's 640-wide position to
 * the 320x200 screen, then posts the move (coalesced into evt_move) and the
 * four button events (types 2/4/8/0x10 with sub-codes 4/5/6/7).
 */
#include "input.h"

/* The driver calls this with AX = condition mask, CX = x, DX = y and a far
 * call; the pragma fixes that convention (which is why the prologue reloads
 * DS and the epilogue is `pop ds; retf`). */
void __far __loadds MouseCallback(volatile int cond, int x, int y);
#pragma aux MouseCallback "MouseCallback" parm [eax] [ecx] [edx]

/* @0x30fe0 */
void __far __loadds MouseCallback(volatile int cond, int x, int y)
{
    x = x / 2;
    if (x < 0)
        x = 0;
    else if (x > 0x13f)
        x = 0x13f;
    if (y < 0)
        y = 0;
    else if (y > 0xc7)
        y = 0xc7;
    mouse_raw_x = x;
    mouse_raw_y = y;
    if ((cond & 1) && (evt_mask & 1)) {
        evt_move.x = mouse_x;
        evt_move.y = mouse_y;
        evt_move_pending = &evt_move;
    }
    if (cond & 2)
        MouseButtonEvent(2, 4);
    if (cond & 4)
        MouseButtonEvent(4, 5);
    if (cond & 8)
        MouseButtonEvent(8, 6);
    if (cond & 0x10)
        MouseButtonEvent(0x10, 7);
}
