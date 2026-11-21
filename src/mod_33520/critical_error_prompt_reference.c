/* codegen-flags: -s -od -4r -zp2
 * codegen-compiler: 10.0a
 */

typedef struct { short x, y, x2, y2, w, h; } CeRect;
typedef struct { short type; short a, b, c, d; short key; } CeEvent;

extern short crit_err_installed;
extern char *dat_55560;
extern char dat_55564[];
extern char dat_5556c[];
extern char dat_57efc[];
extern char dat_57f04[];
extern char dat_57f34[];
extern void *cur_bitmap;
extern char vga_bm[];
extern unsigned short evt_mask;
extern short dat_5a8fa;
extern unsigned char cursor_layer_id;
extern short layers[];

extern void cputs(const char *s);
extern void BitmapBlit(short x, short y, const void *src, const void *r);
extern void BitmapBlitAll(short x, short y, const void *src);
extern void LayerInvalidate(unsigned char id);
extern void EvtPump(void);
extern short EvtGet(void *ev);
extern void EvtProcess(void *ev);
extern void CursorLayerShow(void);
extern void exit(int status);
extern void delay(unsigned ms);

void CriticalErrorPrompt(void)
{
    CeRect r;
    CeEvent ev;
    void *saved_bm;
    unsigned long saved_mask;
    unsigned long cur_vis;

    if (crit_err_installed) {
        cputs(dat_57efc);
        cputs(dat_55560);
        cputs(dat_57f04);
    } else {
        saved_bm = cur_bitmap;
        r.x = 0x11;
        r.y = 0x4c;
        r.w = 0x11e;
        r.h = 0x30;
        r.x2 = (short)(*(long *)&r.x + *(long *)&r.w - 1);
        r.y2 = (short)(*(long *)&r.y + *(long *)&r.h - 1);
        cur_bitmap = dat_5556c;
        BitmapBlit(0, 0, vga_bm, &r);
        cur_bitmap = vga_bm;
        BitmapBlitAll(0x11, 0x4c, dat_55564);
        cur_vis = (unsigned short)layers[cursor_layer_id * 9];
        LayerInvalidate(cursor_layer_id);
        layers[cursor_layer_id * 9] = 0;
    }
    saved_mask = evt_mask;
    EvtPump();
    evt_mask = 0x380;
    EvtPump();
    for (;;) {
        if (EvtGet(&ev) != 0) {
            EvtProcess(&ev);
            if ((unsigned)ev.type == 0x80) {
                if (ev.key == 0x41 || ev.key == 0x61)
                    exit(1);
                if (ev.key == 0x52 || ev.key == 0x72)
                    break;
            }
        }
    }
    dat_5a8fa = 0;
    if (crit_err_installed) {
        cputs(dat_57f34);
    } else {
        if ((short)cur_vis != 0)
            CursorLayerShow();
        evt_mask = (unsigned short)saved_mask;
        cur_bitmap = vga_bm;
        BitmapBlitAll(0x11, 0x4c, dat_5556c);
        cur_bitmap = saved_bm;
        delay(0xfa);
    }
}
