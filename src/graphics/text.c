/* codegen-flags: -s -ot -ol -4r -d1+ -zp2
 * codegen-compiler: 10.0a
 * Module mod_31dc0 (text part: 0x31dcc..0x31f70 DrawText) and mod_32060
 * (0x32060..0x320f0 TextWidth).  Reference C: the two functions are byte
 * near misses (TextWidth's allocator keeps the glyph table in ebp in the
 * original; DrawText's scratch-global stores differ in order), so they are
 * difftested instead - tests/test_graphics_lib.py.
 */
#include <string.h>
#include "graphics.h"

/* @0x31dcc */
void DrawText(short x, short y, const char *s)
{
    short x0 = x;
    unsigned short line_start = 1;
    unsigned char *data = cur_bitmap->data;
    unsigned char ch;
    int w;

    text_glyph_table = cur_font->table;
    text_first_char = cur_font->first;
    text_rows = cur_font->rows;
    text_bytes_per_row = cur_font->bytes_per_row;
    text_glyph_bytes = cur_font->bytes_per_row * cur_font->rows;
    text_max_x = cur_bitmap->w - cur_font->bytes_per_row * 4;

    while (*s) {
        if (line_start) {
            text_dest = data + cur_bitmap->w * y + x;
            line_start = 0;
        }
        ch = *s;
        if (ch == '\n') {
            y += cur_font->rows + text_line_gap;
            x = x0;
            line_start = 1;
        } else if (ch == '\t') {
            w = x - x0;
            x += text_tab_width - w % text_tab_width;
            line_start = 1;
        } else if (ch == '@') {
            if (s[1] == '1' || s[1] == '2') {
                unsigned char base = s[1] == '1' ? text_esc_colors[0] : text_esc_colors[1];
                text_colors[1] = base;
                text_colors[2] = base + 1;
                text_colors[3] = base + 2;
                s += 2;
                continue;
            }
            if (s[1] == '@')
                s++;
            x += text_glyph_fn('@');
        } else {
            x += text_glyph_fn(ch);
        }
        s++;
    }
}

/* @0x32060 */
int TextWidth(const Font *font, const char *s)
{
    const unsigned char *table = font->table;
    short w = 0, max = 0;

    while (*s) {
        unsigned char ch = *s;
        if (ch == '\n') {
            if (w > max) max = w;
            w = 0;
        } else if (ch == '\t') {
            w += text_tab_width;
        } else if (ch == '@') {
            if (s[1] == '1' || s[1] == '2') {
                s += 2;
                continue;
            }
            if (s[1] == '@')
                s++;
            w += table[(ch - font->first) * 3 + 2];
        } else {
            w += table[(ch - font->first) * 3 + 2];
        }
        s++;
    }
    if (w > max) max = w;
    return max;
}
