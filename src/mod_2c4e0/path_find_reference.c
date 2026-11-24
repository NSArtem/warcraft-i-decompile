/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -zp2 */
#include "game_2c4e0.h"

extern unsigned char dat_5008c[5];
extern unsigned short scenario_tileset_id;
extern unsigned char hostility[25];
extern unsigned short dat_5189c[];
extern unsigned char *dat_5a474;
extern Point path_start;
extern Point path_dest;
extern unsigned short path_block_mask;
extern unsigned short path_distance;
extern int PathPeekStep(Unit *u, Point *out);
extern short PathScan(int dir, Point *out);
extern short PathCostWalk(int dir, Point *to);
extern void PathStoreSteps(unsigned char *path, int count, Point *to, int dir);
extern short PathTrace(short *start, int mask);
extern void PathBlockArea(int mask, Unit *u);
extern short PathDistance(Point *a, Point *b);
extern short PathNeedsPath(Point *p);

#define IDX (*(long *)((char *)&idx - 2) >> 16)

/* @0x2cc54 */
int PathFind(Unit *u)
{
    Point p;
    short idx;
    short ok;
    short cost;
    short c2;

    idx = u->path_idx;
    if (IDX < 20 && u->path[IDX] != 0xfe) {
        return 1;
    }
    ok = 0;
    path_start = *(Point *)&u->tx;
    path_dest = u->dest;
    u->path_idx = 0;
    path_distance = PathDistance(&path_start, &path_dest);
    path_block_mask = 0x3cc;
    if (dat_5008c[u->owner] != 0 && (!(u->type >= 2 && u->type <= 3)) && *(long *)&u->pad3a[0] == 0) {
        if (scenario_tileset_id == 0xc6) {
            *(unsigned char *)&path_block_mask &= 0xf3;
        } else if (u->timer36 == 0) {
            path_block_mask &= ~dat_5189c[u->owner];
        }
    }
    if (u->order_next2 == 6 && *(long *)&u->pad3a[0] == 0) {
        idx = u->owner;
    } else {
        idx = 4;
    }
    dat_5a474 = hostility + IDX * 5;
    PathBlockArea(0xffff, u->target);
    if (PathTrace(&idx, 0xffff) == 0 && IDX < 20) {
        p = path_dest;
        if (PathScan(0xff, &p) != 0 && PathNeedsPath(&p) == 0) {
            cost = PathCostWalk(IDX, &p);
            PathStoreSteps(u->path, cost, &p, 0);
            ok = 1;
        } else {
            cost = 0x7fff;
        }
        if (cost > 4) {
            PathTrace(&idx, 0xffff);
            p = path_dest;
            if (PathScan(1, &p) != 0 && PathNeedsPath(&p) == 0) {
                c2 = PathCostWalk(IDX, &p);
                if (c2 < cost) {
                    PathStoreSteps(u->path, c2, &p, 0);
                    ok = 1;
                }
            }
        }
        if (ok == 0) {
            PathTrace(&idx, 0xffff);
            goto store;
        }
    } else {
store:
        PathStoreSteps(u->path, IDX, &path_dest, 1);
        ok = 1;
    }
    PathTrace(&idx, 0x1fff);
    PathBlockArea(0x1fff, u->target);
    if (ok == 0) {
        return 0;
    }
    return PathPeekStep(u, &p);
}
