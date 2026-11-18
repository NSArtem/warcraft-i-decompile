/* codegen-flags: -s -od -4r -zp2
 * The empty marker whose address is one past the DPMI-locked ISR code region
 * in the source (`&IsrRegionEnd - &IsrRegionStart + 1` is passed to
 * DpmiLockRegion by EvtInit 0x31740-0x31754).  Same OD style as the start
 * marker; reference C, T4.
 */
void IsrRegionEnd(void)
{
}
