/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* The full-screen info page reached from the F1 / Ctrl+H game command: clear
 * the visible screen, upload the page's own palette (resource 0x101) and run
 * page 0xff (a 320x200 picture with its two 17x17 tiles).  No red tint. */
#include "gamedlg.h"

/* @0x1ade4 */
void HelpScreen(void)
{
    unsigned char pal[0x300];

    ModalScreen(1, 0);
    memset((void *)0xa0000, 0, 0xfa00);
    ResourceBegin(0x101, 0);
    ResourceRead(pal, 0);
    PaletteSet(0, 0xff, pal);
    DialogRun(0xff, 0, 0, 0xa, 0);
    ModalScreen(0, 0);
}
