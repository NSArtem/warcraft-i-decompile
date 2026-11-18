/* codegen-compiler: 10.0a */
/* 0x18fb0: the victory epilogue (main 0x1e158 calls it at 0x1e32f). */
#include "mod_16390.h"

void OutroPlay(void)
{
    LayerInvalidate(cursor_layer_id);
    layers[cursor_layer_id].active = 0;
    outro_is_orc = (scenario_race == 1);
    cur_font = &alt_font;
    TextSetColorBase(0xf3);
    OutroPlayFlic();
    OutroShowCredits();
    CursorLayerShow();
}
