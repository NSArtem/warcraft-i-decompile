/* codegen-compiler: 10.0a */
#include "mod_2ced0_c7.h"

extern unsigned short map_scroll_x;
extern unsigned short map_scroll_y;
extern short ui_mouse_x;
extern short ui_mouse_y;
extern short unit_pixel_size[52][2];
extern void *unit_array;
extern struct Unit *map_order_target;
extern unsigned short PlaceBoxActive(void);
extern int TargetModeIsActive(void);

void MapPickOrderTarget(unsigned short *cursor_shape)
{
    short scroll_x;
    short scroll_y;
    short mouse_x;
    short mouse_y;
    struct Unit *u;
    short left;
    unsigned bits;
    short width;
    short height;
    int pos;
    unsigned char owner;

    scroll_x = (short)(map_scroll_x << 4);
    scroll_y = (short)(map_scroll_y << 4);
    mouse_x = (short)(scroll_x + ui_mouse_x - 72);
    mouse_y = (short)(scroll_y + ui_mouse_y - 12);
    u = unit_array;
    left = 200;
    goto test_count;

check_unit:
    bits = (*(volatile unsigned short *)&u->flags & 0x020fU) & 0xffffU;
    if (bits != 0)
        goto next_unit;
    bits = (*(const volatile unsigned short *)&u->pad0e & 0x0100U) & 0xffffU;
    if (bits != 0)
        goto next_unit;
    bits = u->type;
    width = unit_pixel_size[bits][0];
    height = unit_pixel_size[bits][1];
    pos = (short)(u->pixel_x - scroll_x);
    if (pos > 240 || pos + width < 0)
        goto next_unit;
    pos = (short)(u->pixel_y - scroll_y);
    if (pos > 176 || pos + height < 0)
        goto next_unit;
    if ((unsigned short)(mouse_x - u->pixel_x) > (unsigned short)width)
        goto next_unit;
    if ((unsigned short)(mouse_y - u->pixel_y) > (unsigned short)height)
        goto next_unit;
    if (PlaceBoxActive() != 0) {
        *cursor_shape = 0;
        goto done;
    }
    if ((short)TargetModeIsActive() != 0) {
        owner = u->owner;
        if (owner == 0) {
            *cursor_shape = 4;
            goto done;
        }
        if (owner != 4) {
            *cursor_shape = 3;
            goto done;
        }
        *cursor_shape = 2;
        goto done;
    }
    *cursor_shape = 5;
    goto done;

next_unit:
    ++u;
test_count:
    if (--left != -1)
        goto check_unit;
    u = 0;
done:
    map_order_target = u;
}
