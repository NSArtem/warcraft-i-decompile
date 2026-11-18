/* codegen-flags: -s -od -4r -zp2
 * The empty marker whose address is the start of the DPMI-locked ISR code
 * region (EvtInit 0x31740-0x31754).  "OD" style (docs/subsystems/codegen.md):
 * the object resets all registers and reserves a frame, so OW2 cannot
 * reproduce it byte for byte (section 3) - reference C, T4.
 */
void IsrRegionStart(void)
{
}
