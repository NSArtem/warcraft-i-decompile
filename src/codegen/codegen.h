/*
 * Shared declarations for the codegen-matching samples (docs/subsystems/codegen.md).
 *
 * The functions in this directory are byte-for-byte reconstructions found while
 * studying which compiler configuration reproduces war.exe.  Each file starts
 * with a codegen-flags line giving the wcc386 flags that match it; every
 * function carries an address annotation comment (at-sign plus hex address)
 * for tools/wc1/codegen_sweep.py.
 */
#ifndef CODEGEN_H
#define CODEGEN_H

/*
 * Variadic game routines that never return (FatalError, 0x30bf0).  The original
 * compiler treated a call to such a stack-convention function as clobbering
 * eax, ebx, ecx and edx, so every caller saves ebx/ecx/edx in its prologue
 * (e.g. 0x1132c, 0x123cc, 0x1d9d4).  OW2's __cdecl assumes eax/ecx/edx only,
 * so the original's convention must be requested explicitly.
 */
extern void FatalError(const char *fmt, ...);
#pragma aux FatalError "_*" parm caller [] modify [eax ebx ecx edx]

#endif
