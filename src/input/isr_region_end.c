/* codegen-flags: -s -od -4r -zp2
 * codegen-compiler: 10.0a
 * The empty marker whose address is one past the DPMI-locked ISR code region
 * in the source (`&IsrRegionEnd - &IsrRegionStart + 1` is passed to
 * DpmiLockRegion by EvtInit 0x31740-0x31754).  Same OD style as the start
 * marker; T3 under Watcom 10.0a, which emits the original's `sub esp,0`
 * frame (OW2 writes `sub esp,4`, so it was reference C there).
 */
void IsrRegionEnd(void)
{
}
