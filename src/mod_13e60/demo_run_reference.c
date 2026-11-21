/* codegen-compiler: 10.0a */
#include "mod_13e60.h"

extern short demo_idle_timer;

/* @0x13f0c */
void DemoRun(void)
{
    short r;
    unsigned short i;

    i = demo_step_index;
    demo_mode = 1;
    do {
        i++;
        if (demo_steps[i].fn == 0) {
            i = 0;
        }
        demo_step_index = i;
        r = (short)demo_steps[i].fn();
        i = demo_step_index;
    } while (r == 0);
    demo_idle_timer = 0x10e;
}
