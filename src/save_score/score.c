/* codegen-flags: -s -ot -ol -4r -zp2
 * Module SCORE.C (0x24e50..0x25820), game code, "OPT" style
 * (docs/subsystems/codegen.md).
 *
 * Byte-identical functions of the module live here and are taken from C by
 * the build (src = ... in analysis/symbols/save_score.toml).  The other
 * functions of the range are reference C in score_reference.c: same logic,
 * but OW2 allocates a different register for one value in each of them
 * (the V2/V3 differences of docs/subsystems/codegen.md section 4), so they
 * are verified differentially in tests/test_save_score.py instead.
 * See docs/subsystems/save_score.md.
 */
#include "save_score.h"

extern unsigned short score_cap;                   /* 0x5a0d2 */
extern unsigned short score_rate;                  /* 0x5a0cc */
extern unsigned short score_cap_tbl[12];           /* 0x5315c */
extern unsigned short score_rate_tbl[12];         /* 0x53174 */

/* @0x257c0  dead code: the fixed-level variant of ScoreInit's two table
 * loads (no caller in the image - kept by the linker). */
void ScoreSetUncapped(void)
{
    score_cap = score_cap_tbl[11];
    score_rate = score_rate_tbl[11];
}
