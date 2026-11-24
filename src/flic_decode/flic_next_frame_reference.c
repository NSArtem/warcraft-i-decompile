/* codegen-compiler: 10.0a */
#include "playflic.h"
#include "flic_decode_state.h"

/* @0x19450 */
short FlicNextFrame(void)
{
    if (flic_decoder_open == 0) {
        return 0;
    }
    return FlicDecodeFrame();
}
