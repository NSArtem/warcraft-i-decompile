#ifndef MOD_2B400_F1_H
#define MOD_2B400_F1_H

#include "war.h"

/* 0x2b7c4: default Watcom register calling convention. */
void DrawAnimatedResourceCounter(const char *format, short x, short y,
                                 int *displayed_count, int target_count);

#endif /* MOD_2B400_F1_H */
