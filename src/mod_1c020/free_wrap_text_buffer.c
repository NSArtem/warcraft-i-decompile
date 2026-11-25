/* codegen-compiler: 10.0a */
#include "mod_1c020.h"

/* 0x1c2f4 loads wrap_text_buffer; 0x1c2f9 jumps to GdsFree. */
void FreeWrapTextBuffer(void)
{
    GdsFree(wrap_text_buffer);
}
