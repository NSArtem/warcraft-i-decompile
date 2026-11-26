/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * NetSendSelection (0x219d8): broadcast the selection list (type 3) - the
 * count and one 16-bit unit_array index per unit.  Only caller fn_262a0, which
 * sends it when the requested list differs from the current one.  Each machine
 * keeps both players' selections (selected_units[player*16]); the receiver's
 * fn_25f9c writes them under net_event_pending.
 * Reference C: the logic is right, the code is not byte-identical.  Watcom
 * 10.0a keeps the count in a register and saves ebp (`push ebp`), while the
 * original spills the count to the frame ([esp+0x84], `cmp cx,[esp+0x84]`)
 * and uses no ebp - first difference at 0x219dc.  17 spellings tried
 * (count as a parameter/const/dword/volatile local, the length as an
 * accumulator, the store indexed by i*2 or by len, pointer-walk variants):
 * the compiler always folds len = 5+2*count and frees a register.  T4
 * difftest: tests/test_packet.py::test_t4_net_send_selection. */
#include "packet.h"

/* @0x219d8 */
void NetSendSelection(unsigned short count, Unit **units)
{
    unsigned char msg[PKT_BUF];
    unsigned short len, i;

    msg[0] = PKT_SELECTION;
    *(unsigned short *)(msg + 3) = count;
    len = 5;
    for (i = 0; i != count; i++) {
        *(unsigned short *)(msg + 5 + i * 2) =
            (unsigned short)RefRelocate((int)units[i], (int)unit_array, 1);
        len += 2;
    }
    PacketSend(len, msg);
    StatusPanelLockAdjust(1);
}
