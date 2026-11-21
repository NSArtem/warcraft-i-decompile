/* codegen-compiler: 10.0a */
#include "mod_16390.h"

/* @0x166bc */
void DialogRelocate(Dialog *d)
{
    int *p;
    unsigned long v;
    int *q;
    short *e;
    DialogItem *it;

    *(long *)&d->art += (long)d;
    *(long *)&d->unk16 += (long)d;
    *(long *)&d->unk1a += (long)d;
    *(long *)&d->cb += (long)d;
    *(long *)&d->unk22 += (long)d;
    *(long *)&d->items += (long)d;

    p = d->params;
    if (p != 0) {
        v = ((unsigned long *)d->cb)[2];
        if (v == (unsigned long)-1) ((unsigned long *)d->cb)[2] = 0; else ((unsigned long *)d->cb)[2] = p[v];
        v = ((unsigned long *)d->cb)[4];
        if (v == (unsigned long)-1) ((unsigned long *)d->cb)[4] = 0; else ((unsigned long *)d->cb)[4] = p[v];
        v = ((unsigned long *)d->cb)[3];
        if (v == (unsigned long)-1) ((unsigned long *)d->cb)[3] = 0; else ((unsigned long *)d->cb)[3] = p[v];
        v = ((unsigned long *)d->cb)[5];
        if (v == (unsigned long)-1) ((unsigned long *)d->cb)[5] = 0; else ((unsigned long *)d->cb)[5] = p[v];
    } else {
        ((unsigned long *)d->cb)[2] = 0;
        ((unsigned long *)d->cb)[4] = 0;
        ((unsigned long *)d->cb)[3] = 0;
        ((unsigned long *)d->cb)[5] = 0;
    }

    q = (int *)d->unk1a;
    while (*q != -1) {
        while (*q != -1) {
            if (*q != 0) *q = *q + (int)d;
            q++;
        }
        q++;
    }

    v = *(unsigned long *)d->cb;
    *(unsigned long *)d->cb = v + (unsigned long)d;

    e = (short *)d->unk22;
    while (*e != -1) {
        if ((unsigned short)*e == 3) {
            *(int *)(e + 3) = d->params[*(unsigned short *)(e + 3)];
        } else {
            *(int *)(e + 3) += (int)d;
        }
        e += 5;
    }

    it = d->items;
    while (it->type != 0xffff) {
        *(long *)&it->art += (long)d;
        *(long *)&it->art_pressed += (long)d;
        if (it->type == 8 || it->type == 3 || it->type == 4 || it->type == 5) {
            if (it->type != 5) it->art = 0;
            it->art_pressed = 0;
        }
        if (it->type == 0 || it->type == 3 || it->type == 5 || it->type == 6 ||
            it->type == 7 || it->type == 8 || it->type == 10 || it->type == 9) {
            *(long *)&it->text += (long)d;
        } else if (it->type == 11) {
            it->text = (void *)((int *)d->params)[(unsigned short)(unsigned long)it->text];
        }
        if (it->type == 7 || it->type == 10) {
            *(int *)&it->id += (int)d;
        }
        it++;
    }
}
