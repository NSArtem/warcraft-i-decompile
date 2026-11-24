/* codegen-compiler: 10.0a */
#include "mod_1c020_c.h"

typedef struct Bitmap { char b[12]; } Bitmap;

extern Bitmap dat_59840;
extern const unsigned char *dat_5985c;
extern void LayerInvalidate(unsigned char id);
extern void ScreenUpdate(void);
extern void GrpFrameBitmap(const unsigned char *grp, unsigned char frame, Bitmap *out);

/* @0x1c24c */
void CreditDrawC(int frame)
{
    LayerInvalidate(16);
    GrpFrameBitmap(dat_5985c, (unsigned char)frame, (Bitmap *)((unsigned char *)&dat_59840 + 8));
    LayerInvalidate(16);
    ScreenUpdate();
}
