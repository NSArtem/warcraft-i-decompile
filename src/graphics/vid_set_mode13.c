/* codegen-flags: -s -ot -ol -4r -d1+ -zp2
 * codegen-compiler: 10.0a
 * Module mod_31d40 (0x31d40..0x31dc0), DBG style, BIOS video mode switch.
 *
 * The two BIOS calls are written as `#pragma aux` bodies (the Watcom way to
 * emit a fixed instruction sequence); the rest is plain C.  Compiled-C
 * behaviour is difftested against the original in tests/test_graphics_lib.py
 * (the int 10h handler is a Python model there).
 */
#include <string.h>
#include "graphics.h"

#pragma aux bios_get_video_mode = "mov ah,0x0f" "int 0x10" \
        parm [] value [eax] modify exact [eax];
#pragma aux bios_set_video_mode = "int 0x10" parm [ax] modify exact [eax];

void __cdecl FatalError(const char *fmt, ...);          /* 0x30bf0 */
extern const char vga_required_msg[];                   /* 0x57e84 */

/* @0x31d40  switch to mode 13h, remember the text mode we came from (the
 * BIOS reports it in al), publish the 320x200 framebuffer descriptor and
 * abort if the mode did not take. */
void VidSetMode13(void)
{
    saved_video_mode = (unsigned char)bios_get_video_mode();
    bios_set_video_mode(0x13);
    vga_bm.w = 0x140;
    vga_bm.h = 0xc8;
    vga_bm.data = (unsigned char *)0xa0000;
    if (((unsigned)bios_get_video_mode() & 0xff) != 0x13)
        FatalError(vga_required_msg);
}
