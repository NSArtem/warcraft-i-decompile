#ifndef MOD_32A80_C_H
#define MOD_32A80_C_H

typedef struct Event { unsigned short type; unsigned char pad[6]; unsigned char key; unsigned char mods; unsigned short ch; } Event;
void KeyModClear(unsigned char mask);
void KeyModSet(unsigned char mask);
void KeyModToggle(unsigned char mask);
void EvtProcess(Event *ev);

#endif
