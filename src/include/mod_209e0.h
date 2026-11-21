#ifndef MOD_209E0_H
#define MOD_209E0_H

/* mod_209e0 (0x209e0..0x20a7c): network packet checksum / send / receive.
 * Packet layout: +0 u16 checksum, +2 u16 word (seq/id), +4 u8 length, +5 u8 error flag, payload from +4. */

unsigned short NetChecksum(unsigned char *buf, unsigned short len);       /* 0x209e0 */
int NetReceivePacketChecked(unsigned char *pkt);                          /* 0x20a14 */
void NetSendPacketChecksummed(unsigned char *pkt, unsigned short word);   /* 0x20a50 */


#endif
