/* codegen-compiler: 10.0a */
#include "mod_16390.h"

extern short dat_516ae;
extern unsigned short evt_mask;
void SetCursorShape(unsigned char id);
void LayerInitFullScreen(unsigned char id);

/* @0x180a8 */
unsigned short DialogRun(unsigned int id, short x, short y, unsigned short layer, int *params)
{
    void (*saved[10])(Event *ev);
    unsigned short saved_mask;
    unsigned short saved_l22;
    short faded;
    Dialog *d;

    EvtPump();
    TextSetEscapeColors(0xf6, 0xf3);
    d = DialogLoad((unsigned short)id);
    d->layer = layer;
    d->x = x;
    d->y = y;
    d->params = params;
    DialogRelocate(d);
    DialogCreate(d);
    SetCursorShape((unsigned char)((screen_mode == 0 && dat_516ae != 0) ? 1 : 0));
    CursorLayerShow();
    mouse_in_preview = 0;
    LayerInvalidate((unsigned char)layer);
    LayerInvalidate((unsigned char)(layer + 1));
    ScreenUpdate();
    saved_mask = evt_mask;
    memcpy(saved, event_handlers, sizeof(saved));
    if (dat_516ae != 0) {
        KeyStateClear();
    }
    UiInputInit();
    event_handlers[0] = DialogKeyHandler;
    dialog_left_press = DialogLeftPressHandler;
    status_frame_callback = DialogLeftReleaseHandler;
    dialog_idle = DialogIdleHandler;
    saved_l22 = layers[22].active;
    layers[22].active = 0;
    faded = palette_faded;
    if (faded != 0) {
        LayerInitFullScreen(0xe);
        PaletteFadeIn(1);
    }
    DialogLoop(d);
    if (faded != 0) {
        PaletteFadeOut(1);
        layers[14].active = 0;
    }
    layers[22].active = saved_l22;
    evt_mask = saved_mask;
    memcpy(event_handlers, saved, sizeof(saved));
    SetCursorShape(0);
    TextSetEscapeColors(0xf6, 0xf3);
    DialogCallClose(d);
    DialogFree(d);
    if (dialog_auto_update != 0) {
        ScreenUpdate();
    }
    if (setup_quit != 0) {
        EvtPump();
    }
    return dialog_result;
}
