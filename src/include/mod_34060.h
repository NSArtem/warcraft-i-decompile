#ifndef MOD_34060_H
#define MOD_34060_H

/* mod_34060: DPMI free-memory query.
 * Uses int386x (0x30e7f) and segread (0x30e57) from the Watcom runtime. */

/* 0x34060: DPMI 0500h Get Free Memory Information; returns buffer dword at
 * +0x10 (total unlocked pages) * 4, i.e. KB. */
unsigned long DpmiGetFreeMemoryKB(void);

#endif /* MOD_34060_H */
