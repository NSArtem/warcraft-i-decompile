/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -zp2 */
#include "mod_16390.h"

/* @0x1700c */
DialogItem *DialogItemLoop(Dialog *d)
{
    DialogItem *it;
    short hot;

    it = d->items;
    while (it->type != (unsigned short)-1) {
        if (it->type != 4 && it->type != 3 && it->type != 8) {
            if ((short)DialogItemHitTest(d, it) != 0)
                break;
        }
        it++;
    }
    if (it->type == 5) {
        ListSelectAtMouse(d, it);
        while (it->type != (unsigned short)-1)
            it++;
    }
    if (it->type != (unsigned short)-1) {
        DialogHighlightOn();
        DialogDrawItemState(d, it, 1, 1);
        hot = 1;
    }
    while (left_button_held != 0) {
        UiEventPumpNet();
        DialogPreviewCursor();
        ScreenUpdate();
        if (setup_quit != 0 || DialogCheckDone(d) != 0)
            return 0;
        if (it->type != (unsigned short)-1) {
            if ((short)DialogItemHitTest(d, it) != 0) {
                if (hot == 0) {
                    DialogHighlightOn();
                    DialogDrawItemState(d, it, 1, 1);
                    hot = 1;
                }
                if (auto_repeat_delay == 0) {
                    auto_repeat_delay = 1;
                    if ((it->flags & 2) != 0)
                        DialogActivateItem(d, it);
                }
            } else if (hot != 0) {
                DialogHighlightOff();
                DialogDrawItemState(d, it, 0, 0);
                hot = 0;
            }
        }
    }
    if (it->type != (unsigned short)-1 && (short)DialogItemHitTest(d, it) != 0) {
        if (hot != 0)
            DialogHighlightOff();
        DialogDrawItemState(d, it, 0, 0);
        ScreenUpdate();
        return it;
    }
    return 0;
}
