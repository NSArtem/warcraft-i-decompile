#ifndef SPELL_H
#define SPELL_H

/* SPELL.C (0x27670..0x27b20) - spell handlers and dispatch.
 * Unit layout is defined elsewhere; only pointers are used here.
 * Handler signature: int h(struct Unit *u, short cast);
 *   cast == 0: check only (returns 0 if mana too low)
 *   cast != 0: perform the spell and deduct mana.
 */
struct Unit;

typedef int (*SpellHandler)(struct Unit *u, short cast);

/* 0x53474: 29 entries, indexed by unit byte +0x1f (spell id).
 * Entries beyond those directly referenced are other handlers/default. */
extern SpellHandler spell_handler_table[];   /* 0x53474 */
extern char spell_invalid_msg[];             /* 0x57d38 "spell:1" */
extern unsigned char spell_summon_owner;     /* 0x5a7c8 */

int SpellHeal(struct Unit *u, short cast);          /* 0x27670 */
int SpellHolyVision(struct Unit *u, short cast);    /* 0x27740 */
int SpellInvisibility(struct Unit *u, short cast);  /* 0x277a0 */
int SpellUnholyArmor(struct Unit *u, short cast);   /* 0x277d4 */
int SpellPoisonCloud(struct Unit *u, short cast);   /* 0x27824 */
int SpellRainOfFire(struct Unit *u, short cast);    /* 0x2784c */
int SpellRaiseDead(struct Unit *u, short cast);     /* 0x278ac */
int SpellSummon(struct Unit *u, short cast);        /* 0x279c0 */
int SpellInvalid(struct Unit *u, short cast);       /* 0x27a8c */
void SpellCastOrder(struct Unit *u);                /* 0x27aa4 */
void SpellCastNextOrder(struct Unit *u);            /* 0x27adc */

#endif
