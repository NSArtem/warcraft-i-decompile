/* codegen-compiler: 10.0a */
#include "mod_19b80_c.h"

extern unsigned short dat_5a7c2;
extern unsigned long status_help_text[];
extern void (*event_handlers[10])(void);
extern void (*dialog_left_press)(void);
extern void (*dialog_right_press)(void);
extern void (*dialog_idle)(void);
extern void (*dialog_pre_event)(void);
extern void UiInputInit(void);
extern void fn_19fd8(void);
extern void fn_1a130(void);
extern void fn_1a14c(void);
extern void fn_19f94(void);
extern void fn_1a168(void);

/* @0x1a328 */
void GameScreenInputInit(void)
{
    if (dat_5a7c2 != 0) {
        ((unsigned short *)status_help_text)[0xa8] = 0;
        status_help_text[0] = 0;
        status_help_text[2] = 0;
    }
    UiInputInit();
    event_handlers[0] = fn_19fd8;
    dialog_left_press = fn_1a130;
    dialog_right_press = fn_1a14c;
    dialog_idle = fn_19f94;
    dialog_pre_event = fn_1a168;
}
