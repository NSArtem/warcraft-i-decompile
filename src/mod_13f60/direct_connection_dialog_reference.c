/* codegen-compiler: 10.0a */
#include "mod_13f60.h"

extern unsigned long serial_baud;
extern unsigned short serial_port;
extern unsigned short serial_irq;
extern unsigned char setup_state;
unsigned short DialogRun(unsigned int id, short x, short y, unsigned short layer, void **params);
int BaudToIndex(long baud);
long IndexToBaud(int index);
int IrqToIndex(int irq);
int IndexToIrq(int index);
void SetIrq(void);
void fn_1d538(void);

/* @0x16044 */
void DirectConnectionDialog(void)
{
    long v[6];

    v[1] = BaudToIndex(serial_baud);
    v[5] = (*(long *)((char *)&serial_port - 2) >> 16) - 1;
    v[2] = v[5];
    v[3] = IrqToIndex(*(long *)&serial_port >> 16);
    v[4] = (long)SetIrq;
    if (DialogRun(0x184, 0, 0x46, 0x10, (void **)v) != 0) {
        setup_state = 2;
    } else {
        serial_port = (unsigned short)(v[2] + 1);
        serial_baud = IndexToBaud(v[1]);
        serial_irq = IndexToIrq(v[3]);
        fn_1d538();
        own_campaign = 1;
        setup_state = 0xe;
    }
}
