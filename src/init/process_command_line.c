/* codegen-compiler: 10.0a */
#include "war.h"

extern union { unsigned long w; unsigned char b[4]; } cheat_flags;
extern char *strlwr(char *s);
extern short ParseStartupOption(const char *arg);
extern short CmdProcessText(char *text, unsigned char *flags);
extern void PrintUsageAndExit(void);
extern void SetCheatFlags(unsigned long flags);

/* 0x1d74d skips argv[0]; 0x1d764..0x1d784 parses each argument and publishes flags. */
void ProcessCommandLine(void)
{
    unsigned long flags;
    char **args;

    flags = cheat_flags.w;
    args = _argv + 1;
    while (*args != 0) {
        strlwr(*args);
        if (ParseStartupOption(*args) == 0 && CmdProcessText(*args, (unsigned char *)&flags) == 0)
            PrintUsageAndExit();
        SetCheatFlags(flags);
        ++args;
    }
}
