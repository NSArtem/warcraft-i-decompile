/* codegen-compiler: 10.0a */
/* 0x209d4 NetSerialPortIrq: the IRQ of COM1..COM4, net_port_irq 0x52a6c =
 * {4, 3, 4, 3}.  The original reads the word through the dword that ends at
 * it (`mov eax,[0x52a6a+2*index]; sar eax,0x10`), the codegen.md dword-view
 * idiom also used by SndSetSfxVolume 0x27384. */
#include "network.h"

#define PORT_IRQ(n) (*(int *)((char *)&net_port_irq[n] - 2) >> 16)

int NetSerialPortIrq(int index)
{
    return PORT_IRQ(index);
}
