/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "save_score.h"

extern unsigned long harvested_gold[5];
extern unsigned long harvested_lumber[5];
extern char score_txt_harvest[];
extern unsigned short score_stats[6];
extern int sprintf(char *buf, const char *fmt, ...);

/* @0x2553c */
int ScorePageHarvest(int page_changed)
{
    char buf[256];

    if ((short)page_changed != 0
        || *(unsigned long *)&score_stats[0] != harvested_gold[0]
        || *(unsigned long *)&score_stats[2] != harvested_lumber[0]) {
        *(unsigned long *)&score_stats[0] = harvested_gold[0];
        *(unsigned long *)&score_stats[2] = harvested_lumber[0];
        page_changed = 1;
    }
    if ((short)page_changed != 0) {
        sprintf(buf, score_txt_harvest, *(unsigned long *)&score_stats[0],
                *(unsigned long *)&score_stats[2]);
        ScorePanelText(buf);
    }
    return page_changed;
}
