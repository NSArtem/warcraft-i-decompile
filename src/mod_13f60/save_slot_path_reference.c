/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 *
 * Module mod_13f60 (DGLS.C): the save-slot path builder.
 * Reference C (T4): same code and same control flow as the original, but the
 * extension pointer lands in ecx instead of edx (see t3_blocker). */
#include <stdio.h>

#include "mod_13f60.h"

/* @0x14740: "<exe_dir>\save<slot+1>.sav" (or ".net" for a linked game). */
void SaveSlotPath(char *path, unsigned short slot)
{
    char buf[0x90];
    char *ext;

    if (dat_516ae != 0 || game_start_mode == 2)
        ext = str_ext_net;
    else
        ext = str_ext_sav;
    sprintf(buf, fmt_save_d, slot + 1);
    _makepath(path, 0, exe_dir, buf, ext);
}
