/* codegen-compiler: 10.0a */
#ifndef MOD_25820_H
#define MOD_25820_H

#include "war.h"

typedef struct Unit Unit;

extern short mouse_scroll_initial_delays[5];
extern short mouse_scroll_repeat_delays[5];
extern short key_scroll_repeat_delays[5];
extern unsigned char map_scroll_cursor_shapes[9]; /* 0x5327a; 0x5327b is element 1. */
extern short key_scroll_countdown;
extern unsigned short mouse_position_scroll_phase;
extern unsigned short ui_mouse_x_read_prefix; /* 0x59426: low word of the dword view whose high word is ui_mouse_x. */
extern short mouse_scroll_countdown;
extern unsigned short mouse_edge_scroll_requested;
extern unsigned char mouse_scroll_initial_enabled;
extern unsigned char mouse_scroll_repeat_enabled;
extern unsigned short mouse_position_scroll_key;
extern unsigned short scroll_key_up_left;
extern unsigned short scroll_key_up;
extern unsigned short scroll_key_up_right;
extern unsigned short scroll_key_left;
extern unsigned short scroll_key_right;
extern unsigned short scroll_key_down_left;
extern unsigned short scroll_key_down;
extern unsigned short scroll_key_down_right;
extern unsigned short scroll_alt_key_up;
extern unsigned short scroll_alt_key_left;
extern unsigned short scroll_alt_key_right;
extern unsigned short scroll_alt_key_down;

extern unsigned int opt_mouse_scroll;
extern unsigned int opt_key_scroll;
extern short ui_mouse_x;
extern short ui_mouse_y;
extern short ui_button_bits;
extern unsigned short map_cursor_shape;
extern unsigned short ui_input_locked;
extern unsigned short map_scroll_x;
extern unsigned short map_scroll_y;
extern unsigned short map_scroll_y_max;
extern unsigned short map_scroll_x_max;
extern Unit *map_order_target;

void MapScrollAddInputDeltas(short *dx, short *dy);
void MapScrollFilterMouseDeltas(short *dx, short *dy);
unsigned short MapScrollApplyDeltas(short dx, short dy);
unsigned short MapScrollFromMouseEdges(short enable_edges);
unsigned int MapScrollUpdateWithoutEdges(void);
void MapScrollSetMouseRepeat(unsigned char enabled);

#endif
