/* codegen-flags: -s -ot -ol -4r -zp2
 * Module mod_32030 (0x32030..0x32060), video library text setup, "OPT" style (no frame, unlike its neighbours). */
extern unsigned char text_color_a, text_color_b, text_color_c;     /* 0x5ad03.. */
extern void (*text_glyph_fn)(void);                                /* 0x5ad07 */
extern void DrawGlyph2bpp(void);

/* @0x32030 */
void TextSetColorBase(unsigned char c)
{
    text_color_a = c;
    text_color_b = c + 1;
    text_color_c = c + 2;
    text_glyph_fn = DrawGlyph2bpp;
}
