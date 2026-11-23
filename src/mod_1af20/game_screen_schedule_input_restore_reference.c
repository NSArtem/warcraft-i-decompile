/* codegen-compiler: 10.0a */
#include "mod_1af20.h"
#include "mod_25820.h"


void GameScreenScheduleInputRestore(void)
{
    MapScrollSetMouseRepeat(1);
    status_frame_callback = GameScreenRestoreInput; /* 0x1b56a: store 0x1b43c. */
}
