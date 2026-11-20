/* codegen-compiler: 10.0a */
#include "mod_3cc5e_c.h"

void __cdecl RectCopyTransparent(const unsigned char *src, unsigned char *dst, int src_skip, int dst_skip, int width, int height)
{
    int n;
    unsigned char c;

    do {
        n = width;
        do {
            c = *src;
            if (c != 0) {
                *dst = c;
            }
            src++;
            dst++;
            n--;
        } while (n != 0);
        src += src_skip;
        dst += dst_skip;
        height--;
    } while (height != 0);
}
