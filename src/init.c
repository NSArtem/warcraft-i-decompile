/*
 * Program initialisation: executable/CD paths.
 *
 * Module assignment: provisional. The Insider's Guide lists an INIT.C among
 * the original sources, but which functions it contained is not yet
 * established (see analysis/symbols/startup.toml for per-function evidence).
 */
#include <string.h>
#include "war.h"

/* 0x1d7cc -- verified by `python3 -m wc1.match src/init.c` */
void InitPaths(void)
{
    strcpy(exe_dir, _argv[0]);
    *strrchr(exe_dir, '\\') = '\0';
    memset(cd_path, 0, sizeof(cd_path));
    if (LoadFile("path.war", cd_path, 0, 0x72, 1) == 0)
        strcpy(cd_path, exe_dir);
    else
        TrimAtWhitespace(cd_path);
    strlwr(exe_dir);
    strlwr(cd_path);
}
