/* codegen-flags: -s -od -4r -zp2
 * codegen-compiler: 10.0a
 * KeyboardISR (0x31104): the IRQ1 handler (installed by EvtHookKeyboard with
 * DOS int 21h ax=2509h).  Watcom's __interrupt convention reproduces the
 * pushal / ds,es,fs,gs / `cld` / __GETDS prologue and the iretd epilogue.
 *
 * Reads the scancode from port 0x60, folds the 0xE0 prefix through
 * scancode_fixup_table and swallows the 6-byte 0xE1 pause sequence, posts
 * type 0x80 (make) / 0x100 (break) key events through EvtPost with the
 * key_down_table typematic filter, then acknowledges the controller
 * (port 0x61 bit 7 pulse) and the PIC (port 0x20).
 */
#include "input.h"

/* the handler is referenced by name from the vector table (conv = asm) */
#pragma aux KeyboardISR "KeyboardISR"

unsigned inp(unsigned port);                 /* 0x349b0 */
unsigned outp(unsigned port, unsigned value);/* 0x349bc */

/* @0x31104 */
void __interrupt KeyboardISR(void)
{
    unsigned char scan;
    short post = 1;

    scan = inp(0x60);
    if (scan == 0xe0) {
        kbd_e0_prefix = 1;
        post = 0;
        goto ack;
    } else if (scan == 0xe1) {
        kbd_e1_count++;
        post = 0;
        goto ack;
    } else if (kbd_e0_prefix) {
        kbd_e0_prefix = 0;
        scan = scancode_fixup_table[scan & 0x7f] | (scan & 0x80);
    } else if (kbd_e1_count) {
        ++kbd_e1_count;
        if (kbd_e1_count == 6) {
            kbd_e1_count = 0;
            scan = kbd_pause_flag ? 0xf5 : 0x75;
        } else
            post = 0;
    }
    if (post) {
        if (scan & 0x80) {
            evt_key.type = 0x100;
            evt_key.sub = 2;
            scan &= 0x7f;
            key_down_table[scan] = 0;
        } else if (key_down_table[scan] == 0) {
            evt_key.type = 0x80;
            evt_key.sub = 0;
            key_down_table[scan] = 1;
        } else
            post = 0;
        evt_key.scan = scan;
        if (post)
            EvtPost(&evt_key);
    }
ack:
    scan = inp(0x61);
    outp(0x61, scan | 0x80);
    outp(0x61, scan & 0x7f);
    outp(0x20, 0x20);
}
