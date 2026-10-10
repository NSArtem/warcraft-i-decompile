/*
 * DATA.WAR resource archive access (see docs/subsystems/resources.md).
 *
 * Module assignment: unknown. The Insider's Guide module list has no
 * resource-archive source name that could be matched to this code.
 *
 * STATUS: behaviour-equivalent but NOT a T3 match. The original (an older
 * Watcom) has an ebp frame and allocates edi/esi differently; tried -od -ox
 * -os -of, with and without pointer-increment source forms. fseek and the
 * fatal printf (0x31a80, 0x30bf0) are not yet named in the symbol database,
 * which wc1.match needs as well. Not referenced by the build (no src= entry).
 */
#include "resources.h"

/* 0x3452c */
long ResourceSeek(unsigned short id)
{
    unsigned long *p = archive_offsets + (unsigned short)(id - 2);
    unsigned long start = *p++;
    unsigned long next = *p;

    if (start == 0xFFFFFFFFUL)
        fatal_error("demo failure %d", (unsigned short)(id - 2) + 2);
    fseek(archive_file, start, 0);
    return next - start + 1;
}
