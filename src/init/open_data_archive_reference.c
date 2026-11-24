/* codegen-compiler: 10.0a */
#include "war.h"

typedef struct _FILE FILE;

extern FILE *FindDataFile(const char *name);
extern void InitResources(FILE *archive);
extern int strcmp(const char *a, const char *b);
extern char path_war[9];
extern const char data_archive_name[9];
extern const char data_archive_subdir[5];
extern const char data_archive_no_other_dir[1];
extern const char data_archive_missing_format[214];

/* @0x1d9d4 */
void OpenDataArchive(void)
{
    FILE *fp;

    fp = FindDataFile(data_archive_name);
    if (fp != 0) {
        InitResources(fp);
        return;
    }
    FatalError(data_archive_missing_format, data_archive_subdir, data_archive_name, exe_dir,
               strcmp(exe_dir, cd_path) != 0 ? cd_path : data_archive_no_other_dir, path_war);
}
