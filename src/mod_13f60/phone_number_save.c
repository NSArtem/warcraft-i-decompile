/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "mod_13f60.h"
#include <string.h>

/* @0x15558: capture the phone edit control's text into the staging buffer
 * dat_59230 (the dialog's OK path copies it to phone_number 0x52a28); the
 * counterpart of PhoneNumberLoad 0x15568, the two adjacent net_settings
 * callbacks (0x51650/0x51654). */
void PhoneNumberSave(Control *c)
{
    strcpy(dat_59230, c->text);
}
