/* codegen-compiler: 10.0a */
#include "mod_2ced0_c.h"

extern void *unit_array;
extern void *object_array;
extern void *draw_list[201];
extern short unit_type_size[52][2];
extern short unit_half_size[52][2];
extern void *dat_5a7b4;
extern void *dat_5a7b8;
extern unsigned short spell_order;
extern unsigned short pending_order;
extern unsigned char map_cursor_flags;
extern void *BulletCreate(int type);
extern unsigned char *SaveReadStream(void *dst, unsigned count, unsigned char *pos);
extern void SaveRelocUnits(void *u);
extern void SaveRelocObjects(void *o);
extern void DrawListRebuild(void);
extern void *memset(void *s, int c, unsigned n);

/* @0x2d4b8 */
unsigned char *UnitsInitGame(unsigned char *pos)
{
    unsigned short i;
    unsigned char *o;
    Unit *u;
    short n;
    void *b;

    map_cursor_flags = 0;
    memset(draw_list, 0, 0x324);
    spell_order = 0;
    pending_order = 0;
    if (pos) {
        pos = SaveReadStream(unit_array, 0x47e0, pos);
        SaveRelocUnits(unit_array);
        pos = SaveReadStream(object_array, 0xed8, pos);
        SaveRelocObjects(object_array);
        dat_5a7b8 = object_array;
        b = (char *)object_array + 0x26;
    } else {
        u = (Unit *)unit_array;
        n = 200;
        while (--n != -1) {
            u->flags = 1;
            u++;
        }
        o = (unsigned char *)object_array;
        n = 100;
        while (--n != -1) {
            o[1] = 1;
            o += 0x26;
        }
        dat_5a7b8 = BulletCreate(5);
        b = BulletCreate(6);
    }
    dat_5a7b4 = b;
    for (i = 0; i < 0x34; i++) {
        unit_half_size[i][0] = (short)(unit_type_size[i][0] << 3);
        unit_half_size[i][1] = (short)(unit_type_size[i][1] << 3);
    }
    DrawListRebuild();
    return pos;
}
