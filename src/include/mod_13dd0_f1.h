#ifndef MOD_13DD0_F1_H
#define MOD_13DD0_F1_H

#include "war.h"

extern unsigned char cursor_shape_table[16][12]; /* 0x58e50; subsequent records are table elements. */
extern unsigned char current_cursor_shape_id;   /* 0x58f10 */
extern unsigned char default_cursor_shape[12];  /* 0x5aa6c */

void InitCursorShapes(void);                    /* 0x13dfc */

#endif
