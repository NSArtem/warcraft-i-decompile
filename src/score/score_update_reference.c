/* codegen-compiler: 10.0a */
#include "graphics.h"
#include "save_score.h"

extern Rect score_panel_rect;
extern short (*score_page_fns[4])(short);
extern unsigned short score_page_shown;
extern unsigned short score_page;

/* @0x25684 */
void ScoreUpdate(void)
{
    Rect saved;

    if (score_page_fns[score_page]((short)(score_page_shown != score_page)) != 0) {
        score_page_shown = score_page;
        if (score_page == 0) {
            layers[0x10].active = score_page;
            layers[0x11].active = 1;
        } else {
            layers[0x10].active = 1;
            layers[0x11].active = 0;
        }
        /* The six dirty-rectangle words start at dirty_x1. */
        saved = *(Rect *)&dirty_x1;
        *(Rect *)&dirty_x1 = score_panel_rect;
        ScreenUpdate();
        *(Rect *)&dirty_x1 = saved;
    }
}
