/* codegen-compiler: 10.0a */
#include "mod_1bf80.h"

typedef struct Event Event;

extern void (*event_handlers[10])(Event *);
extern void (*status_frame_callback)(void);
extern void (*status_click_callback)(void);
extern void (*dialog_idle)(void);
extern void UiInputInit(void);
extern void UiEventPump(void);
extern void EvtPump(void);
extern void ScreenUpdate(void);

/* @0x1bf94 */
short WaitInputOrTimeout(short ticks)
{
    short zero;
    short flag;
    short init;
    void (*cb)(void);

    UiInputInit();
    EvtPump();
    event_handlers[0] = (void (*)(Event *))WaitSetDone;
    cb = WaitSetDone;
    status_frame_callback = cb;
    status_click_callback = cb;
    if (ticks != 0) {
        dialog_idle = WaitTickDown;
        wait_ticks_left = ticks;
    } else {
        wait_ticks_left = 1;
    }
    init = 0;
    wait_done_flag = init;
    zero = 0;
    do {
        UiEventPump();
        ScreenUpdate();
        flag = wait_done_flag;
        if (zero != flag) {
            break;
        }
    } while (flag != wait_ticks_left);
    return wait_done_flag;
}
