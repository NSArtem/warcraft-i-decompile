/* status.h - the unit status / command panel (STATUS.C, 0x27b20..0x295d0).
 *
 * The panel is the 72x128 window at the bottom-left of the screen
 * (status_panel_rect at 0x53570: x 0..71, y 72..199, drawn into the offscreen
 * bitmap status_panel_bm 0x53568 and blitted as layer 0x13).  It shows the
 * displayed unit's portrait, name, health bar and the command buttons of its
 * unit type.  unit_panel_table (0x549c4, 61 x 14-byte entries) is the per-type
 * command card: a block of 0x14-byte CommandButton records plus a "content
 * changed?" and an extra-line painter.  Every button carries an availability
 * test, a label for the info line, a keyboard scan code and an action in the
 * order layer (CMD.C).
 *
 * Layout, data model and per-function notes: docs/subsystems/status.md.
 * Unit record offsets: docs/subsystems/game_2c4e0.md.
 */
#ifndef WC1_STATUS_H
#define WC1_STATUS_H

/* ---------------------------------------------------------------- records */

/* A rectangle {left, top, right, bottom, width, height} as the graphics
 * library uses it. */
typedef struct Rect {
    short x1;
    short y1;
    short x2;
    short y2;
    short w;
    short h;
} Rect;

/* An 8-bit bitmap: size plus the GdsAlloc'd pixel data (8 bytes; the game
 * keeps these in place, e.g. 0x53528). */
typedef struct Bitmap {
    unsigned short w;
    unsigned short h;
    void *data;
} Bitmap;

/* The selected unit (0x5c bytes).  Only the fields this area reads are
 * named; the rest is the layout of docs/subsystems/game_2c4e0.md. */
typedef struct Unit {
    short x;                    /* 0x00 pixel position */
    short y;                    /* 0x02 */
    unsigned short anim;        /* 0x04 animation script offset */
    unsigned char anim_phase;   /* 0x06 */
    unsigned char anim_frame;   /* 0x07 */
    unsigned char dir;          /* 0x08 facing */
    unsigned char pad09;        /* 0x09 */
    short tx;                   /* 0x0a tile position */
    short ty;                   /* 0x0c */
    unsigned short sflags;      /* 0x0e secondary flags (0x10 = busy) */
    unsigned short flags;       /* 0x10 main flags (0x80 = dead/dying) */
    unsigned char pad12[4];     /* 0x12 */
    unsigned short hp;          /* 0x16 */
    unsigned char pad18[2];     /* 0x18 */
    unsigned char damage;       /* 0x1a health fraction 0..255 */
    unsigned char type;         /* 0x1b unit type 0..0x35 */
    unsigned char type_copy;    /* 0x1c type the panel shows (menu id) */
    unsigned char sprite;       /* 0x1d */
    unsigned char owner;        /* 0x1e */
    unsigned char order;        /* 0x1f */
    unsigned char next_order;   /* 0x20 */
    unsigned char next_arg;     /* 0x21 */
    unsigned char path[20];     /* 0x22 */
    unsigned short timer;       /* 0x36 */
    unsigned short timer2;      /* 0x38 */
    unsigned char pad3a[4];     /* 0x3a */
    unsigned char prod_type;    /* 0x3e unit type being built/trained */
    unsigned char pad3f[7];     /* 0x3f */
    union {                     /* 0x46: two views of the same dword */
        unsigned long progress; /*   build/training progress */
        struct {
            unsigned char b0, b1, b2;
            unsigned char state; /* 0x49 carrying (0x20) / loaded (0x80) */
        } b;
    } work;
    unsigned char pad4a[4];     /* 0x4a */
    unsigned char dest;         /* 0x4e work state */
    unsigned char pad4f[1];     /* 0x4f */
    short dest_x;               /* 0x50 */
    short dest_y;               /* 0x52 */
    unsigned long target;       /* 0x54 target unit / gold left */
    unsigned long damage_bm;    /* 0x58 */
} Unit;

/* A command button: the 0x14-byte records of the blocks the per-type
 * descriptor points at (e.g. 0x53b00 for the footman/grunt card).  The action
 * pointer sits at offset 0x0f - the original's record is byte-packed with a
 * trailing pad, hence the packing here. */
