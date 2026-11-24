/* codegen-compiler: 10.0a */
#include "mod_2ced0_c5.h"

typedef struct Rect { short x1, y1, x2, y2; } Rect;
typedef struct Bitmap { short w, h, r0, r1; } Bitmap;
typedef struct Obj {
    unsigned char pad0[6];
    short tx, ty;
    unsigned char pad_a[0x26 - 10];
} Obj;
typedef struct Unit {
    short x, y;
    unsigned char pad4[3];
    unsigned char c7, c8, pad9;
    short tx, ty, w0e;
    unsigned short flags;
    unsigned char pad12[9];
    unsigned char type;
    unsigned char pad1c, gfx, color;
    unsigned char pad1f[23];
    unsigned short s36, s38;
    unsigned char pad3a[30];
    Obj *link;
} Unit;

extern unsigned short map_scroll_x;
extern unsigned short map_scroll_y;
extern unsigned char minimap_player_colors[];
extern long dat_51b9a[];
extern unsigned char dat_552a8[16];
extern void *session_side_graphics[];
extern short unit_type_size[][2];
extern short unit_pixel_size[][2];
extern short unit_half_size[][2];
extern void (*sprite_blitters[8])(short, short, const Bitmap *, const Rect *);
extern Obj *object_array;
extern Unit *draw_list[];
extern Obj *damage_fire_heavy;
extern Obj *damage_fire_light;
extern unsigned char map_cursor_flags;
extern unsigned char draw_color;
extern void UnitDrawSprite(const Obj *u, short scroll_x, short scroll_y);
extern void VLine(short x, unsigned short y, unsigned short len);
extern void HLine(short x, unsigned short y, unsigned short len);
extern void GrpFrameInfo(const unsigned char *grp, unsigned frame, Bitmap *out, short *xoff, short *yoff, short *maxw, short *maxh);

/* @0x2d8c8 */
void UnitsDraw(void)
{
    short sx, sy;
    Unit **pp;
    Unit *u;
    Rect r, cr;
    Bitmap bm;
    short xo, yo, mw, mh;
    short px, py, i, n, cw, ch;
    short x0, x1, y0, y1;
    Obj *o;

    sx = (short)(map_scroll_x << 4);
    sy = (short)(map_scroll_y << 4);
    for (pp = draw_list; *pp != 0; pp++) {
        u = *pp;
        u->flags |= 0x10;
        if ((u->flags & 0x20d) != 0) continue;
        if (u->w0e & 0x100) continue;
        if (u->s36 != 0 && u->color != 0) continue;
        GrpFrameInfo((unsigned char *)session_side_graphics[u->gfx], (unsigned char)(u->c7 + dat_552a8[u->c8 * 2]), &bm, &xo, &yo, &mw, &mh);
        px = (short)(u->x - sx + unit_half_size[u->type][0]);
        if (u->c8 >= 5)
            px = (short)(px + ((unsigned short)mw / 2 - (unsigned short)xo - bm.w));
        else
            px = (short)(px + ((unsigned short)xo - (unsigned short)mw / 2));
        py = (short)(u->y - sy - (unsigned short)mh / 2 + (unsigned short)yo + unit_half_size[u->type][1]);
        if (px >= 240 || py >= 176) continue;
        if (px + bm.w <= 0 || py + bm.h <= 0) continue;
        cr.x1 = (short)-px; cr.y1 = (short)-py;
        if (cr.x1 < 0) { cr.x1 = 0; cw = bm.w; } else { px = (short)(px + cr.x1); cw = (short)(bm.w - cr.x1); }
        if (cr.y1 < 0) { cr.y1 = 0; ch = bm.h; } else { py = (short)(py + cr.y1); ch = (short)(bm.h - cr.y1); }
        if (cw >= 240 - px) cw = (short)(240 - px);
        if (ch >= 176 - py) ch = (short)(176 - py);
        cr.x2 = (short)(cr.x1 + cw - 1);
        cr.y2 = (short)(cr.y1 + ch - 1);
        u->flags &= 0xef;
        sprite_blitters[u->c8]((short)(px + 0x48), (short)(py + 12), &bm, &cr);
        if (u->type >= 0x20 && u->link != 0) {
            u->link->tx = (short)(unit_type_size[u->type][0] * 16 / 2 + u->tx * 16);
            u->link->ty = (short)((unit_type_size[u->type][1] * 16) / 2 + u->ty * 16 - 16);
            UnitDrawSprite(u->link, sx, sy);
        }
    }
    damage_fire_heavy->ty = -16;
    damage_fire_heavy->tx = damage_fire_heavy->ty;
    damage_fire_light->ty = damage_fire_heavy->ty;
    damage_fire_light->tx = damage_fire_heavy->ty;
    o = object_array;
    for (n = 100; n-- != 0; o++)
        UnitDrawSprite(o, sx, sy);
    for (pp = draw_list; *pp != 0; pp++) {
        u = *pp;
        if (u->flags & 0x10) continue;
        if (!(u->flags & 0x40)) {
            if (map_cursor_flags == 0 || u->type < 0x20 || u->color != 0) {
                if ((u->s36 == 0 && u->s38 == 0) || u->color != 0) continue;
            }
        }
        x0 = (short)(u->x - sx + unit_half_size[u->type][0] - 1 - (short)(dat_51b9a[u->type] >> 17));
        y0 = (short)(u->y - sy + unit_half_size[u->type][1] - 1 - (short)(unit_pixel_size[u->type][1] >> 1));
        x1 = (short)(x0 + unit_pixel_size[u->type][0]);
        y1 = (short)(y0 + unit_pixel_size[u->type][1]);
        for (i = 0; i < 3 && x0 < 240 && x1 >= 0 && y0 < 176 && y1 >= 0; i++) {
            if (i == 0) {
                if (u->flags & 0x40) draw_color = minimap_player_colors[u->color];
                else {
                    if (map_cursor_flags == 0 || u->type < 0x20) continue;
                    draw_color = 0xdb;
                }
            } else {
                if (u->s36 == 0 && u->s38 == 0) break;
                if (u->s38 != 0 && u->color != 0) continue;
                if (i == 1) {
                    if (u->s36 <= 0x2ee && u->s38 <= 0xfa) continue;
                    draw_color = 0x72;
                } else draw_color = 0x74;
            }
            px = (x0 > 0) ? x0 : 0;
            xo = (x1 >= 0xef) ? 0xef : x1;
            py = (y0 > 0) ? y0 : 0;
            mh = (y1 >= 0xaf) ? 0xaf : y1;
            mw = (short)(mh - py + 1);
            if (mw != 0) {
                if (px == x0) VLine((short)(px + 0x48), (unsigned short)(py + 12), (unsigned short)mw);
                if (xo == x1) VLine((short)(xo + 0x48), (unsigned short)(py + 12), (unsigned short)mw);
            }
            yo = (short)(xo - px + 1);
            if (yo != 0) {
                if (py == y0) HLine((short)(px + 0x48), (unsigned short)(py + 12), (unsigned short)yo);
                if (mh == y1) HLine((short)(px + 0x48), (unsigned short)(mh + 12), (unsigned short)yo);
            }
            x0++; y0++; x1--; y1--;
        }
    }
}
