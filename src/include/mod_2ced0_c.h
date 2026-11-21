#ifndef MOD_2CED0_C_H
#define MOD_2CED0_C_H

typedef struct Unit Unit;
typedef struct Rect { short x1; short y1; short x2; short y2; } Rect;
typedef struct Bitmap { short w; short h; short pad[4]; } Bitmap;
struct Unit {
    unsigned char type;
    unsigned char sflags;
    unsigned char pad2[4];
    short x;
    short y;
    unsigned char pad_a[3];
    unsigned char frame_base;
    unsigned char dir;
    unsigned char pad_f;
    unsigned short flags;
    unsigned char pad12[4];
    unsigned short hp;
    unsigned char pad18[2];
    unsigned char b1a;
    unsigned char b1b;
    unsigned char b1c;
    unsigned char pad1d;
    unsigned char owner;
    unsigned char pad1f[45];
    short timer;
    unsigned char b4e;
    unsigned char pad4f;
    short s50;
    union { short s; Unit *p; } u52;
    unsigned char pad56[2];
    void *ptr58;
};

#endif
