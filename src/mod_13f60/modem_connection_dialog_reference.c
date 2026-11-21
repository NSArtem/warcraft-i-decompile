/* codegen-compiler: 10.0a */
#include "mod_13f60.h"
#include <string.h>

typedef struct Net8 { unsigned long v[8]; } Net8;

extern unsigned long net_settings[8];
extern unsigned long dat_5163c;
extern unsigned short dat_51640;
extern unsigned long dat_51644;
extern int (*edit_char_hook)(unsigned char);
extern unsigned long modem_baud;
extern unsigned short modem_port;
extern unsigned short modem_irq;
extern unsigned char net_side;
extern unsigned long dat_592c8[8];
extern unsigned short modem_setup_init;
extern unsigned char setup_state;
unsigned short DialogRun(unsigned int id, short x, short y, unsigned short layer, void **params);
int BaudToIndex(long baud);
long IndexToBaud(int index);
int IrqToIndex(int irq);
int IndexToIrq(int index);
void fn_1d538(void);

/* @0x15ca8 */
void ModemConnectionDialog(void)
{
    int (*old)(unsigned char);
    unsigned short r;
    long t;

    if (modem_setup_init == 0) {
        modem_setup_init = 1;
        *(Net8 *)dat_592c8 = *(Net8 *)net_settings;
        dat_592c8[0] = net_side;
        t = (*(long *)((char *)&modem_port - 2) >> 16) - 1;
        dat_592c8[7] = t;
        dat_592c8[2] = t;
        dat_592c8[1] = BaudToIndex(modem_baud);
        dat_592c8[3] = IrqToIndex(*(long *)&modem_port >> 16);
    }
    old = edit_char_hook;
    edit_char_hook = (int (*)(unsigned char))IsPhoneChar;
    r = DialogRun(0x182, 0, 0x46, 0x10, (void **)dat_592c8);
    switch (r) {
    case 0:
        modem_setup_init = 0;
        *(Net8 *)net_settings = *(Net8 *)dat_592c8;
        own_campaign = (dat_592c8[0] == 0);
        strcpy(phone_number, dat_59230);
        modem_port = dat_51640 + 1;
        net_side = (unsigned char)net_settings[0];
        modem_baud = IndexToBaud(dat_5163c);
        modem_irq = IndexToIrq(dat_51644);
        fn_1d538();
        setup_state = 0xe;
        break;
    case 1:
        modem_setup_init = 0;
        setup_state = 2;
        break;
    case 2:
        setup_state = 0xb;
        break;
    }
    edit_char_hook = old;
}
