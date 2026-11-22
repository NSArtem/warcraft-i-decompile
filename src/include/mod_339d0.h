#ifndef MOD_339D0_H
#define MOD_339D0_H

/* Palette buffers (768 bytes = 256 * RGB), defined elsewhere (graphics). */
extern unsigned char palette_base[768];    /* 0x5ad60 */
extern unsigned char palette_cur[768];     /* 0x5b060 */
extern unsigned char palette_target[768];  /* 0x62570 */

/* 0x339d0: for entries [first, first+count): palette_base = palette_cur
 * (snapshot), palette_target = target_rgb. */
void PaletteBeginFade(unsigned char first, unsigned short count,
                      const unsigned char *target_rgb);

#endif
