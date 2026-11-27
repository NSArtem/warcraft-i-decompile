/* codegen-compiler: 10.0a */
/* 0x18458: event table index 3 - the mouse moved. */
#include "mod_16390.h"

void UiMouseMove(Event *ev)
{
    if (status_mouse_callback != 0)
        status_mouse_callback();
    DemoIdleTimerReset();
}
