/* codegen-compiler: 10.0a */
/* 0x1806c: load the shared dialog frame art (resource 0xf5). */
#include "mod_16390.h"

void DialogArtLoad(void)
{
    ResourceBegin(0xf5, 0);
    ResourceReadHeaderBody(&dialog_art_bm, 0);
}
