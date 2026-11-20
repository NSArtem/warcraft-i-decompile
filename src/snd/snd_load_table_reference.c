/* codegen-compiler: 10.0a */
#include "audio.h"

extern void *snd_data_ptrs[60];
extern unsigned int snd_data_sizes[60];
extern const unsigned short *snd_cur_table;
extern unsigned short cfg_dig_driver;
extern unsigned short snd_table_count;
extern unsigned long ResourceBegin(unsigned short id, unsigned long *packed_len);
extern void *ResourceRead(void *dest, unsigned count);
extern void DpmiUnlockRegion(void *addr, unsigned size);
extern void GdsFree(void *p);

/* @0x267fc */
void SndLoadTable(const unsigned short *ids)
{
    const unsigned short *p;
    const unsigned short *q;
    unsigned short id;
    unsigned short key;
    unsigned short i;

    p = ids;
    if (ids == 0) {
        p = snd_cur_table;
        snd_cur_table = ids;
        snd_table_count = 0;
    } else {
        snd_cur_table = ids;
    }
    while ((id = *p) != 0) {
        key = id & 0x7fff;
        if (cfg_dig_driver != 0xffff) {
            if ((id & 0x8000) != 0) {
                i = snd_table_count - 1;
                q = p - 1;
                while (i != 0xffff) {
                    if (key == *q) {
                        snd_data_ptrs[snd_table_count] = snd_data_ptrs[i];
                        snd_data_sizes[snd_table_count] = snd_data_sizes[i];
                        break;
                    }
                    q--;
                    i--;
                }
            } else if (snd_cur_table != 0) {
                snd_data_sizes[snd_table_count] = ResourceBegin(id, 0);
                snd_data_ptrs[snd_table_count] = ResourceRead(0, 0);
                DpmiLockRegion(snd_data_ptrs[snd_table_count], snd_data_sizes[snd_table_count]);
            } else {
                DpmiUnlockRegion(snd_data_ptrs[snd_table_count], snd_data_sizes[snd_table_count]);
                GdsFree(snd_data_ptrs[snd_table_count]);
                snd_data_ptrs[snd_table_count] = 0;
            }
        }
        p++;
        snd_table_count++;
    }
    if (snd_cur_table == 0) {
        snd_table_count = 0;
    }
}
