/*
 * PLAYFLIC.C (war.exe 0x22c50..0x23d10): the FLIC movie/intro player and the
 * credits animation driver.  See analysis/symbols/playflic.toml and
 * docs/subsystems/playflic.md for the evidence behind every name.
 *
 * Structure of the object (from the code):
 *
 *   0x22c50..0x22d3f  the movie core: one tick (0x22c50), present a frame
 *                     (0x22c68), rewind+show (0x22cfc), next frame (0x22d20),
 *                     the credit-line loader (0x22d40);
 *   0x22d40..0x22e5d  (0x22d40 is that loader) and 0x22e60..0x22f47 the
 *                     callbacks the script installs: skip check (0x22e60),
 *                     per-frame hook (0x22e84), palette fade step (0x22eac),
 *                     fade over N frames (0x22eec), open the selected movie
 *                     (0x22f48);
 *   0x22ff4..0x23667  the 28 script opcode handlers, one per entry of the
 *                     table at 0x52ea8, all with the signature
 *                     `unsigned char *op(unsigned char *p)` where p points
 *                     just past the opcode word; the return value is the next
 *                     opcode (0 ends the script);
 *   0x23668..0x2379f  the script interpreter IntroRunScript (0x23668);
 *   0x237a0..0x23ade  the two credits animation ticks (0x237a0, 0x2393c);
 *   0x23ae0..0x23d08  the top level IntroPlay (0x23ae0) and its four callers
 *                     (0x23c74, 0x23c94, 0x23cb4, 0x23cd4) plus the
 *                     unreachable FlicOverrun (0x23cf4).
 *
 * NOTE (evidence: no relocation anywhere in the image points into this
 * range, the only references are this object's own opcode table 0x52ea8 and
 * the tick slot 0x59eb4 - docs/subsystems/playflic.md section 1): in this
 * build the whole object is unreachable dead code.
 *
 * The script format (docs/subsystems/playflic.md section 3) is a stream of
 * little-endian words: a word opcode (0x00..0x1b, index into 0x52ea8)
 * followed by that op's arguments; every handler returns the address of the
 * next opcode word, 0 ends the script.
 */
#ifndef PLAYFLIC_H
#define PLAYFLIC_H

#include "input.h"          /* Event, Evt* */

/*
 * The graphics library owns Bitmap/Rect/Layer/Font and cur_bitmap/
 * palette_base/palette_target/layers/cur_font (src/include/graphics.h).
 * They are repeated here, like cmd_123f0.h does, so that this header stays
 * self-contained: this object was compiled seeing DrawText WITHOUT its
 * short prototype (its call sites sign-extend: 0x22cc0), and a duplicate
 * `int` declaration cannot coexist with graphics.h's `short` one.
 */
typedef struct Bitmap {
    short w, h;
    unsigned char *data;
} Bitmap;

typedef struct Rect {
    short x1, y1, x2, y2, w, h;
} Rect;

/* ------------------------------------------------------- this area: data */

extern unsigned char *intro_dest;       /* 0x59eb0  blit destination for a frame */
extern void (*intro_tick)(void);        /* 0x59eb4  credits animation tick or 0 */
extern const char *credit_line[3];      /* 0x59eb8  the three visible credit lines */
extern unsigned short credit_line_x[3]; /* 0x59ecc  centred x of each line */
extern unsigned char *frame_image;      /* 0x59ec4  decoded 320x200 frame */
extern unsigned char *frame_chunk;      /* 0x59ec8  chunk/record read buffer */
extern unsigned short frame_size;       /* 0x59eea  width*height of the movie */
extern unsigned short line_height;      /* 0x59ef4  font line height + 2 */
extern unsigned short scroll_target;    /* 0x59ee0  op 0x0c target bottom y */
extern unsigned short flic_sel;         /* 0x59ef6  index into flic_files[] */
extern unsigned short fade_frames;      /* 0x59ede  op 0x06 fade length, 0xffff = none */
extern unsigned short line_timer;       /* 0x59ee2  frames to the next credit scroll */
extern unsigned short credits_on;       /* 0x59ee4  1 = three-line credit display */
extern unsigned short abort_request;    /* 0x59ee6  op 0x02 asked for a clean exit */
extern unsigned short line_index;       /* 0x59ee8  credit_lines[] cursor */
extern unsigned short sound_timer;      /* 0x59eec  op 0x0c plays sound 0 after 20 ticks */
extern unsigned short skip_next_flic;   /* 0x59eee  op 0x1a: skip the next movie */
extern unsigned short frame;            /* 0x59ef0  current frame number */
extern unsigned short line_count;       /* 0x59ef2  active credit lines */
extern unsigned short intro_tick_count; /* 0x59ef8  frames played so far */
extern unsigned short intro_abort;      /* 0x59efa  1 = leave the script */
extern unsigned short frame_ready;      /* 0x59efc  set once per displayed frame */
extern unsigned short flic_open;        /* 0x52c60  1 while a movie is open */
extern Bitmap intro_bitmap;             /* 0x52c64  {320,200,frame_image} */
extern unsigned short intro_sounds[];   /* 0x52c6c  sound ids, 0-terminated */

