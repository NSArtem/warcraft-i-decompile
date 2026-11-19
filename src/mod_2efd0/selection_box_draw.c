/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* SelectionBoxDraw (0x2f3dc): viewport layer callback tail - outline the
 * drag rectangle in colour 0xdf while a drag is running.
 *
 * The original loads min_x/min_y through the dword two bytes before them
 * (`mov edx,[0x5a7d4]; sar edx,0x10`), i.e. the source kept a 32-bit view
 * of the pair; spelled here as such (the same idiom as SndSetSfxVolume and
 * game_state, docs/subsystems/codegen.md). */
#include "mod_2efd0.h"

/* The original signs the two short arguments straight from the 32-bit
 * expression (`mov edx,[0x5a7d4]; sar edx,0x10`), which 10.0a only emits
 * when the parameters are int; Open Watcom 2 keeps the header's declaration
 * (same ABI, it just compiles the file). */
#if __WATCOMC__ <= 1100
void RectOutline(int x, int y, unsigned short w, unsigned short h);
#endif

#define BOX_MIN_X (*(int *)((char *)&selection_box.min_x - 2) >> 16)
#define BOX_MIN_Y (*(int *)((char *)&selection_box.min_y - 2) >> 16)

/* @0x2f3dc */
void SelectionBoxDraw(void)
{
    if (!selection_box.visible)
        return;
    draw_color = 0xdf;
    RectOutline(BOX_MIN_X, BOX_MIN_Y, selection_box.w, selection_box.h);
}
