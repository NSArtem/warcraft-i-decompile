/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* Reference C (T4) for 0x1aca8 SaveErrorDialog: the save failed - show the
 * local disk error, or the other machine's failure when the command arrived
 * from the link.  T3 is blocked by the module's CONST pool: the original has
 * 'Disk Error!  Unable to save game!' at 0x51ea6 (2 mod 4, right after the
 * previous dialog's string) and 'Remote system failed to save game!' at
 * 0x51ec8 without padding, while a file of its own pools the two strings from
 * a 4-aligned start and inserts 2 bytes of padding (0x24 instead of 0x22). */
#include "gamedlg.h"

/* @0x1aca8 */
void SaveErrorDialog(void)
{
    const char *text;

    if (net_event_pending == 0)
        text = "Disk Error!  Unable to save game!";
    else
        text = "Remote system failed to save game!";
    ShowMessageRace(text, 0x176);
}
