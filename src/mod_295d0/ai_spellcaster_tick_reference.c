/* codegen-compiler: 10.0a */
/* mod_295d0 REFERENCE C (not built).  AiSpellcasterTick 0x2a8f4: the AI's
 * automatic spell casting for the four spellcaster types (Cleric 0x0c,
 * Conjurer 0x0a, Necrolyte 0x0d, Warlock 0x0b).  Each branch tests the
 * owner's research rows (spell_available) and the unit's mana (+0x1a) and
 * either casts a spell through the spell order (spell_order + callback
 * fn_21168) or queues a summon as the next order; when nothing is cast the
 * unit falls through to the idle behaviour 0x2ab54-free tail.
 * See docs/subsystems/mod_295d0.md. */
#include "mod_295d0.h"

extern int AiCastInvisibility(Unit *u);        /* 0x2a48c */
extern int AiCastHeal(Unit *u);                /* 0x2a270 */
extern int AiCastUnholyArmor(Unit *u);         /* 0x2a624 */
extern int AiCastRaiseDead(Unit *u);           /* 0x2a3cc */
extern int AiCastPointSpell(Unit *u);          /* 0x2a774 */
extern Unit *AiDefendTownHall(Unit *u);        /* 0x2a168 */
extern int AiGuardStartArea(Unit *u);          /* 0x29f40 */
extern void AiIdleUnitTick(Unit *u);           /* 0x2ab54 */

/* 0x2a9cf: the shared "nothing cast" tail. */
static void AiSpellIdle(Unit *u)
{
    Unit *t;

    t = AiDefendTownHall(u);
    if (t != 0) {
        UnitOrderTarget(u, 0, 0, t, fn_20f30);
        return;
    }
    if ((u->order_flags & 0x14) == 0) {
        if (u->work_x == u->tx && u->work_y == u->ty)
            return;
        UnitOrderTarget(u, u->work_x, u->work_y, 0, fn_20f30);
        return;
    }
    AiGuardStartArea(u);
}

/* @0x2a8f4 */
void AiSpellcasterTick(Unit *u)
{
    int type = u->type;
    int mana = u->energy;

    if (type == 0x0c) {                        /* Cleric: heal, invisibility */
        if (spell_available[5][1] != 0 && mana >= 0x7d) {
            if (AiCastInvisibility(u))
                return;
        }
        if (spell_available[3][1] != 0 && mana >= 3) {
            if (AiCastHeal(u))
                return;
        }
        AiSpellIdle(u);
        return;
    }
    if (type == 0x0a) {                        /* Conjurer */
        if (mana >= 0xff) {
            if (spell_available[2][1] != 0) {
                UnitSetNextOrder(u, 0x16);
                return;
            }
            if (spell_available[0][1] != 0) {
                UnitSetNextOrder(u, 0x19);
                return;
            }
        }
        if (spell_available[1][1] != 0 && mana >= 0x96) {
            spell_order = 0x1a;
            if (AiCastPointSpell(u))
                return;
            spell_order = 0;
        }
        AiSpellIdle(u);
        return;
    }
    if (type == 0x0d) {                        /* Necrolyte */
        if (spell_available[5][1] != 0 && mana >= 0x7d) {
            if (AiCastUnholyArmor(u))
                return;
        }
        if (spell_available[3][1] != 0 && mana >= 0x46) {
            if (AiCastRaiseDead(u))
                return;
        }
        AiSpellIdle(u);
        return;
    }
    if (type == 0x0b) {                        /* Warlock */
        if (mana >= 0xff) {
            if (spell_available[2][1] != 0) {
                UnitSetNextOrder(u, 0x17);
                return;
            }
            if (spell_available[0][1] != 0) {
                UnitSetNextOrder(u, 0x18);
                return;
            }
        }
        if (spell_available[1][1] != 0 && mana >= 0x32) {
            spell_order = 0x1b;
            if (AiCastPointSpell(u))
                return;
            spell_order = 0;
        }
        AiSpellIdle(u);
        return;
    }
    if ((u->flags2 & 0x100) != 0)
        return;
    if (mana >= 0xff) {
        UnitSetNextOrder(u, 0x17);
        return;
    }
    if (mana >= 0x3c) {
        UnitSetNextOrder(u, 0x18);
        return;
    }
    AiIdleUnitTick(u);
}
