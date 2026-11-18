/*
 * Graphics / input declarations (see analysis/symbols/graphics.toml and
 * input.toml for the evidence behind every name and address).
 */
#ifndef GRAPHICS_H
#define GRAPHICS_H

/* 8-byte bitmap descriptor used by the whole drawing library. */
typedef struct Bitmap {
    short w;                    /* +0 */
    short h;                    /* +2 */
    unsigned char *data;        /* +4, w*h bytes, row stride == w */
} Bitmap;

/* 12-byte rectangle: inclusive corners plus size. */
typedef struct Rect {
    short x1, y1, x2, y2;       /* +0..+6 */
    short w, h;                 /* +8, +0xa */
} Rect;

/* One screen layer (18 bytes, `layers` 0x5aa90).  ScreenUpdate draws the
 * active layers from 31 down to 0 through the callback. */
typedef struct Layer {
    unsigned short active;      /* +0 */
    short x, y;                 /* +2, +4 */
    short w, h;                 /* +6, +8 */
    void *data;                 /* +0xa */
    void (*callback)(short x, short y, Rect *r, void *data);  /* +0xe */
} Layer;

/* Font resource header: 4 bytes then the glyph table (DATA.WAR 0xd7 etc.). */
typedef struct Font {
    unsigned char first;            /* +0, first character code */
    unsigned char bytes_per_row;    /* +1 */
    unsigned char rows;             /* +2, glyph height */
    unsigned char pad;              /* +3 */
    unsigned char *table;           /* +4, 3-byte records {u16 offset, u8 width} */
} Font;

/* Cursor image descriptor (12 bytes at 0x5aa60): the two hotspot words
 * followed by the bitmap (DATA.WAR resource 0x109).  The three fields have
 * their own symbols (0x5aa60 cursor_hotspot_x is named by the mod_16390
 * area, 0x5aa62/0x5aa64 here). */
typedef struct CursorImage {
    short hot_x, hot_y;
    Bitmap bm;
} CursorImage;

extern Bitmap *cur_bitmap;              /* 0x55438 */
extern unsigned char draw_color;        /* 0x5ad30 */
extern unsigned char ui_color_base;     /* 0x62880 */
extern short dirty_x1, dirty_y1, dirty_x2, dirty_y2;   /* 0x5acd0.. */
extern short dirty_w, dirty_h;          /* 0x5acd8, 0x5acda */

extern Bitmap backbuf_bm;               /* 0x5a870, 320x200 offscreen */
extern Bitmap vga_bm;                   /* 0x5ace0, 320x200 at 0xa0000 */
extern unsigned char saved_video_mode;  /* 0x5ace8 */
extern Bitmap cursor_save_bm;           /* 0x5ad10, 16x16 save-under */
extern Rect cursor_save_rect;           /* 0x5ad18 */
extern short cursor_hotspot_x, cursor_hotspot_y;  /* 0x5aa60, 0x5aa62 */
extern Bitmap cursor_bitmap;            /* 0x5aa64 */
extern unsigned char cursor_layer_id;   /* 0x5aa78 */
extern Layer layers[32];                /* 0x5aa90 */

extern unsigned char palette_base[768];   /* 0x5ad60 */
extern unsigned char palette_cur[768];    /* 0x5b060 */
extern unsigned char palette_target[768]; /* 0x62570 */
extern unsigned char palette_cycles[];    /* 0x628a0, 16 x 12 bytes */

extern void *gds_nomem_handler;         /* 0x55440 */

