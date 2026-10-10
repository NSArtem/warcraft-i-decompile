/*
 * Shared declarations for the reconstructed Warcraft sources.
 * Every declaration corresponds to an entry in analysis/symbols/ (address,
 * evidence, confidence); keep the two in sync.
 */
#ifndef WAR_H
#define WAR_H

extern char **_argv;            /* 0x557e4 (Watcom runtime) */

/*
 * FatalError (0x30bf0): printf-like, never returns.  The original compiler
 * treated a call to this stack-convention function as clobbering eax, ebx,
 * ecx and edx, so every caller saves ebx/ecx/edx (e.g. 0x1132c, 0x123cc,
 * 0x1d9d4).  OW2's __cdecl assumes eax/ecx/edx only, hence the pragma
 * (docs/subsystems/codegen.md, V7).
 */
void FatalError(const char *fmt, ...);
#pragma aux FatalError "_*" parm caller [] modify [eax ebx ecx edx]

/* GDS heap: malloc/free with "CHECKSIG" guards (graphics.toml) */
void *GdsAlloc(unsigned size);                           /* 0x32558 */
void GdsFree(void *p);                                   /* 0x32780 */

/* startup / paths */
extern char exe_dir[0xb0];      /* 0x59920 */
extern char cd_path[0x90];      /* 0x59870 */
short LoadFile(const char *name, void *buf, unsigned min_size, unsigned max_size,
               short in_exe_dir);                        /* 0x1d330 */
void TrimAtWhitespace(char *s);                          /* 0x1d798 */
void InitPaths(void);                                    /* 0x1d7cc */

#endif
