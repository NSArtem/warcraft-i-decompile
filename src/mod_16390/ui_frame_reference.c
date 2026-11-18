/* codegen-compiler: 10.0a */
/* 0x18470: event table index 8 - the idle/frame event. */
#include "mod_16390.h"

void UiFrame(Event *ev)
{
    if (dialog_idle != 0)
        dialog_idle();
    fn_13e60();
}