/* one entry of the credit lines table 0x52d18 (stride 6 with -zp2) */
typedef struct CreditLine {
    unsigned short delay;               /* +0 frames until the next scroll */
    const char *text;                   /* +2 the line, "" ends the credits */
} CreditLine;

/* the video font the credits are drawn with (DATA.WAR resource 0xd7) */
typedef struct Font {
    unsigned char first;                /* +0 first character */
    unsigned char rowbytes;             /* +1 bytes per glyph row */
    unsigned char rows;                 /* +2 glyph rows (the line height) */
    unsigned char b3;                   /* +3 */
} Font;

/* one screen layer: 18 bytes, 32 of them at 0x5aa90 (graphics.h has the
 * same layout with the callback field called `callback`) */
typedef struct Layer {
    unsigned short active;              /* +0 */
    short x, y;                         /* +2, +4 */
    short w, h;                         /* +6, +8 */
    void *data;                         /* +0xa Bitmap * for a bitmap layer */
    void (*draw)(short x, short y, const Bitmap *src, const Rect *srcrect); /* +0xe */
} Layer;

/* Watcom 10.0a reads a 16-bit field as (dword at field-2) >> 16 in this
 * object (`mov r,[addr-2]; sar r,16`); the two sites in IntroShowFrame and
 * IntroOpSlideLayer need that exact load, see docs/subsystems/playflic.md 4. */
#define I16(addr) (*(int *)((char *)(addr) - 2) >> 16)

/* credits animation state (0x59ed2..0x59edc) */
extern unsigned short credit_step_d;    /* 0x59ed2 */
extern unsigned short credit_step_c;    /* 0x59ed4 */
extern unsigned short credit_frame_c;   /* 0x59ed6 */
extern unsigned short credit_frame_d;   /* 0x59ed8 */
extern unsigned short credit_step_b;    /* 0x59eda */
extern unsigned short credit_tick;      /* 0x59edc */

extern unsigned char fade_delta[0x2d0]; /* 0x59be0  per-entry fade decrement */

/* the UI event handler table (0x59400, 10 dwords indexed by the event sub
 * code; installed by UiInputInit/IntroRunScript, dispatched by 0x183e8,
 * 0x18398 and 0x18458) - owned by the UI/input areas, listed here for the
 * calls this object makes */
extern void (*event_handlers[10])(Event *ev);
extern unsigned short intro_music_started;  /* 0x55208 shared: see toml */
extern unsigned short palette_faded;        /* 0x55558 shared: see toml */

/* the FLIC decoder's header fields (flic_decode object, 0x19020..0x19470) */
extern unsigned short flic_frames;      /* 0x59446 */
extern unsigned short flic_width;       /* 0x59448 */
extern unsigned short flic_height;      /* 0x5944a */
extern unsigned short flic_palette_on;  /* 0x594ea */

/* the movie file names (one per flic_sel), the opcode table and the scripts */
extern const char *flic_files[32];      /* 0x52bdc */
typedef unsigned short *(*ScriptOp)(unsigned short *p);
extern ScriptOp script_ops[28];         /* 0x52ea8 */
extern const CreditLine credit_lines[]; /* 0x52d18 */
extern const unsigned short script_epilogue[];  /* 0x52c7a */
extern const unsigned short script_no_dig[];    /* 0x52e02 */
extern const unsigned short script_level[];     /* 0x52e96 */
extern const unsigned short script_movie[];     /* 0x52e9a */

/* the credits animation frame tables (docs/subsystems/playflic.md 5) */
extern const unsigned short credit_steps1[];   /* 0x52f18, variant A layer 15 */
extern const unsigned short credit_frames1[];  /* 0x52f40 */
extern const unsigned short credit_steps2[];   /* 0x52f7c, variant A layer 16 */
extern const unsigned short credit_frames2[];  /* 0x52fa4 */
extern const unsigned short credit_steps3[];   /* 0x52ff4, variant B layer 16 */
extern const unsigned short credit_frames3[];  /* 0x5301c */
extern const unsigned short credit_steps4[];   /* 0x5306c, variant B layer 17 */
extern const unsigned short credit_frames4[];  /* 0x53094 */

