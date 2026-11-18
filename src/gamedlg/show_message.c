/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* The generic message box: page `width` (0x176 = Ok/Cancel) at the fixed
 * message geometry, text supplied by the caller.  Returns whether the player
 * dismissed it (action 0). */
#include "gamedlg.h"

/* @0x1a894 */
unsigned short ShowMessage(const char *text, unsigned short width,
                           unsigned short height)
{
    void *p = (void *)text;
    unsigned short r;

    ModalScreen(1, 1);
    r = DialogRun(width, 0x11, 0x46, height, (void **)&p);
    ModalScreen(0, 1);
    return r == 0;
}
