/* codegen-flags: -s -od -4r -zp2
 * codegen-compiler: 10.0a
 * EvtPost (0x30eb8) - reference C (T4).  The body is the original: reject
 * events whose type bit is not in evt_mask (or a null event), cli, refuse
 * when the ring is full, else stamp the current mouse position into the
 * event, copy it into the ring at evt_head and advance/wrap the index; sti
 * only if the caller had interrupts enabled.
 *
 * T3 blocker (codegen): first difference at 0x30ece, 10.0a reads `ev->type` before `evt_mask`
 * (`mov eax,[ev]; mov ax,[eax]; and eax,0xffff` first, mask second) where the
 * original loads the mask into edx first; the flags/return locals are also
 * allocated in a different order (original: ev, ok, flags, ret; 10.0a: ev,
 * flags, ok, ret).  Everything else is byte-identical.  Behaviour is proved
 * by the T4 difftest (tests/test_input_evt.py::test_t4_evt_post).
 */
#include "input.h"

void memcpy(void *dst, const void *src, unsigned n);   /* 0x31789 */
void _disable(void);                                   /* 0x349b8 */
void _enable(void);                                    /* 0x349ba */

#pragma aux getflags = "pushf" "pop ax" value [ax];
short getflags(void);

/* @0x30eb8 */
int EvtPost(Event *ev)
{
    int ok;
    short flags;

    if (ev == 0 || (ev->type & evt_mask) == 0)
        return 0;
    flags = getflags();
    _disable();
    if (evt_count == evt_queue_size)
        ok = 0;
    else {
        evt_count++;
        ev->x = mouse_x;
        ev->y = mouse_y;
        memcpy(&evt_queue[evt_head], ev, sizeof(Event));
        if (++evt_head == evt_queue_size)
            evt_head = 0;
        ok = 1;
    }
    if ((unsigned)flags & 0x200)
        _enable();
    return ok;
}
