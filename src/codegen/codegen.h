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

#include "war.h"     /* FatalError and its calling-convention pragma */

#endif
