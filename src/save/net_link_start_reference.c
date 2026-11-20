/* codegen-compiler: 10.0a */
extern short fn_20a80(void);
extern int atexit(void (*fn)(void));
extern void NetLinkExit(void);

/* @0x23ec0 */
short NetLinkStart(void)
{
    short r;

    r = fn_20a80();
    if (r != 0) {
        atexit(NetLinkExit);
        return 1;
    }
    return r;
}
