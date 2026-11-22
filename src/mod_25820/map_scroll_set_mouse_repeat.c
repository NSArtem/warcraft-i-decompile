/* codegen-compiler: 10.0a */
#include "mod_25820.h"

/* 0x25b81 stores AL unchanged; 0x25b88 clears the countdown word. */
void MapScrollSetMouseRepeat(unsigned char enabled)
{
    mouse_scroll_repeat_enabled = enabled;
    mouse_scroll_countdown = 0;
}
