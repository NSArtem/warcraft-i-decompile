/* codegen-flags: -s -ot -ol -4r -zp2
 * REFERENCE C for SaveWriteImage (0x24bf0), the save-file writer of
 * mod_24860.  Not built: 157 instructions of straight-line block writes; OW2
 * allocates the block pointers differently and its SaveWriteBytes call sites
 * differ, so this is verified as T4 with wc1.cemu (tests/test_mod_24860.py,
 * docs/subsystems/save_format.md).  The on-disk order below is the original's
 * (evidence: the call sites 0x24c1d..0x24df9 and the loader's read order in
 * fn_195ac/fn_1b198/UnitsInitGame).
 */
#include "war.h"
#include "mod_24860.h"

extern int fn_21c20(unsigned code);                  /* 0x21c20 packet-layer error */
extern void fn_146cc(StdFile *fp, int error);        /* 0x146cc save-slot finish */
/* 0x50d7c: RNG seed + scenario/game state block (0x200 bytes); the name is
 * the placeholder from codegen_promo.toml, the object covers 0x50d7c..0x50f7c. */
extern unsigned char dat_50d7c[];

/* @0x24bf0  write the whole save image to `fp` (already positioned at the
 * image start, 0x2c into the save file) and finish the file.
 *
 * The image is a sequence of fixed blocks; every block goes through
 * SaveWriteBytes and a failure aborts the image with the error flag set, which
 * makes the finish routine delete the partial file.  The three record arrays
 * are copied to scratch buffers, rebased to offsets (save_reloc_state mode 1)
 * and written from the copy, so the live game state is not modified.
 */
void SaveWriteImage(StdFile *fp)
{
    unsigned short magic = 0x43;        /* record type word 'C',0 */
    short ok = 1;                       /* 0 = the image is complete */
    unsigned char *tmp = 0;             /* scratch copy for a record block */

    save_reloc_state.w.mode = 1;
    if (SaveWriteBytes((unsigned char *)&magic, 2, fp))
        goto fail;
    if (SaveWriteBytes((unsigned char *)&dat_516ae, 2, fp))
        goto fail;
    if (SaveWriteBytes(net_enemy_record, 0xc, fp))
        goto fail;
    if (SaveWriteBytes((unsigned char *)net_send_state, 6, fp))
        goto fail;
    if (SaveWriteBytes(net_send_ring, 0x550, fp))
        goto fail;
    if (SaveWriteBytes((unsigned char *)net_ring_state, 4, fp))
        goto fail;
    if (SaveWriteBytes((unsigned char *)prefs_block, 0x14, fp))
        goto fail;
    if (SaveWriteBytes(scenario_unit_mask, 0xbb8, fp))
        goto fail;
    if (SaveWriteBytes(dat_50d7c, 0x200, fp))
        goto fail;                       /* 0x50d7c: RNG seed + scenario state */
    if (SaveWriteBytes(tile_map, 0x2000, fp))
        goto fail;
    if (SaveWriteBytes(map_flags, 0x2000, fp))
        goto fail;
    tmp = GdsAlloc(0x4000);
    memcpy(tmp, object_map, 0x4000);
    SaveRelocObjectMap((int *)tmp);
    if (SaveWriteBytes(tmp, 0x4000, fp))
        goto fail;
    GdsFree(tmp);
    if (SaveWriteBytes(fog_map, 0x2000, fp))
        goto fail;
    tmp = GdsAlloc(0x47e0);
    memcpy(tmp, unit_array, 0x47e0);
    SaveRelocUnits((SaveUnitRec *)tmp);
    if (SaveWriteBytes(tmp, 0x47e0, fp))
        goto fail;
    GdsFree(tmp);
    tmp = GdsAlloc(0xed8);
    memcpy(tmp, object_array, 0xed8);
    SaveRelocObjects((SaveObjectRec *)tmp);
    if (SaveWriteBytes(tmp, 0xed8, fp))
        goto fail;
    GdsFree(tmp);
    tmp = 0;
    ok = 0;
fail:
    if (tmp)
        GdsFree(tmp);
    if (ok)
        fn_21c20(0xe);
    fn_146cc(fp, ok);
}
