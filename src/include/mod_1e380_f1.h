#ifndef MOD_1E380_F1_H
#define MOD_1E380_F1_H

#include "war.h"

typedef struct Unit Unit;

extern unsigned long scenario_unit_mask;
extern unsigned short scenario_race;
extern unsigned short scenario_race_enemy;
extern unsigned short scenario_palette_cycle_enable_mask;
extern unsigned short custom_game;
extern unsigned short custom_map_group;
extern const unsigned char custom_unit_race_swap[];
extern short unit_type_size[52][2];
extern unsigned short net_play_flag;
extern const char place_custom_error[13];
extern void *unit_array;

unsigned char *ApplyScenarioTerrainKindRects(unsigned char *records, const unsigned char *kind_map);
unsigned char *ApplyScenarioTerrainOwnerRects(unsigned char *records, const unsigned char *owner_map);
/* Returns the end of the 200-slot scan if there is no match. */
Unit *FindCustomStartAnchor(unsigned owner);
void PlaceCustomUnitCopies(unsigned owner, int count, Unit *anchor, int type);
void PlaceCustomStartingUnits(const int *counts, unsigned owner);
unsigned char *LoadScenarioUnitRecords(unsigned char *records, const unsigned char *owner_map);
unsigned char *LoadScenarioPaletteCycles(unsigned char *records);
unsigned char *LoadScenarioPlacementRecords(unsigned char *records, const unsigned char *value_map);

#endif
