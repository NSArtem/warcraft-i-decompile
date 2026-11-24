/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -zp2 */
#include "mod_1c020_c.h"

typedef struct Bitmap { char b[12]; } Bitmap;

extern Bitmap dat_59830;
extern const unsigned char *dat_59854;
extern void LayerInvalidate(unsigned char id);
extern void ScreenUpdate(void);
extern void GrpFrameBitmap(const unsigned char *grp, unsigned char frame, Bitmap *out);

/* @0x1c284 */
void CreditDrawD(int frame)
{
    LayerInvalidate(17);
    GrpFrameBitmap(dat_59854, (unsigned char)frame, &dat_59830);
    LayerInvalidate(17);
    ScreenUpdate();
}
