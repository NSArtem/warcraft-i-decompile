/* codegen-compiler: 10.0a */
#include "mod_13dd0_c.h"

typedef struct CursorDesc {
    unsigned long a;
    unsigned long b;
    unsigned long c;
} CursorDesc;

extern unsigned char dat_58f10;
extern CursorDesc dat_58e50[];
extern void CursorSetImage(const void *desc);

/* @0x13dd0 */
void SetCursorShape(unsigned char id)
{
    if (id != dat_58f10) {
        dat_58f10 = id;
        CursorSetImage(&dat_58e50[id]);
    }
}
