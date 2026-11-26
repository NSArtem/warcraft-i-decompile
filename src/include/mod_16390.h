/* DLGS.C-descended dialog engine and epilogue screen (war.exe 0x16390..0x19020).
 * See analysis/symbols/mod_16390.toml and docs/subsystems/mod_16390.md.
 */
#ifndef WC1_MOD_16390_H
#define WC1_MOD_16390_H

/* one screen layer (graphics.toml / playflic.h): 18 bytes, 32 at 0x5aa90 */
typedef struct Layer {
    unsigned short active;              /* +0 */
    short x, y;                         /* +2, +4 */
    short w, h;                         /* +6, +8 */
    void *data;                         /* +0xa */
    void (*draw)(short x, short y, const void *src, const void *r);  /* +0xe */
} Layer;

typedef struct Rect {
    short x, y;                         /* +0, +2 */
    short right, bottom;                /* +4, +6 */
    short w, h;                         /* +8, +0xa */
} Rect;

typedef struct Font {
    unsigned char first;                /* +0 */
    unsigned char rowbytes;             /* +1 */
    unsigned char rows;                 /* +2 */
    unsigned char b3;                   /* +3 */
} Font;

typedef struct Bitmap {
    unsigned short w, h;                /* +0, +2 */
    void *data;                         /* +4 */
} Bitmap;

/* 8-byte entry of the dialog art list (dialog+0x12), -1 terminated */
typedef struct DialogArt {
    short id;                           /* +0 resource id (0xf5 = the shared art) */
    unsigned short kind;                /* +2 */
    void *data;                         /* +4 GdsAlloc'ed bitmap data */
} DialogArt;

typedef struct DialogCallbacks {
    unsigned long unk0;                 /* +0 */
    unsigned long unk4;                 /* +4 */
    void (*select)(void *params);       /* +0x8 selection changed */
    void (*open)(void *params);         /* +0xc dialog opened */
    short (*check)(void *params);       /* +0x10 finished? nonzero = yes */
    void (*close)(void *params);        /* +0x14 dialog closing */
} DialogCallbacks;

/* one entry of the 0x1c-byte dialog item list (dialog+0x26) */
typedef struct DialogItem {
    unsigned short type;                /* +0 */
    unsigned short flags;               /* +2 bit 0 = wrap, bit 1 = hover-activates */
    short x, y;                         /* +4, +6 */
    unsigned short code;                /* +8 */
    Bitmap *art;                        /* +0xa normal art */
    Bitmap *art_pressed;                /* +0xe pressed art */
    void *text;                         /* +0x12 string / string array / count */
    unsigned short id;                  /* +0x16 list id / result code / maxlen */
    unsigned short unk18;               /* +0x18 */
    unsigned short hotkey;              /* +0x1a */
} DialogItem;

typedef struct Dialog {
    unsigned short layer;               /* +0 */
    short x, y;                         /* +2, +4 */
    int *params;                        /* +6 parameter table from DialogRun */
    short w, h;                         /* +0xa, +0xc */
    void *bitmap;                       /* +0xe GdsAlloc'ed dialog bitmap */
    DialogArt *art;                     /* +0x12 */
    void *unk16;                        /* +0x16 */
    void *unk1a;                        /* +0x1a */
    DialogCallbacks *cb;                /* +0x1e */
    unsigned char *unk22;               /* +0x22 10-byte entries */
    DialogItem *items;                  /* +0x26 */
} Dialog;

/* the 12-byte input event (docs/subsystems/input.md) */
typedef struct Event {
    unsigned short type;                /* +0 0x80 key down, 0x100 key up, ... */
    unsigned short sub;                 /* +2 handler table index */
    short x, y;                         /* +4, +6 */
    unsigned char scan;                 /* +8 */
    unsigned char mods;                 /* +9 */
    short key;                          /* +0xa translated ASCII */
} Event;

/* Watcom 10.0a reads a 16-bit field as (dword at field-2) >> 16 (playflic.h) */
#define I16(addr) (*(int *)((char *)(addr) - 2) >> 16)

/* graphics / input / resource / string helpers (their areas' names) */
extern Layer layers[32];                        /* 0x5aa90 */
extern unsigned char cursor_layer_id;            /* 0x5aa78 */
extern short cursor_hotspot_x;                  /* 0x5aa60 */
extern short cursor_hotspot_y;                  /* 0x5aa62 */
extern void (*event_handlers[10])(Event *ev);   /* 0x59400 */