#pragma pack(1)            /* not push/pop: Watcom 10.0a knows only pack(n) / pack() */
typedef struct CommandButton {
    unsigned short icon;        /* 0x00 icon slot 0..5 -> command_button_rect */
    unsigned short face;        /* 0x02 frame in unit_icon_grp */
    unsigned short (*available)(short is_unit); /* 0x04 */
    const char *label;          /* 0x08 text for the info line */
    unsigned char key;          /* 0x0c keyboard scan code */
    unsigned char kind;         /* 0x0d 1 = build/train (arg = unit type) */
    unsigned char arg;          /* 0x0e order argument / research row */
    void (*action)(unsigned char arg); /* 0x0f order-layer command */
    unsigned char pad13;        /* 0x13 */
} CommandButton;
#pragma pack()             /* back to the command line's -zp */

/* One entry of unit_panel_table (0x549c4), one per unit type (and per build
 * menu 0x35..0x3c). */
typedef struct UnitPanel {
    unsigned short nbuttons;         /* +0 count of buttons in *buttons */
    const CommandButton *buttons;    /* +2 */
    unsigned short (*changed)(void); /* +6 "panel content changed?" */
    void (*draw)(void);              /* +0xa extra lines (0 = none) */
} UnitPanel;

/* --------------------------------------------------------------- globals */

/* Scenario mask and per-player upgrades (SetCheatFlags 0x1284c, fn_104b0). */
extern unsigned long scenario_unit_mask;         /* 0x50004 */
extern unsigned char dat_50008[10][5];           /* 0x50008 player_upgrade */
extern unsigned char upgrade_level_cost[];       /* 0x51880 */

/* Per-player counters the panel shows. */
extern unsigned short player_selection_count[2]; /* 0x5a110 */
extern unsigned short net_event_pending;         /* 0x5a11a */
extern unsigned short player_active_men[4];      /* 0x58e28 */
extern unsigned short player_summoned[5];        /* 0x58dce */
extern unsigned short player_food[5];            /* 0x58de2 */
extern unsigned short player_mills[5];           /* 0x58e0a */
extern unsigned short player_blacksmiths[5];     /* 0x58e14 */
extern unsigned short player_stables[5];         /* 0x58e3c */
extern void *player_town_hall[5];                /* 0x58db0 */

/* Panel state. */
extern const CommandButton *status_button;       /* 0x5a2c0 hovered button */
extern Unit *status_unit;                        /* 0x5a2c4 displayed unit */
extern Unit *status_unit_req;                    /* 0x5a2c8 requested unit */
extern const Rect *status_button_rect;           /* 0x5a2cc hovered rect */
extern unsigned short status_dirty;              /* 0x5a2d0 redraw request */
extern unsigned short status_unused_d2;          /* 0x5a2d2 (never read) */
extern unsigned short status_men_used;           /* 0x5a2d4 cached "used" */
extern unsigned short status_lock;               /* 0x5a2d6 input lock */
extern unsigned short status_men_grown;          /* 0x5a2d8 cached "grown" */
extern unsigned short status_visible;            /* 0x5a2da */
extern unsigned short status_unit_type;          /* 0x5a2dc shown type */
extern unsigned short status_sel_count;          /* 0x5a2de shown count */
extern unsigned short status_pressed;            /* 0x5a2e0 armed */
extern unsigned char status_work_state;          /* 0x5a2e2 */
extern unsigned char status_flags_cache;         /* 0x5a2e3 */
extern unsigned long status_progress_cache;      /* 0x5a2e4 */
extern char status_text_prod[0x54];              /* 0x5a2e8 */
extern char status_text_repair[0x14];            /* 0x5a268 */
extern unsigned short status_hp_cache[4];        /* 0x5a2b8 */
extern unsigned short status_damage_cache[4];    /* 0x5a260 */
extern unsigned short status_help_kind;          /* 0x5a420 */
extern unsigned short status_help_gold;          /* 0x5a422 */
extern unsigned short status_help_lumber;        /* 0x5a424 */
extern const char *status_help_text;             /* 0x59500 */
extern const char *status_text;                  /* 0x55148 */

