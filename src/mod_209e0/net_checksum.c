/* codegen-compiler: 10.0a */
#include "mod_209e0.h"

extern unsigned _rotl(unsigned value, unsigned shift);

/* @0x209e0 */
unsigned short NetChecksum(unsigned char *buf, unsigned short len)
{
    unsigned v = 0;

    while (len--) {
        v ^= *buf++;
        _rotl(v, 3);
    }
    v ^= v >> 16;
    return (unsigned short)v;
}
