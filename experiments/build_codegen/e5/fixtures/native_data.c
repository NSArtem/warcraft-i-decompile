/* codegen-compiler: 10.0a */
/* Experimental explicit _DATA storage, native -ot. Canonical C is untouched.
 * These are separate char arrays, not a workaround for an interior layout. */
#include "gamedlg.h"
char e5_disk[] = "Disk Error!  Unable to save game!";
char e5_remote[] = "Remote system failed to save game!";
void SaveErrorDialog(void)
{
    const char *text;
    if (net_event_pending == 0)
        text = e5_disk;
    else
        text = e5_remote;
    ShowMessageRace(text, 0x176);
}
