/* codegen-compiler: 10.0a */
#include "mod_13dd0_c.h"
#include "mod_13dd0_f1.h"

extern unsigned char current_cursor_shape_id;
extern void CursorSetImage(const void *desc);

/* @0x13dd0 */
void SetCursorShape(unsigned char id)
{
    if (id != current_cursor_shape_id) {
        current_cursor_shape_id = id;
        CursorSetImage(&cursor_shape_table[id]);
    }
}
