/* codegen-flags: -s -od -4r -zp2
 * codegen-compiler: 10.0a
 */
#include "mod_33520_c1.h"

extern short dat_5555c;
extern short crit_error_flag;
extern short file_open_noprompt;
extern void fn_336e4(void);
extern void fn_3374c(void);

void CritErrInstall(void)
{
    dat_5555c = 1;
    crit_error_flag = 0;
    file_open_noprompt = 0;
    DpmiLockRegion(&crit_error_flag, 4);
    DpmiLockRegion((void *)fn_336e4, (unsigned)((char *)fn_3374c - (char *)fn_336e4) + 1);
    _harderr(CritErrHandler);
}
