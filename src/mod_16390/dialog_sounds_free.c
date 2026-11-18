/* codegen-compiler: 10.0a */
/* 0x18054: release the dialog sound-effect table. */
#include "mod_16390.h"

void DialogSoundsFree(void)
{
    SndReleaseAll();
    SndLoadTable(0);
    dialog_sounds_loaded = 0;
}
