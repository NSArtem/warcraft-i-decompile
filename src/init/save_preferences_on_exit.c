/* codegen-compiler: 10.0a */
#include "war.h"

extern const char preferences_filename[];
extern long prefs_block[5];
extern short SaveFileInExeDir(const char *name, const void *buf, unsigned size);

/* 0x1d556 tests the status byte; 0x1d569 saves the block on zero status. */
void SavePreferencesOnExit(char status)
{
    if (status == 0)
        SaveFileInExeDir(preferences_filename, prefs_block, sizeof(prefs_block));
}
