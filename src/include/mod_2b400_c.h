#ifndef MOD_2B400_C_H
#define MOD_2B400_C_H

/* 0x2b67c: EAX supplies text; DL is saved and tested at 0x2b727. */
void StatusBarDrawText(const char *text, unsigned char show_costs);
/* 0x2b824: compares displayed and target counts at 0x2b836..0x2b84e. */
void ResourceCountersUpdate(void);

#endif
