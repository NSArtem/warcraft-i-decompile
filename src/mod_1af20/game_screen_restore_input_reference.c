/* codegen-compiler: 10.0a */
#include "mod_1af20.h"
#include "mod_25820.h"

extern void GameScreenInputInit(void); /* 0x1b443: tail jump to 0x1a328. */

void GameScreenRestoreInput(void)
{
    MapScrollSetMouseRepeat(0);
    GameScreenInputInit();
}
