/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "war.h"

extern char spell_invalid_msg[];   /* 0x57d38 */

/* @0x27a8c */
int SpellInvalid(void)
{
    FatalError(spell_invalid_msg);
    return 0;
}
