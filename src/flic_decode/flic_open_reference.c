/* codegen-compiler: 10.0a */
#include "playflic.h"
#include "flic_decode_state.h"

extern FILE *FindDataFile(const char *name);

/* @0x1933c */
short FlicOpen(const char *name, void *chunk, void *image, unsigned first,
               unsigned last)
{
    flic_chunk_buffer = (unsigned char *)chunk;
    flic_image_buffer = (unsigned char *)image;
    flic_palette_first = (int)first;
    flic_palette_last = (int)last;
    flic_palette_on = 1;
    flic_file_header.frames = 0;
    flic_file = FindDataFile(name);
    if (flic_file == 0) {
        return 0;
    }
    if (FlicReadBytes(&flic_file_header, sizeof(flic_file_header)) == 0) {
        return 0;
    }
    return flic_decoder_open = (flic_file_header.magic == 0xaf12 &&
                                flic_file_header.depth == 8 &&
                                flic_file_header.flags == 3 &&
                                flic_file_header.reserved_14 == 0) ? 1 : 0;
}
