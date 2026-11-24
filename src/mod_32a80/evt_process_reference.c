/* codegen-flags: -s -od -4r -zp2
 * codegen-compiler: 10.0a
 */
#include "mod_32a80_c.h"

extern unsigned char key_ascii_table[128];
extern unsigned char key_shifted_table[0x39];
extern unsigned char key_keypad_table[0x54];
extern unsigned short key_down_table[128];
extern unsigned short selection_box_enable_b;
extern unsigned char key_modifiers;

void EvtProcess(Event *ev)
{
    union {
        unsigned long l;
        unsigned char b[4];
    } u;

    if (ev == 0 || (ev->type & 0x380) == 0)
        return;
    if (ev->type == 0x80) {
        switch (ev->key) {
        case 0x36: KeyModSet(1); break;
        case 0x2a: KeyModSet(2); break;
        case 0x1d:
        case 0x71: KeyModSet(4); break;
        case 0x38:
        case 0x74: KeyModSet(8); break;
        case 0x46: KeyModToggle(0x10); break;
        case 0x45: KeyModToggle(0x20); break;
        case 0x3a: KeyModToggle(0x40); break;
        case 0x52:
        case 0x7e: KeyModToggle(0x80); break;
        }
    } else if (ev->type == 0x100) {
        switch (ev->key) {
        case 0x36: KeyModClear(1); break;
        case 0x2a: KeyModClear(2); break;
        case 0x1d:
        case 0x71:
            if (key_down_table[0x1d] == 0 && selection_box_enable_b == 0)
                KeyModClear(4);
            break;
        case 0x38:
        case 0x74:
            if (key_down_table[56] == 0 && key_down_table[116] == 0)
                KeyModClear(8);
            break;
        }
    }
    ev->mods = key_modifiers & 0xf;
    u.b[0] = ev->key;
    if (key_modifiers & 0xc) {
        u.b[1] = key_modifiers & 0xf;
    } else {
        u.b[0] = key_ascii_table[u.b[0]];
        if (u.b[0] == 0) {
            u.b[0] = ev->key;
            if (u.b[0] >= 0x47 && u.b[0] <= 0x53 && (key_modifiers & 0x20)) {
                u.b[1] = 0;
                u.b[0] = key_keypad_table[u.b[0]];
            } else if (key_modifiers & 0x3) {
                u.b[1] = key_modifiers & 0x3;
            } else {
                u.b[1] = u.b[0];
                u.b[0] = 0;
            }
        } else {
            u.b[1] = 0;
            if (u.b[0] >= 0x61 && u.b[0] <= 0x7a) {
                if (key_modifiers & 0x43)
                    u.b[0] -= 0x20;
            } else if (key_modifiers & 0x3) {
                u.b[0] = key_shifted_table[ev->key];
            }
        }
    }
    ev->ch = (unsigned short)u.l;
}
