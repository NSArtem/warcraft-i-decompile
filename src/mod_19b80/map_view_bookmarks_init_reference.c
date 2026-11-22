/* codegen-compiler: 10.0a */
#include "mod_19b80.h"

typedef struct StatusBarBmp {
    short w;
    short h;
    void *pixels;
} StatusBarBmp;

typedef struct ViewPt {
    short x;
    short y;
} ViewPt;

extern StatusBarBmp status_bar_bitmap;
extern void *player_town_hall[5];
extern char *unit_array;
extern const char *status_help_text;
extern const char *status_help_text_pending;
extern unsigned short status_help_timer;
extern unsigned short status_aux_timer;
extern short status_bar_blit_x;
extern short status_bar_blit_y;
extern short status_bar_blit_w;
extern short status_bar_blit_h;
extern void *status_bar_blit_bitmap;
extern void (*status_bar_blit_func)(void);
extern void BitmapBlitTransparent(void);
extern void *GdsAlloc(unsigned size);

/* @0x19db4 */
void MapViewBookmarksInit(void)
{
    ViewPt p;
    char *u;
    short n;
    unsigned short i;

    status_help_timer = 0;
    status_help_text_pending = 0;
    status_help_text = 0;
    status_aux_timer = 0;
    status_bar_bitmap.pixels = GdsAlloc(0x960);
    status_bar_blit_x = 0x48;
    status_bar_blit_y = 0xa0;
    status_bar_blit_w = 0xf0;
    status_bar_blit_h = 10;
    status_bar_blit_bitmap = &status_bar_bitmap;
    status_bar_blit_func = BitmapBlitTransparent;
    p.x = 0;
    p.y = 0;
    u = (char *)player_town_hall[0];
    if (u == 0) {
        u = unit_array;
        n = 200;
        while (--n != -1) {
            if (u[0x1e] == 0) {
                goto found;
            }
            u += 0x5c;
        }
    } else {
found:
        p = *(ViewPt *)(u + 10);
    }
    p.x -= 7;
    p.y -= 5;
    if (p.x < 0) {
        p.x = 0;
    } else if (p.x >= 0x40) {
        p.x = 0x3f;
    }
    if (p.y < 0) {
        p.y = 0;
    } else if (p.y >= 0x40) {
        p.y = 0x3f;
    }
    for (i = 0; i < 3; i++) {
        map_bookmarks[i] = p;
    }
}
