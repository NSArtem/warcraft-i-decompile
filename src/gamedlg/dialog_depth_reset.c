/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* Clear the modal dialog nesting counter (ModalScreen 0x1a560): called once
 * when a scenario starts (0x1976c in fn_195ac). */
#include "gamedlg.h"

/* @0x1a714 */
void ModalDepthReset(void)
{
    dialog_depth = 0;
}
