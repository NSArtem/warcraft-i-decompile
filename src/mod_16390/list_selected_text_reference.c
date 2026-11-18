/* codegen-compiler: 10.0a */
/* 0x163a8: text of the row currently selected in a list control. */
#include "mod_16390.h"

const char *ListSelectedText(Dialog *d, DialogItem *item)
{
    const char **texts = (const char **)item->text;
    unsigned short sel = ((unsigned short *)d->params)[item->id * 2];

    return texts[sel];
}
