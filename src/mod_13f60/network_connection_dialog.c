/* codegen-compiler: 10.0a */
#include "mod_13f60.h"

extern int (*edit_char_hook)(unsigned char);
extern unsigned char setup_state;
unsigned short DialogRun(unsigned int id, short x, short y, unsigned short layer, void **params);
void NumberFormat(void);
void NumberParse(void);
void NumberPrev(void);
void NumberNext(void);

/* @0x15fbc */
void NetworkConnectionDialog(void)
{
    unsigned long p[4];
    int (*old)(unsigned char);

    p[0] = (unsigned long)NumberFormat;
    p[1] = (unsigned long)NumberParse;
    p[2] = (unsigned long)NumberPrev;
    p[3] = (unsigned long)NumberNext;
    own_campaign = 1;
    old = edit_char_hook;
    edit_char_hook = (int (*)(unsigned char))IsNumberChar;
    if (DialogRun(0x185, 0, 0x46, 0x10, (void **)p) != 0) {
        setup_state = 2;
    } else {
        net_node_number = edit_value;
        setup_state = 0xe;
    }
    edit_char_hook = old;
}
