#ifndef MOD_3ABB0_C_H
#define MOD_3ABB0_C_H

typedef struct Bitmap {\n    short w;\n    short h;\n    unsigned char *data;\n} Bitmap;\n\nvoid GrpFrameInfo(const unsigned char *grp, unsigned frame, Bitmap *out, short *xoff, short *yoff, short *maxw, short *maxh);

#endif
