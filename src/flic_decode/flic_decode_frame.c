/* codegen-compiler: 10.0a */
#include "playflic.h"

/* 0x192f0: check the frame magic at 0x1930d and decode each chunk. */
short FlicDecodeFrame(void)
{
    int i;
    short result;

    result = FlicReadBytes(&flic_frame_header, 16);
    if (result == 0)
        return result;
    if (flic_frame_header.magic != 0xf1fa)
        return 0;

    for (i = 0; i < (int)flic_frame_header.chunks; ++i) {
        result = FlicDecodeChunk();
        if (result == 0)
            return result;
    }
    return 1;
}
