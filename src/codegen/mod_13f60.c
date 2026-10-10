/* codegen-flags: -s -ot -ol -4r -zp2
 * Module mod_13f60 (0x13f60..0x16390), game code, "OPT" style.
 * -zp2: the struct below is packed (field at +0x16, not +0x18; -zp2 and -zp1 both give that, -zp4/-zp8 do not). */
#include <string.h>

extern short dat_516ae;
extern char dat_59230[];
extern void fn_150f0(int a, int b);
extern short fn_23edc(void);

struct item { char pad[0x16]; char *name; };

/* @0x15170 */
void fn_15170(int a)
{
    fn_150f0(a, 0);
}

/* @0x15230 */
int fn_15230(void)
{
    dat_516ae = fn_23edc();
    return 1;
}

/* @0x15558 */
void fn_15558(struct item *p)
{
    strcpy(dat_59230, p->name);
}
