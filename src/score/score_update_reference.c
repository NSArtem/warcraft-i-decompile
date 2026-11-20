/* codegen-compiler: 10.0a */
#include "save_score.h"

typedef struct DRect {
    long a;
    long b;
    long c;
} DRect;

extern DRect score_panel_rect;
extern short (*score_page_fns[4])(short);
extern unsigned short score_page_shown;
extern unsigned short score_page;
extern unsigned short dat_5abb0;
extern unsigned short dat_5abc2;
extern DRect dirty_x1;
extern void ScreenUpdate(void);

/* @0x25684 */
void ScoreUpdate(void)
{
    DRect saved;

    if (score_page_fns[score_page]((short)(score_page_shown != score_page)) != 0) {
        score_page_shown = score_page;
        if (score_page == 0) {
            dat_5abb0 = score_page;
            dat_5abc2 = 1;
        } else {
            dat_5abb0 = 1;
            dat_5abc2 = 0;
        }
        saved = dirty_x1;
        dirty_x1 = score_panel_rect;
        ScreenUpdate();
        dirty_x1 = saved;
    }
}
