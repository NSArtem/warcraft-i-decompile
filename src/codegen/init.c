/* codegen-flags: -s -ot -ol -4r -zp2
 * Module INIT.C (0x1d2a0..0x1dca0), game code, "OPT" style.
 * (InitPaths of src/init.c is the other function of this module that matches.) */

/* @0x1d798  verified by `python3 -m wc1.match src/codegen/init.c --cflags "<flags above>"`.
 *
 * The store is volatile only to stop OW2 from propagating the stored 0 into the
 * loop test (it would then return directly: `pop edx; ret`); the original reloads
 * the byte (`cmp byte [edx],0`) after the store.
 */
void TrimAtWhitespace(char *s)
{
    while (*s) {
        unsigned c = (unsigned char)*s;

        if (c == '\r' || c == '\n' || c == 0x1a || c == ' ' || c == '\t')
            *(volatile char *)s = '\0';
        else
            s++;
    }
}
