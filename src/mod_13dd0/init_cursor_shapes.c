/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "mod_13dd0_f1.h"

extern void SetCursorShape(unsigned char id);
extern unsigned long ResourceBegin(unsigned short id, unsigned long *packed_len);
extern void ResourceReadHeaderBodyAt4(void *p, void *dest);

typedef struct CursorShapeRecord {
    unsigned char bytes[12];
} CursorShapeRecord;

/* @0x13dfc */
void InitCursorShapes(void)
{
    unsigned short index;
    unsigned short resource_id;

    *(CursorShapeRecord *)cursor_shape_table[0] =
        *(const CursorShapeRecord *)default_cursor_shape;
    index = 1;
    resource_id = 0x10a;
    goto test_index;

load_shape:
    ResourceBegin(resource_id, 0);
    ResourceReadHeaderBodyAt4(cursor_shape_table[index], 0);
    ++resource_id;
    ++index;

test_index:
    if (index < 16)
        goto load_shape;

    current_cursor_shape_id = 0xff;
    SetCursorShape(0);
}
