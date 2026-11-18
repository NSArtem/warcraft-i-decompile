/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 *
 * Module mod_13f60 (DLG_SET.C): the character filters of the two text fields
 * (edit_char_hook 0x5176c). */
#include "mod_13f60.h"

/* @0x15c50: digits and space. */
short IsNumberChar(int c)
{
    c &= 0xff;
    if (c == ' ' || c >= '0' && c <= '9')
        return 1;
    return 0;
}

/* @0x15c70: a dial-string character (digits plus the ATDT punctuation). */
short IsPhoneChar(unsigned char c)
{
    int v = c;

    if (IsNumberChar(v) != 0 || v == '-' || v == '(' || v == ')' || v == '*'
        || v == ',' || v == '#')
        return 1;
    return 0;
}
