/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "mod_13f60.h"

extern unsigned char setup_state;
extern char net_error_text[0x38];
unsigned short DialogRun(unsigned int id, short x, short y, unsigned short layer, void **params);

/* @0x16278 */
void ConnectionFailed(void)
{
    void *p;

    p = net_error_text;
    DialogRun(0x176, 0x11, 0x46, 0x10, &p);
    setup_state = 0;
}
