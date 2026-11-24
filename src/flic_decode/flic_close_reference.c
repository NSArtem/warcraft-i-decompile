/* codegen-compiler: 10.0a */
#include "playflic.h"
#include "flic_decode_state.h"

extern int FileClose(FILE *fp);

/* @0x193dc */
void FlicClose(void)
{
    if (flic_decoder_open != 0) {
        flic_decoder_open = 0;
        FileClose(flic_file);
    }
}
