/* codegen-compiler: 10.0a */
#include "mod_1eba0_f2.h"

extern void ScoreSetPage(int page); /* 0x1efa9 */
extern void MouseSetRange(unsigned xmin, unsigned ymin, unsigned xmax, unsigned ymax); /* 0x1efd1 */

void MinimapBeginScrollInput(void)
{
    ScoreSetPage(0);
    MouseSetRange((unsigned short)side_panel_rect_x1,
                  (unsigned short)side_panel_rect_y1,
                  (unsigned short)side_panel_rect_x2,
                  (unsigned short)side_panel_rect_y2);
    status_click_callback = MinimapEndScrollInput;
    status_frame_callback = MinimapEndScrollInput;
    status_mouse_callback = (void (*)(void *))MinimapScrollFromMouse;
    MinimapScrollFromMouse();
}
