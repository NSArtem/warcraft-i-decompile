/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * BitmapCloneAlloc (0x25390), built from C: T3 under Watcom 10.0a.  Split out of
 * src/save_score/score_reference.c (reference C under OW2), whose declarations it repeats;
 * one function per object (wcc386 aligns the next function).
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

/* @0x25390  bitmap "clone": fresh GDS allocation of w*h bytes + memcpy.
 * Near miss: OW2 keeps dst in ecx and never moves src out of edx (original:
 * dst in ebx, src saved to ecx, size in edx) - V3; ours is 2 bytes shorter
 * before the first call. */
void BitmapCloneAlloc(struct Bitmap *dst, const struct Bitmap *src)
{
    unsigned short n;

    dst->h = src->h;
    dst->w = src->w;
    n = dst->w * dst->h;
    dst->data = GdsAlloc(n);
    memcpy(dst->data, src->data, n);
}
