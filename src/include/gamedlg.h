/* gamedlg.h - GAMEDLG.C (0x1a3c0..0x1af20): the game's modal dialog boxes.
 *
 * Every dialog in this module is a "page" resource (an id in the 0xff..0x1dc
 * range) run by the generic box routine DialogBox 0x180a8; the page carries
 * the frame, the caption, the buttons and their action numbers.  The module
 * wraps DialogRun with the screen switch (ModalScreen 0x1a560, which allocates
 * a full-screen modal layer and hides the in-game UI layers 13..22), the
 * per-race frame offset (id + scenario_race: each page has a human and an orc
 * variant) and one function per dialog.
 *
 * Layout, page table and per-function notes: docs/subsystems/gamedlg.md.
 */
#ifndef WC1_GAMEDLG_H
#define WC1_GAMEDLG_H

/* ---------------------------------------------------------------- records */

/* An 8-bit bitmap: size plus the pointable pixel data (graphics.toml). */
typedef struct Bitmap {
    unsigned short w;
    unsigned short h;
    void *data;
} Bitmap;

/* One screen layer (graphics.toml/playflic.h `layers`): 32 entries of 18
 * bytes at 0x5aa90.  Layer 23 is the modal dialog's full-screen layer
 * (0x5ac2e). */
typedef struct Layer {
    unsigned short active;              /* +0 */
    short x, y;                         /* +2, +4 */
    short w, h;                         /* +6, +8 */
    void *data;                         /* +0xa */
    void (*draw)(short x, short y, const Bitmap *src, const void *rect);  /* +0xe */
} Layer;

/* The 5-dword preferences block 0x532b4 (PREFS.WAR), which is also the
 * parameter block the Options page edits (OptionsDialog 0x1a800). */
typedef struct Prefs {
    long game_speed;                    /* +0x0  0..6, the page's 7 labels */
    unsigned int music_volume;          /* +0x4  = opt_music_volume 0x532b8 */
    unsigned int sfx_volume;            /* +0x8  = opt_sfx_volume 0x532bc */
    unsigned int mouse_scroll;          /* +0xc  = 0x532c0 */
    unsigned int key_scroll;            /* +0x10 = 0x532c4 */
} Prefs;

/* The Options page's parameter block: the preferences, then the two callbacks
 * the page invokes (OptionsRefresh/OptionsApplyTimer) and the apply timer. */
typedef struct OptionsParams {
    Prefs prefs;
    void (*refresh)(struct OptionsParams *p);   /* +0x14 */
    int (*timer)(struct OptionsParams *p);      /* +0x18 */
    unsigned long next_apply;                   /* +0x1c clock tick */
} OptionsParams;

void OptionsRefresh(struct OptionsParams *p);   /* 0x1a79c */
int OptionsApplyTimer(struct OptionsParams *p); /* 0x1a778 */

/* ------------------------------------------------------------ the runtime */

/* 0x180a8 DialogRun (named in analysis/symbols/mod_16390.toml): run page `id`
 * at (x, y) for the page's text layer and with the parameter block `params`;
 * returns the action number of the button the player pressed. */
unsigned short DialogRun(unsigned int id, short x, short y,
                         unsigned short layer, void **params);

/* 0x1a560: the modal screen switch around every page (see the .md). */
void ModalScreen(short on, short dim);          /* 0x1a560 */
void ModalDepthReset(void);                     /* 0x1a714 */

/* 0x1a3c0/0x1a4b8: the dark red "network waiting" screen. */
void BuildDimPalette(unsigned char *map);       /* 0x1a3c0 */
void DimScreenImage(void);                      /* 0x1a4b8 */

/* Print a message in a race-specific frame (the page id gets the
 * scenario_race offset added); returns "the player dismissed the box". */
unsigned short ShowMessageRace(const char *text, unsigned short id);  /* 0x1a720 */
unsigned short ShowMessage(const char *text, unsigned short width,
                           unsigned short height);                   /* 0x1a894 */

/* The dialogs. */
void OptionsDialog(void);                       /* 0x1a800 */
void VersionMismatchDialog(void);               /* 0x1a8e4 */
void SaveVersionDialog(void);                   /* 0x1a914 */
void TwoPlayerComputerDialog(void);             /* 0x1a95c */
unsigned short NetTimeoutDialog(void);          /* 0x1a9a4 */
void VictoryDialog(void);                       /* 0x1aa7c */
void DefeatDialog(void);                        /* 0x1ab28 */
unsigned short QuitDialog(void);                /* 0x1ab50 */
unsigned short GameSaveDialog(void);            /* 0x1abc0 */
void SaveErrorDialog(void);                     /* 0x1aca8 */
unsigned short GameLoadDialog(void);            /* 0x1accc */
void HelpScreen(void);                          /* 0x1ade4 */
void GameMenuDialog(void);                      /* 0x1ae70 */

