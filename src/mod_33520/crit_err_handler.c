/* codegen-flags: -s -od -4r -d1+ -zp2 */
/* codegen-compiler: 10.0a */
#include "mod_33520_c1.h"

extern short crit_error_flag;

int __far CritErrHandler(unsigned deverr, unsigned errcode, unsigned __far *devhdr)
{
    if (deverr & 0x8000)
        _hardresume(3);
    crit_error_flag = 1;
    _hardresume(3);
    return 3;
}
