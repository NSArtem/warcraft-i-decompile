/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -zp2 */
#include "status.h"

void UnitPanelDraw(const UnitPanel *panel)
{
    const CommandButton *b;
    unsigned short i;
    short armed;

    b = panel->buttons;
    for (i = 0; i < panel->nbuttons; i++, b++) {
        armed = (status_visible && b == status_button && status_pressed);
        ButtonDraw(b, armed);
    }
    if (panel->draw != 0 && (status_unit->flags & 0x80))
        panel->draw();
}
