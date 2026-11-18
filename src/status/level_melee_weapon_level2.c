/* codegen-flags: -s -ot -ol -4r -zp2 */
/* 0x27e48 - the player's upgrade row 1 == 2: picks the icon variant of the
 * command button (attack buttons use the weapon level, stop buttons the
 * armour level) and gates the matching 'upgrade ...' research button. */
extern unsigned char dat_50008[10][5];            /* 0x50008 player_upgrade */

unsigned short MeleeWeaponIs2(short is_unit)
{
    unsigned long mask = is_unit ? 0x0f : 0xff;

    return (dat_50008[1][0] & (unsigned char)mask) == 2;
}
