/* codegen-flags: -s -ot -ol -4r -zp2
 * Module mod_31dc0 (0x31dc0..0x31f70), "OPT" style. */
extern unsigned char esc_color_1, esc_color_2;

/* @0x31dc0 */
void TextSetEscapeColors(unsigned char a, unsigned char b)
{
    esc_color_1 = a;
    esc_color_2 = b;
}
