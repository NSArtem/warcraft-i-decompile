/* codegen-flags: -s -ot -ol -4r -zp2
 * Module mod_19470 (0x19470..0x19b80), game code, "OPT" style. */

extern long dat_50d7c;

/* @0x19478  linear congruential generator: seed = seed*0x015a4e35+1, returns bits 16..30 */
int fn_19478(void)
{
    dat_50d7c = dat_50d7c * 0x15a4e35L + 1;
    return (int)(dat_50d7c >> 16) & 0x7fff;
}
