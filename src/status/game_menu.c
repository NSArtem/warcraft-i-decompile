/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* 0x281e8 - the F10 "menu" button of the info line (button record 0x53aec):
 * sends network packet 8, which is how the game menu is opened. */
void NetSendControlPacket(unsigned short id);            /* 0x21c20 */

void OpenGameMenu(void)
{
    NetSendControlPacket(8);
}
