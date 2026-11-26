/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -5r -d1+ -zp2 */

extern void HLine(short x, short y, unsigned short len);
extern void VLine(short x, short y, unsigned short len);

/* @0x348c0 */
void RectOutline(short x, short y, unsigned short w, unsigned short h)
{
    HLine(x, y, w);
    HLine(x, (short)(y + h - 1), w);
    VLine(x, y, h);
    VLine((short)(x + w - 1), y, h);
}
