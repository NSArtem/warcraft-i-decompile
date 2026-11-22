/* codegen-compiler: 10.0a */
#include "mod_1c9c0.h"

/* 0x1cadb passes destination, source and the product formed at 0x1caca. */
extern void fn_103ba(void *dest, const void *src, unsigned count);

typedef struct SpriteCloneEntry {
    unsigned short prefix;
    unsigned char width;
    unsigned char height;
    unsigned long offset;
} SpriteCloneEntry;

typedef struct SpriteClonePrefix {
    unsigned short count;
    unsigned short reserved;
    SpriteCloneEntry first_entry;
} SpriteClonePrefix;

void *CloneSpriteResource(const void *src, unsigned size)
{
    void *dest;
    const SpriteCloneEntry *from;
    SpriteCloneEntry *to;
    unsigned short remaining;
    unsigned count;
    unsigned long offset;
    const unsigned char *pixels_from;
    unsigned char *pixels_to;

    dest = GdsAlloc(size);
    *(SpriteClonePrefix *)dest = *(const SpriteClonePrefix *)src;
    from = &((const SpriteClonePrefix *)src)->first_entry;
    to = &((SpriteClonePrefix *)dest)->first_entry;
    remaining = ((const SpriteClonePrefix *)src)->count;
    goto test_remaining;
    do {
        *to = *from;
        count = (unsigned)from->width * (unsigned)from->height;
        pixels_from = (const unsigned char *)src;
        offset = from->offset;
        pixels_from += offset;
        pixels_to = (unsigned char *)dest;
        pixels_to += offset;
        fn_103ba(pixels_to, pixels_from, count);
        ++from;
        ++to;
    test_remaining:
        --remaining;
    } while (remaining != (unsigned short)-1);
    return dest;
}
