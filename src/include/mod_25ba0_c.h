#ifndef MOD_25BA0_C_H
#define MOD_25BA0_C_H

typedef struct Unit Unit;
Unit *SelectionNext(void);
Unit *SelectionFirst(void);
void SelectionSet(unsigned short count, Unit **list);

#endif
