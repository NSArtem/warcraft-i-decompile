/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* Reference C for IssueOrderAt (0x2f0a8): the code is right but the object
 * layout is not reproducible in one translation unit.
 *
 * The original places it immediately after SelectionClickUnit's `ret`
 * (0x2f0a7) with no padding - its `jne` at 0x2f0b9 returns to that shared
 * ret.  wcc386 10.0a does merge the epilogue of a second function with the
 * first one's, but it also puts that second function on a 16-byte boundary,
 * i.e. 8 bytes of `lea eax,[eax]`/`mov ecx,ecx` filler between the two
 * (measured over every optimization flag set that reproduces
 * SelectionClickUnit's 0xd8 bytes).  A standalone object (this file) starts
 * at 0 but ends with its own `ret`, so the `jne` goes forward (disp 0x1d)
 * where the original goes backward (disp 0xec).
 *
 * Under -os the layout matches (2-byte alignment) but SelectionClickUnit's
 * prologue/codegen changes completely, so the object cannot have been
 * compiled with it.  T4: tests/test_mod_2efd0.py::test_t4_issue_order_at
 * runs this C against the original with NetSendOrder, SelectionFirst and
 * fn_1b9b8 stubbed. */
#include "mod_2efd0.h"

/* @0x2f0a8 */
void IssueOrderAt(short x, short y, Unit *target)
{
    NetSendOrder(x, y, target);
    if (net_event_pending == 0)
        fn_1b9b8(SelectionFirst());
}
