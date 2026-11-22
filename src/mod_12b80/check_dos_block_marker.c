/* codegen-compiler: 10.0a */
#include "mod_12b80.h"

/* 0x12c4d loads the marker byte; 0x12c52 compares it with 'T'. */
void CheckDosBlockMarker(void)
{
    if ((unsigned char)dos_block_marker_tail[0] == 'T') {
        FatalError(dos_block_check_error);
    }
}
