/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* EndScreenMovie (0x2fac4): the animated part of the win/lose screen.
 *
 * It installs the screen's event callbacks, plays one sound, then loops
 * while end_screen_done is clear: pump the input, animate the 13 numbers and
 * (once they have finished) draw the rank name into the text layer, advance
 * the movie one frame every second EndScreenTick, and when the first movie
 * ends open the second one of the pair.  The movie frame is blitted into
 * `screen` (a 320x200 bitmap whose data buffer EndScreen allocated). */
#include "mod_2efd0.h"

/* @0x2fac4 */
void EndScreenMovie(void *chunk, Bitmap *screen)
{
    char *second;
    char *rank;
    unsigned short frame;
    unsigned short ticks;
    int shown;
    int second_movie;

    second = (game_mode == 6) ? movie_win2 : movie_lose2;
    ticks = 0;
    shown = 0;
    second_movie = 0;
    rank = RankName();
    UiInputInit();
    EvtPump();
    event_handlers[0] = (void (*)(Event *))EndScreenInput;
    status_frame_callback = (void (*)(void))EndScreenInput;
    status_click_callback = (void (*)(void))EndScreenInput;
    dialog_idle = EndScreenTick;
    movie_state = 1;
    end_screen_done = 0;
    end_screen_ticks = 0;
    frame = 1;
    SndPlay((unsigned short)EndScreenSoundId());
    while (!end_screen_done) {
        UiEventPump();
        if (--ticks == 0xffff) {
            PacketTick();
            ticks = 0x1e;
        }
        ScreenUpdate();
        if (!shown) {
            if (EndScreenAnimate() == 0) {
                shown = 1;
                *(unsigned short *)&layers[14] = 1;
                LayerInvalidate(0xe);
                ScreenUpdate();
                SndStop(0);
                SndPlay(1);
                cur_bitmap = &end_text_bm;
                DrawText(0x30 - TextWidth(cur_font, rank) / 2, 2, rank);
                LayerInvalidate(0xf);
                ScreenUpdate();
            }
        }
        if (end_screen_ticks >= 2) {
            end_screen_ticks = 0;
            if (second_movie) {
                if (frame == flic_frames + 1) {
                    frame = 2;
                    FlicRestart();
                } else {
                    frame++;
                    FlicNextFrame();
                }
            } else {
                if (frame == flic_frames) {
                    second_movie = 1;
                    frame = 2;
                    FlicClose();
                    FlicOpen(second, chunk, screen->data, 1, 0xcf);
                    FlicRewind();
                } else {
                    frame++;
                    FlicNextFrame();
                }
            }
            if (flic_frames != 0) {
                cur_bitmap = &end_screen_bm;
                BitmapBlit(0, 0, &end_screen_bm, &end_panel_rect);
                LayerInvalidate(0xd);
            }
        }
    }
    FlicClose();
    SndReleaseAll();
    movie_state = 0;
}
