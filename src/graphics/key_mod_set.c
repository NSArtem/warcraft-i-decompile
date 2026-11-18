/* codegen-flags: -s -od -4r -zp2
 * codegen-compiler: 10.0a
 * Keyboard modifier state (module mod_32a80, OD style).  TOML entries live in
 * input.toml (input area); behaviour difftested here.
 */
#include <string.h>
#include "graphics.h"

extern unsigned char key_modifiers;             /* input.toml */
extern unsigned short key_down_table[128];      /* input.toml */

/* @0x32a80 */

void KeyModSet(unsigned char mask)
{
    key_modifiers |= mask;
}

/* @0x32afc */
