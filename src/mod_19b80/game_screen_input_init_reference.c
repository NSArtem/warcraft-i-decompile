/* codegen-compiler: 10.0a */
#include "mod_19b80.h"

extern unsigned short dat_5a7c2;
extern unsigned long status_help_text[];
extern void (*event_handlers[10])(void *);
extern void (*dialog_left_press)(void);
extern void (*dialog_right_press)(void);
extern void (*dialog_idle)(void);
extern void (*dialog_pre_event)(void);
extern void UiInputInit(void);

/* @0x1a328 */
void GameScreenInputInit(void)
{
    if (dat_5a7c2 != 0) {
        ((unsigned short *)status_help_text)[0xa8] = 0;
        status_help_text[0] = 0;
        status_help_text[2] = 0;
    }
    UiInputInit();
    event_handlers[0] = GameHotkeyDispatch;
    dialog_left_press = UiReleaseDispatch;
    dialog_right_press = UiPressDispatch;
    dialog_idle = StatusHelpTimersTick;
    dialog_pre_event = GameScreenMouseUpdate;
}
