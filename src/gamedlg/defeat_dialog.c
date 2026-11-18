/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* The defeat screen's message ('You failed to achieve victory...').  In a
 * linked game the winner's machine sends the end command instead, so nothing
 * is shown here. */
#include "gamedlg.h"

/* @0x1ab28 */
void DefeatDialog(void)
{
    game_mode = 7;
    if (net_play_flag == 0)
        ShowMessageRace("You failed to achieve victory...", 0x176);
}
