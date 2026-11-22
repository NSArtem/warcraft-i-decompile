#ifndef MOD_33520_H
#define MOD_33520_H

#include "war.h"

typedef struct Bitmap Bitmap;
struct CritErrControlDescriptor;

extern Bitmap *cur_bitmap;                                  /* 0x55438 */
extern short crit_err_installed;                            /* 0x5555c */
extern const char *crit_err_message;                         /* 0x55560 */
extern Bitmap crit_err_panel_bitmap;                        /* 0x55564 */
extern Bitmap crit_err_button_bitmap;                       /* 0x55574 */
extern Bitmap crit_err_button_thin_bitmap;                  /* 0x5557c */
extern struct CritErrControlDescriptor crit_err_control;    /* 0x55584 */
extern unsigned char ui_color_base;                         /* 0x62880 */

/* Watcom 32-bit register calling convention (-4r). */
void CritErrInitDialog(void);                               /* 0x337d0 */

#endif
