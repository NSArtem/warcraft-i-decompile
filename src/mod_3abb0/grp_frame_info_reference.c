/* codegen-flags: -s -os -ol -4r -d1+ -zp2
 * codegen-compiler: 10.0a
 */

typedef struct Bitmap {
    short w;
    short h;
    unsigned char *data;
} Bitmap;

void GrpFrameInfo(const unsigned char *grp, unsigned frame, Bitmap *out, short *xoff, short *yoff, short *maxw, short *maxh);

/* @0x3abb0 */
void GrpFrameInfo(const unsigned char *grp, unsigned frame, Bitmap *out, short *xoff, short *yoff, short *maxw, short *maxh)
{
    const unsigned char *e;

    e = grp + 4 + (frame & 0xff) * 8;
    *xoff = e[0];
    *yoff = e[1];
    *maxw = grp[2];
    *maxh = grp[3];
    out->w = e[2];
    out->h = e[3];
    out->data = (unsigned char *)grp + *(long *)(e + 4);
}
