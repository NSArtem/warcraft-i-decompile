/* codegen-compiler: 10.0a */
#include "graphics.h"
#include "save_score.h"

extern unsigned short scenario_race;
extern unsigned short scenario_number;
extern struct Rect score_panel_rect;
extern struct Bitmap score_panel_bm;
extern struct Bitmap score_panel_clean;
extern unsigned short score_cap_tbl[12];
extern unsigned short score_rate_tbl[12];
extern unsigned short score_rate;
extern unsigned short score_pool;
extern unsigned short score_page_shown;
extern unsigned short score_cap;
extern unsigned short score_page;
extern void MinimapPanelInit(void);
extern void LayerAdd(Bitmap *bm, const Rect *r, unsigned short id, unsigned short res, void (*blit)());

/* @0x25718 */
void ScoreInit(void)
{
    int i;

    score_page = 0;
    score_page_shown = 0;
    MinimapPanelInit();
    LayerAdd(&score_panel_bm, &score_panel_rect, 0x10, (unsigned short)(scenario_race + 0xe6), BitmapBlit);
    BitmapCloneAlloc(&score_panel_clean, &score_panel_bm);
    layers[0x10].active = 0;
    score_pool = 0x9c4;
    i = ((int)scenario_number - 0x77) / 2;
    if (i < 0 || i > 11)
        i = 11;
    score_cap = score_cap_tbl[i];
    score_rate = score_rate_tbl[i];
}
