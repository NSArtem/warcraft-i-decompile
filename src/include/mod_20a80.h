#ifndef MOD_20A80_H
#define MOD_20A80_H

/* Network driver vtable: 6 function pointers at 0x59b90..0x59ba4.
 * net_driver[0] (0x59b90) is declared elsewhere; the remaining slots are
 * the separate globals below. */
extern void (*net_driver_connect)(void);   /* 0x59b94 */
extern void (*net_driver_stop)(void);      /* 0x59b98 */
extern void (*net_driver_receive)(void);   /* 0x59b9c */
extern void (*net_driver_send)(void);      /* 0x59ba0 */
extern void (*net_driver_drain)(void);     /* 0x59ba4 */

int NetDriverSelect(void);                                              /* 0x20a80 */
unsigned NetDriverConnectShowCursor(void);                              /* 0x20b2c */
void NetDriverShutdown(void);                                           /* 0x20b70 */
unsigned NetDriverReceiveChecked(void *buf_off, unsigned buf_seg);      /* 0x20ba8 */
void NetDriverSendRepeated(void *buf_off, unsigned buf_seg, unsigned short len); /* 0x20bd4 */
void NetDriverDrain(void);                                              /* 0x20c1c */

#endif
