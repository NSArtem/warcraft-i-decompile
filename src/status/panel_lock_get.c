/* codegen-flags: -s -ot -ol -4r -zp2 */
extern unsigned short status_lock;                 /* 0x5a2d6 */

/* 0x2941c - read the panel's input lock counter. */
unsigned short StatusPanelLockGet(void)
{
    return status_lock;
}
