/* codegen-compiler: 10.0a */
#include "mod_13f60.h"
#include <string.h>

typedef struct Net8 { unsigned long v[8]; } Net8;

extern unsigned long net_settings[8];
extern int (*edit_char_hook)(unsigned char);
extern unsigned long modem_baud;
extern unsigned short modem_port;
extern unsigned short modem_irq;
extern unsigned char net_side;
extern unsigned long modem_dialog_values[8];
extern unsigned short modem_setup_init;
extern unsigned char setup_state;
unsigned short DialogRun(unsigned int id, short x, short y, unsigned short layer, void **params);
int BaudToIndex(long baud);
long IndexToBaud(int index);
int IrqToIndex(int irq);
int IndexToIrq(int index);
void SaveModemSettings(void);

/* @0x15ca8 */
void ModemConnectionDialog(void)
{
    int (*old)(unsigned char);
    unsigned short r;
    long t;

    if (modem_setup_init == 0) {
        modem_setup_init = 1;
        *(Net8 *)modem_dialog_values = *(Net8 *)net_settings;
        modem_dialog_values[0] = net_side;
        t = (*(long *)((char *)&modem_port - 2) >> 16) - 1;
        modem_dialog_values[7] = t;
        modem_dialog_values[2] = t;
        modem_dialog_values[1] = BaudToIndex(modem_baud);
        modem_dialog_values[3] = IrqToIndex(*(long *)&modem_port >> 16);
    }
    old = edit_char_hook;
    edit_char_hook = (int (*)(unsigned char))IsPhoneChar;
    r = DialogRun(0x182, 0, 0x46, 0x10, (void **)modem_dialog_values);
    switch (r) {
    case 0:
        modem_setup_init = 0;
        *(Net8 *)net_settings = *(Net8 *)modem_dialog_values;
        own_campaign = (modem_dialog_values[0] == 0);
        strcpy(phone_number, dat_59230);
        /* The original reads just the low word of the port slot. */
        modem_port = *(unsigned short *)&net_settings[2] + 1;
        net_side = (unsigned char)net_settings[0];
        modem_baud = IndexToBaud(net_settings[1]);
        modem_irq = IndexToIrq(net_settings[3]);
        SaveModemSettings();
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
