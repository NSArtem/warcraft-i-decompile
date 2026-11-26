#ifndef MOD_25BA0_F1_H
#define MOD_25BA0_F1_H

#include "war.h"
#include <string.h>

typedef struct Unit Unit;

extern const unsigned short player_selection_masks[2]; /* 0x51dbc */
extern void *unit_array;                              /* 0x59640 */
extern void *selected_units[2][4];                    /* 0x5a0f0: 0x10-byte row stride */
extern unsigned short player_selection_count[2];     /* 0x5a110; element 1 at 0x5a112 */
extern unsigned short selection_uses_unit_display_type; /* 0x5a116 */
extern unsigned short selection_local;                /* 0x5a118 */
extern unsigned short net_event_pending;              /* 0x5a11a */
extern unsigned char selection_first_display_type;    /* 0x5a11c */
extern unsigned short scenario_race;                  /* 0x50088 */
extern unsigned short type_is_creature[52];           /* 0x51cc0 */

/* Default Watcom register convention. */
void SelectionRebuildFromUnitFlags(void);             /* 0x25ba0 */
void SelectionClearCurrent(void);                     /* 0x25cd8 */
void SelectionSetDisplayType(unsigned short type);     /* 0x25d60 */
void SelectionRestoreDisplayTypes(void);              /* 0x25d7c */
void SelectionRefreshStatus(void);                    /* 0x25d98 */
void SelectionRemoveUnit(Unit *u);                     /* 0x25e58 */

unsigned short PlaceBoxActive(void);
void PlaceBoxCancel(void);
Unit *SelectionFirst(void);
Unit *SelectionNext(void);
void StatusPanelSetUnit(Unit *u);
void fn_25f9c(unsigned short count, Unit **units);
int TargetModeIsActive(void);
void TargetModeExit(void);

/* Selection-facing Unit layout: 0x25c0d advances by 0x5c; 0x25bfc reads flags at 0x10; 0x25d86/0x25d89 copy 0x1b to 0x1c; 0x25dd2 tests 0x1e. */
struct Unit {
    unsigned char reserved_00[0x10];
    unsigned short selection_flags;
    unsigned char reserved_12[9];
    unsigned char base_type;
    unsigned char display_type;
    unsigned char reserved_1d;
    unsigned char owner;
    unsigned char reserved_1f[0x3d];
};

#endif