extern Font *cur_font;                  /* 0x5acf0 */
extern Font *default_font;              /* 0x55444 */
extern unsigned char text_colors[4];    /* 0x5ad02 */
extern unsigned char text_esc_colors[2];/* 0x5ad0b */
extern int (*text_glyph_fn)(unsigned char ch);  /* 0x5ad07 */
extern short text_tab_width;            /* 0x5543c */
extern short text_line_gap;             /* 0x5543e */
extern unsigned char *text_dest;         /* 0x5acf4, DrawGlyph2bpp writes here */
extern short text_max_x;                /* 0x5acf8 */
extern unsigned char *text_glyph_table; /* 0x5acfa */
extern unsigned short text_glyph_bytes; /* 0x5acfe */
extern unsigned char text_bytes_per_row;/* 0x5ad00 */
extern unsigned char text_rows;         /* 0x5ad01 */
extern unsigned char text_first_char;   /* 0x5ad06 */
extern unsigned short palette_faded;    /* 0x55558 (playflic.toml) */
extern short mouse_x, mouse_y;          /* 0x5a8ca, 0x5a8cc (input.toml) */
extern short mouse_raw_x, mouse_raw_y;  /* 0x5a8b0, 0x5a8b2 (input.toml) */

void HLine(short x, unsigned short y, unsigned short len);        /* 0x3ac10 */
void VLine(short x, unsigned short y, unsigned short len);        /* 0x32970 */
void BitmapClear(unsigned char color);                            /* 0x31fc0 */
void FillRect(short x, short y, unsigned short w, unsigned short h); /* 0x326a0 */
int __cdecl RectClip(Rect *src, Rect *dst);                        /* 0x3cb10 */
void __cdecl RectCopy(const unsigned char *src, unsigned char *dst, int src_skip,
                      int dst_skip, int width, int height);        /* 0x3cc5e */
void __cdecl RectCopyTransparent(const unsigned char *src, unsigned char *dst,
                                 int src_skip, int dst_skip, int width, int height); /* 0x3ccb2 */
void DirtyRectAddBox(short x1, short y1, short x2, short y2);     /* 0x33a30 */
void DirtyRectUnion(const short *r);                              /* 0x328c0 */
void DirtyRectAddLayer(unsigned char id);                         /* 0x349f0 */
void LayerInvalidate(unsigned char id);                           /* 0x31f70 */
void CursorLayerShow(void);                                       /* 0x32940 */
void CursorMoveTo(short x, short y);                              /* 0x330a0 */
void CursorSaveUnder(void);                                       /* 0x320f0 */
void CursorRestoreUnder(void);                                    /* 0x32188 */
void ScreenUpdate(void);                                          /* 0x321e8 */
void LayerFillCallback(short x, short y, Rect *r, void *data);    /* 0x32f10 */
void LayerInitFullScreen(unsigned char id);                       /* 0x32f4c */

void BitmapBlit(short x, short y, const Bitmap *src, const Rect *srcrect);  /* 0x32410 */
void BitmapBlitTransparent(short x, short y, const Bitmap *src,
                           const Rect *srcrect);                  /* 0x325d0 */
void BitmapBlitTransparentAll(short x, short y, const Bitmap *src); /* 0x326f0 */
void DrawText(short x, short y, const char *s);                    /* 0x31dcc */
int TextWidth(const Font *font, const char *s);                    /* 0x32060 */
void GrpFrameBitmap(const unsigned char *grp, unsigned char frame, Bitmap *out); /* 0x33110 */

void VidSetMode13(void);                                          /* 0x31d40 */
void VidRestoreTextMode(void);                                    /* 0x31d94 */
void PaletteSet(unsigned char first, unsigned short count, const unsigned char *rgb); /* 0x33150 */
void __cdecl VgaSetPaletteRange(const unsigned char *rgb, unsigned first, unsigned count); /* 0x331be */
void __cdecl PaletteCycleEnable(unsigned char id);                /* 0x31920 */
void PaletteCycleStepList(unsigned id);                           /* 0x33220 */
void PaletteCyclesUpdate(void);                                   /* 0x33324 */
void PaletteFadeIn(unsigned short steps);                         /* 0x32e80 */

void GdsOutOfMemory(void);                                        /* 0x32540 */
void *GdsAlloc(unsigned size);                                    /* 0x32558 */
void GdsFree(void *p);                                            /* 0x32780 */

#endif
