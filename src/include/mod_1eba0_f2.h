#ifndef MOD_1EBA0_F2_H
#define MOD_1EBA0_F2_H

#include "war.h"

/* The pitch and pixel pointer are read at 0x1ed00 and 0x1ec8a. */
typedef struct Bitmap {
    short pitch;
    unsigned short reserved;
    unsigned char *pixels;
} Bitmap;

/* Passed by address to LayerAdd at 0x1ebc2. */
typedef struct Rect {
    short x1, y1, x2, y2;
} Rect;

extern unsigned short scenario_race;                /* 0x50088 */
extern unsigned short map_scroll_x;                 /* 0x500d0 */
extern unsigned short map_scroll_y;                 /* 0x500d2 */
extern unsigned short minimap_redraw_state;          /* 0x50d80 */
extern union { unsigned long w; unsigned char b[4]; } cheat_flags; /* 0x51214 */
extern unsigned char minimap_player_colors[5];       /* 0x51808 */
extern short unit_type_size[52][2];                  /* 0x51abc; 0x51abe is unit_type_size[0][1] */
extern short minimap_bitmap_pitch_read_prefix;      /* 0x5297a; low word of the dword pitch load */
extern Bitmap minimap_panel_bitmap;                 /* 0x5297c; pitch at +0, pixels pointer at +4 (0x52980) */
extern Rect score_panel_rect;                       /* 0x53140 */
extern Bitmap *cur_bitmap;                          /* 0x55438 */
extern unsigned char *minitile_pixels;               /* 0x58570 */
extern unsigned short *fog_map;                     /* 0x58578 */
extern unsigned short *tile_map;                    /* 0x58584 */
extern unsigned short (*fog_cell_table)[4];         /* 0x5858c */
extern void *player_town_hall[5];                    /* 0x58db0 */
extern void (*status_mouse_callback)(void *);       /* 0x5940c */
extern void (*status_frame_callback)(void);         /* 0x59414 */
extern void (*status_click_callback)(void);         /* 0x5941c */
extern short ui_mouse_x;                            /* 0x59428 */
extern short ui_mouse_y;                            /* 0x5942a */
extern void (*map_aux_handler)(void);               /* 0x59514 */
extern void *unit_array;                            /* 0x59640 */
extern short minimap_draw_rect[4];                   /* 0x599e0; x1, y1, x2, y2 at +0, +2, +4, +6 */
extern short minimap_draw_size[2];                   /* 0x599e8; width, height at +0, +2 */
extern short side_panel_rect_x1;                    /* 0x599ec */
extern short side_panel_rect_y1;                    /* 0x599ee */
extern short side_panel_rect_x2;                    /* 0x599f0 */
extern short side_panel_rect_y2;                    /* 0x599f2 */
extern short minimap_input_size[2];                  /* 0x599f4; width, height at +0, +2 */
extern unsigned short minimap_pixel_offset;         /* 0x599f8 */
extern short minimap_redraw_countdown;               /* 0x599fa */
extern unsigned short minimap_last_scroll_y;        /* 0x599fc */
extern unsigned short minimap_last_scroll_x;        /* 0x599fe */
extern unsigned char draw_color;                    /* 0x5ad30 */

/* The target build uses Watcom's default register convention. */
void MinimapPanelInit(void);
void MinimapPanelFree(void);
void MinimapDrawTerrain(void);
short MinimapRedraw(short force);
void MinimapScreenToTile(short *x, short *y);
void MinimapEndScrollInput(void);
void MinimapScrollFromMouse(void);
void MinimapBeginScrollInput(void);
void MinimapIssueOrder(void *mouse_event);

#endif
