/* codegen-compiler: 10.0a */
#include "mod_19470.h"

extern short dat_516ae;
extern void SetCursorShape(unsigned char id);
extern void MusicStart(unsigned track);
extern void SndFadeOutAndStopAll(int ms);
extern void EvtPump(void);
extern void LayerInvalidate(unsigned char id);
extern void CursorLayerShow(void);
extern void PaletteFadeIn(unsigned short steps);
extern void PaletteFadeOut(unsigned short steps);

void GameRunSession(void)
{
    if (custom_game != 0) {
        net_play_flag = dat_516ae;
        if (net_play_flag != 0) {
            screen_mode = (short)own_campaign;
        } else {
            own_campaign = 1;
            screen_mode = 1;
        }
    } else {
        net_play_flag = 0;
        dat_516ae = 0;
        own_campaign = 1;
        screen_mode = 1;
    }

    MusicStart(scenario_music_track);
    movie_state = 1;
    EvtPump();
    GameUpdateFrame(1, 1);
    ++minimap_redraw_state;
    EvtPump();
    GameUpdateFrame(1, 1);
    movie_state = 0;
    ++minimap_redraw_state;
    if (demo_mode != 0) {
        LayerInvalidate(cursor_layer_id);
        layers[cursor_layer_id].state = 0;
    } else {
        CursorLayerShow();
    }

    game_tick_delay_phase = 0;
    PaletteFadeIn(10);
    game_speed_cache = -1;
    packet_tick_countdown = 1;
    dialog_enabled = 1;
    do {
        GameRunActiveLoop();
    } while (GameHandlePendingLoad() == 0);
    dialog_enabled = 0;
    SndFadeOutAndStopAll(25);
    LayerInvalidate(cursor_layer_id);
    layers[cursor_layer_id].state = 0;
    PaletteFadeOut(1);
    SetCursorShape(0);
}
