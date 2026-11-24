/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -zp2 */
extern int NetDriverSelect(void);
extern int atexit(void (*fn)(void));
extern void NetLinkExit(void);

/* @0x23ec0 */
short NetLinkStart(void)
{
    short r;

    r = (short)NetDriverSelect();
    if (r != 0) {
        atexit(NetLinkExit);
        return 1;
    }
    return r;
}
