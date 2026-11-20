/* codegen-compiler: 10.0a */
#include "mod_3ca30_c.h"

extern unsigned char *text_dest;
extern short text_max_x;
extern unsigned char *text_glyph_table;
extern unsigned char text_bytes_per_row;
extern unsigned char text_rows;
extern unsigned char text_colors[4];
extern unsigned char text_first_char;

/* @0x3ca30 */
int DrawGlyph2bpp(unsigned char ch)
{
    unsigned char *dst = text_dest;
    unsigned char *tbl = text_glyph_table;
    unsigned char *g = tbl + (short)((unsigned short)ch - text_first_char) * 3;
    unsigned char *src = tbl + *(unsigned short *)g;
    short row;
    short col;
    short k;
    unsigned short bits;
    unsigned char b;

    for (row = 0; row < text_rows; row++) {
        bits = g[2];
        for (col = 0; col < text_bytes_per_row; col++) {
            if (bits == 0) {
                dst += 4;
            } else {
                b = *src++;
                for (k = 0; k < 4; k++) {
                    if (bits != 0) {
                        unsigned char p = b & 3;
                        if (p != 0) {
                            *dst = text_colors[p];
                        }
                        b >>= 2;
                        bits--;
                    }
                    dst++;
                }
            }
        }
        dst += (unsigned short)text_max_x;
    }
    text_dest += g[2];
    return g[2];
}
