#ifndef MOD_2CED0_C6_H
#define MOD_2CED0_C6_H

typedef struct Unit {
    short x;
    short y;
    unsigned char pad4[2];
    unsigned char f6;
    unsigned char pad7;
    unsigned char f8;
    unsigned char pad9;
    short tx;
    short ty;
    unsigned short flagsE;
    union {
        unsigned short flags;
        struct { unsigned char flagsLo; unsigned char flagsHi; } b;
    } ;
    unsigned char pad12[4];
    short hp;
    unsigned char pad18[2];
    unsigned char f1a;
    unsigned char type;
    unsigned char f1c;
    unsigned char pad1d;
    unsigned char owner;
    unsigned char pad1f[0x1f];
    short s3e;
    short s40;
    short s42;
    short s44;
    unsigned char *ptr46;
    unsigned char b48;
    unsigned char pad49[3];
    short s4c;
    short s50;
    struct Unit *target;
    long l54;
    unsigned char pad58[4];
} Unit;

#endif
