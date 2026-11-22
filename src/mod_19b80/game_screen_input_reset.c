/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "mod_19b80.h"

extern void (*status_mouse_callback)(void *);
extern void (*status_frame_callback)(void);
extern void (*status_click_callback)(void);
extern void (*dialog_pre_event)(void);
extern void GameScreenInputInit(void);
extern void SetCursorShape(unsigned char id);

/* @0x1a388 */
void GameScreenInputReset(unsigned char cursor)
{
    status_frame_callback = GameScreenInputInit;
    status_click_callback = GameScreenInputInit;
    status_mouse_callback = 0;
    dialog_pre_event = 0;
    SetCursorShape(cursor);
}
