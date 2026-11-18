/* codegen-compiler: 10.0a */
/* 0x18040: load the dialog sound-effect table. */
#include "mod_16390.h"

void DialogSoundsLoad(void)
{
    SndLoadTable(dialog_sound_table);
    dialog_sounds_loaded = 1;
}