/* The STATUS.C string pool (analysis/symbols/status.toml). */
extern const char str_menu[];                    /* 0x57d40 "menu (@1F10@2)" */
extern const char str_food_usage[];              /* 0x57d50 "food usage:" */
extern const char str_used[];                    /* 0x57d5c "used %d" */
extern const char str_grown[];                   /* 0x57d64 "grown %d" */
extern const char str_gold_left[];               /* 0x57d70 "gold left" */
extern const char str_long[];                    /* 0x57d7c "%ld" */
extern const char str_training[];                /* 0x57d80 "training a%s" */
extern const char str_building_wall[];           /* 0x57d90 "building a wall" */
extern const char str_repair_cost[];             /* 0x57da0 */
extern const char str_carrying_gold[];           /* 0x57dc8 */
extern const char str_carrying_lumber[];         /* 0x57dd8 */
extern const char str_select_target[];           /* 0x57de8 */

/* Panel artwork, geometry and the command-card data. */
extern Bitmap status_bar_icon_bm;                /* 0x53520 */
extern Bitmap status_info_bm_normal;             /* 0x53528 */
extern Bitmap status_info_bm_pressed;            /* 0x53530 */
extern Bitmap status_button_bm_normal;           /* 0x53538 */
extern Bitmap status_button_bm_pressed;          /* 0x53540 */
extern Bitmap status_panel_art;                  /* 0x53548 */
extern Bitmap status_carry_bm[2];                /* 0x53550 gold, 0x53558 lumber */
extern const unsigned char *unit_icon_grp;       /* 0x53560 */
extern const unsigned char *unit_portrait_grp;   /* 0x53564 */
extern Bitmap status_panel_bm;                   /* 0x53568 */
extern Rect status_panel_rect;                   /* 0x53570 */
extern unsigned char bar_color_table[3][2];      /* 0x5357c */
extern Rect status_info_src_rect;                /* 0x53584 */
extern Rect status_info_rect;                    /* 0x53590 */
extern Rect command_button_rect[6];              /* 0x514e4 */
extern const UnitPanel unit_panel_table[0x3d];   /* 0x549c4 */
extern const CommandButton status_info_button;   /* 0x53aec */
extern const unsigned short unit_max_hp[];       /* 0x51978 */
extern const unsigned short unit_lumber_cost[];  /* 0x51a84 */
typedef struct UnitName {                        /* unit_names entry, 8 bytes */
    unsigned short face;        /* +0 frame in unit_portrait_grp/unit_icon_grp */
    unsigned short flags;       /* +2 1 for the spellcasters and some monsters */
    const char *name;           /* +4 */
} UnitName;
extern const UnitName unit_names[0x36];          /* 0x54e54 */
extern const char *const unit_suffix_train[];    /* 0x5506c " training a%s" */
extern const char *const research_text[];        /* 0x550f8 research descriptions */
extern const unsigned char score_value[];        /* 0x51a4c */

/* ------------------------------------------------------------- graphics */
extern Bitmap *cur_bitmap;                       /* 0x55438 */
extern void *cur_font;                           /* 0x5acf0 */
extern unsigned char draw_color;                 /* 0x5ad30 */
extern unsigned char score_font[8];              /* 0x59228 (a font object) */
extern short dirty_x1, dirty_y1, dirty_x2, dirty_y2, dirty_w, dirty_h; /* 0x5acd0 */
extern void (*status_frame_callback)(void);      /* 0x59414 */
extern void (*status_click_callback)(void);      /* 0x5941c */
extern void (*status_mouse_callback)(void *pt);  /* 0x5940c */

