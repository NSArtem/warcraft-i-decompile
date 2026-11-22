/* codegen-compiler: 10.0a */
typedef struct Unit Unit;

/* 0x1b5e1: the call to 0x1b11c passes sign-extended coordinates in EAX and EDX. */
extern void MapCenterOnTile(int x, int y);

void MapCenterOnUnit(Unit *unit)
{
    unsigned char *record = (unsigned char *)unit;

    if (record != 0)
        MapCenterOnTile(*(long *)(record + 8) >> 16,
                        *(long *)(record + 10) >> 16);
}
