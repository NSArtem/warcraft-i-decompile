/* codegen-compiler: 10.0a */
#include "mod_1e380_f1.h"

/* 0x1e593 finds the anchor before 0x1e5a7 checks the network flag. */
void PlaceCustomStartingUnits(const int *counts, unsigned owner)
{
    Unit *anchor;
    int race;

    anchor = FindCustomStartAnchor(owner);
    if (owner == 0) {
        race = scenario_race;
    } else {
        if (net_play_flag == 0)
            return;
        race = scenario_race_enemy;
    }

    PlaceCustomUnitCopies(owner, counts[6], anchor, race + 10);
    PlaceCustomUnitCopies(owner, counts[4], anchor, race + 4);
    PlaceCustomUnitCopies(owner, counts[5], anchor, race + 12);
    PlaceCustomUnitCopies(owner, counts[2], anchor, race + 8);
    PlaceCustomUnitCopies(owner, counts[1], anchor, race);
    PlaceCustomUnitCopies(owner, counts[3], anchor, race + 6);
    PlaceCustomUnitCopies(owner, counts[0], anchor, race + 2);
}
