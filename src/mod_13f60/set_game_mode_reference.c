/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 *
 * Module mod_13f60 (DLGS.C): the game-mode selector of the setup menu.
 * Reference C (T4): the original reads game_mode through the dword at
 * 0x59614 (`mov edx,[0x59614]; sar edx,0x10; cmp edx,9`), which a plain
 * `short game_mode` read cannot reproduce (see t3_blocker). */
#include "mod_13f60.h"

/* @0x15314 */
void SetGameMode(int mode)
{
    if (game_mode != 9)
        game_mode = mode;
}
