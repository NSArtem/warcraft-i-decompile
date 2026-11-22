/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -d1+ -zp2 */
#define fn_1c2bc fn_1c2bc_short_declaration
#include "mod_16390.h"
#undef fn_1c2bc
extern void fn_1c2bc(unsigned int id);

void OutroShowCredits(void)
{
    const unsigned char *grp;
    int frame;
    Bitmap emblem;
    Bitmap background;
    Bitmap panel;
    Rect text_rect;
    char *credits;
    const char *page;
    short y;

    text_rect = *(const Rect *)(const void *)outro_text_params;
    if (outro_is_orc != 0) {
        ResourceBegin(0x1ce, 0);
        grp = ResourceRead(0, 0);
        frame = 0;
        GrpFrameBitmap(grp, (unsigned char)frame, &emblem);
        dat_5aba0 = 89;
        dat_5aba2 = 0;
        dat_5aba4 = emblem.w;
        dat_5aba6 = emblem.h;
        dat_5aba8 = &emblem;
        dat_5abac = BitmapBlit;
        dat_5ab9e = 1;
        LayerInvalidate(15);
    }

    LayerAdd(&background, &full_screen_rect, 16,
             (unsigned short)(outro_is_orc ? 0x1cc : 0x1ca),
             (void (*)())BitmapBlit);
    ResourceBegin((unsigned short)(outro_is_orc ? 0x1cd : 0x1cb), 0);
    ResourceRead(palette, 0);
    PaletteSet(0, 256, palette);
    fn_1c2bc((unsigned int)scenario_race + 0x1d1);
    fn_1c10c(&panel);
    SndLoadTable(outro_is_orc ? credits_orc_sounds : credits_human_sounds);
    outro_tick = 0;
    outro_frame = 1;
    PaletteFadeIn(150);

    {
        unsigned layer;
        int zero;

        layer = 13;
        zero = 0;
        while ((*(const int *)(const void *)&status_bar_blit_x >> 16) +
               (*(const int *)(const void *)&status_bar_blit_w >> 16) - 1 != 30) {
            UiEventPump();
            ScreenUpdate();
            if ((unsigned short)outro_frame == 20) {
                outro_frame = (short)zero;
                SndPlay((unsigned)zero);
            }
            if ((unsigned short)outro_tick < 2)
                continue;
            outro_tick = (short)zero;
            LayerInvalidate((unsigned char)layer);
            --status_bar_blit_y;
            LayerInvalidate((unsigned char)layer);
            OutroShowFrame(frame++, grp, &emblem);
            if (frame == 31)
                frame = zero;
        }
    }
    LayerInvalidate(13);
    status_aux_flag = 0;
    ScreenUpdate();
    ResourceFreeBody(&panel);

    credits = GdsAlloc(0x1000);
    memset(credits, 0, 0x1000);
    ResourceBegin(0x1d3, 0);
    ResourceRead(credits, 0);
    LayerAdd(&panel, &text_rect, 13, 0xffff, (void (*)())OutroDrawLine);
    page = OutroDrawTextPage(&panel, credits);
    if (*page != '\0') {
        unsigned layer;

        layer = 13;
        do {
            for (;;) {
                int target_y;

                target_y = 40 - ((const Font *)cur_font)->rows;
                if ((*(const int *)(const void *)&status_bar_blit_x >> 16) == target_y)
                    break;
                UiEventPump();
                ScreenUpdate();
                if ((unsigned short)outro_tick < 2)
                    continue;
                outro_tick = 0;
                LayerInvalidate((unsigned char)layer);
                --status_bar_blit_y;
                LayerInvalidate((unsigned char)layer);
                OutroShowFrame(frame++, grp, &emblem);
                if (frame == 31)
                    frame = 0;
            }
            page = OutroDrawTextPage(&panel, page);
            LayerInvalidate((unsigned char)layer);
            status_bar_blit_y += ((const Font *)cur_font)->rows;
            LayerInvalidate((unsigned char)layer);
        } while (*page != '\0');
    }

    cur_bitmap = &panel;
    BitmapClear(0);
    status_bar_blit_x = status_bar_blit_y = 40;
    y = (short)((128 - ((const Font *)cur_font)->rows) / 2);
    DrawText((short)((240 - (short)TextWidth(cur_font, str_the_end)) / 2),
             y, str_the_end);
    LayerInvalidate(13);
    ScreenUpdate();
    {
        void (*end)(void);

        end = OutroEnd;
        event_handlers[0] = (void (*)(Event *))end;
        status_frame_callback = end;
        status_click_callback = end;
    }
    if (outro_done == 0) {
        do {
            UiEventPump();
            ScreenUpdate();
            if ((unsigned short)outro_tick >= 2) {
                outro_tick = 0;
                OutroShowFrame(frame++, grp, &emblem);
                if (frame == 31)
                    frame = 0;
            }
        } while (outro_done == 0);
    }

    PaletteFadeOut(150);
    SndReleaseAll();
    MusicClear();
    SndLoadTable(0);
    dat_5ab9e = 0;
    dat_5abb0 = 0;
    status_aux_flag = 0;
    if (outro_is_orc != 0)
        GdsFree((void *)grp);
    ResourceFreeBody(&panel);
    ResourceFreeBody(&background);
}
