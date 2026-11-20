/* codegen-compiler: 10.0a */
#include "save_score.h"

extern unsigned long scenario_unit_mask;
extern unsigned short dat_50098;
extern unsigned short player_score[4];
extern char score_txt_empty[];
extern char score_txt_score[];
extern unsigned short score_stats[6];
extern int sprintf(char *buf, const char *fmt, ...);

/* @0x25600 */
int ScorePageScore(int page_changed)
{
    char buf[256];
    unsigned short sc = player_score[0];
    char *rank;
    char *extra;

    if ((short)page_changed != 0 || sc != score_stats[0]) {
        score_stats[0] = sc;
        page_changed = 1;
    }
    if ((short)page_changed != 0) {
        rank = RankName();
        if (dat_50098 != 0)
            extra = (char *)&scenario_unit_mask + dat_50098;
        else
            extra = score_txt_empty;
        sprintf(buf, score_txt_score, score_stats[0], rank, extra);
        ScorePanelText(buf);
    }
    return page_changed;
}
