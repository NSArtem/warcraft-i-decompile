/* codegen-compiler: 10.0a */
#include "mod_400e4_c.h"

/* @0x400e4 stack-convention (cdecl-like) transparent flipped rect copy */
void __cdecl RectCopyTransparentFlipH(const unsigned char *src, unsigned char *dst, int src_skip, int dst_skip, int width, int height)
{
    int n;
    unsigned char c;

    src = src + width - 1;
    do {
        n = width;
        do {
            c = *src;
            if (c) {
                *dst = c;
            }
            src--;
            dst++;
            n--;
        } while (n);
        src += src_skip;
        dst += dst_skip;
        height--;
    } while (height);
}
