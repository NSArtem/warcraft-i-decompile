/* mod_20c30.h - the build/placement box (PLACEBOX.C, 0x21df0..0x22c50) and
 * the tail of PACKET.C (0x21c20..0x21ce8), plus mod_21cf0 (0x21cf0..0x21de4).
 *
 * This is the "Select location" flow: a peasant/peon starts a build, every
 * frame the map draws a coloured box over the tile under the mouse, a click
 * confirms (which either creates the building unit, or stamps road/wall
 * terrain), a right click cancels.  The placement state is broadcast to the
 * other machine as packet types 4/5/6 (docs/subsystems/mod_20c30.md).
 *
 * The unit record is the one documented by docs/subsystems/game_2c4e0.md and
 * repeated in mod_104b0.h; the layer/bitmap types are graphics.h's. */
#ifndef MOD_20C30_H
#define MOD_20C30_H

#include "mod_104b0.h"          /* Unit, Point, Flags, hostility, ... */
#include "graphics.h"           /* Bitmap, Rect, Layer, layers, cur_bitmap */

/* ---------------------------------------------------------------- packet layer */
/* NetSync (0x5a0a2 area, save_score.toml) is 18 bytes; the sender only copies
 * it, so this header keeps it opaque. */
void NetSendControlPacket(unsigned short id);          /* 0x21c20 */
void NetSendCheatFlags(unsigned long flags);           /* 0x21c44 */
void NetSendChatText(const char *text, unsigned short len);  /* 0x21c68 */
void NetSendSyncMessage(void *msg);                    /* 0x21cb8 */

/* ---------------------------------------------------------------- layers */
void ResourceFreeBody(Bitmap *hdr);                    /* 0x21cf0 */
void LayerAdd(Bitmap *bm, const Rect *r, unsigned short id,
              unsigned short res, void (*blit)());      /* 0x21d0c */

/* ---------------------------------------------------------------- placement state */
#define PLACE_LAYER     21                 /* layers[21] at 0x5ac0a */
#define PLACE_ROAD      0x34               /* pseudo unit type: cobbled road */
#define PLACE_WALL      0x35               /* pseudo unit type: wall */
#define PLACE_MAX_PX    0x30               /* 3x3 tiles: 48x48 pixels */

extern unsigned short net_event_pending;       /* 0x5a11a (network player) */
extern unsigned char place_type[2];            /* 0x59bd0 unit type per player */
extern unsigned char place_active[2];          /* 0x59bd2 1 while placing */
extern unsigned short place_valid;             /* 0x59bd4 last tile-check code */
extern Bitmap place_box_bm;                    /* 0x52b24 48x48 scratch bitmap */
extern const char *place_error[];              /* 0x52bc4 tile-check messages */
extern short unit_type_size[];                 /* 0x51abc {w,h} words per type */
extern unsigned char order_props[];            /* 0x534f4 per-order property bits */
extern unsigned char order_sound[];            /* 0x5328c per-order sound id */
extern unsigned short owner_block_mask[];      /* 0x51dca per-player map mask */
extern unsigned char order_range[];            /* 0x52b04 per-order range */
extern void *place_colors_bad;                 /* 0x50bbc palette-cycle list */
extern void *place_colors_ok;                  /* 0x50c1c palette-cycle list */
extern unsigned short map_cursor_shape;        /* 0x59520 */
extern unsigned char map_cursor_flags;         /* 0x5a7c9 bit 0 = placing */
extern void (*map_press_handler)(void *evt);   /* 0x59510 */
extern void (*map_release_handler)(void *evt); /* 0x59518 */

/* callbacks restored/stored by the placement code (other areas' functions;
 * named here only so the relocations resolve) */
void MapReleaseDefault(void *evt);             /* 0x1b448 */
void MapPressDefault(void *evt);               /* 0x1b578 */
void PlaceBoxRelease(void *evt);               /* 0x1b4dc */
void PlaceBoxPress(void *evt);                 /* 0x21af8 */

/* graphics/resource library entries this area calls (declared in the other
 * areas' headers too; repeated here so a single include is enough) */
void ResourceBegin(unsigned short id, void *len);      /* 0x31870 */
void ResourceReadHeaderBody(void *hdr4, void *dest);   /* 0x323e0 */
void * _fmemset(void __far *dst, int c, unsigned n);   /* 0x30c50 */
void RectOutline(short x1, short y1, short x2, short y2);  /* 0x328c0 */
void Line(short x1, short y1, short x2, short y2);     /* 0x3ac10 */
void __cdecl PaletteCycleSetup(unsigned char id, unsigned char period,
                               unsigned char first, unsigned char last,
                               void *list, unsigned char count); /* 0x34860 */
