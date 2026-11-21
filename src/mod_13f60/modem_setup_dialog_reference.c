/* codegen-compiler: 10.0a */
#include "mod_13f60.h"
#include <string.h>

extern unsigned char dial_pulse;
extern unsigned char setup_state;
unsigned short DialogRun(unsigned int id, short x, short y, unsigned short layer, void **params);
void CheckBoxToggle(void);
void ModemInitStringsLoad(void);
void ModemInitStringsStore(void);
void fn_1d538(void);

/* @0x15e1c */
void ModemSetupDialog(void)
{
    unsigned long p[4];

    p[0] = (dial_pulse != 0);
    p[1] = (unsigned long)CheckBoxToggle;
    p[2] = (unsigned long)ModemInitStringsLoad;
    p[3] = (unsigned long)ModemInitStringsStore;
    if (DialogRun(0x183, 0, 0x46, 0x10, (void **)p) == 0) {
        strcpy(modem_init1, dat_59230);
        strcpy(modem_init2, edit_buffer1);
        strcpy(modem_hangup, edit_buffer2);
        dial_pulse = (p[0] == 1);
        fn_1d538();
    }
    setup_state = 0xa;
}
