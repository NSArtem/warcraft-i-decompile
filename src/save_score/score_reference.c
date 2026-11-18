/* codegen-flags: -s -ot -ol -4r -zp2
 * REFERENCE C for SCORE.C (0x24e50..0x25820) - not built, no src = entry.
 * TotalActiveMen, TotalActiveBuildings, BitmapCloneAlloc and ScorePanelText
 * are T3 under Watcom 10.0a (2026-11-18) and built from their own files
 * (total_active_men.c, total_active_buildings.c, bitmap_clone_alloc.c,
 * score_panel_text.c); what follows is the OW2 history.
 *
 * Every function here has the same logic as the original (it is checked
 * differentially in tests/test_save_score.py), but `wc1.match` /
 * `wc1.codegen_sweep` report one register-allocation difference each: OW2
 * and the original Watcom disagree about *which* free register a value gets
 * (codegen.md section 4, V2/V3 - not steerable from C).  The guard test
 * test_reference_c_stays_a_near_miss asserts they stay non-matching; if one
 * starts matching under a future toolchain it must be promoted into
 * score.c.  See docs/subsystems/save_score.md section 6 for the exact
 * remaining diffs.
 */
#include "save_score.h"

/* ---- module data (evidence and addresses in save_score.toml) ---------- */
extern unsigned short player_score[4];             /* 0x50e34 */
extern unsigned short player_active_men[4];        /* 0x58e28 */
extern unsigned short player_active_buildings[4];  /* 0x58e00 */
extern unsigned short score_pool;                 /* 0x5a0ce */
extern unsigned short score_cap;                  /* 0x5a0d2 */
extern unsigned short score_rate;                  /* 0x5a0cc */
extern unsigned short score_page;                  /* 0x5a0d4 */
extern unsigned char score_value[20];              /* 0x51a4c */
extern unsigned short rank_thresholds[19];        /* 0x5318c */
extern char *rank_names_human[19];                 /* 0x531b4 */
extern char *rank_names_orc[19];                   /* 0x53200 */
extern unsigned short scenario_race;               /* 0x50088 (cmd_123f0) */
extern int game_state;                            /* 0x59614: high word =
                                                      game_mode (cmd_123f0) */

struct Bitmap { short w; short h; unsigned char *data; };  /* -zp2 */
extern struct Bitmap score_panel_bm;               /* 0x5314c */
extern struct Bitmap score_panel_clean;            /* 0x53154 */
extern unsigned char score_font[];                 /* 0x59228 */
extern struct Bitmap *cur_bitmap;                  /* 0x55438 (graphics) */
extern void *cur_font;                             /* 0x5acf0 (graphics) */
extern short text_line_gap;                        /* 0x5543e (graphics) */

extern void *GdsAlloc(unsigned size);              /* 0x32558 */
extern void *memcpy(void *dst, const void *src, unsigned n);
extern void TextSetColorBase(unsigned char c);      /* 0x32030 */
extern void DrawText(short x, short y, const char *s); /* 0x31dcc */

/* @0x24e50 TotalActiveMen: built from C (T3 under Watcom 10.0a) in src/save_score/total_active_men.c. */

/* @0x24e70 TotalActiveBuildings: built from C (T3 under Watcom 10.0a) in src/save_score/total_active_buildings.c. */

/* @0x24e90  player 0's per-tick income: score_rate (+500 in mode 6) out of
 * the shared pool, clamped at score_cap.
 * Near miss: OW2 keeps the sum in ebx and the cap in ecx (original: ecx/ebx)
 * - V3. */
void ScoreTickIncome(void)
{
    int delta = score_rate;
    int score, sum, cap;

    if (game_state >> 16 == 6)
        delta += 500;
    score = player_score[0];
    sum = score + delta;
    cap = score_cap;
    if (sum > cap)
        delta = cap - score;
    player_score[0] += delta;
    score_pool -= delta;
}

/* @0x25390 BitmapCloneAlloc: built from C (T3 under Watcom 10.0a) in src/save_score/bitmap_clone_alloc.c. */

/* @0x253cc ScorePanelText: built from C (T3 under Watcom 10.0a) in src/save_score/score_panel_text.c. */

/* @0x255b8  score -> rank index -> side-specific title.
 * Near miss: the loop counter lands in ecx (original: edx), so the saved
 * register pair is ebx/ecx instead of ebx/edx - V3. */
char *RankName(void)
{
    unsigned short score = player_score[0];
    int off, i, race;

    for (off = 0, i = 0; off < 0x24; off += 2, i++) {
        if (score <= *(unsigned short *)((unsigned)rank_thresholds + off))
            break;
    }
    race = scenario_race;
    if (race == 1)
        return rank_names_orc[i];
    return rank_names_human[i];
}

/* @0x257f8  page selector: 4 wraps to 0, > 4 clamps to 3.
 * Near miss: OW2 assigns the derived v to eax and evicts `page` to edx with
 * `mov edx,eax; xor eax,eax; mov ax,dx` (original: v in edx, `xor edx,edx;
 * mov dx,ax`, page keeps eax) - V3; 2 bytes longer. */
void ScoreSetPage(int page)
{
    int v = (unsigned short)page;

    if (v == 4)
        v = v ^ page;
    else if (v > 4)
        v = 3;
    score_page = v;
}