Unit *SelectionFirst();                                /* 0x25cc4 */

/* map/input state shared with the map view and the UI */
extern short ui_mouse_x, ui_mouse_y;                   /* 0x59428/0x5942a */
extern unsigned short map_scroll_x, map_scroll_y;      /* 0x500d0/0x500d2 */
extern unsigned short net_play_flag;                   /* 0x52586 */
extern unsigned short *map_flags;                       /* 0x5857c 64x64 tile flags */
extern Unit **object_map;                               /* 0x58580 pointer to the 64x64 unit array */
extern unsigned char hostility[25];                     /* 0x51883 owner x owner */
extern unsigned char unit_sight_range[];                /* 0x51c6c per unit type */

/* collaborators outside this area */
void fn_214d4(unsigned len, void *msg);                 /* 0x214d4 packet send */
void fn_19f70(const char *msg, unsigned code);          /* 0x19f70 message line */
const char *fn_20d74(unsigned short player, int pay, unsigned char type); /* 0x20d74 */
void fn_20c30(unsigned id);                            /* 0x20c30 */
void fn_20c4c(void);                                   /* 0x20c4c */
void fn_20c6c(void);                                   /* 0x20c6c */
void fn_20cc0(void);                                   /* 0x20cc0 */
Unit *UnitCreate(short px, short py, unsigned char type); /* 0x2e6f4 */
int  fn_21b24(Point p);                                /* 0x21b24 */
void fn_1b9b8(void);                                   /* 0x1b9b8 */
void fn_1bd54(void);                                   /* 0x1bd54 */
void fn_1df0c(Point start, Point dest, void *trace);   /* 0x1df0c trace init */
void fn_1df94(void *trace, Point *a, Point *b);        /* 0x1df94 next delta */
void fn_2c100(Point p, unsigned short mask);           /* 0x2c100 road */
void fn_2c268(Point p);                                /* 0x2c268 wall */
unsigned short fn_2bbe4(Point *p);                     /* 0x2bbe4 gold mine search */
void fn_26360(Unit *u, unsigned sound);                /* 0x26360 */
void fn_25b6c(int on);                                 /* 0x25b6c */
void fn_13928(Unit *u);                                /* 0x13928 */
void fn_13954(Unit *u);                                /* 0x13954 */
void fn_2ea4c(Unit *u);                                /* 0x2ea4c */
int  fn_2edac(Unit *u, int use_arg);                   /* 0x2edac */
void fn_2e100(Unit *u, short x, short y, Unit *target,
              void (*cb)(Unit *));                     /* 0x2e100 */
unsigned short fn_13360(short x, short y);             /* 0x13360 */
unsigned short fn_1346c(short x, short y);             /* 0x1346c */
unsigned short fn_1357c(short x, short y);             /* 0x1357c */
void fn_21094(Unit *u);                                /* 0x21094 */
void fn_210dc(Unit *u);                                /* 0x210dc */

/* ---------------------------------------------------------------- PLACEBOX.C */
unsigned short WorkerReturnToMine(Unit *u);            /* 0x21df0 */
unsigned short UnitIsPassable(Unit *u);                /* 0x21e58 */
int  TileBlockedByUnit(Unit *u, Point *p);             /* 0x21ec0 */
unsigned short OrderUpdateMove(Unit *u);               /* 0x222e8 */
void MoveOrderTick(Unit *u, Point *dest);              /* 0x21f90 */
unsigned short UnitClearTargets(Unit *u);              /* 0x2207c */
void OrderClampDest(Unit *u);                          /* 0x220e8 */
unsigned short OrderTargetInRange(Unit *u, unsigned char arg); /* 0x2220c */
int  OrderArgInRange(Unit *u);                         /* 0x222d8 */
void PathSetReachableDest(Unit *u);                    /* 0x223bc */
void UnitOrderTargetFinish(Unit *u);                   /* 0x22464 */
void PlaceBoxInit(void);                               /* 0x224e0 */
unsigned short PlaceBoxActive(void);                   /* 0x22538 */
void PlaceBoxShutdown(void);                           /* 0x2254c */
unsigned short PlaceBoxCheck(Point p, unsigned char type); /* 0x2256c */
void PlaceBoxUpdate(void);                             /* 0x2261c */
void PlaceBoxStart(unsigned char type);                /* 0x22798 */
void PlaceBoxCancel(void);                             /* 0x22930 */
int  PlaceBoxCreateBuilding(Unit *worker, Point p);    /* 0x229c8 */
int  PlaceBoxRoad(Point p);                            /* 0x22a4c */
int  PlaceBoxWall(Unit *worker, Point p);              /* 0x22a98 */
void PlaceBoxConfirm(Point p);                         /* 0x22ae4 */

#endif
