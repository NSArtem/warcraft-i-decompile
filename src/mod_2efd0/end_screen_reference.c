/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* EndScreen (0x2fcfc): the mission-end screen.
 *
 * Loads the side's panel bitmap and palette, opens win1/win2 (or lose1/
 * lose2), fills the 13 score numbers' targets from the mission counters,
 * plays the mission music, fades in, runs EndScreenMovie, then tears
 * everything down again. */
#include "mod_2efd0.h"

/* @0x2fcfc */
void EndScreen(void)
{
    Bitmap screen;
    Bitmap panel;            /* the layer-13 picture, resource or movie frame */
    Bitmap rank;             /* the layer-14 rank name */
    Bitmap text;             /* the layer-15 numbers bitmap (end_text_bm) */
    Rect rank_rect;
    char palbuf[0x270];
    void *chunk;
    void *image;
    Bitmap *movie_bm;
    int i;
    unsigned short track;

    screen.w = 0x140;
    screen.h = 0xc8;
    screen.data = 0;
    LayerInvalidate(cursor_layer_id);
    layers[cursor_layer_id].active = 0;
    ResourceBegin(0x19f + scenario_race, 0);
    ResourceRead(palette, 0);
    end_screen_bm.w = 0xb8;
    end_screen_bm.h = 0x70;
    end_screen_bm.data = GdsAlloc(0x5080);
    cur_bitmap = &end_screen_bm;
    chunk = GdsAlloc(0xfa00);
    image = GdsAlloc(0xfa00);
    screen.data = (unsigned char *)image;
    if (FlicOpen(game_mode == 6 ? movie_win1 : movie_lose1, chunk, image,
                 1, 0xcf) == 0 || FlicRewind() == 0) {
        if (game_mode == 6) {
            ResourceBegin(0x1a2, 0);
            ResourceRead(palbuf, 0);
            ResourceBegin(0x1a1, 0);
        } else {
            ResourceBegin(0x1a4, 0);
            ResourceRead(palbuf, 0);
            ResourceBegin(0x1a3, 0);
        }
        ResourceReadHeaderBody(&end_screen_bm, end_screen_bm.data);
        memcpy(palette + 3, palbuf + 3, 0x26d);
    } else {
        BitmapBlit(0, 0, &screen, &end_panel_rect);
    }
    memset(&panel, 0, 8);
    LayerAdd(&panel, &full_screen_rect, 0x19d + scenario_race, 0x10,
             BitmapBlit);
    if (game_mode == 6) {
        rank_rect.x1 = 0x10;
        rank_rect.y1 = 0x1c;
        rank_rect.w = 0x5c;
        rank_rect.h = 0x17;
    } else {
        rank_rect.x1 = 0x15;
        rank_rect.y1 = 0x1c;
        rank_rect.w = 0x4f;
        rank_rect.h = 0x13;
    }
    rank_rect.x2 = rank_rect.x1 + rank_rect.w - 1;
    rank_rect.y2 = rank_rect.y1 + rank_rect.h - 1;
    memset(&rank, 0, 8);
    LayerAdd(&rank, &rank_rect, 0x1a5 + (game_mode != 6), 0xe,
             BitmapBlitTransparent);
    layers[14].active = 0;
    cur_font = &alt_font;
    TextSetColorBase(0xf3);
    end_text_bm.data = GdsAlloc(0x9100);
    layers[15].active = 1;
    layers[15].x = 0xe;
    layers[15].y = 0x40;
    layers[15].w = end_text_bm.w;
    layers[15].h = end_text_bm.h;
    layers[15].data = (void *)&end_text_bm;
    layers[15].callback = (void (*)(short, short, Rect *, void *))BitmapBlitTransparent;
    LayerInvalidate(0xf);
    memset(end_screen_value, 0, 0x34);
    EndScreenDraw();
    ScoreTickIncome();
    end_screen_target[0] = dead_men[1] + dead_men[2] + dead_men[3];
    end_screen_target[1] = dead_men[0];
    end_screen_target[2] = dead_men[0] + player_active_men[0];
    end_screen_target[3] = end_screen_target[0] + player_active_men[1] +
                           player_active_men[2] + player_active_men[3];
    end_screen_target[4] = dead_buildings[1] + dead_buildings[2] +
                           dead_buildings[3];
    end_screen_target[5] = dead_buildings[0];
    end_screen_target[6] = dead_buildings[0] + player_building_count[0];
    end_screen_target[7] = end_screen_target[4] + player_building_count[1] +
                           player_building_count[2] + player_building_count[3];
    end_screen_target[8] = harvested_gold[0];
    end_screen_target[9] = harvested_gold[1] + harvested_gold[2] +
                           harvested_gold[3];
    end_screen_target[10] = harvested_lumber[0];
    end_screen_target[11] = harvested_lumber[1] + harvested_lumber[2] +
                            harvested_lumber[3];
    end_screen_target[12] = player_score[0];
    if (game_mode == 6)
        track = (scenario_race == 1) ? 0xb : 0xa;
    else
        track = (scenario_race == 1) ? 9 : 8;
    SndLoadTable(end_sound_ids);
    MusicStart(track);
    PaletteFadeIn(0x96);
    EndScreenMovie(chunk, &screen);
    PaletteFadeOut(0x96);
    MusicClear();
    SndLoadTable(0);
    layers[13].active = 0;
    layers[15].active = 0;
    layers[14].active = 0;
    layers[15].active = 0;
    GdsFree(chunk);
    ResourceFreeBody(&end_screen_bm);
    ResourceFreeBody(&end_text_bm);
    ResourceFreeBody(&panel);
    ResourceFreeBody(&screen);
    ResourceFreeBody(&rank);
    CursorLayerShow();
}
