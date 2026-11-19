/* codegen-compiler: 10.0a */
/* mod_1b800.  SndTrainingComplete 0x1ba14: 'training complete'.  Called by
 * OrderUpdateProduce 0x143cc.  See docs/subsystems/mod_1b800.md. */
#include "mod_1b800.h"

/* @0x1ba14 */
void SndTrainingComplete(void)
{
    SndEvent(0x11, 0);
}
