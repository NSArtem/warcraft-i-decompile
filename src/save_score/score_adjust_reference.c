/* codegen-flags: -s -ot -ol -4r -zp2
 * REFERENCE C for the six SCORE.C adjusters (0x24ee0..0x25390), the exact
 * arithmetic documented in docs/subsystems/save_score.md section 3.1.  Not
 * built: each one is a register-allocation or code-order near miss under
 * OW2 (see the t3_blocker of each entry in analysis/symbols/save_score.toml);
 * verified as T4 against the original with wc1.cemu
 * (tests/test_save_score.py::test_t4_score_adjusters).
 *
 * All six skip their body when dat_5a7c2 (0x5a7c2) is non-zero, read the
 * owner byte (+0x1e) of the unit passed in, and use score_value[owner]
 * (0x51a4c) of the affected player.  Divisions are truncating signed
 * divisions (the original uses idiv and the sar/sbb /2, /4 and /8 idioms).
 */
#include "save_score.h"
#include "game_2c4e0.h"

extern unsigned short player_score[4];             /* 0x50e34 */
extern unsigned short player_active_men[4];        /* 0x58e28 */
extern unsigned short player_active_buildings[4];  /* 0x58e00 */
extern unsigned short score_pool;                  /* 0x5a0ce */
extern unsigned short score_cap;                   /* 0x5a0d2 */
extern unsigned char score_value[20];              /* 0x51a4c */
extern unsigned short dat_5a7c2;                   /* 0x5a7c2: skip flag */
extern unsigned short TotalActiveMen(void);
extern unsigned short TotalActiveBuildings(void);

/* @0x24ee0  award for a new man: half* of the value out of the pool.
 * (*) value/4 after the force-ratio; clamps pool then cap. */
void ScoreAddForMen(Unit *u)
{
    int others = TotalActiveMen();
    int mine = player_active_men[u->owner];

    int value;
    int delta;

    others -= mine;

    if (dat_5a7c2 != 0)
        return;
    if (mine == 0)
        mine = 1;
    if (others == 0)
        others = 1;
    value = score_value[u->owner];
    if (mine > others)
        value = value * others / mine;
    delta = value / 4;
    if (delta > score_pool)
        delta = score_pool;
    if (player_score[u->owner] + delta > score_cap)
        delta = score_cap - player_score[u->owner];
    player_score[u->owner] += delta;
    score_pool -= delta;
}

/* @0x24fa0  the same award for a new building, with the /2 step. */
void ScoreAddForBuildings(Unit *u)
{
    int others = TotalActiveBuildings();
    int mine = player_active_buildings[u->owner];

    int value;
    int delta;

    others -= mine;

    if (dat_5a7c2 != 0)
        return;
    if (mine == 0)
        mine = 1;
    if (others == 0)
        others = 1;
    value = score_value[u->owner];
    if (mine > others)
        value = value * others / mine;
    delta = value / 2;
    if (delta > score_pool)
        delta = score_pool;
    if (player_score[u->owner] + delta > score_cap)
        delta = score_cap - player_score[u->owner];
    player_score[u->owner] += delta;
    score_pool -= delta;
}

/* @0x2505c  claw-back for a lost man: value/4, capped by the loser's own
 * score, returned to the pool.  Note the asymmetric forcing: `others` is
 * forced to 1 when either counter is 0; `mine` is never forced. */
void ScoreSubForMen(Unit *u)
{
    int others = TotalActiveMen();
    int mine = player_active_men[u->owner];

    int value;
    int delta;

    others -= mine;

    if (dat_5a7c2 != 0)
        return;
    if (mine == 0)
        others = 1;
    if (others == 0)
        others = 1;
    value = score_value[u->owner];
    if (others > mine)
        value = value * mine / others;
    delta = value / 4;
    if (delta > player_score[u->owner])
        delta = player_score[u->owner];
    player_score[u->owner] -= delta;
    score_pool += delta;
}

/* @0x250fc  the buildings version of the claw-back.  The original reads the
 * MEN counters here although its caller is the buildings accounting - its
 * own copy-paste quirk, kept as found (docs/subsystems/save_score.md). */
void ScoreSubForBuildings(Unit *u)
{
    int others = TotalActiveMen();
    int mine = player_active_men[u->owner];

    int value;
    int delta;

    others -= mine;

    if (dat_5a7c2 != 0)
        return;
    if (mine == 0)
        others = 1;
    if (others == 0)
        others = 1;
    value = score_value[u->owner];
    if (others > mine)
        value = value * mine / others;
    delta = value / 2;
    if (delta > player_score[u->owner])
        delta = player_score[u->owner];
    player_score[u->owner] -= delta;
    score_pool += delta;
}

/* @0x25198  (eax = killer owner, edx = victim unit).  Self-inflicted: half
 * the victim's value off the victim's score, pool untouched.  Otherwise the
 * victim's owner is awarded value/8 out of the pool with the killer's
 * force ratio, clamped pool then cap. */
void ScoreOnMenKilled(unsigned short killer, Unit *victim)
{
    int others = TotalActiveMen();
    int mine = player_active_men[(unsigned short)killer];

    int owner;
    int value;
    int delta;

    others -= mine;

    if (dat_5a7c2 != 0)
        return;
    owner = victim->owner;
    if ((unsigned short)killer == owner) {
        delta = score_value[owner] / 2;
        if (delta > player_score[owner])
            delta = player_score[owner];
        player_score[owner] -= delta;
        return;
    }
    if (mine == 0)
        mine = 1;
    if (others == 0)
        others = 1;
    value = score_value[owner];
    if (mine > others)
        value = value * others / mine;
    delta = value / 8;
    if (delta > score_pool)
        delta = score_pool;
    if (player_score[owner] + delta > score_cap)
        delta = score_cap - player_score[owner];
    player_score[owner] += delta;
    score_pool -= delta;
}

/* @0x2529c  the buildings version of the killed award.  Self-inflicted:
 * the FULL value (no halving).  Otherwise value/4 with the killer's
 * buildings ratio and the same pool/cap clamps. */
void ScoreOnBuildingKilled(unsigned short killer, Unit *victim)
{
    int others = TotalActiveBuildings();
    int mine = player_active_buildings[(unsigned short)killer];

    int owner;
    int value;
    int delta;

    others -= mine;

    if (dat_5a7c2 != 0)
        return;
    owner = victim->owner;
    if ((unsigned short)killer == owner) {
        delta = score_value[owner];
        if (delta > player_score[owner])
            delta = player_score[owner];
        player_score[owner] -= delta;
        return;
    }
    if (mine == 0)
        mine = 1;
    if (others == 0)
        others = 1;
    value = score_value[owner];
    if (mine > others)
        value = value * others / mine;
    delta = value / 4;
    if (delta > score_pool)
        delta = score_pool;
    if (player_score[owner] + delta > score_cap)
        delta = score_cap - player_score[owner];
    player_score[owner] += delta;
    score_pool -= delta;
}
