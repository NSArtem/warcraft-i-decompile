/* codegen-compiler: 10.0a */
#include "mod_3cc5e_c.h"

void __cdecl RectCopy(const unsigned char *src, unsigned char *dst, int src_skip, int dst_skip, int width, int height)
{
    unsigned n;

    do {
        n = (unsigned)width >> 1;
        if (width & 1) {
            for (; n != 0; n--) {
                *(unsigned short *)dst = *(const unsigned short *)src;
                src += 2;
                dst += 2;
            }
            *dst++ = *src++;
        } else {
            do {
                *(unsigned short *)dst = *(const unsigned short *)src;
                src += 2;
                dst += 2;
                n--;
            } while (n != 0);
        }
        src += src_skip;
        dst += dst_skip;
        height--;
    } while (height != 0);
}
