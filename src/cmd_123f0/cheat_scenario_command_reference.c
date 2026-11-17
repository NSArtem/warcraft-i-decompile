/* codegen-flags: -s -ot -oa -4r -zp2 */
/* CMD.C 0x1295c - see docs/subsystems/cmd_123f0.md.
 * REFERENCE C (not built, no `src =` entry): 210 bytes against the original 208 with 140
 * different - OW2 keeps the string pointer and the strtoul endptr in other registers and
 * does not share the `return 1` tail (codegen.md V3). */
#include <stdlib.h>
#include <string.h>

#include "cmd_123f0.h"

/*
 * "orc<N>"/"human<N>" - start scenario N (1..12) of the chosen race.  The
 * scenario resource numbers interleave: human 1..12 are 119,121,...,141 and
 * orc 1..12 are 120,122,...,142 (0x12a0a `add esi,0x77` / 0x129c2 `add esi,0x78`
 * on 2*(n-1)).  Reaching this at all needs the "corwin of amber" developer bit
 * (0x12965 `test byte [0x51217],0x80`); in a network game (net_play_flag) the
 * command is accepted but does nothing.
 */
/* @0x1295c */
short CheatScenarioCommand(char *text, unsigned char *flags)
{
    char *end;
    unsigned long n;

    if (!(cheat_flags.b[3] & 0x80))
        return 0;
    if (!strncmp(text, race_command_text, 3)) {
        if (net_play_flag)
            return 1;
        scenario_race = 1;
        n = strtoul(text + 3, &end, 10);
        if (!n || n > 12)
            return 1;
        scenario_number = (unsigned short)((n - 1) * 2 + 0x78);
    } else if (!strncmp(text, race_command_text + 4, 5)) {
        if (net_play_flag)
            return 1;
        scenario_race = 0;
        n = strtoul(text + 5, &end, 10);
        if (!n || n > 12)
            return 1;
        scenario_number = (unsigned short)((n - 1) * 2 + 0x77);
    } else {
        return 0;
    }
    game_mode = 5;
    return 1;
}