/* -------------------------------------------------- this area: functions */

void IntroTick(void);                                  /* 0x22c50 */
void IntroShowFrame(void);                             /* 0x22c68 */
unsigned short *IntroShowFirstFrame(unsigned short *p); /* 0x22cfc */
short IntroNextFrame(void);                            /* 0x22d20 */
void IntroLoadCreditLines(void);                       /* 0x22d40 */
void IntroCheckSkip(Event *ev);                        /* 0x22e60 */
void IntroFrame(void);                                 /* 0x22e84 */
void IntroFadeStep(void);                              /* 0x22eac */
short IntroFadeFrames(unsigned short frames);          /* 0x22eec */
unsigned short *IntroBeginFlic(unsigned short *p);     /* 0x22f48 */

unsigned short *IntroOpPlayFlic(unsigned short *p);    /* 0x22ff4 op 0x00 */
unsigned short *IntroOpEndFlic(unsigned short *p);       /* 0x2300c op 0x01 */
unsigned short *IntroOpQuit(unsigned short *p);          /* 0x23024 op 0x02 */
unsigned short *IntroOpFirstFrame(unsigned short *p);    /* 0x23030 op 0x03 */
unsigned short *IntroOpClearScreen(unsigned short *p);   /* 0x23054 op 0x04 */
unsigned short *IntroOpPlayFrames(unsigned short *p);    /* 0x23070 op 0x05 */
unsigned short *IntroOpPlayToEnd(unsigned short *p);     /* 0x230e8 op 0x06 */
unsigned short *IntroOpPlaySound(unsigned short *p);     /* 0x2315c op 0x07 */
unsigned short *IntroOpSyncSound(unsigned short *p);     /* 0x23170 op 0x08 */
unsigned short *IntroOpWaitSound(unsigned short *p);     /* 0x231cc op 0x09 */
unsigned short *IntroOpWaitFrames(unsigned short *p);    /* 0x231ec op 0x0a */
unsigned short *IntroOpStopTick(unsigned short *p);      /* 0x2322c op 0x0b */
unsigned short *IntroOpSlideLayer(unsigned short *p);    /* 0x23238 op 0x0c */
unsigned short *IntroOpHold(unsigned short *p);          /* 0x232e8 op 0x0d */
unsigned short *IntroOpWaitAnim(unsigned short *p);      /* 0x232ec op 0x0f */
unsigned short *IntroOpSetupFade(unsigned short *p);     /* 0x23330 op 0x10 */
unsigned short *IntroOpWaitSoundB(unsigned short *p);    /* 0x23394 op 0x11 */
unsigned short *IntroOpPaletteOff(unsigned short *p);    /* 0x233b4 op 0x12 */
unsigned short *IntroOpBlankPalette(unsigned short *p);  /* 0x233c0 op 0x13 */
unsigned short *IntroOpFadeIn(unsigned short *p);        /* 0x23410 op 0x14 */
unsigned short *IntroOpFadeOut(unsigned short *p);       /* 0x23458 op 0x15 */
unsigned short *IntroOpLoadPalette(unsigned short *p);   /* 0x234a0 op 0x16 */
unsigned short *IntroOpCreditArea(unsigned short *p);    /* 0x234d8 op 0x17 */
unsigned short *IntroOpStartCredits(unsigned short *p);  /* 0x23530 op 0x18 */
unsigned short *IntroOpScrollCredits(unsigned short *p); /* 0x235ec op 0x19 */
unsigned short *IntroOpSecondPass(unsigned short *p);    /* 0x23650 op 0x1a */
unsigned short *IntroOpFreeSound(unsigned short *p);     /* 0x2365c op 0x1b */

unsigned short IntroRunScript(const unsigned short *script, int blank_on_abort); /* 0x23668 */
void CreditsTickA(void);                               /* 0x237a0 */
void CreditsTickB(void);                               /* 0x2393c */
void IntroPlay(void);                                  /* 0x23ae0 */
void CreditsSetAnim(short which);                      /* 0x23c74 */
void IntroPlayLevel(int target);                       /* 0x23c94 */
void IntroPlayMovieA(int index);                       /* 0x23cb4 */
void IntroPlayMovieB(int index);                       /* 0x23cd4 */
void FlicOverrun(void);                                /* 0x23cf4 */

