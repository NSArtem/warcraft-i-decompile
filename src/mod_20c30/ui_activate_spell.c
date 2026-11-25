/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "mod_20c30.h"

extern unsigned short spell_mana_cost_by_order[]; /* 0x2124d: word table indexed by order. */
extern const char msg_not_enough_spell_mana[30]; /* 0x2126d: message at 0x57228. */
extern unsigned short pending_order; /* 0x2127f: word store of order. */
extern void NetSendTargetMode(void); /* 0x21295 calls 0x21980. */
extern void IssueOrderAt(short x, short y, Unit *target); /* 0x212a2 calls 0x2f0a8. */

void UiActivateSpell(unsigned char order)
{
    Unit *u;

    u = SelectionFirst(0x2c);
    if (((const unsigned char *)u)[0x1a] < spell_mana_cost_by_order[order]) {
        fn_19f70(msg_not_enough_spell_mana, 0x24);
        return;
    }
    pending_order = order;
    if ((order_props[order] & 1) != 0) {
        NetSendTargetMode();
        return;
    }
    IssueOrderAt(0, 0, 0);
}
