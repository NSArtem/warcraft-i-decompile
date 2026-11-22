/* codegen-compiler: 10.0a */
#include "mod_19b80.h"

extern unsigned short demo_mode;
extern short fn_1b690(void *evt);
extern void fn_1b5d0(void *u);
extern void *SelectionFirst(void);
extern void ScoreSetPage(int page);
extern unsigned short StatusPanelHandleKey(void *evt);
extern void KeyStateClear(void);
extern void NetSendControlPacket(unsigned short id);

/* @0x19fd8 */
void GameHotkeyDispatch(void *evt)
{
    unsigned short key;
    unsigned short k2;
    unsigned short id;

    key = (unsigned short)(((unsigned char *)evt)[8] + (((unsigned char *)evt)[9] << 8));
    k2 = key & 0xf0ff;
    id = 0;
    if (demo_mode != 0) {
        id = 1;
    } else if (fn_1b690(evt) == 0) {
        if (key == 0x42d) {
            id = 2;
        } else if (k2 == 0xd) {
            id = 3;
        } else if (k2 == 0xc) {
            id = 4;
        } else if (key == 0x418) {
            id = 5;
        } else if (key == 0x57) {
            id = 6;
        } else if (key == 0x58) {
            id = 7;
        } else if (key == 0x3b || key == 0x423) {
            id = 9;
        } else if (key == 0x2e) {
            fn_1b5d0(SelectionFirst());
        } else if (key >= 0x3f && key <= 0x42) {
            ScoreSetPage((unsigned short)(key - 0x3f));
        } else if (k2 >= 0x3c && k2 < 0x3f) {
            if ((key & 0x300) != 0) {
                MapViewSave((unsigned short)(k2 - 0x3c));
            } else {
                MapViewRecall((unsigned short)(k2 - 0x3c));
            }
        } else if (StatusPanelHandleKey(evt) == 0) {
            if (key == 0x39) {
                KeyStateClear();
            }
        }
    }
    if (id != 0) {
        NetSendControlPacket(id);
    }
}
