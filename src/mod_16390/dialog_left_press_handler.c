/* codegen-compiler: 10.0a */
/* 0x16ca8: left button pressed: arm the auto-repeat. */
#include "mod_16390.h"

void DialogLeftPressHandler(void)
{
    left_button_held = 1;
    auto_repeat_delay = 8;
}