void TextSetColorBase(unsigned char c);          /* 0x32030 */
void DrawText(short x, short y, const char *s);  /* 0x31dcc */
void FillRect(short x, short y, unsigned short w, unsigned short h); /* 0x326a0 */
void BitmapBlit(short x, short y, const Bitmap *src, const Rect *src_rect);  /* 0x32410 */
void BitmapBlitAll(short x, short y, const Bitmap *src);            /* 0x33b00 */
void BitmapBlitTransparentAll(short x, short y, const Bitmap *src); /* 0x326f0 */
void GrpFrameBitmap(const unsigned char *grp, unsigned char frame, Bitmap *out); /* 0x33110 */
void ScreenUpdate(void);                         /* 0x321e8 */
void LayerInvalidate(unsigned char id);          /* 0x31f70 */
void DirtyRectUnion(const Rect *r);              /* 0x328c0 */
void DirtyRectAddBox(short x1, short y1, short x2, short y2); /* 0x33a30 */
int sprintf(char *buf, const char *fmt, ...);    /* 0x31be2 */
void *GdsAlloc(unsigned size);                   /* 0x32558 */
void GdsFree(void *p);                           /* 0x32780 */
void ResourceBegin(unsigned short id, void *len);/* 0x31870 */
void *ResourceRead(void *dest, unsigned count);  /* 0x32740 */
void ResourceReadHeaderBody(void *dst, void *arg); /* 0x323e0 */
void LayerAdd(Bitmap *bm, const Rect *rect, unsigned short id,
              unsigned short res, void (*blit)());                 /* 0x21d0c */
void LayerFree(Bitmap *bm);                      /* 0x21cf0 */
void SetCursorShape(unsigned char id);           /* 0x13dd0 */
void GameScreenInputInit(void);                  /* 0x1a328 */
void StatusHelpTextSet(const char *text);        /* 0x19f80 */
void NetSendControlPacket(unsigned short id);    /* 0x21c20 */

/* Selection iterator (mod_25ba0).  The original declares SelectionFirst with
 * an unspecified argument list: the cancel-button gates call it with the
 * constants 0x62/0x63 (which the iterator ignores), every other caller passes
 * nothing, and eax keeps the caller's value. */
Unit *SelectionFirst();                          /* 0x25cc4 */
Unit *SelectionNext();                           /* 0x25c50 */

/* The panel's own functions (this area). */
unsigned short UnitPanelStateChanged(void);
unsigned short FarmPanelChanged(void);
unsigned short GoldMinePanelChanged(void);
unsigned short WorkerPanelChanged(void);
void FarmPanelDraw(void);
void GoldMinePanelDraw(void);
void StatusTextForUnit(void);
void StatusPanelCacheUnitState(void);
void StatusPanelDraw(void);
void HealthBarDraw(short x, short y, const Unit *u);
void HealthBarDrawSingle(void);
void ProgressBarDraw(void);
void UnitPanelDraw(const UnitPanel *panel);
void StatusPanelTextRefresh(short x, short y);
void UnitPanelUpdate(void);
void StatusPanelLockAdjust(short on);
void StatusPanelLockClear(void);
unsigned short StatusPanelLockGet(void);
void StatusPanelPressUpdate(const void *pt);
void StatusPanelClick(const void *pt);
void StatusPanelShow(const void *pt);
unsigned short StatusPanelHandleKey(const void *evt);
void StatusPanelSetUnit(Unit *u);
void StatusPanelInit(void);
void StatusPanelFree(void);

/* The panel's command-card callbacks (this area). */
unsigned short CanCancelUpgrade(short is_unit);
unsigned short CanCancelTraining(short is_unit);
unsigned short CanCancelConstruction(short is_unit);
unsigned short CanBuildBasicStructure(short is_unit);
unsigned short CanBuildAdvancedStructure(short is_unit);
unsigned short OneUnitSelected(short is_unit);
unsigned short CanBuildBlacksmith(short is_unit);
unsigned short CanBuildChurch(short is_unit);
unsigned short CanBuildStable(short is_unit);
unsigned short CanBuildTower(short is_unit);
unsigned short CanRebuildTownHall(short is_unit);
unsigned short SelectionIsWorkersFalse(short is_unit);
unsigned short ButtonAvailable(const CommandButton *b);
void ButtonDraw(const CommandButton *b, short pressed);
unsigned short ResearchCost(unsigned short player, unsigned char row,
                            const unsigned char **level);

#endif /* WC1_STATUS_H */
