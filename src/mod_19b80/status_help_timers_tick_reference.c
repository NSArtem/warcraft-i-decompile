/* codegen-compiler: 10.0a */
#include "mod_19b80.h"

extern const char *status_help_text_pending;
extern unsigned short status_help_timer;
extern unsigned short status_aux_timer;
extern unsigned short status_aux_flag;

/* @0x19f94 */
void StatusHelpTimersTick(void)
{
    unsigned short a = status_help_timer;
    unsigned short b = status_aux_timer;

    if (a != 0) {
        a--;
        if (a == 0) {
            status_help_text_pending = 0;
        }
    }
    if (b != 0) {
        b--;
        if (b == 0) {
            status_aux_flag = b;
        }
    }
    status_aux_timer = b;
    status_help_timer = a;
}
