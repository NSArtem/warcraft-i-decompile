/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module SAVE.C (0x23ec0..0x24860), game code, "OPT" style
 * (docs/subsystems/codegen.md).
 *
 * Byte-identical functions of the module live here and are taken from C by
 * the build (src = ... in analysis/symbols/save_score.toml); the rest of
 * SAVE.C is reference C in save_reference.c (same logic, but it calls the
 * still-unnamed link primitives fn_131d8/fn_12f24, and OW2's register
 * allocation differs) and is verified differentially in
 * tests/test_save_score.py.  See docs/subsystems/save_score.md.
 */
#include "save_score.h"

/* @0x2417c  inclusive interval test, endpoints in either order
 *
 * The source shape matters for the codegen: each *positive* branch test
 * returns 1 in place, and every failure falls or jumps to the one shared
 * `return 0` at the end (the original merges the zero exits, not the one
 * exits - see docs/subsystems/save_score.md section 6). */
int WordInRange(unsigned short value, unsigned short lo, unsigned short hi)
{
    if (lo < hi) {
        if (value <= hi && value >= lo)
            return 1;
    } else {
        if (value >= lo || value <= hi)
            return 1;
    }
    return 0;
}
