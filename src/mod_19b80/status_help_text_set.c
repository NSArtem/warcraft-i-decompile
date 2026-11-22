/* codegen-compiler: 10.0a */
#include "mod_19b80.h"

extern const char *status_help_text;
extern unsigned short status_help_kind;

/* @0x19f80 */
void StatusHelpTextSet(const char *text)
{
    status_help_text = text;
    status_help_kind = 0;
}
