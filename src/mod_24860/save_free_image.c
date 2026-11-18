/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * SaveFreeImage (0x249e0), built from C: T3 under Watcom 10.0a.  Split out of
 * src/mod_24860/save_io_reference.c (reference C under OW2), whose declarations it repeats;
 * one function per object (wcc386 aligns the next function).
 */
#include "war.h"
#include "mod_24860.h"

/* @0x249e0  free the loaded image and clear its pointer.
 *
 * Near miss: the zero of the pointer store lives in edx (pushed/popped around
 * the call) in the original, in eax in OW2 (codegen.md V2, scratch register
 * for a constant store).
 */
void SaveFreeImage(void)
{
    GdsFree(save_image);
    save_image = 0;
}
