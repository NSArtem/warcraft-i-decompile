/* codegen-compiler: 10.0a */
#include "mod_13f60.h"

extern unsigned short scenario_race;
extern long army_setup[0x13];
extern unsigned short dialog_auto_update;
extern unsigned short setup_changed;
extern unsigned short preview_visible;
extern unsigned char setup_state;
extern unsigned char setup_return_state;
extern ControlTitleBitmap dat_592c0;
extern unsigned short dat_5ab8c;
extern unsigned short dat_5ab8e;
extern unsigned short dat_5ab90;
extern unsigned short dat_5ab92;
extern unsigned short dat_5ab94;
extern void *dat_5ab96;
extern void (*dat_5ab9a)(void);
extern void BitmapBlit(void);
extern void ArmyTotalsText(long *army);
extern void ArmySetupDialog(void);
extern void ControlTitleDraw(void);
extern void ResourceFreeBody(void *hdr);
extern unsigned long ResourceBegin(unsigned short id, unsigned long *packed_len);
extern void LayerInvalidate(unsigned char id);
extern void ScreenUpdate(void);
extern void ResourceReadHeaderBody(void *hdr4, void *dest);

/* @0x1599c */
void SetArmyScreen(void)
{
    short saved = screen_mode;
    short cur;

    ArmyTotalsText(army_setup);
    if (dat_516ae != 0) {
        ResourceBegin((unsigned short)(scenario_race + 0x1d8), 0);
        ResourceReadHeaderBody(&dat_592c0, 0);
        dat_5ab8e = own_campaign ? 0xc0 : 6;
        dat_5ab90 = 0x4d;
        dat_5ab92 = dat_592c0.width;
        dat_5ab94 = dat_592c0.height;
        dat_5ab96 = &dat_592c0;
        dat_5ab9a = BitmapBlit;
        dat_5ab8c = 1;
        LayerInvalidate(0xe);
        if (preview_visible == 0)
            dat_5ab8c = preview_visible;
    }
    dialog_auto_update = 0;
    ArmySetupDialog();
    if (dat_516ae != 0) {
        do {
            if (preview_visible != 0) {
                LayerInvalidate(0xe);
                dat_5ab8c = 0;
            }
            setup_changed = 0;
            screen_mode = (screen_mode == 0);
            ControlTitleDraw();
            if (preview_visible != 0) {
                dat_5ab8c = 1;
                LayerInvalidate(0xe);
            }
            ArmySetupDialog();
        } while (setup_changed != 0);
        cur = screen_mode;
        if (saved != cur) {
            screen_mode = (cur == 0);
            ControlTitleDraw();
        }
        LayerInvalidate(0xe);
        dat_5ab8c = 0;
        ResourceFreeBody(&dat_592c0);
    }
    dialog_auto_update = 1;
    ScreenUpdate();
    setup_state = setup_return_state;
}
