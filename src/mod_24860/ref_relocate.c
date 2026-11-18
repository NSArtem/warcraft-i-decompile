/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Byte-matched function of module mod_24860 (the save-file loader/writer),
 * taken from C by the build (src = ... in analysis/symbols/mod_24860.toml).
 *
 * This file holds one function because the module also contains the loader
 * SaveLoadImage 0x24900, which is reference C (save_io_reference.c), so two
 * built functions could not be placed in sequence.  See
 * docs/subsystems/save_format.md.
 */
#include "mod_24860.h"

/* @0x248e0  convert one reference between "offset from a base" and
 * "absolute pointer" form.
 *
 * to_offset != 0 is the save direction (pointer -> offset), 0 the load
 * direction (offset -> pointer).  The sentinel differs: a null pointer is
 * stored as -1, and -1 loads back as null.  Called by the record rebasing
 * helpers below (0x24a90 etc. with to_offset = save_reloc_state.w.mode) and
 * by the packet code at 0x21637 (to_offset = 0: an id from a unit list
 * becomes a unit pointer, -1 becomes null).
 */
int RefRelocate(int ref, int base, short to_offset)
{
    if (to_offset) {
        if (ref == 0)
            return -1;
        return ref - base;
    }
    if (ref == -1)
        return 0;
    return ref + base;
}
