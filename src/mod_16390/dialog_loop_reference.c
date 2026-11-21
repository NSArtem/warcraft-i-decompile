/* codegen-compiler: 10.0a */
#include "mod_16390.h"

extern int dat_59614;

/* @0x17e54 */
void DialogLoop(Dialog *d)
{
    DialogItem *it;
    DialogItem *prev = 0;
    DialogItem *hit;
    short quit;

    dialog_running = 1;
    left_button_held = 0;
    last_key = 0;
    do {
        UiEventPumpNet();
        DialogPreviewCursor();
        ScreenUpdate();
        quit = setup_quit;
        if (quit != 0 || (dat_59614 >> 16) == 9) {
            dialog_result = *(short *)((char *)d->cb + 6);
            return;
        }
        if (DialogCheckDone(d) != 0) {
            dialog_result = (short)d->cb->unk4;
            return;
        }
        if (last_key != 0) {
            if (I16(&last_key) == 0xd) {
                dialog_running = quit;
                dialog_result = (short)d->cb->unk4;
            } else if (I16(&last_key) == 0x1b) {
                dialog_running = quit;
                dialog_result = *(short *)((char *)d->cb + 6);
            } else if (I16(&last_key) == 0x4800 || I16(&last_key) == 0x7700) {
                ListScrollBy(d, -1);
            } else if (I16(&last_key) == 0x5000 || I16(&last_key) == 0x7c00) {
                ListScrollBy(d, 1);
            } else {
                it = d->items;
                while (it->type != 0xffff) {
                    if (it->hotkey == I16(&last_key) || it->hotkey == 0x7e) {
                        DialogActivateItem(d, it);
                    }
                    it++;
                }
            }
            last_key = 0;
        }
        if (left_button_held != 0) {
            hit = DialogItemLoop(d);
            if (hit != 0) {
                DialogActivateItem(d, hit);
            }
        }
        it = d->items;
        while (it->type != 0xffff) {
            if (it->type == 0 || it->type == 6 || it->type == 7 ||
                it->type == 9 || it->type == 10) {
                if (DialogItemHitTest(d, it) != 0) {
                    break;
                }
            }
            it++;
        }
        if (it != prev) {
            if (prev != 0 && prev->type != 0xffff) {
                DialogDrawItemState(d, prev, 0, 0);
            }
            if (it->type != 0xffff) {
                DialogDrawItemState(d, it, 0, 1);
            }
            prev = it;
        }
    } while (dialog_running != 0);
}
