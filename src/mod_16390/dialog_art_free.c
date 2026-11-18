/* codegen-compiler: 10.0a */
/* 0x18088: release the shared dialog frame art. */
#include "mod_16390.h"

void DialogArtFree(void)
{
    if (dialog_art_data != 0) {
        GdsFree(dialog_art_data);
        dialog_art_data = 0;
    }
}
