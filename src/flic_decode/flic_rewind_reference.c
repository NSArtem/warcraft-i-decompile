/* codegen-compiler: 10.0a */
#include "playflic.h"
#include "flic_decode_state.h"

/* @0x193fc */
short FlicRewind(void)
{
    if (flic_decoder_open == 0) {
        return 0;
    }
    FlicSeek(flic_file_header.rewind_offset, 0);
    return FlicDecodeFrame();
}
