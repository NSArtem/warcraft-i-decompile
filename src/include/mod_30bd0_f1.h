#ifndef MOD_30BD0_F1_H
#define MOD_30BD0_F1_H

/*
 * mod_30bd0_f1: video backbuffer setup wrapper.
 *
 * VidAllocBackbuffer (0x3b360) and fn_3b3a0 (0x3b3a0) are declared in other
 * headers. The disassembly at 0x30bd0 shows VidAllocBackbuffer receiving
 * eax=0 and edx=arg, so its real prototype may take two args.
 */

/* 0x30bd0: arg is the 16-bit value passed in ax, zero-extended to edx */
void VidSetupBackbuffer(unsigned short arg);

#endif /* MOD_30BD0_F1_H */