void LayerInvalidate(unsigned char id);
void DirtyRectUnion(const short *rect);
void ScreenUpdate(void);
void CursorLayerShow(void);
void CursorMoveTo(short x, short y);
void FillRect(short x, short y, unsigned short w, unsigned short h);
void BitmapBlit(short x, short y, const Bitmap *src, const void *srcrect);
void BitmapBlitTransparent(short x, short y, const Bitmap *src, const void *srcrect);
void BitmapBlitTransparentAll(short x, short y, const Bitmap *src);
void BitmapClear(unsigned char color);
void DrawText(short x, short y, const char *s);
int TextWidth(const void *font, const char *s);
void TextSetColorBase(unsigned char c);
void TextSetEscapeColors(unsigned char c1, unsigned char c2);
void GrpFrameBitmap(const unsigned char *grp, unsigned char frame, Bitmap *out);
void PaletteSet(unsigned char first, unsigned short count, const unsigned char *rgb);
void PaletteFadeIn(unsigned short steps);
void PaletteFadeOut(unsigned short steps);
void MouseSetRange(short xmin, short ymin, short xmax, short ymax);
void KeyStateClear(void);
void EvtPump(void);
int EvtGet(Event *out);
void EvtProcess(Event *ev);
unsigned long ResourceBegin(unsigned short id, unsigned long *packed_len);
void *ResourceRead(void *dest, unsigned count);
void ResourceReadHeaderBody(void *hdr4, void *dest);
void ResourceFreeBody(void *hdr);
void *GdsAlloc(unsigned size);
void GdsFree(void *p);
void *memcpy(void *dst, const void *src, unsigned n);
void *memset(void *s, int c, unsigned n);
char *strcpy(char *dst, const char *src);
unsigned strlen(const char *s);
int strcmp(const char *a, const char *b);
void SndPlay(unsigned id);
void SndPlayLooped(unsigned id);
void SndReleaseAll(void);
void SndLoadTable(const unsigned short *ids);
void SndToggleMusic(void);
void SndToggleSfx(void);
void MusicStart(unsigned track);
void MusicClear(void);
int FlicOpen(const char *name, void *chunk, void *image, unsigned first, unsigned last);
void FlicClose(void);
int FlicRewind(void);
int FlicRestart(void);
int FlicNextFrame(void);

/* this area's own functions (analysis/symbols/mod_16390.toml) */
int EditDefaultCharFilter(int ch);
const char *ListSelectedText(Dialog *d, DialogItem *item);
void ListDraw(Dialog *d, DialogItem *item);
void DialogDrawItems(Dialog *d);
Dialog *DialogLoad(unsigned int id);
void DialogRelocate(Dialog *d);
void DialogCallOpen(Dialog *d);
void DialogCallClose(Dialog *d);
void DialogCreate(Dialog *d);
void DialogFree(Dialog *d);
void DialogKeyHandler(Event *ev);
void DialogIdleHandler(void);
void DialogLeftPressHandler(void);
void DialogLeftReleaseHandler(void);
int DialogItemHitTest(Dialog *d, DialogItem *item);
void DialogHighlightOn(void);
void DialogHighlightOff(void);
void DialogDrawItemState(Dialog *d, DialogItem *item, int pressed, int focus);
void ListSelectAtMouse(Dialog *d, DialogItem *item);
short DialogCheckDone(Dialog *d);
void DialogPreviewCursor(void);
DialogItem *DialogItemLoop(Dialog *d);
void DialogEraseText(Dialog *d);
void DialogDrawText(Dialog *d);
void ListSelPrev(Dialog *d, DialogItem *item);
void ListSelNext(Dialog *d, DialogItem *item);
void DialogCallSelect(Dialog *d);
void EditFieldDraw(Rect r, short caret);
int EditFieldRun(Dialog *d, DialogItem *item, char *dest, const char *src, unsigned short maxlen);
void ListScrollBy(Dialog *d, int delta);
void DialogActivateItem(Dialog *d, DialogItem *item);
void DialogLoop(Dialog *d);
void DialogSoundsLoad(void);
void DialogSoundsFree(void);
void DialogArtLoad(void);
void DialogArtFree(void);
unsigned short DialogRun(unsigned int id, short x, short y, unsigned short layer, int *params);
void NoOp(void);
void UiKeyDispatch(Event *ev);
void UiButtonPress(Event *ev);
void UiButtonRelease(Event *ev);
void UiMouseMove(Event *ev);
void UiFrame(Event *ev);
void UiInputInit(void);
void UiEventPump(void);
void UiEventPumpNet(void);
void OutroTick(void);
void OutroEnd(void);
void OutroDrawLine(short x, short y, Bitmap *src, Rect *r);
const char *OutroDrawTextPage(Bitmap *bm, const char *text);
void OutroShowFrame(int frame, const unsigned char *grp, Bitmap *out);
void OutroPlayFlic(void);
void OutroShowCredits(void);
void OutroPlay(void);

