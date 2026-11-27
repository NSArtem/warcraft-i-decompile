#ifndef MOD_2B2F0_H
#define MOD_2B2F0_H

/* mod_2b2f0 (0x2b2f0..0x2b400): per-slot target-mode flags.
 * target_mode_flags (0x5a350) is unsigned short[4], indexed by
 * net_event_pending.  dat_59514 (0x59514) is a callback pointer
 * (map_aux_handler) stored between map_press_handler (0x59510) and
 * map_release_handler (0x59518). */

extern unsigned short target_mode_flags[4];   /* 0x5a350 */
extern void (*map_aux_handler)(void);         /* 0x59514 */

void TargetModeClear(void);                   /* 0x2b2f0 */
unsigned short TargetModeIsActive(void);      /* 0x2b308 */
void TargetModeEnter(void);                   /* 0x2b31c */
void TargetModeExit(void);                    /* 0x2b390 */

#include <string.h>

#endif
