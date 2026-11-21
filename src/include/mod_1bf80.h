#ifndef MOD_1BF80_H
#define MOD_1BF80_H

/* mod_1bf80 (0x1bf80..0x1c020): modal wait-for-input-or-timeout loop */

extern short wait_done_flag;    /* 0x59690 */
extern short wait_ticks_left;   /* 0x59692 */

void WaitTickDown(void);                    /* 0x1bf80 */
void WaitSetDone(void);                     /* 0x1bf88 */
short WaitInputOrTimeout(short ticks);      /* 0x1bf94 */

#endif
