/* codegen-compiler: 10.0a */
#include "mod_2b2f0.h"

extern unsigned short net_event_pending;
extern unsigned char map_cursor_shape;
extern void (*map_press_handler)(void *);
extern void (*map_release_handler)(void *);
extern const char str_select_target[];
extern void fn_19f70(const char *msg, unsigned code);
extern void fn_20c30(unsigned id);
extern void fn_20cc0(void);
extern int fn_25b6c(int on);
extern void fn_1effc(void);
extern void fn_1b48c(void *);
extern void NetSendTargetCancel(void *);

/* @0x2b31c */
void fn_2b31c(void)
{
    if (target_mode_flags[net_event_pending] == 0) {
        target_mode_flags[net_event_pending] = 1;
        if (net_event_pending == 0) {
            fn_19f70(str_select_target, 0);
            map_aux_handler = fn_1effc;
            map_release_handler = fn_1b48c;
            map_press_handler = NetSendTargetCancel;
            map_cursor_shape = 2;
            fn_25b6c(1);
            fn_20c30(0x39);
        }
        fn_20cc0();
    }
}
