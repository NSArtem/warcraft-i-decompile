#ifndef MOD_1DCA0_H
#define MOD_1DCA0_H

/* IPX real-mode wrappers (mod_1dca0). The 0x32-byte register block is the
 * DPMI real-mode call structure (ebx at +0x10, eax at +0x1c, es at +0x22). */

unsigned short IpxInstalled(void);                               /* 0x1dca0; result in AX */
unsigned IpxOpenSocket(unsigned socket);                         /* 0x1dce0 */
void IpxCloseSocket(unsigned socket);                            /* 0x1dd20 */
void IpxGetInternetworkAddress(unsigned seg, unsigned off);      /* 0x1dd5c */
void IpxRelinquishControl(void);                                 /* 0x1dda0 */
void IpxListen(unsigned seg, unsigned off);                      /* 0x1ddd0 */
void IpxSendPacket(unsigned seg, unsigned off);                  /* 0x1de14 */

#endif
