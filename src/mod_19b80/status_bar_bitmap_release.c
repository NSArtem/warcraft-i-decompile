/* codegen-compiler: 10.0a */
#include "mod_19b80.h"

extern char status_bar_bitmap[];
extern void ResourceFreeBody(void *p);

/* @0x19ed0 */
void StatusBarBitmapRelease(void)
{
    ResourceFreeBody(status_bar_bitmap);
}
