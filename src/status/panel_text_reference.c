/* codegen-flags: -s -ot -ol -4r -zp2 */
/* Reference C for the panel's text lines of STATUS.C: FarmPanelDraw 0x28298,
 * GoldMinePanelDraw 0x2839c, ResearchCost 0x28c60 and StatusTextForUnit
 * 0x28d58.  The strings are the STATUS.C pool at 0x57d50..0x57dd9. */
#include "status.h"

/* 0x28298 - the farm panel (types 0x20/0x21) extra lines: str_food_usage with
 * str_used (active men minus summoned creatures) and str_grown (the food
 * capacity from farms); the grown line turns red (colour 0xf6) when the
 * player is over the cap.  Reached through unit_panel_table[0x20].draw. */
void FarmPanelDraw(void)
{
    char buf[0x20];
    unsigned long used;

    cur_font = score_font;
    used = player_active_men[0] - player_summoned[0];
    status_men_used = used;
    status_men_grown = player_food[0];
    TextSetColorBase(0xf3);
    DrawText(3, 0x2e, str_food_usage);
    sprintf(buf, str_used, status_men_used);
    DrawText(0xb, 0x40, buf);
    if (status_men_grown < status_men_used)
        TextSetColorBase(0xf6);
    sprintf(buf, str_grown, status_men_grown);
    DrawText(3, 0x38, buf);
}

/* 0x2839c - the gold mine panel (type 0x32): str_gold_left and the amount,
 * which lives in the unit's +0x54 dword. */
void GoldMinePanelDraw(void)
{
    char buf[0x20];

    cur_font = score_font;
    TextSetColorBase(0xf3);
    DrawText(3, 0x2e, str_gold_left);
    sprintf(buf, str_long, status_unit->target);
    DrawText(0xb, 0x36, buf);
}

/* 0x28c60 - the cost of one research row for one player, in tens of gold
 * (the panel multiplies everything by 10).  Rows 0/1/2/9 are the four
 * weapon/speed/armour upgrades and cost upgrade_level_cost[level] (75, 150,
 * then 0 = maxed); rows 3..8 are the six spells with fixed costs 75/150/300.
 * *level receives the address of the row's level byte for the player. */
unsigned short ResearchCost(unsigned short player, unsigned char row,
                            const unsigned char **level)
{
    const unsigned char *p;
    const unsigned char *level_addr;
    unsigned short cost;

    switch (row) {
    case 0:
        p = &dat_50008[0][0];
        break;
    case 1:
        p = &dat_50008[1][0];
        break;
    case 2:
        p = &dat_50008[2][0];
        break;
    case 3:
        p = &dat_50008[3][0];
        cost = 0x4b;
        *level = p + player;
        return cost * 10;
    case 4:
        p = &dat_50008[4][0];
        cost = 0x96;
        *level = p + player;
        return cost * 10;
    case 5:
        p = &dat_50008[5][0];
        cost = 0x12c;
        *level = p + player;
        return cost * 10;
    case 6:
        p = &dat_50008[6][0];
        cost = 0x4b;
        *level = p + player;
        return cost * 10;
    case 7:
        p = &dat_50008[7][0];
        cost = 0x96;
        *level = p + player;
        return cost * 10;
    case 8:
        p = &dat_50008[8][0];
        cost = 0x12c;
        *level = p + player;
        return cost * 10;
    default:                     /* row 9 and, in the original, any row > 9 */
        p = &dat_50008[9][0];
        break;
    }
    level_addr = p + player;
    *level = level_addr;
    cost = upgrade_level_cost[*level_addr];
    return cost * 10;
}

/* 0x28d58 - the info line's text for the displayed unit into status_text:
 *   worker (type 2/3) carrying    -> str_carrying_gold / str_carrying_lumber
 *   building training (order 0xf) -> "training a<suffix>" / str_building_wall
 *   building researching (0x10)   -> the research text of the produced type
 *   otherwise, when damaged       -> str_repair_cost
 * Only the local player's units get a text (owner must be 0). */
void StatusTextForUnit(void)
{
    Unit *u;
    const char *text;
    unsigned long type;
    unsigned long missing;
    unsigned long order;

    text = 0;
    u = status_unit;
    if (u != 0 && u->owner == 0) {
        type = u->type;
        if (type < 0x20) {
            if (type >= 2 && type <= 3 && (u->work.b.state & 0x20)) {
                if (u->work.b.state & 0x80)
                    text = str_carrying_gold;
                else
                    text = str_carrying_lumber;
            }
        } else if (u->sflags & 0x10) {
            order = u->order;
            if (order == 0x0f) {
                if (u->prod_type <= 0x1f) {
                    sprintf(status_text_prod, str_training,
                            unit_suffix_train[u->prod_type]);
                    text = status_text_prod;
                } else if (u->prod_type == 0x35) {
                    text = str_building_wall;
                }
            } else if (order == 0x10) {
                text = research_text[u->prod_type];
            }
        } else {
            missing = unit_max_hp[type] - u->hp;
            if (missing != 0) {
                sprintf(status_text_repair,
                        str_repair_cost,
                        missing / 8 + 1);
                text = status_text_repair;
            }
        }
    }
    status_text = text;
}
