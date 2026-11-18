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

void KeyStateClear(void)
{
    key_modifiers = 0;
    memset(key_down_table, 0, 0x100);
}

/* @0x32ab0 */
