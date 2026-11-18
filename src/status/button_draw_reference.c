/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -zp2 */
/* Reference C for 0x284a8 ButtonDraw (STATUS.C): the background bitmap of a
 * command button plus its icon frame; the info-line pseudo button has its own
 * background.  One function per file so every callee is an external symbol
 * (the T4 difftest stubs them). */
#include "status.h"

/* 0x284a8 - draw one command button: background (normal/pressed bitmap at
 * command_button_rect[b->icon]) and the icon frame b->face of unit_icon_grp
 * on top of it.  The info line (status_info_button, 0x53aec) uses its own
 * background at (3,0x74).  Unavailable buttons are not drawn. */
void ButtonDraw(const CommandButton *b, short pressed)
{
    Bitmap icon;
    const Bitmap *bg;
    short x;
    short y;

    if (b == &status_info_button) {
        BitmapBlit(3, 0x74, pressed ? &status_info_bm_pressed : &status_info_bm_normal,
                   &status_info_src_rect);
        return;
    }
    if (!ButtonAvailable(b))
        return;
    /* 0x284f2-0x28513: x = rect.x1 is read first, then y = rect.y1-0x48, and
     * x stays in a register (edi) while y is spilled */
    x = command_button_rect[b->icon].x1;
    y = command_button_rect[b->icon].y1 - 0x48;
    bg = pressed ? &status_button_bm_pressed : &status_button_bm_normal;
    BitmapBlitAll(x, y, bg);
    x = x + 2;
    y = y + 2 + (pressed != 0);
    GrpFrameBitmap(unit_icon_grp, b->face, &icon);
    BitmapBlitAll(x, y, &icon);
}
