/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* A message box whose page id gets the scenario_race offset, so the frame is
 * the human or the orc variant (every page has both). */
#include "gamedlg.h"

/* @0x1a720 */
unsigned short ShowMessageRace(const char *text, unsigned short id)
{
    void *p = (void *)text;
    unsigned short r;

    ModalScreen(1, 1);
    r = DialogRun((unsigned short)(id + scenario_race), 0x11, 0x46, 0xa,
                  (void **)&p);
    ModalScreen(0, 1);
    return r == 0;
}
