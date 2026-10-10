/*
 * Shared declarations for the reconstructed Warcraft sources.
 * Every declaration corresponds to an entry in analysis/symbols/ (address,
 * evidence, confidence); keep the two in sync.
 */
#ifndef WAR_H
#define WAR_H

extern char **_argv;            /* 0x557e4 (Watcom runtime) */

/* startup / paths */
extern char exe_dir[0xb0];      /* 0x59920 */
extern char cd_path[0x90];      /* 0x59870 */
short LoadFile(const char *name, void *buf, unsigned min_size, unsigned max_size,
               short in_exe_dir);                        /* 0x1d330 */
void TrimAtWhitespace(char *s);                          /* 0x1d798 */
void InitPaths(void);                                    /* 0x1d7cc */

#endif
