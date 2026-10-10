/* codegen-flags: -s -ot -ol -4r -zp2
 * Module mod_32030 (0x32030..0x32060), video library text setup, "OPT" style (no frame, unlike its neighbours). */
extern unsigned char text_colors[4];                    /* 0x5ad02: glyph pixel value -> colour */
extern int (*text_glyph_fn)(unsigned char ch);          /* 0x5ad07 */
extern int DrawGlyph2bpp(unsigned char ch);

/* @0x32030 */
void TextSetColorBase(unsigned char c)
{
    text_colors[1] = c;
    text_colors[2] = c + 1;
    text_colors[3] = c + 2;
    text_glyph_fn = DrawGlyph2bpp;
}
