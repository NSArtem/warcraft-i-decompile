#ifndef MOD_2C3F0_H
#define MOD_2C3F0_H

#include "war.h"

typedef struct Rect Rect;

/* Only the first word and the 18-byte record stride are established here. */
typedef struct Layer {
    unsigned short first_word;
    unsigned char remaining[16];
} Layer;

extern unsigned short intro_music_started;    /* 0x55208 */
extern Rect setup_menu_top_rect;               /* 0x5520a */
extern Rect setup_menu_body_rect;              /* 0x55216 */
extern unsigned char palette[768];             /* 0x58f20 */
extern void *slot_file;                        /* 0x59610 */
extern unsigned char cursor_layer_id;          /* 0x5aa78 */
extern Layer layers[32];                       /* 0x5aa90 */

/* 0x5abd4 and 0x5abe6 are layers[0x12].first_word and
 * layers[0x13].first_word, respectively, not separate globals. */

void RunSetupMenu(void);                      /* 0x2c3f0; Watcom register ABI */

#endif
