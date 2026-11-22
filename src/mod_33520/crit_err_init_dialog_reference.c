/* codegen-compiler: 10.0a */
/* codegen-flags: -s -od -4r -zp2 */
#include "war.h"

typedef struct Bitmap Bitmap;
struct CritErrControlDescriptor;

extern Bitmap *cur_bitmap;
extern short crit_err_installed;
extern const char *crit_err_message;
extern unsigned char ui_color_base;

/* Address-only linker symbols; no object layout is needed here. */
extern unsigned char crit_err_panel_bitmap[];
extern unsigned char crit_err_button_bitmap[];
extern unsigned char crit_err_button_thin_bitmap[];
extern unsigned char crit_err_control[];

extern void CritErrInstall(void);
extern void DrawBevelPanel(short x, short y, unsigned short w, unsigned short h);
extern void DrawBevelPanelThin(short x, short y, unsigned short w, unsigned short h);
extern void DrawTextCentered(short y, const char *s, unsigned char color);
extern void fn_3d2b0(short selection, struct CritErrControlDescriptor *control,
                     unsigned char color, unsigned char highlight);

void CritErrInitDialog(void)
{
    CritErrInstall();
    crit_err_installed = 0;

    cur_bitmap = (Bitmap *)crit_err_button_bitmap;
    DrawBevelPanel(0, 0, 0x3a, 0x0f);
    cur_bitmap = (Bitmap *)crit_err_button_thin_bitmap;
    DrawBevelPanelThin(0, 0, 0x3a, 0x0f);
    cur_bitmap = (Bitmap *)crit_err_panel_bitmap;
    DrawBevelPanel(0, 0, 0x11e, 0x30);
    DrawTextCentered(8, crit_err_message, (unsigned char)(ui_color_base + 3));
    fn_3d2b0(-1, (struct CritErrControlDescriptor *)crit_err_control,
             ui_color_base, (unsigned char)(ui_color_base + 6));
}
