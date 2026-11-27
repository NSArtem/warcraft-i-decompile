/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -zp2 */
#include "mod_2b2f0.h"

extern unsigned short net_event_pending;
extern unsigned char map_cursor_shape;
extern void (*map_press_handler)(void *);
extern void (*map_release_handler)(void *);
extern void fn_19f70(const char *msg, unsigned code);
extern void fn_20c4c(int arg);
extern void fn_20c6c(void);
extern int fn_25b6c(int on);
extern void MinimapBeginScrollInput(void);
extern void MapReleaseDefault(void *);
extern void MapPressDefault(void *);

/* @0x2b390 */
void TargetModeExit(void)
{
    if (target_mode_flags[net_event_pending] != 0) {
        target_mode_flags[net_event_pending] = 0;
        if (net_event_pending == 0) {
            fn_19f70(0, 0);
            map_aux_handler = MinimapBeginScrollInput;
            map_release_handler = MapReleaseDefault;
            map_press_handler = MapPressDefault;
            map_cursor_shape = 0;
            fn_25b6c(0);
            fn_20c4c(0);
        }
        fn_20c6c();
    }
}
