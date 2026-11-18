/* codegen-compiler: 10.0a */
/* 0x187a4: the epilogue's per-frame tick. */
#include "mod_16390.h"

void OutroTick(void)
{
    outro_tick++;
    if (outro_frame != 0)
        outro_frame++;
}
