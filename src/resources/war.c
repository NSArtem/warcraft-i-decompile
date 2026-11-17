/*
 * DATA.WAR resource archive access (see docs/subsystems/resources.md).
 *
 * Module assignment: unknown. The Insider's Guide module list has no
 * resource-archive source name that could be matched to this code.
 *
 * STATUS: behaviour-equivalent but NOT a T3 match.  The object is "DBG"
 * style (ebp frame, docs/subsystems/codegen.md); with -d1+ the frame is
 * reproduced but esi/edi are assigned in the other order (V3) and the
 * pointer arithmetic is folded differently (V5), so this is T4 (wc1.cemu,
 * tests/test_resources_lzss.py::test_resource_seek_c_matches_original).
 */
/* codegen-flags: -s -ot -ol -4r -d1+ -zp2 */
#include "resources.h"

/* 0x3452c */
long ResourceSeek(unsigned short id)
{
    unsigned long *p = archive_offsets + (unsigned short)(id - 2);
    unsigned long start = *p++;
    unsigned long next = *p;

    if (start == 0xFFFFFFFFUL)
        FatalError("demo failure %d", (unsigned short)(id - 2) + 2);
    FileSeek(archive_file, start, 0);
    return next - start + 1;
}
