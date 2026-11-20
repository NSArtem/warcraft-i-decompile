/* codegen-compiler: 10.0a */
#include "save_score.h"

struct Rect {
    long a;
    long b;
    long c;
};

struct Bitmap {
    short w;
    short h;
    unsigned char *data;
};

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
extern unsigned short dat_5abb0;
extern void fn_1eba0(void);
extern void BitmapBlit(void);
extern void LayerAdd(struct Bitmap *bm, const struct Rect *r, unsigned short id, unsigned short res, void (*blit)(void));

/* @0x25718 */
void ScoreInit(void)
{
    int i;

    score_page = 0;
    score_page_shown = 0;
    fn_1eba0();
    LayerAdd(&score_panel_bm, &score_panel_rect, 0x10, (unsigned short)(scenario_race + 0xe6), BitmapBlit);
    BitmapCloneAlloc(&score_panel_clean, &score_panel_bm);
    dat_5abb0 = 0;
    score_pool = 0x9c4;
    i = ((int)scenario_number - 0x77) / 2;
    if (i < 0 || i > 11)
        i = 11;
    score_cap = score_cap_tbl[i];
    score_rate = score_rate_tbl[i];
}
