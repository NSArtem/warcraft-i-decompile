/* codegen-flags: -s -ot -ol -4r -zp2 */
extern unsigned short status_lock;                 /* 0x5a2d6 */

/* 0x29410 - drop the panel's input lock (called when a save/load finishes). */
void StatusPanelLockClear(void)
{
    status_lock = 0;
}
