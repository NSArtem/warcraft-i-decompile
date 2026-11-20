/* codegen-compiler: 10.0a */
#include "save_score.h"

extern unsigned short dead_men[5];
extern unsigned short dead_buildings[5];
extern unsigned short dat_50dac[5];
extern unsigned short dat_50db6[5];
extern char score_txt_men[];
extern unsigned short player_active_buildings[4];
extern unsigned short player_active_men[4];
extern unsigned short score_stats[6];
extern int sprintf(char *buf, const char *fmt, ...);

/* @0x25428 */
int ScorePageMen(int page_changed)
{
    char buf[256];

    if ((short)page_changed != 0
        || score_stats[0] != player_active_men[0]
        || score_stats[3] != player_active_buildings[0]
        || score_stats[1] != dead_men[0]
        || score_stats[4] != dead_buildings[0]
        || score_stats[2] != dat_50dac[0]
        || score_stats[5] != dat_50db6[0]) {
        score_stats[0] = player_active_men[0];
        score_stats[3] = player_active_buildings[0];
        score_stats[1] = dead_men[0];
        score_stats[4] = dead_buildings[0];
        score_stats[2] = dat_50dac[0];
        score_stats[5] = dat_50db6[0];
        page_changed = 1;
    }
    if ((short)page_changed != 0) {
        sprintf(buf, score_txt_men, score_stats[0], score_stats[3], score_stats[1],
                score_stats[4], score_stats[2], score_stats[5]);
        ScorePanelText(buf);
    }
    return page_changed;
}
