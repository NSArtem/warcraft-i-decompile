/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* CMD.C 0x12a2c - see docs/subsystems/cmd_123f0.md and
 * analysis/symbols/cmd_123f0.toml.  One function per object: wcc386 aligns
 * every following function to 16 bytes, so a multi-function file would make
 * wc1.match compare trailing filler against the *next* original function. */
#include "cmd_123f0.h"
/*
 * The cheat words, in the order tested (offsets into cheat_code_text):
 *   0x00 "corwin of amber"  flag byte 3 bit 7  - developer mode, gates 0x2c
 *   0x42 "pot of gold"      bit 0x20           - SetCheatFlags adds resources
 *   0x4e "eye of newt"      bit 0x08           - all spells (Insider's Guide)
 *   0x5a "iron forge"       bit 0x10           - all technology
 *   0x65 "sally shears"     bit 0x01           - no fog on the viewport
 *   0x72 "hurry up guys"    bit 0x02           - production/decay timers off
 *   0x2c "there can be only one" bit 0x04      - needs the developer bit set
 *   0x10 "yours truly"      bit 0x100          - force victory
 *   0x1c "crushing defeat"  bit 0x80           - force defeat
 *   0x80 "ides of march"    bit 0x40           - game_mode = 10
 */
/* @0x12a2c */
short CheatCodeCommand(char *text, unsigned char *flags)
{
    if (!CheatCodeMatch(text, cheat_code_text + 0x00)) {
        flags[3] ^= 0x80;
        return 1;
    }
    if (!CheatCodeMatch(text, cheat_code_text + 0x42)) {
        flags[0] ^= 0x20;
        return 1;
    }
    if (!CheatCodeMatch(text, cheat_code_text + 0x4e)) {
        flags[0] ^= 0x08;
        return 1;
    }
    if (!CheatCodeMatch(text, cheat_code_text + 0x5a)) {
        flags[0] ^= 0x10;
        return 1;
    }
    if (!CheatCodeMatch(text, cheat_code_text + 0x65)) {
        flags[0] ^= 0x01;
        return 1;
    }
    if (!CheatCodeMatch(text, cheat_code_text + 0x72)) {
        flags[0] ^= 0x02;
        return 1;
    }
    if (!cheat_flags.f.dev)
        return 0;
    if (!CheatCodeMatch(text, cheat_code_text + 0x2c)) {
        flags[0] ^= 0x04;
        return 1;
    }
    if (!CheatCodeMatch(text, cheat_code_text + 0x10)) {
        flags[1] ^= 0x01;
        return 1;
    }
    if (!CheatCodeMatch(text, cheat_code_text + 0x1c)) {
        flags[0] ^= 0x80;
        return 1;
    }
    if (CheatCodeMatch(text, cheat_code_text + 0x80))
        return 0;
    flags[0] ^= 0x40;
    return 1;
}
