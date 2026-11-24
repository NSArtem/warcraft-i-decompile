/* codegen-compiler: 10.0a */
#include "game_2c4e0.h"

extern void fn_1df0c(Point start, Point dest, void *out);
extern int fn_1df94(void *cur, Point *dx, Point *dy);
extern unsigned short UnitIsPassable(Unit *u);
extern unsigned short *map_flags;
extern Unit **object_map;
extern unsigned char *map_cost;
extern Point dat_5a470;
extern unsigned char *dat_5a474;
extern Point path_start;
extern Point path_dest;
extern unsigned short path_block_mask;
extern unsigned char path_dir;

/* @0x2c958 */
int PathTrace(Point *start, int mask)
{
    short st[4];
    Point cur;
    Point dx, dy;
    unsigned short idx;
    unsigned short *fp;
    unsigned short f;
    unsigned char d;
    short ok;
    short *count;
    Unit *o;

    count = (short *)start;
    fn_1df0c(path_start, path_dest, st);
    ok = 1;
    dat_5a470 = path_start;
    path_dir = 0xfe;
    cur = path_start;
    *count = 0;
    idx = (unsigned short)(cur.y * 64 + cur.x);
    fp = map_flags + idx;
    ((unsigned char *)fp)[1] |= 0x20;
    *fp &= (unsigned short)mask;
    for (;;) {
        d = (unsigned char)fn_1df94(st, &dx, &dy);
        if (path_dir == 0xfe) {
            path_dir = d;
        }
        *(unsigned short *)(map_cost + idx * 2) = (unsigned short)(d * 0x101);
        cur.x += dx.x;
        cur.y += dy.x;
        idx = (unsigned short)(cur.y * 64 + cur.x);
        if (ok != 0) {
            f = map_flags[idx];
            if ((f & 0x100) != 0) {
                o = object_map[idx];
                if (dat_5a474[o->owner] != 0 || UnitIsPassable(o) != 0) {
                    f &= 0xfeff;
                }
            }
            if ((f & path_block_mask) != 0) {
                if (cur.x != path_dest.x || cur.y != path_dest.y) {
                    ok = 0;
                }
            } else {
                dat_5a470 = cur;
                path_dir = d;
                (*count)++;
                if (*count >= 20) {
                    return 1;
                }
            }
        }
        if (ok == 0) {
            fp = map_flags + idx;
            ((unsigned char *)fp)[1] |= 0x80;
            *fp &= (unsigned short)mask;
        }
        if (cur.x == path_dest.x && cur.y == path_dest.y) {
            break;
        }
    }
    return ok;
}
