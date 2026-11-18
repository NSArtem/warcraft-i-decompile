/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* The link handshake's version check (NetLinkHandshake 0x23edc): this build's
 * version byte differs from the other machine's.  No modal screen switch
 * here: the game screen (and dialog_enabled) is not up yet. */
#include "gamedlg.h"

/* @0x1a8e4 */
void VersionMismatchDialog(void)
{
    const char *text = "Warcraft version numbers are different.";

    DialogRun(0x176, 0x11, 0x46, 0xa, (void **)&text);
}
