/* codegen-compiler: 10.0a */
#include "mod_20a80.h"

extern unsigned char cursor_layer_id;
extern unsigned short layers[];
extern void LayerInvalidate(unsigned char id);
extern void ScreenUpdate(void);
extern void CursorLayerShow(void);

/* @0x20b2c */
unsigned NetDriverConnectShowCursor(void)
{
    unsigned r;

    LayerInvalidate(cursor_layer_id);
    layers[cursor_layer_id * 9] = 0;
    ScreenUpdate();
    r = ((unsigned (*)(void))net_driver_connect)();
    ((void (*)(unsigned))CursorLayerShow)(r);
    ScreenUpdate();
    return r;
}