/* ------------------------------- callees outside this area (declarations) */
/*
 * The FLIC decoder object (analysis/modules.toml "flic_decode",
 * 0x19020..0x19470) and the layer/event helpers are other areas' code; only
 * the entries this object calls are declared (and provisionally named in
 * playflic.toml - the owning areas should take them over).
 */
short FlicOpen(const char *name, void *chunk, void *image, unsigned first,
               unsigned last);                /* 0x1933c */
void FlicClose(void);                         /* 0x193dc */
short FlicRewind(void);                       /* 0x193fc */
short FlicRestart(void);                      /* 0x19420 */
void FlicPaletteOff(void);                    /* 0x19444 */
short FlicNextFrame(void);                    /* 0x19450 */

void UiInputInit(void);                       /* 0x18488 */
void UiEventPump(void);                       /* 0x184cc */

void CreditDrawA(int frame);                  /* 0x1c1dc layer 14 */
void CreditDrawB(int frame);                  /* 0x1c214 layer 15 */
void CreditDrawC(int frame);                  /* 0x1c24c layer 16 */
void CreditDrawD(int frame);                  /* 0x1c284 layer 17 */

void ResourceFreeBody(void *hdr);             /* 0x21cf0 */

/* ------------------------------------------------------------ library ---- */
void DrawText(int x, int y, const char *s);                     /* 0x31dcc (the original's declaration promoted to int) */
int TextWidth(const Font *font, const char *s);                /* 0x32060 */
void PaletteSet(unsigned char first, unsigned short count,
                const unsigned char *rgb);                      /* 0x33150 */
void PaletteLerp(unsigned char first, unsigned char last,
                 unsigned short step, unsigned short steps);    /* 0x34c70 */
void PaletteFadeOut(unsigned short steps);                      /* 0x32fb0 */
void __cdecl VgaSetPaletteRange(const unsigned char *rgb, unsigned first,
                                unsigned count);                /* 0x331be */
void TextSetColorBase(unsigned char c);                         /* 0x32030 */
void BitmapBlit(short x, short y, const Bitmap *src, const Rect *srcrect); /* 0x32410 */
void LayerInvalidate(unsigned char id);                         /* 0x31f70 */
void ScreenUpdate(void);                                        /* 0x321e8 */
void *GdsAlloc(unsigned size);                                  /* 0x32558 */
void GdsFree(void *p);                                          /* 0x32780 */
unsigned long ResourceBegin(unsigned short id, unsigned long *packed_len); /* 0x31870 */
void *ResourceRead(void *dest, unsigned count);                 /* 0x32740 */
void ResourceReadHeaderBody(void *hdr4, void *dest);            /* 0x323e0 */

void SndPlay(unsigned id);                                      /* 0x26958 */
short SndActiveCount(void);                                     /* 0x27320 (the original's PLAYFLIC.C saw a 16-bit result: `test ax,ax` at 0x2317c) */
void SndReleaseAll(void);                                       /* 0x271f4 */
void SndLoadTable(const unsigned short *ids);                   /* 0x267fc */
void MusicStart(unsigned track);                                /* 0x26784 */
void MusicClear(void);                                          /* 0x267e0 */

void *memcpy(void *dst, const void *src, unsigned n);           /* 0x31789 */
void *memset(void *s, int c, unsigned n);                       /* 0x30c50 */

/* Variadic cdecl entry (docs/subsystems/codegen.md V7: the original's callers
 * save ebx, ecx and edx because the callee is assumed to clobber them). */
void __cdecl FatalError(const char *fmt, ...);
#pragma aux FatalError "_*" parm caller [] modify [eax ebx ecx edx];

/* externs of this object that are used by several of its files */
extern unsigned char palette[];                 /* 0x58f20, loaded palette */
extern unsigned char palette_base[768];         /* 0x5ad60, fade start */
extern unsigned char palette_target[768];       /* 0x62570, fade end */
extern Bitmap *cur_bitmap;                      /* 0x55438 */
extern Font *cur_font;                          /* 0x5acf0 */
extern unsigned char cursor_layer_id;           /* 0x5aa78, the topmost layer index (graphics.toml) */
extern Layer layers[32];                        /* 0x5aa90, 18 bytes/entry */
extern unsigned short intro_state;              /* 0x55208 */
extern unsigned short palette_fade_state;       /* 0x55558 */
extern unsigned short cfg_dig_driver;           /* 0x59902 */

#endif
