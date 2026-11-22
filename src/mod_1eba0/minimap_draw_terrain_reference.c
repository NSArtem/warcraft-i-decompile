/* codegen-compiler: 10.0a */
#include "mod_1eba0_f2.h"

void MinimapDrawTerrain(void)
{
    unsigned long reveal;
    int index;
    unsigned char *dst;
    unsigned short row, col;
    unsigned int offset, cell_offset, sample;
    unsigned short tile, fog, cell;
    unsigned char pixel;

    reveal = cheat_flags.w & 1;
    index = 0;
    dst = minimap_panel_bitmap.pixels + minimap_pixel_offset;
    row = 0;
    do {
        col = 0;
        offset = (unsigned int)index * 2;
        do {
            if (reveal == 0) {
                fog = *(const volatile unsigned short *)
                    ((const unsigned char *)fog_map + offset);
                fog &= 0x1f;
                if ((int)fog != 0) {
                    pixel = 0x60;
                    goto store_pixel;
                }
            }
            tile = *(const unsigned short *)
                ((const unsigned char *)tile_map + offset);
            cell_offset = (unsigned int)(unsigned short)(tile & 0x7ff) * 8;
            cell = *(const unsigned short *)
                ((const unsigned char *)fog_cell_table + cell_offset);
            cell &= 0xffe0U;
            sample = cell;
            sample += sample;
            pixel = minitile_pixels[sample + 0x3f];
store_pixel:
            *dst++ = pixel;
            offset += 2;
            ++index;
            ++col;
        } while (col < 0x40);
        /* The high word of the load at 0x1ed00 is the signed pitch. */
        dst += (*(const long *)(const void *)&minimap_bitmap_pitch_read_prefix >> 16) - 0x40;
        ++row;
    } while (row < 0x40);
}
