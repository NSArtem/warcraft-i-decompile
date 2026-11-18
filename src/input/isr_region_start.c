/* codegen-flags: -s -od -4r -zp2
 * codegen-compiler: 10.0a
 * The empty marker whose address is the start of the DPMI-locked ISR code
 * region (EvtInit 0x31740-0x31754).  "OD" style (docs/subsystems/codegen.md):
 * the object resets all registers and reserves a frame.  OW2 cannot
 * reproduce it byte for byte (`sub esp,4` for the original's `sub esp,0`,
 * section 3); Watcom 10.0a does: T3, built from C.
 */
void IsrRegionStart(void)
{
}
