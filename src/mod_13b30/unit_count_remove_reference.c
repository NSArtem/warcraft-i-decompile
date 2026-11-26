/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -5r -zp2 */
#include "mod_13b30_f1.h"

extern unsigned short player_building_count[5];
extern unsigned short player_active_men[4];
extern unsigned short *unit_type_counter[0x34];

/* @0x13c84 */
void UnitCountRemove(struct Unit *u)
{
    unsigned t = *((unsigned char *)u + 0x1b);

    if ((int)t >= 0x20 && (int)t <= 0x32) {
        player_building_count[*((unsigned char *)u + 0x1e)]--;
    } else {
        player_active_men[*((unsigned char *)u + 0x1e)]--;
    }
    if ((*(unsigned short *)((unsigned char *)u + 0x10) & 0x80) != 0) {
        t = *((unsigned char *)u + 0x1b);
        if (unit_type_counter[t] != 0) {
            unit_type_counter[t][*((unsigned char *)u + 0x1e)]--;
        }
        t = *((unsigned char *)u + 0x1b);
        if (unit_count_callback[t] != 0) {
            unit_count_callback[t](u, -1);
        }
    }
}
