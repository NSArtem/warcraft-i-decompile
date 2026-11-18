/* codegen-flags: -s -ot -ol -4r -zp2 */
/* 0x27b20 - availability test of the "move", "stop", "attack", "repair" and
 * "cancel" buttons (unit_panel_table entries, e.g. 0x53b04/0x53b14/0x53b50):
 * always offered. */
unsigned short ButtonAlwaysAvailable(void)
{
    return 1;
}
