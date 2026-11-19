/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * PacketDispatch (0x215f0): execute one command packet.  pkt[0] is the packet
 * type (the cd_215a8 jump table, 18 entries), pkt+3 the payload.  The case
 * order below is the order the original's code is laid out in (3, 6, 4, 5,
 * 7, ...) - Watcom emits the cases in source order.
 * Every command row except the last three first releases one status-panel lock
 * (the send side takes one with StatusPanelLockAdjust(1)).
 * Reference C: every case body is byte-identical; only the switch's
 * index/jump-table sequence differs - the original does
 * `xor edx,edx; mov dl,al; lea eax,[edi+3]; jmp dword [cs:edx*4+0x215a8]`
 * while 10.0a emits `and eax,0xff; lea edx,[eax*4+table]; lea eax,[edi+3];
 * jmp dword [edx]` (first difference at 0x21604, 7 bytes on the `ja`
 * displacement).  The same switch shape compiled alone and after another
 * function of the module gives the same form, so the trigger is not the
 * table's position; the cases, the frame (0x10 for Unit *units[4]) and the
 * case order are confirmed by the matching bodies.  Also: the object's table
 * sits 0x50 bytes before the function (the compiler pads it to 16), the
 * original's 0x48, so the object cannot be placed in sequence anyway (the
 * table belongs to the asm gap after fn_21554).  T4 difftest:
 * tests/test_packet.py::test_t4_packet_dispatch. */
#include "packet.h"

extern void fn_25f9c(unsigned short count, Unit **units);      /* 0x25f9c */
extern void fn_260c8(int arg1, int arg2, Unit *target, void (*handler)(Unit *, short, short, Unit *, void *)); /* 0x260c8 */
extern void fn_2b31c(void);                                    /* 0x2b31c target mode on */
extern void fn_2b390(void);                                    /* 0x2b390 target mode off */
extern void fn_2e384(Unit *u);                                 /* 0x2e384 cancel construction */
extern void fn_19c14(unsigned short command);                  /* 0x19c14 menu dispatcher */
extern void fn_19edc(char *text, unsigned short flag, unsigned short mode); /* 0x19edc */
extern void PlaceBoxStart(unsigned char type);                 /* 0x22798 */
extern void PlaceBoxCancel(void);                              /* 0x22930 */
extern void PlaceBoxConfirm(unsigned long cell);               /* 0x22ae4 */
/* 0x52a80: the order id -> executor table (4-byte pointers, ORDER.C) */
extern void (*order_handlers[])(Unit *, short, short, Unit *, void *);
extern unsigned short spell_order;                             /* 0x5a7c0 */

/* @0x215f0 */
void PacketDispatch(unsigned char *pkt)
{
    Unit *units[4];
    unsigned short i;

    switch (pkt[0]) {
    case 0:
    case 1:
    case 2:
        break;
    case 3:
        StatusPanelLockAdjust(0);
        for (i = 0; i != *(unsigned short *)(pkt + 3); i++)
            units[i] = (Unit *)RefRelocate(*(int *)(pkt + 1 + i * 2) >> 16,
                                           (int)unit_array, 0);
        fn_25f9c(*(unsigned short *)(pkt + 3), units);
        break;
    case 6:
        StatusPanelLockAdjust(0);
        PlaceBoxConfirm(*(unsigned long *)(pkt + 3));
        break;
    case 4:
        StatusPanelLockAdjust(0);
        PlaceBoxStart(pkt[3]);
        break;
    case 5:
        StatusPanelLockAdjust(0);
        PlaceBoxCancel();
        break;
    case 7:
        StatusPanelLockAdjust(0);
        fn_2b31c();
        break;
    case 8:
        StatusPanelLockAdjust(0);
        fn_2b390();
        break;
    case 9:
        StatusPanelLockAdjust(0);
        spell_order = *(unsigned short *)(pkt + 9);
        if (order_handlers[spell_order] == 0)
            FatalError("pktunit: %d %d", spell_order, net_event_pending);
        fn_260c8(*(int *)(pkt + 1) >> 16, *(int *)(pkt + 3) >> 16,
                 (Unit *)RefRelocate(*(int *)(pkt + 5) >> 16, (int)unit_array, 0),
                 order_handlers[spell_order]);
        fn_2b390();
        spell_order = 0;
        break;
    case 0xa:
        StatusPanelLockAdjust(0);
        fn_2e384((Unit *)RefRelocate(*(int *)(pkt + 1) >> 16, (int)unit_array, 0));
        break;
    case 0xb:
        StatusPanelLockAdjust(0);
        UnitStartResearch(SelectionFirst(), pkt[3]);
        break;
    case 0xc:
        StatusPanelLockAdjust(0);
        UnitStartTraining(SelectionFirst(), pkt[3]);
        break;
    case 0xd:
        StatusPanelLockAdjust(0);
        UnitCancelProduction(SelectionFirst());
        break;
    case 0xe:
        fn_19c14(*(unsigned short *)(pkt + 3));
        break;
    case 0xf:
        if (net_event_pending == 1)
            fn_19edc((char *)(pkt + 3), net_event_pending, 0x48);
        break;
    case 0x10:
        SetCheatFlags(*(unsigned long *)(pkt + 3));
        break;
    case 0x11:
        NetLoadSyncMessage(pkt + 3);
        break;
    }
}
