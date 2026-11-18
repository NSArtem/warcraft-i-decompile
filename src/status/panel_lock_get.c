/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
extern unsigned short status_lock;                 /* 0x5a2d6 */

/* 0x2941c - read the panel's input lock counter. */
unsigned short StatusPanelLockGet(void)
{
    return status_lock;
}
