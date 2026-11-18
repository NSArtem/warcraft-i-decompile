/* codegen-flags: -s -od -4r -zp2
 * codegen-compiler: 10.0a
 * EvtGet (0x31598) - reference C (T4).  Pop the next event: the ring first,
 * then a coalesced mouse-move event (evt_move_pending), then - at most every
 * 5 clock ticks - a synthetic idle event (type 0x400) carrying the cursor
 * position.  cli/sti around it, restoring the caller's interrupt flag.
 *
 * T3 blocker (regalloc): the body is byte-identical except that 10.0a
 * allocates the `flags` local in the original's top return-value slot (the
 * original frame is out -0x14, now -0x10, flags -0xc, ok -8, ret -4; 10.0a
 * gives out -0x14, ret -0x10, now -0xc, ok -8, flags -4).  Every spelling
 * tried (declaration orders, short/int/long/volatile ok and flags, the
 * initializer moved, `now` in an inner block) leaves the same single
 * 1-byte difference at +0x1e.  Behaviour is proved by the T4 difftest
 * (tests/test_input_evt.py::test_t4_evt_get).
 */
#include "input.h"

void _disable(void);                                   /* 0x349b8 */
void _enable(void);                                    /* 0x349ba */
unsigned long clock(void);                             /* 0x30e98 */

#pragma aux getflags = "pushf" "pop ax" value [ax];
short getflags(void);

/* @0x31598 */
int EvtGet(Event *out)
{
    int ok = 1;
    short flags;
    unsigned long now;

    flags = getflags();
    _disable();
    if (evt_count == 0) {
        if (evt_move_pending) {
            *out = *evt_move_pending;
            evt_move_pending = 0;
        } else {
            now = clock();
            if (now - evt_last_idle >= 5) {
                evt_last_idle = now;
                evt_idle.x = mouse_x;
                evt_idle.y = mouse_y;
                *out = evt_idle;
            } else
                ok = 0;
        }
    } else {
        evt_count--;
        *out = evt_queue[evt_tail];
        if (++evt_tail == evt_queue_size)
            evt_tail = 0;
    }
    if ((unsigned)flags & 0x200)
        _enable();
    return ok;
}
