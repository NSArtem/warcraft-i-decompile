/* codegen-compiler: 10.0a */
#include "mod_1af20.h"

extern void fn_25b80(int on); /* 0x1b43e: call to 0x25b80 with eax = 0. */
extern void GameScreenInputInit(void); /* 0x1b443: tail jump to 0x1a328. */

void GameScreenRestoreInput(void)
{
    fn_25b80(0);
    GameScreenInputInit();
}