/* shared data this object reads/writes (analysis/symbols/mod_16390.toml) */
extern const unsigned short dialog_sound_table[];   /* 0x51758 {0x1e7,0} */
extern void (*event_handler_table[10])(Event *ev);  /* 0x51770 */
extern const char *str_orc_finale;              /* 0x51798 (char[12]) */
extern const char *str_human_finale;            /* 0x517a4 (char[12]) */
extern const unsigned short outro_orc_sounds[];     /* 0x517b0 */
extern const unsigned short outro_human_sounds[];   /* 0x517b6 */
extern const unsigned short credits_orc_sounds[];   /* 0x517be */
extern const unsigned short credits_human_sounds[]; /* 0x517c2 */
extern Bitmap outro_bitmap;                     /* 0x18790 */
extern const short outro_text_params[6];        /* 0x18798 */
extern const char str_empty_slot[];             /* 0x56bd8 */
extern const char str_the_end[];                /* 0x56be8 */
extern Font alt_font;                           /* 0x59220 the second (setup/credits) font */
extern Bitmap dialog_art_bm;                    /* 0x593e0 */
extern void *dialog_art_data;                   /* 0x593e4 */
extern char *edit_buffer;                       /* 0x593e8 */
extern short edit_cursor;                       /* 0x593ec */
extern short auto_repeat_delay;                 /* 0x593ee */
extern short mouse_in_preview;                  /* 0x593f0 */
extern short dialog_result;                     /* 0x593f2 */
extern short dialog_sounds_loaded;              /* 0x593f4 */
extern short last_key;                          /* 0x593f8 */
extern short dialog_running;                    /* 0x593fa */
extern short left_button_held;                  /* 0x593fc */
extern void (*dialog_left_press)(void);         /* 0x59410 */
extern void (*dialog_right_press)(void);        /* 0x59418 */
extern void (*dialog_idle)(void);               /* 0x59420 */
extern void (*dialog_pre_event)(void);          /* 0x59424 */
extern void (*status_mouse_callback)(void);     /* 0x5940c (status.toml) */
extern void (*status_frame_callback)(void);     /* 0x59414 (status.toml) */
extern void (*status_click_callback)(void);     /* 0x5941c (status.toml) */
extern short ui_mouse_x;                        /* 0x59428 */
extern short ui_mouse_y;                        /* 0x5942a */
extern short ui_net_forward;                    /* 0x5942c */
extern unsigned short ui_button_bits;           /* 0x5942e */
extern short outro_done;                        /* 0x59430 */
extern short outro_is_orc;                      /* 0x59432 */
extern short outro_frame;                       /* 0x59434 */
extern short outro_tick;                        /* 0x59436 */

/* other areas' named data this object touches */
extern unsigned short screen_mode;              /* 0x593f6 (mod_13f60) */
extern short setup_quit;                        /* 0x5176a */
extern short dialog_auto_update;                /* 0x51768 */
extern short preview_rect[];                    /* 0x5175c 6 words */
extern unsigned short scenario_race;            /* 0x50088 */
extern short net_play_flag;                     /* 0x52586 */
extern unsigned char palette[];                 /* 0x58f20 */
extern void *cur_bitmap;                        /* 0x55438 */
extern void *cur_font;                          /* 0x5acf0 */
extern unsigned char draw_color;                /* 0x5ad30 */
extern void *default_font;                      /* 0x55444 */
extern void (*edit_char_hook)(int ch);          /* 0x5176c */
extern unsigned short flic_frames;              /* 0x59446 */
extern short mouse_raw_x, mouse_raw_y;          /* 0x5a8b0, 0x5a8b2 */
extern short palette_faded;                     /* 0x55558 */

/* event sources of the two-player path (save_score area) */
void NetSendLocalEvent(Event *ev);
int NetQueryRemoteEvent(Event *ev);

/* other areas' unnamed functions this object calls */
void DemoIdleTimerReset(void);                            /* 0x13e94 */
int DemoIdleTick(void);                         /* 0x13e60 */
short fn_21d0c(void *box, const short *rect, short mode, unsigned short id, void *cb);  /* 0x21d0c */
void fn_1c2bc(unsigned short id);               /* 0x1c2bc */
void *fn_1c10c(void *bitmap);                   /* 0x1c10c */

extern const Rect full_screen_rect; /* 0x18c17: rectangle argument to LayerAdd */
extern void LayerAdd(Bitmap *bm, const Rect *r, unsigned short id, unsigned short res, void (*blit)()); /* 0x21d0c; calls at 0x18c1f and 0x18da5 */
extern unsigned short status_aux_flag; /* 0x18d4f: cleared before ScreenUpdate */
extern short status_bar_blit_x; /* 0x18e85: assigned 40 */
extern short status_bar_blit_y; /* 0x18d14: decremented while scrolling */
extern short status_bar_blit_w; /* 0x18cc3: preceding word of dword read for the bottom edge */

#endif
