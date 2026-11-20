/* codegen-compiler: 10.0a */
#include "playflic.h"

extern void *FindDataFile(const char *name);
extern short fn_19020(void *buf, unsigned short n);

extern unsigned char *dat_594d8;
extern unsigned char *dat_594d4;
extern unsigned dat_594d0;
extern unsigned dat_594dc;
extern void *dat_594e0;
extern char dat_59440[];
extern unsigned short dat_59444;
extern unsigned short dat_5944c;
extern unsigned short dat_5944e;
extern unsigned short dat_59454;
extern unsigned short dat_517c8;

/* @0x1933c */
short FlicOpen(const char *name, void *chunk, void *image, unsigned first,
               unsigned last)
{
    dat_594d8 = (unsigned char *)chunk;
    dat_594d4 = (unsigned char *)image;
    dat_594d0 = first;
    dat_594dc = last;
    flic_palette_on = 1;
    flic_frames = 0;
    dat_594e0 = FindDataFile(name);
    if (dat_594e0 == 0) {
        return 0;
    }
    if (fn_19020(dat_59440, 0x80) == 0) {
        return 0;
    }
    return dat_517c8 = (dat_59444 == 0xaf12 && dat_5944c == 8 &&
                        dat_5944e == 3 && dat_59454 == 0) ? 1 : 0;
}