void NetPumpEvents(void);          /* 0x19b80 (mod_19b80) */
void GameScreenInputInit(void);    /* 0x1a328 (mod_19b80) */

/* ------------------------------------------------------------------- data */

extern Bitmap backbuf_bm;                   /* 0x5a870 */
extern Bitmap *cur_bitmap;                  /* 0x55438 */
extern Layer layers[32];                    /* 0x5aa90 */
extern unsigned char palette[];             /* 0x58f20 */
extern unsigned char palette_target[];      /* 0x62570 */
extern short screen_mode;                   /* 0x593f6 */
extern short game_mode;                     /* 0x59616 */
extern unsigned short net_play_flag;        /* 0x52586 */
extern unsigned short net_event_pending;    /* 0x5a11a */
extern unsigned short scenario_race;        /* 0x50088 */
extern unsigned short setup_quit;           /* 0x5176a */
extern unsigned short load_not_cancelled;   /* 0x516b0 */
extern unsigned short dat_5a7c2;            /* 0x5a7c2 */
extern const char *status_help_text;        /* 0x59500 */
extern Prefs prefs_block;                   /* 0x532b4 */
extern unsigned int opt_music_volume;       /* 0x532b8 */
extern unsigned int opt_sfx_volume;         /* 0x532bc */
extern unsigned int opt_mouse_scroll;       /* 0x532c0 */
extern unsigned int opt_key_scroll;         /* 0x532c4 */
extern unsigned short cfg_dig_driver;       /* 0x59902 */
extern unsigned short cfg_mdi_driver;       /* 0x59912 */
extern void *slot_file;                     /* 0x59610 */
extern unsigned short save_slot;            /* 0x593cc */
extern void (*event_handlers[])(void *ev);  /* 0x59400, 10 entries */
extern long game_speed_cache;               /* 0x594f0 */
extern short dirty_x1, dirty_y1, dirty_x2, dirty_y2;    /* 0x5acd0 */
extern short dirty_w, dirty_h;                          /* 0x5acd8 */

/* The module's own state: the modal layer's bitmap (0x59620), the saved
 * "layer active" words of layers 13..22 (0x59628), the nesting counter
 * (0x5963c) and the two flags 0x517cc/0x51e24. */
extern Bitmap dialog_bitmap;                /* 0x59620 */
extern void *dialog_buffer;                 /* 0x59624 */
extern unsigned short dialog_layer_state[10];  /* 0x59628 */
extern unsigned short dialog_depth;         /* 0x5963c */
extern unsigned short dialog_enabled;       /* 0x517cc */
extern unsigned short dialog_active;        /* 0x51e24 */

unsigned long ResourceBegin(unsigned short id, unsigned long *packed_len); /* 0x31870 */
void *ResourceRead(void *dest, unsigned count);          /* 0x32740 */
void GdsFree(void *p);                                  /* 0x32780 */
void *GdsAlloc(unsigned size);                          /* 0x32558 */
void BitmapBlitAll(short x, short y, const Bitmap *src);/* 0x33b00 */
void BitmapBlit(short x, short y, const Bitmap *src, const void *srcrect);  /* 0x32410 */
void PaletteSet(unsigned char first, unsigned short count,
                const unsigned char *rgb);              /* 0x33150 */
void DirtyRectAddBox(short x1, short y1, short x2, short y2);  /* 0x33a30 */
void DirtyRectAlignAndPresent(void);                    /* 0x33aa0 */
void ScreenUpdate(void);                                /* 0x321e8 */
void SndApplyOptions(const int *opts);                  /* 0x2674c */
long clock(void);                                       /* 0x30e98 */
int fclose(void *fp);                                   /* 0x33887 */
void SaveWriteImage(void *fp);                          /* 0x24bf0 */
void *SaveSlotCreate(unsigned short height, unsigned short id,
                     short *cancelled);                 /* 0x14ad8 */
void *SaveSlotOpen(int layer, int dialog_id, short *cancelled);  /* 0x1498c */

#endif
