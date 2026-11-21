/* codegen-flags: -s -od -4r -d1+ -zp2 */
/* codegen-compiler: 10.0a */
#include "mod_33520_c1.h"

extern short crit_err_installed;
extern short crit_error_flag;
extern short file_open_noprompt;
extern void CritErrLockStart(void);
extern void CritErrLockEnd(void);

void CritErrInstall(void)
{
    crit_err_installed = 1;
    crit_error_flag = 0;
    file_open_noprompt = 0;
    DpmiLockRegion(&crit_error_flag, 4);
    DpmiLockRegion((void *)CritErrLockStart, (unsigned)((char *)CritErrLockEnd - (char *)CritErrLockStart) + 1);
    _harderr(CritErrHandler);
}
