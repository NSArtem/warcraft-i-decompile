/* codegen-flags: -s -ot -ol -4r -zp2
 * REFERENCE C for the record rebasing helpers of mod_24860 (0x24a68,
 * 0x24aa8, 0x24b88).  Not built: the instruction bodies match the original,
 * but the original duplicates the loop decrement/test at the bottom
 * (`dec esi; cmp si,-1; jne`) where OW2 keeps one test and jumps back to it
 * (a loop-layout difference of the older compiler), so these are verified as
 * T4 with wc1.cemu - tests/test_mod_24860.py, docs/subsystems/save_format.md.
 */
#include "war.h"
#include "mod_24860.h"

/* @0x24a68  rebase the 0x1000 dwords of the 64x64 tile -> unit map
 * (object_map): on load every stored offset becomes a unit pointer, on save
 * every pointer becomes an offset, both relative to unit_array.
 */
void SaveRelocObjectMap(int *map)
{
    short n = 0x1000;

    do {
        *map = RefRelocate(*map, (int)unit_array, save_reloc_state.raw >> 16);
        map++;
    } while (--n != -1);
}

/* @0x24aa8  rebase the pointer fields of the 200 unit records.
 *
 * Free slots (flags bit 0) are skipped.  The loader also clears the flag bits
 * 0x18 of +0x11 and copies the type byte to the type copy at +0x1c.
 *
 * Units (type <= 0x1f) carry pointers into unit_array at +0x3a, +0x42 and
 * +0x52; buildings and map objects (0x20..0x32) carry a pointer into the
 * scenario data at +0x46 (+0x3a is rebased for every live record) and an
 * overlay object pointer at +0x58.
 */
void SaveRelocUnits(SaveUnitRec *u)
{
    short n = 200;

    do {
        unsigned f;

        f = u->flags.w & 1;
        if (f == 0) {
            u->flags.b.hi &= 0xe7;
            u->type_copy = u->type;
            u->link3a = RefRelocate(u->link3a, (int)unit_array,
                                    save_reloc_state.raw >> 16);
            {
                int t = u->type;            /* promoted int, like the original compare */

                if (t <= 0x1f) {
                    u->link42 = RefRelocate(u->link42, (int)unit_array,
                                            save_reloc_state.raw >> 16);
                    u->target = RefRelocate(u->target, (int)unit_array,
                                            save_reloc_state.raw >> 16);
                } else if (t >= 0x20 && t <= 0x32) {
                    u->placement = RefRelocate(u->placement, 0x50008,
                                               save_reloc_state.raw >> 16);
                    u->overlay = RefRelocate(u->overlay, (int)object_array,
                                             save_reloc_state.raw >> 16);
                }
            }
        }
        u++;
    } while (--n != -1);
}

/* @0x24b88  rebase the two unit pointers of the 100 object records;
 * free records (byte +1 bit 0) are skipped.
 */
void SaveRelocObjects(SaveObjectRec *o)
{
    short n = 100;

    do {
        unsigned f;

        f = o->flags & 1;
        if (f == 0) {
            o->link22 = RefRelocate(o->link22, (int)unit_array,
                                    save_reloc_state.raw >> 16);
            o->link1e = RefRelocate(o->link1e, (int)unit_array,
                                    save_reloc_state.raw >> 16);
        }
        o++;
    } while (--n != -1);
}
