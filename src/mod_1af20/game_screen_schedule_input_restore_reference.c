/* codegen-compiler: 10.0a */
#include "mod_1af20.h"

extern void fn_25b80(int on); /* 0x1b565: call to 0x25b80 with eax = 1. */

void GameScreenScheduleInputRestore(void)
{
    fn_25b80(1);
    status_frame_callback = GameScreenRestoreInput; /* 0x1b56a: store 0x1b43c. */
}
