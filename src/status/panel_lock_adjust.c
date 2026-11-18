/* codegen-flags: -s -ot -ol -4r -zp2 */
/* 0x29424 - a dialog opened (on != 0) or closed (on == 0): the panel's input
 * lock is counted up/down, but only while no network
 * event is pending ([0x5a11a] == 0, i.e. the local game is running). */
extern unsigned short status_lock;                 /* 0x5a2d6 */
extern unsigned short net_event_pending;           /* 0x5a11a */

void StatusPanelLockAdjust(short on)
{
    unsigned short lock = status_lock;

    if (net_event_pending == 0) {
        if (on)
            lock++;
        else if (lock)
            lock--;
    }
    status_lock = lock;
}
