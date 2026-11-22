#ifndef MOD_1AF20_H
#define MOD_1AF20_H

#include "war.h"

typedef struct Unit Unit;

extern unsigned short scenario_race;
extern unsigned short map_scroll_x_low_word;
extern unsigned short map_scroll_x;
extern unsigned short map_scroll_y;
extern unsigned short scenario_tile_map_resource_id;
extern unsigned short scenario_map_flags_resource_id;
extern unsigned short scenario_fog_cell_resource_id;
extern unsigned short scenario_tileset_id;
extern unsigned short scenario_palette_resource_id;
extern union { unsigned long w; unsigned char b[4]; } cheat_flags;
extern unsigned short demo_mode;
extern unsigned char *minitile_pixels;
extern unsigned char *terrain_cache;
extern unsigned short *fog_map;
extern unsigned short *map_flags;
extern void **object_map;
extern unsigned short *tile_map;
extern unsigned char *map_cost;
extern unsigned short (*fog_cell_table)[4];
extern unsigned char palette[768];
extern void (*status_frame_callback)(void);
extern void (*map_press_handler)(void *);
extern void (*map_release_handler)(void *);
extern unsigned short map_cursor_shape;
extern void *unit_array;
extern void *object_array;
extern unsigned short ui_input_locked;
extern char chat_input_text[];
extern Unit *map_order_target;
extern unsigned short map_input_state_word;
extern unsigned short map_viewport_enabled;
extern short map_viewport_left;
extern short map_viewport_top;
extern short map_viewport_width;
extern short map_viewport_height;
extern unsigned long map_viewport_aux;
extern void (*map_viewport_callback)();

/* 0x590a0 is &palette[0x180]: 0x1b2e9 passes it to ResourceRead. */
/* 0x59651 is the high byte of ui_input_locked in memory, but the indexed stores at 0x1b76b and 0x1b796 write chat_input_text[index - 1] with index >= 1. */
/* The dword loads at 0x1b41d and 0x1b426 use the upper words of adjacent word pairs; the lower words do not contribute to the scroll arguments. */

void MapFreeBuffers(void);
void MapCenterOnTile(short x, short y);
void MapFindStartTile(int *x, int *y);
unsigned char *MapInitBuffers(unsigned char *save_pos);
void GameScreenRestoreInput(void);
void MapIssueTargetOrder(void *evt);
void GameScreenScheduleInputRestore(void);
void MapCenterOnUnit(Unit *unit);
void GameScreenCancelOrPlace(void);
int GameScreenHandleChatKey(void *evt);

#endif
