/* codegen-compiler: 10.0a */
#include "playflic.h"

typedef struct PaletteTriplet {
    unsigned char red, green, blue;
} PaletteTriplet;

/* 0x19064 */
int FlicDecodePaletteChunk(void)
{
    PaletteTriplet colors[256];
    unsigned char *p;
    unsigned short color;
    int result;

    p = flic_chunk_buffer;
    color = 0;
    if (FlicReadBytes(p, (unsigned short)(flic_chunk_header.size - 6)) == 0) {
        result = 0;
    } else {
        unsigned short packets;
        register int packet;
        int first;
        int last;

        packets = *(const unsigned short *)p;
        packet = 0;
        p += 2;
        for (; packet < (int)packets; ++packet) {
            register unsigned short count;
            register int i;

            color += *p++;
            count = *p++;
            if (count == 0)
                count = 256;
            for (i = 0; i < (int)count; ++i) {
                int red;
                PaletteTriplet *out;

                red = (int)*p >> 2;
                out = &colors[color];
                out->red = (unsigned char)red;
                ++p;
                out->green = (int)*p++ >> 2;
                out->blue = (int)*p++ >> 2;
                ++color;
            }
        }

        first = flic_palette_first;
        last = flic_palette_last;
        for (; first <= last; ++first)
            ((PaletteTriplet *)palette)[first] = colors[first];

        if (flic_palette_on != 0)
            VgaSetPaletteRange(palette, 0, 256);
        result = 1;
    }
    return result;
}
