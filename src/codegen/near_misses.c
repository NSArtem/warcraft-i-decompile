/* codegen-near: -s -ot -ol -4r -zp2
 * Functions whose C is believed correct (same operations, same order) but where OW2 -ot picks eax for
 * a scratch value that the original keeps in edx (`push edx; xor edx,edx; mov [m],dx; pop edx`).  No
 * flag or source spelling tried (-os/-ox/-ob/-oh/-ok/-oa, CPU models, locals of every width, volatile)
 * changes this; see docs/subsystems/codegen.md "Register allocation".  They are kept as the closest
 * reproduction and tests/test_codegen.py asserts that they still do NOT match, so an upgraded
 * toolchain that fixes the allocation order is noticed.
 */

extern short dat_59616, dat_593fc;
extern short dat_5175c, dat_5175e, dat_51760, dat_51762, dat_51764, dat_51766;

/* @0x13ef8  module mod_13e60 */
int fn_13ef8(void)
{
    short z = 0;

    dat_59616 = z;
    return 1;
}

/* @0x14c74  module mod_13f60: six words set to -1, the -1 kept in edx */
void fn_14c74(void)
{
    dat_5175c = -1; dat_5175e = -1; dat_51760 = -1;
    dat_51762 = -1; dat_51764 = -1; dat_51766 = -1;
}

/* @0x16cbc  module mod_16390 */
void fn_16cbc(void)
{
    short z = 0;

    dat_593fc = z;
}
