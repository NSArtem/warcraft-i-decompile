/*
 * Declarations for mod_24860, the save-file loader/writer object
 * 0x24860..0x24e50 (analysis/symbols/mod_24860.toml, prose:
 * docs/subsystems/save_format.md).
 *
 * The module has two halves:
 *   * the save-file reader 0x248e0..0x249f8: RefRelocate (offset <-> pointer
 *     conversion), the stream helpers over the loaded image (SaveReadStream /
 *     SaveSkipStream), the file loader SaveLoadImage and its free;
 *   * the record rebasing helpers 0x24a68..0x24b88 and the writer
 *     SaveWriteImage + SaveWriteBytes.
 *
 * The 0x5c-byte unit record and the 0x26-byte object record are only viewed
 * through the fields the save code touches; the complete unit layout is
 * docs/subsystems/game_2c4e0.md.  Compile with -zp2 (structure packing 2).
 */
#ifndef MOD_24860_H
#define MOD_24860_H

typedef unsigned long word32;

/*
 * The 1994 Watcom stdio FILE, only the fields SaveWriteBytes reads.  The
 * layout is the original's (ptr +0, count +4, base +8, two flag bytes at
 * +0xc/+0xd, buffer size +0x14 - see the clib fputc 0x33f90); OW2's
 * <stdio.h> uses a different struct, so it is declared here.
 */
typedef struct StdFile {
    unsigned char *ptr;         /* 0x00 next character position */
    int            cnt;         /* 0x04 characters left in the buffer */
    unsigned char *base;        /* 0x08 buffer start */
    unsigned char  flag;        /* 0x0c access mode bits (0x02 = writable) */
    unsigned char  mode;        /* 0x0d status bits (0x04 line buffered, 0x10 dirty) */
    unsigned short handle;      /* 0x0e file handle */
    int            unknown;     /* 0x10 */
    unsigned       bufsiz;      /* 0x14 buffer size */
} StdFile;

/* ---------------------------------------------------------------- the records
 * Save-module view of the 200-unit array (base in unit_array, stride 0x5c).
 * Field meanings are the ones the save code exercises; offsets in comments.
 */
/* The 16-bit flag word at +0x10: bit 0 marks a free record (the loader skips
 * those); the loader clears the high-byte bits 0x18 (0x24ad2). */
typedef union SaveUnitFlags {
    unsigned short w;                 /* 0x10 */
    struct {
        unsigned char lo;             /* 0x10 */
        unsigned char hi;             /* 0x11 */
    } b;
} SaveUnitFlags;

typedef struct SaveUnitRec {
    unsigned char  reserved00[0x10];  /* 0x00 pixel/tile position, animation, flags2 */
    SaveUnitFlags  flags;             /* 0x10 */
    unsigned char  reserved12[9];     /* 0x12..0x1a hp, damage fraction */
    unsigned char  type;              /* 0x1b unit type (>= 0x20 = building/object) */
    unsigned char  type_copy;         /* 0x1c type copy (also used by the death code) */
    unsigned char  reserved1d[0x1d];  /* 0x1d..0x39 sprite, owner, order, path, timers */
    int            link3a;            /* 0x3a related-unit pointer/offset */
    int            tile_save;         /* 0x3e saved tile position (special objects) */
    int            link42;            /* 0x42 second unit link (units); a tile Point for special objects */
    int            placement;         /* 0x46 scenario_data link (buildings) */
    unsigned char  reserved4a[8];     /* 0x4a..0x51 */
    int            target;            /* 0x52 target unit pointer/offset */
    unsigned short reserved56;        /* 0x56 */
    int            overlay;           /* 0x58 damage-overlay object pointer/offset */
} SaveUnitRec;                        /* 0x5c */

/* Save-module view of the 100-object array (base in object_array, stride 0x26).
 * The records hold the small draw objects (damage bars, corpses); fn_119c0
 * 0x119c0 hands out a free one by scanning for flags bit 0 == 1. */
