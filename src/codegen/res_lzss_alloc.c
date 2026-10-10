/* codegen-flags: -s -ot -ol -4r -d1+ -zp2
 * Module res_lzss_alloc (0x41530..0x41550), LZSS decoder ring buffer, "DBG" style. */
extern unsigned char *lzss_ring;
extern void *fn_32558(unsigned size);   /* GDS malloc */

/* @0x41530 */
void LzssAllocRing(void)
{
    lzss_ring = fn_32558(0x1000);
}
