/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -zp2 */
#include "mod_1c020_c.h"

typedef struct Bitmap { char b[12]; } Bitmap;

extern Bitmap dat_59830;
extern const unsigned char *dat_59860;
extern void LayerInvalidate(unsigned char id);
extern void ScreenUpdate(void);
extern void GrpFrameBitmap(const unsigned char *grp, unsigned char frame, Bitmap *out);

/* @0x1c1dc */
void CreditDrawA(int frame)
{
    LayerInvalidate(14);
    GrpFrameBitmap(dat_59860, (unsigned char)frame, (Bitmap *)(dat_59830.b + 8));
    LayerInvalidate(14);
    ScreenUpdate();
}
