#ifndef MOD_3D2B0_H
#define MOD_3D2B0_H

#include "war.h"

typedef struct Font Font;
typedef struct Bitmap Bitmap;

/* Field offsets describe the original 32-bit DOS target. */
typedef struct CritErrButton {
    const char *label;           /* 0x00: NULL skips text drawing */
    const Bitmap *bitmap;        /* 0x04: NULL terminates the array */
    unsigned char unknown_08[4]; /* 0x08 */
    short x;                     /* 0x0c */
    short y;                     /* 0x0e */
    short label_x;               /* 0x10: written when label is non-NULL */
    short label_y;               /* 0x12: written when label is non-NULL */
} CritErrButton;

extern Font *default_font;
extern Font *cur_font;

/* Watcom register convention (-4r). */
void CritErrDrawButtons(short selected_index, CritErrButton *buttons,
                        unsigned char normal_color, unsigned char selected_color);

extern void DrawText(short x, short y, const char *s); /* 0x31dcc; called at 0x3d350 */
extern void TextSetColorBase(unsigned char c); /* 0x32030; called at 0x3d33d */
extern int TextWidth(const Font *font, const char *s); /* 0x32060; called at 0x3d2ff */
extern void BitmapBlitAll(short x, short y, const Bitmap *src); /* 0x33b00; called at 0x3d2e9 */

#endif /* MOD_3D2B0_H */
