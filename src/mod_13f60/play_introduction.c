/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "mod_13f60.h"

extern unsigned char setup_state;
extern void SetGameMode(int mode);

/* @0x15644 */
void PlayIntroduction(void)
{
    SetGameMode(0);
    setup_state = 0x10;
}
