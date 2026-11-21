/* codegen-compiler: 10.0a */
#include "mod_16390.h"

typedef struct TextEnt {
    unsigned short type;
    short x, y;
    char *s;
} TextEnt;

/* @0x168b4 */
void DialogCreate(Dialog *d)
{
    DialogArt *a;
    DialogCallbacks *cb;
    TextEnt *t;
    void *mine;
    short w;

    for (a = d->art; a->id != -1; a++) {
        if (a->id == 0xf5 && dialog_art_data != 0) {
            a->id = dialog_art_bm.w;
            a->kind = dialog_art_bm.h;
            a->data = GdsAlloc(I16(&dialog_art_bm.h) * I16(&dialog_art_bm.w));
            memcpy(a->data, dialog_art_data, I16(&dialog_art_bm.w) * I16(&dialog_art_bm.h));
        } else {
            ResourceBegin(a->id, 0);
            ResourceReadHeaderBody(a, 0);
        }
    }

    cb = d->cb;
    layers[d->layer + 1].x = d->x;
    layers[d->layer + 1].y = d->y;
    layers[d->layer + 1].w = ((Bitmap *)cb->unk0)->w;
    layers[d->layer + 1].h = ((Bitmap *)cb->unk0)->h;
    layers[d->layer + 1].data = (void *)cb->unk0;
    layers[d->layer + 1].draw = (void (*)(short, short, const void *, const void *))BitmapBlit;
    layers[d->layer + 1].active = 1;
    LayerInvalidate((unsigned char)(d->layer + 1));

    d->w = ((Bitmap *)cb->unk0)->w;
    d->h = ((Bitmap *)cb->unk0)->h;
    d->bitmap = GdsAlloc(d->w * d->h);
    layers[d->layer].x = d->x;
    layers[d->layer].y = d->y;
    layers[d->layer].w = d->w;
    layers[d->layer].h = d->h;
    mine = &d->w;
    layers[d->layer].data = mine;
    layers[d->layer].draw = (void (*)(short, short, const void *, const void *))BitmapBlitTransparent;
    layers[d->layer].active = 1;
    LayerInvalidate((unsigned char)d->layer);
    cur_bitmap = mine;
    BitmapClear(0);
    DialogCallOpen(d);
    cur_font = default_font;
    TextSetColorBase(0xf3);

    for (t = (TextEnt *)d->unk22; (short)t->type != -1; t++) {
        if (t->type == 4) {
            cur_bitmap = (void *)d->cb->unk0;
            BitmapBlitTransparentAll(I16(&t->x), I16(&t->y), (Bitmap *)t->s);
            cur_bitmap = mine;
        } else {
            w = (short)TextWidth(default_font, t->s);
            if (t->type == 0 || t->type == 3) {
                t->x = t->x - w / 2;
            } else if (t->type == 2) {
                t->x = t->x - w;
            }
            DrawText(I16(&t->x), I16(&t->y), t->s);
        }
    }
    DialogDrawItems(d);
}
