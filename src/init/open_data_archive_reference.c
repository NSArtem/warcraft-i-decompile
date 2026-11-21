/* codegen-compiler: 10.0a */
#include "war.h"

typedef struct _FILE FILE;

extern FILE *FindDataFile(const char *name);
extern void InitResources(FILE *archive);
extern int strcmp(const char *a, const char *b);
extern char path_war[9];
extern char dat_52541[];
extern char dat_5254a[];
extern char dat_56d6c[];
extern char dat_56d70[];

/* @0x1d9d4 */
void OpenDataArchive(void)
{
    FILE *fp;

    fp = FindDataFile(dat_52541);
    if (fp != 0) {
        InitResources(fp);
        return;
    }
    FatalError(dat_56d70, dat_5254a, dat_52541, exe_dir,
               strcmp(exe_dir, cd_path) != 0 ? cd_path : dat_56d6c, path_war);
}
