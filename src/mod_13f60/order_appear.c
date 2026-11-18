/* codegen-flags: -s -ot -ol -4r -zp2
 * mod_13f60 (0x13f60..0x16390, DISPATCH.C): the unit order update handlers.
 * Every handler takes the unit in eax and returns non-zero when the order is
 * done (fn_2ec0c calls it at 0x2ed19 through order_update_table 0x5158c). */
/* codegen-compiler: 10.0a */

struct Unit {
    char pad0[0x1f];
    unsigned char order;            /* 0x1f */
};

/* @0x13fe8: order 0x1c, set for a freshly created skeleton (0x2e821). */
int OrderUpdateAppear(struct Unit *u)
{
    (void)u;
    return 1;
}
