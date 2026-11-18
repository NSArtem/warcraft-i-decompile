/* codegen-flags: -s -od -4r -zp2
 * codegen-compiler: 10.0a
 * Module mod_32a80 (0x32b40..0x32e80), OD style: EVTPRO.C - translate a
 * keyboard event into modifier bits and the ascii|scan<<8 word.
 * The TOML entry lives in input.toml (input area); behaviour is difftested
 * in tests/test_graphics_lib.py.
 */
#include "graphics.h"

typedef struct Event {
    unsigned short type;        /* +0 */
    unsigned short sub;         /* +2 */
    short x, y;                 /* +4, +6 */
    unsigned char scan;         /* +8 */
    unsigned char mod;          /* +9 */
    unsigned short key;         /* +0xa */
} Event;

extern unsigned char key_modifiers;             /* input.toml */
extern unsigned short key_down_table[128];      /* input.toml */
extern unsigned char key_ascii_table[128];      /* 0x55448 */
extern unsigned char key_shifted_table[0x39];   /* 0x554c8 */
extern unsigned char key_keypad_table[0x54];    /* 0x55501 */

/* @0x32b40 */
void EvtProcess(Event *ev)
{
    unsigned char ch, ascii;

    if (ev == 0 || (ev->type & 0x380) == 0)
        return;
    if (ev->type == 0x80) {
        switch (ev->scan) {
        case 0x1d: KeyModSet(4); break;
        case 0x2a: KeyModSet(2); break;
        case 0x36: KeyModSet(1); break;
        case 0x38: KeyModSet(8); break;
        case 0x3a: KeyModToggle(0x40); break;
        case 0x45: KeyModToggle(0x20); break;
        case 0x46: KeyModToggle(0x10); break;
        case 0x52: KeyModToggle(0x80); break;
        case 0x71: KeyModSet(4); break;
        case 0x74: KeyModSet(8); break;
        case 0x7e: KeyModToggle(0x80); break;
        }
    } else if (ev->type == 0x100) {
        switch (ev->scan) {
        case 0x1d:
        case 0x71:
            if (key_down_table[0x1d] == 0 && key_down_table[0x71] == 0)
                KeyModClear(4);
            break;
        case 0x2a: KeyModClear(2); break;
        case 0x36: KeyModClear(1); break;
        case 0x38:
        case 0x74:
            if (key_down_table[0x38] == 0 && key_down_table[0x74] == 0)
                KeyModClear(8);
            break;
        }
    }
    ev->mod = key_modifiers & 0x0f;
    ch = ev->scan;
    if ((key_modifiers & 0x0c) != 0) {
        ascii = key_modifiers & 0x0f;
    } else {
        ch = key_ascii_table[ch];
        if (ch != 0) {
            ascii = 0;
            if (ch >= 'a' && ch <= 'z') {
                if ((key_modifiers & 0x43) != 0)
                    ch -= 0x20;
            } else if ((key_modifiers & 0x03) != 0) {
                ch = key_shifted_table[ev->scan];
            }
        } else {
            ch = ev->scan;
            if (ev->scan >= 0x47 && ev->scan <= 0x53 && (key_modifiers & 0x20) != 0) {
                ascii = 0;
                ch = key_keypad_table[ev->scan];
            } else if ((key_modifiers & 0x03) != 0) {
                ascii = key_modifiers & 0x03;
            } else {
                ascii = ev->scan;
                ch = 0;
            }
        }
    }
    ev->key = ch | (ascii << 8);
}
