/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * SaveSkipStream (0x249c8), built from C: T3 under Watcom 10.0a.  Split out of
 * src/mod_24860/save_io_reference.c (reference C under OW2), whose declarations it repeats;
 * one function per object (wcc386 aligns the next function).
 */
#include "war.h"
#include "mod_24860.h"

/* @0x249c8  skip `count` bytes of the loaded image; returns the new
 * position and subtracts the count from the bytes-left counter.
 *
 * Near miss: identical bytes except the scratch register of the zero-extended
 * count - OW2 uses ecx, the original ebx (codegen.md V3, register order).
 */
unsigned char *SaveSkipStream(unsigned count, unsigned char *pos)
{
    save_stream_left -= (unsigned short)count;
    return pos + (count & 0xffff);
}
