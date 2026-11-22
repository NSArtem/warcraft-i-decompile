/* codegen-compiler: 10.0a */
#include "mod_19470.h"
#include <stdio.h>

extern void PacketTick(void);
extern unsigned char *SaveStreamValidate(unsigned char *pos);
extern unsigned char *SaveLoadImage(FILE *fp);

/* 0x19908 */
int GameHandlePendingLoad(void)
{
    int i;
    FILE *fp;
    unsigned cleared;

    i = 0;
    do {
        PacketTick();
    } while (++i < 5);

    if (slot_file == 0 && load_not_cancelled == 0)
        return 1;

    fp = (FILE *)slot_file;
    if (fp != 0) {
        void *closed_slot;

        pending_save_image = SaveLoadImage(fp);
        fclose((FILE *)slot_file);
        closed_slot = 0;
        slot_file = closed_slot;
    } else {
        SaveStreamValidate(0);
        pending_save_image = (unsigned char *)fp;
    }

    cleared = 0;
    load_not_cancelled = (unsigned short)cleared;
    if (pending_save_image != 0)
        return 1;
    game_mode = 3;
    return 0;
}
