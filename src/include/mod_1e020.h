/* codegen-compiler: 10.0a */
#ifndef MOD_1E020_H
#define MOD_1E020_H

#include "war.h"

typedef struct Rect Rect;

/* Only the first word and the 18-byte layer stride are identified here. */
typedef struct Layer {
    unsigned short first_word;
    unsigned char unknown_02[16];
} Layer;

extern Rect full_screen_rect;                     /* 0x514d8 */
extern const unsigned short splash_sound_table[]; /* 0x52580 */
extern unsigned char palette[768];                /* 0x58f20 */
extern unsigned char cursor_layer_id;             /* 0x5aa78 */
extern Layer layers[32];                          /* 0x5aa90 */
extern unsigned short status_aux_flag;            /* 0x5ab7a */

/* Uses the default 32-bit Watcom register convention. */
void ShowSplashScreen(void);                      /* 0x1e020 */

#endif
