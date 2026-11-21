/* codegen-compiler: 10.0a */
#include "mod_16390.h"

/* @0x17ce4 */
void DialogActivateItem(Dialog *d, DialogItem *item)
{
    char buf[100];
    void (*fn)(Dialog *);
    unsigned int code;
    unsigned short flag;

    flag = 0;
    switch (item->type) {
    case 0:
    case 9:
        dialog_running = 0;
        dialog_result = item->id;
        return;
    case 1:
        DialogEraseText(d);
        ListSelPrev(d, item);
        DialogCallSelect(d);
        DialogDrawText(d);
        ScreenUpdate();
        return;
    case 2:
        DialogEraseText(d);
        ListSelNext(d, item);
        DialogCallSelect(d);
        DialogDrawText(d);
        ScreenUpdate();
        return;
    case 6:
        fn = (void (*)(Dialog *))d->params[item->id];
        DialogEraseText(d);
        fn(d);
        DialogDrawText(d);
        ListDraw(d, item);
        return;
    case 10:
        flag = 1;
        code = item->code;
    case 7:
        item++;
        strcpy(buf, (char *)item->text);
        cur_bitmap = (void *)&d->w;
        if (EditFieldRun(d, item, buf, buf, item->id)) {
            DialogEraseText(d);
            strcpy((char *)item->text, buf);
            if (flag) {
                dialog_running = 0;
                dialog_result = (short)code;
                DialogDrawText(d);
                ScreenUpdate();
                return;
            }
        } else {
            DialogEraseText(d);
        }
        DialogDrawText(d);
        ScreenUpdate();
        break;
    default:
        break;
    }
}
