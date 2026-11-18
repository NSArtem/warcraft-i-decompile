/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 *
 * Module mod_13f60 (DLG_SET.C): the three modem command strings and the
 * edit-control buffer of the 'Modem Setup' dialog 0x183. */
#include "mod_13f60.h"

/* @0x154ac: copy the stored AT commands into the control's line buffers. */
void ModemInitStringsLoad(Control *c)
{
    char *p = c->text;

    strcpy(p, modem_init1);
    strcpy(p + 0x1b, modem_init2);
    strcpy(p + 0x36, modem_hangup);
}

/* @0x154dc: copy the control's line buffers into the edit buffers. */
void ModemInitStringsStore(Control *c)
{
    char *p = c->text;

    strcpy(dat_59230, p);
    strcpy(edit_buffer1, p + 0x1b);
    strcpy(edit_buffer2, p + 0x36);
}
