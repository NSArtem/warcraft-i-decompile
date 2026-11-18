/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* A loaded save file's version word is not 0x43 (SaveStreamValidate
 * 0x241a4). */
#include "gamedlg.h"

/* @0x1a914 */
void SaveVersionDialog(void)
{
    const char *text = "Saved game uses old version number!";

    ModalScreen(1, 1);
    DialogRun(0x176, 0x11, 0x46, 0xa, (void **)&text);
    ModalScreen(0, 1);
}