typedef struct SaveObjectRec {
    unsigned char  type;              /* 0x00 */
    unsigned char  flags;             /* 0x01 bit 0 = free slot */
    unsigned char  reserved02[0x1c];  /* 0x02..0x1d */
    int            link1e;            /* 0x1e unit pointer/offset */
    int            link22;            /* 0x22 unit pointer/offset */
} SaveObjectRec;                      /* 0x26 */

/*
 * The relocation-direction state word.  The original reads it as one 4-byte
 * object at 0x5a0b2 (fixup 0x24a81 -> 0x5a0b2) and shifts right 16, i.e. the
 * *high* half is the mode; the loader/writer set the mode with a 16-bit store
 * to 0x5a0b4 (fixup 0x2490b/0x24c02 -> 0x5a0b4), which is this union's +2.
 */
typedef union SaveRelocState {
    long raw;                          /* 0x5a0b2: read and shifted */
    struct {
        unsigned short lo;             /* 0x5a0b2 (overlaps save_stream_left) */
        unsigned short mode;           /* 0x5a0b4: 0 = loading, 1 = saving */
    } w;
} SaveRelocState;

/* ---------------------------------------------------------------- the globals */
extern unsigned long save_stream_left;    /* 0x5a0b0 image bytes not yet read */
extern SaveRelocState save_reloc_state;   /* 0x5a0b2 relocation direction */
extern unsigned char *save_image;         /* 0x5313c GdsAlloc'd loaded image */
extern unsigned char *unit_array;         /* 0x59640 200 x 0x5c unit records */
extern unsigned char *object_array;       /* 0x59644 100 x 0x26 object records */
extern int *object_map;                   /* 0x58580 64x64 tile -> unit record */
extern unsigned char *tile_map;           /* 0x58584 64x64 tile graphics words */
extern unsigned char *map_flags;          /* 0x5857c 64x64 tile flag words */
extern unsigned char *fog_map;            /* 0x58578 64x64 fog words */
extern unsigned char scenario_unit_mask[]; /* 0x50004 start of the 0xbb8-byte scenario block */
extern long prefs_block[];                /* 0x532b4 5 words loaded from PREFS.WAR */
extern unsigned short dat_516ae;          /* 0x516ae save-header word (codegen_promo name) */
extern unsigned char net_enemy_record[];  /* 0x5a084 12-byte partner identity block */
extern unsigned char net_send_ring[];     /* 0x58848 10 x 0x88-byte message ring */
extern unsigned short net_ring_state[];   /* 0x58d98 ring index, ring size-1 */
extern unsigned short net_send_state[];   /* 0x58d9c 3 message/sequence words */

/* ---------------------------------------------------------------- the library */
long FileTell(StdFile *fp);                                       /* 0x319c4 */
int FileSeek(StdFile *fp, long offset, int whence);               /* 0x31a80 */
unsigned long FileRead(void *buf, unsigned long size, unsigned long n,
                       StdFile *fp);                              /* 0x31adc */
int fputc(int c, StdFile *fp);                                    /* 0x33f90 */
unsigned char *SaveStreamValidate(unsigned char *pos);            /* 0x241a4 (SAVE.C) */
void *memcpy(void *dst, const void *src, unsigned int n);         /* 0x31789 */

/* ---------------------------------------------------------------- the module */
int RefRelocate(int ref, int base, short to_offset);              /* 0x248e0 */
unsigned char *SaveReadStream(void *dst, unsigned count,
                              unsigned char *pos);                /* 0x249a4 */
unsigned char *SaveSkipStream(unsigned count, unsigned char *pos);/* 0x249c8 */
void SaveFreeImage(void);                                         /* 0x249e0 */
unsigned char *SaveLoadImage(StdFile *fp);                        /* 0x24900 */
short SaveWriteBytes(const unsigned char *data, short count,
                     StdFile *fp);                                  /* 0x249f8 */
void SaveRelocObjectMap(int *map);                                /* 0x24a68 */
void SaveRelocUnits(SaveUnitRec *u);                              /* 0x24aa8 */
void SaveRelocObjects(SaveObjectRec *o);                          /* 0x24b88 */
void SaveWriteImage(StdFile *fp);                                 /* 0x24bf0 */

#endif
