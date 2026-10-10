/* codegen-flags: -s -ot -ol -4r -zp2
 * Module mod_31dc0 (0x31dc0..0x31f70), "OPT" style. */
extern unsigned char text_esc_colors[2];                /* 0x5ad0b: '@1' / '@2' colour bases */

/* @0x31dc0 */
void TextSetEscapeColors(unsigned char c1, unsigned char c2)
{
    text_esc_colors[0] = c1;
    text_esc_colors[1] = c2;
}
