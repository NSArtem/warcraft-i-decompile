/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "mod_13f60.h"

typedef struct MapParams {
    unsigned long v[11];
} MapParams;

extern MapParams map_choice_params;
extern unsigned short custom_game;      /* 0x50e4e; [1]=0x50e50, [2]=0x50e52 */
extern unsigned short setup_changed;
extern unsigned char setup_return_state;
extern unsigned short DialogRun(unsigned int id, short x, short y, unsigned short layer, void **params);

/* @0x151ac */
void SetMapDialog(void)
{
    MapParams p;

    p = map_choice_params;
    if (DialogRun(0x180, 0, 0x46, 0x10, (void **)&p) == 0) {
        if (map_choice_params.v[0] != p.v[0] || map_choice_params.v[5] != p.v[5]) {
            map_choice_params = p;
            setup_changed = 1;
            setup_return_state = 5;
            (&custom_game)[2] = (unsigned short)p.v[5];
            (&custom_game)[1] = (unsigned short)p.v[0];
        }
    }
}
