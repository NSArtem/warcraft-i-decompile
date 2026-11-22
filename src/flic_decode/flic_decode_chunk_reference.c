/* codegen-compiler: 10.0a */
#include "playflic.h"

extern int BitmapDecodeRle(unsigned char *dst, const unsigned char *src, unsigned height, unsigned width); /* 0x1025c */
extern int BitmapDecodeRleSparse(unsigned char *dst, const unsigned char *src); /* 0x102a4 */
extern int fn_10312(unsigned char *dst, const unsigned char *src, unsigned width); /* 0x10312, called at 0x1924b */

/* 0x19174 */
short FlicDecodeChunk(void)
{
    unsigned short type;
    unsigned short count;
    unsigned char *dst;
    int row;
    short result;

    result = FlicReadBytes(&flic_chunk_header, 6);
    if (result == 0)
        goto read_done;

    type = flic_chunk_header.type;
    count = (unsigned short)(flic_chunk_header.size - 6);
    switch (type) {
    case 4:
        return (short)FlicDecodePaletteChunk();

    case 12:
        result = FlicReadBytes(flic_chunk_buffer, count);
        if (result == 0)
            goto read_done;
        return (short)BitmapDecodeRleSparse(flic_image_buffer, flic_chunk_buffer);

    case 7:
        result = FlicReadBytes(flic_chunk_buffer, count);
        if (result == 0)
            goto read_done;
        return (short)fn_10312(flic_image_buffer, flic_chunk_buffer, flic_width);

    case 15:
        result = FlicReadBytes(flic_chunk_buffer, count);
        if (result == 0)
            goto read_done;
        return (short)BitmapDecodeRle(flic_image_buffer, flic_chunk_buffer,
                                      flic_height, flic_width);

    case 16:
        row = 0;
        dst = flic_image_buffer;
        for (; row < (int)flic_height; ++row) {
            result = FlicReadBytes(dst, flic_width);
            if (result == 0)
                goto read_done;
            dst += 320;
        }
        result = 1;
        break;

    case 18:
        FlicSeek(flic_chunk_header.size - 6, 1);
        return 1;

    default:
        return 0;
    }

read_done:
    return result;
}
