/*
 * Declarations for the save_score area (analysis/symbols/save_score.toml,
 * docs/subsystems/save_score.md): the SAVE.C module 0x23ec0..0x24860 (the
 * two-player link half of saving/loading) and the SCORE.C module
 * 0x24e50..0x25820 (per-player score accounting, rank titles and the 72x72
 * score panel).
 *
 * Every layout here is derived from field accesses listed as evidence in the
 * symbol database; compile with -zp2 (structure packing 2,
 * docs/subsystems/codegen.md).
 *
 * File layout of the reconstructed C (docs/subsystems/save_score.md
 * section 7): the byte-matched functions are in save.c / score.c (taken
 * from C by the build); the reference reconstructions that OW2 cannot
 * reproduce byte-identically are in save_reference.c / score_reference.c
 * and are verified differentially in tests/test_save_score.py.
 */
#ifndef SAVE_SCORE_H
#define SAVE_SCORE_H

/* ---------------------------------------------------------------- link layer
 * A link message is the 16-byte buffer at 0x5a000: {u8 size; u8 type|flags;
 * u16 sequence; u8 payload[12]}.  The send routine fn_131d8 stamps the
 * sequence word at +2 and copies the record into the 10 x 136-byte ring at
 * 0x58848 (see docs/subsystems/save_score.md).  Message types: 1 "nothing",
 * 2 game identity, 4 raw data, 5 save/load event; receivers mask with 0x3f.
 */
typedef struct NetRecord {          /* the 12-byte game-identity block */
    unsigned long local_time;       /* +0x00 own [0x532b4] (game start stamp) */
    unsigned long now;              /* +0x04 time(NULL)                       */
    unsigned char campaign;         /* +0x08 [0x52584] low byte               */
    unsigned char cd_present;       /* +0x09 [0x52518]                        */
    unsigned char version;          /* +0x0a always 0x25                      */
    unsigned char side_flags;       /* +0x0b [0x52a5e]                        */
} NetRecord;

/* The 18-byte block the load/save sync message carries (net_sync_msg): the
 * 12-byte NetRecord plus two counter words that NetLoadSyncMessage range
 * checks with WordInRange. */
typedef struct NetSync {
    unsigned long local_time;       /* +0x00 */
    unsigned long now;              /* +0x04 */
    unsigned char campaign;         /* +0x08 */
    unsigned char cd_present;       /* +0x09 */
    unsigned char version;          /* +0x0a */
    unsigned char side_flags;       /* +0x0b */
    unsigned short counter;         /* +0x0c */
    unsigned short counter_other;   /* +0x0e */
} NetSync;

/* Value inside the inclusive interval [lo, hi], endpoints in either order
 * (0x2417c; both callers use a +/-10 tolerance window).  Byte-matched:
 * src/save_score/save.c. */
int WordInRange(unsigned short value, unsigned short lo, unsigned short hi);

/* ---------------------------------------------------------------- score layer
 * The score adjusters take the unit whose state changed and read only its
 * player index (byte +0x1e of the 0x5c-byte unit record, documented by the
 * game_2c4e0 area); `struct Unit` is therefore forward-declared, not
 * repeated here.  `struct Bitmap` is the 8-byte library descriptor
 * { short w, h; unsigned char *data; } owned by the graphics area -
 * likewise only forward-declared, the layout used by this area is in
 * src/save_score/score_reference.c.
 */
struct Unit;
struct Bitmap;

unsigned short TotalActiveMen(void);                        /* 0x24e50 */
unsigned short TotalActiveBuildings(void);                  /* 0x24e70 */
void ScoreTickIncome(void);                                 /* 0x24e90 */
void ScoreAddForMen(struct Unit *u);                        /* 0x24ee0 */
void ScoreAddForBuildings(struct Unit *u);                  /* 0x24fa0 */
void ScoreSubForMen(struct Unit *u);                        /* 0x2505c */
void ScoreSubForBuildings(struct Unit *u);                  /* 0x250fc */
void ScoreOnMenKilled(unsigned short killer, struct Unit *victim);   /* 0x25198 */
void ScoreOnBuildingKilled(unsigned short killer, struct Unit *victim); /* 0x2529c */

void BitmapCloneAlloc(struct Bitmap *dst, const struct Bitmap *src); /* 0x25390 */
void ScorePanelText(const char *s);                         /* 0x253cc */
int  ScorePageMen(int page_changed);                        /* 0x25428 */
int  ScorePageHarvest(int page_changed);                    /* 0x2553c */
char *RankName(void);                                       /* 0x255b8 */
int  ScorePageScore(int page_changed);                      /* 0x25600 */
void ScoreUpdate(void);                                     /* 0x25684 */
void ScoreInit(void);                                       /* 0x25718 */
void ScoreSetUncapped(void);                                /* 0x257c0 */
void ScoreFreePanels(void);                                 /* 0x257dc */
void ScoreSetPage(int page);                                /* 0x257f8 */

/* ---------------------------------------------------------------- SAVE.C */
int  NetLinkStart(void);                                    /* 0x23ec0 */
void NetLinkExit(void);                                     /* 0x240f8 */
unsigned char *SaveStreamValidate(unsigned char *pos);      /* 0x241a4 */
void GamesDifferDialog(void);                               /* 0x24304 */
void EnemyDidNotLoadDialog(void);                           /* 0x24344 */
void NotValidTwoPlayerDialog(void);                         /* 0x243c4 */
void NetLoadSyncMessage(struct NetSync *msg);               /* 0x2445c */
int  NetQueryRemoteEvent(void *buf);                        /* 0x2461c */
int  NetSendLocalEvent(void *buf);                          /* 0x246b4 */
/* 0x24780: watcall args are (eax, edx) = (len, data) - the length is the
 * FIRST argument (0x24781 tests ax, memcpy's ebx count comes from ax). */
void NetSendDataMessage(unsigned short len, void *data);    /* 0x24780 */
/* 0x247d0: the `cwde' at 0x247e1 sign-extends the 16-bit selector before
 * the fn_12f24 poll. */
int  NetRecvDataMessage(short which, void *dst);            /* 0x247d0 */

#endif /* SAVE_SCORE_H */
