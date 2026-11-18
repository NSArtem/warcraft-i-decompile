/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* The loaded save file is flagged as a two-player game against the computer
 * (SaveStreamValidate 0x241a4). */
#include "gamedlg.h"

/* @0x1a95c */
void TwoPlayerComputerDialog(void)
{
    const char *text = "Cannot play a two player game\nagainst the computer.";

    ModalScreen(1, 1);
    DialogRun(0x176, 0x11, 0x46, 0xa, (void **)&text);
    ModalScreen(0, 1);
}
