/* codegen-compiler: 10.0a */
#include "mod_16390.h"

/* @0x188b4 */
void OutroPlayFlic(void)
{
    Bitmap bm;
    char hdr[8];
    const char *name;
    void *chunk;
    int f;

    if (outro_is_orc) {
        name = (const char *)&str_orc_finale;
    } else {
        name = (const char *)&str_human_finale;
    }
    bm = outro_bitmap;
    f = 1;
    bm.data = GdsAlloc(64000);
    chunk = GdsAlloc(64000);
    if (!(short)FlicOpen(name, chunk, bm.data, 1, 0xef) || !(short)FlicRewind()) {
        GdsFree(bm.data);
        GdsFree(chunk);
        return;
    }
    layers[14].x = 0;
    layers[14].y = 0;
    layers[14].w = bm.w;
    layers[14].h = bm.h;
    layers[14].data = &bm;
    layers[14].draw = (void (*)(short, short, const void *, const void *))BitmapBlit;
    layers[14].active = 1;
    LayerInvalidate(0xe);
    palette[723] = 0x42;
    palette[724] = 0x49;
    palette[725] = 0x46;
    PaletteSet(0, 0x100, palette);
    fn_1c2bc((unsigned short)(scenario_race + 0x1cf));
    fn_1c10c(hdr);
    if (outro_is_orc) {
        SndLoadTable(outro_orc_sounds);
        MusicStart(0xd);
        SndPlayLooped(f);
    } else {
        SndLoadTable(outro_human_sounds);
        MusicStart(0xc);
    }
    UiInputInit();
    EvtPump();
    dialog_idle = OutroTick;
    outro_done = 0;
    outro_tick = 0;
    outro_frame = 1;
    PaletteFadeIn(0x96);
    while (I16(&layers[13].x) + I16(&layers[13].w) - 1 != 30) {
        UiEventPump();
        ScreenUpdate();
        if (outro_frame == 0x14) {
            outro_frame = 0;
            SndPlay(0);
        }
        if (outro_tick >= 2) {
            int ok;
            outro_tick = 0;
            LayerInvalidate(0xd);
            layers[13].y--;
            LayerInvalidate(0xd);
            if (f == flic_frames + 1) {
                f = 2;
                ok = FlicRestart();
            } else {
                f++;
                ok = FlicNextFrame();
            }
            if ((short)ok == 0) {
                break;
            }
            LayerInvalidate(0xe);
            if (outro_is_orc == 0) {
                if (f == 0xd || f == 0x17 || f == 0x1a || f == 0x37) {
                    SndPlay(1);
                } else if (f == 0x3f) {
                    SndPlay(2);
                }
            }
        }
    }
    PaletteFadeOut(0x96);
    FlicClose();
    SndReleaseAll();
    SndLoadTable(0);
    layers[14].active = 0;
    layers[13].active = 0;
    GdsFree(bm.data);
    GdsFree(chunk);
    ResourceFreeBody(hdr);
}
