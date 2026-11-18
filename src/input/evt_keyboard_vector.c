/* codegen-flags: -s -od -4r -zp2
 * codegen-compiler: 10.0a
 * EvtHookKeyboard (0x313d0): save the IRQ1 vector with int 21h ax=3509h
 * (ES:BX) and install KeyboardISR with ax=2509h (DS:DX).  EvtUnhookKeyboard
 * (0x31450) puts the saved vector back; EvtStartup registers it as an exit
 * handler.
 */
#include <i86.h>

#include "input.h"

/* the interrupt handler is hand-written (iret, no underscore in its asm
 * name: analysis/symbols/input.toml conv = "asm") */
void __far KeyboardISR(void);
#pragma aux KeyboardISR "KeyboardISR"

/* @0x313d0 */
void EvtHookKeyboard(void)
{
    union REGS r;
    struct SREGS s;

    segread(&s);
    r.w.ax = 0x3509;
    int386x(0x21, &r, &r, &s);
    old_int9 = MK_FP(s.es, r.x.ebx);
    r.w.ax = 0x2509;
    r.x.edx = FP_OFF(KeyboardISR);
    s.ds = FP_SEG(KeyboardISR);
    int386x(0x21, &r, &r, &s);
}

/* @0x31450 */
void EvtUnhookKeyboard(void)
{
    union REGS r;
    struct SREGS s;

    segread(&s);
    r.w.ax = 0x2509;
    r.x.edx = FP_OFF(old_int9);
    s.ds = FP_SEG(old_int9);
    int386x(0x21, &r, &r, &s);
}
