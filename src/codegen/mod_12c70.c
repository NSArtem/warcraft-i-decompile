/* codegen-flags: -s -ot -ol -4r -zp2
 * Module mod_12c70 (0x12c70..0x13270), game code, "OPT" style. */

/* @0x12cd4  cycles a 0..3 counter: inc word [eax]; xor edx,edx; mov dx,[eax]; cmp edx,4; jl */
unsigned short fn_12cd4(unsigned short *p)
{
    int v;

    (*p)++;
    v = *p;             /* the promoted value is compared as int (cmp edx,4 / jl) */
    if (v >= 4)
        *p = 0;
    return *p;
}
