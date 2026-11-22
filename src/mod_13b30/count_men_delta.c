/* codegen-compiler: 10.0a */
#include "mod_13b30_f1.h"

extern unsigned short dead_men[5];
extern void ScoreAddForMen(struct Unit *u);
extern void ScoreSubForMen(struct Unit *u);

/* @0x13b30 */
void CountMenDelta(struct Unit *u, short delta)
{
    if (delta > 0) {
        ScoreAddForMen(u);
    } else {
        dead_men[*((unsigned char *)u + 0x1e)]++;
        ScoreSubForMen(u);
    }
}
