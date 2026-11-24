/* codegen-compiler: 10.0a */
#include "mod_19b80.h"

extern short map_view_rect[4];
extern short status_panel_rect_x1;
extern short status_panel_rect_y1;
extern short status_panel_rect_x2;
extern short status_panel_rect_y2;
extern short side_panel_rect_x1;
extern short side_panel_rect_y1;
extern short side_panel_rect_x2;
extern short side_panel_rect_y2;
extern short ui_mouse_x;
extern short ui_mouse_y;
extern const char *status_help_text;
extern const char *status_help_text_pending;
extern void (*ui_press_handler)(void);
extern void (*ui_release_handler)(void);
extern void (*map_press_handler)(void *);
extern void (*map_aux_handler)(void);
extern void (*map_release_handler)(void *);
extern unsigned short status_help_timer;
extern unsigned short status_help_kind;
extern unsigned short ui_input_locked;
extern unsigned char map_cursor_flags;
extern unsigned short selection_box_enable_a;
extern unsigned short selection_box_enable_b;
extern unsigned short cursor_flag2_condition;
extern void SetCursorShape(unsigned char id);
extern unsigned short PlaceBoxActive(void);
extern unsigned short MapScrollFromMouseEdges(short enable_edges);
extern unsigned int MapScrollUpdateWithoutEdges(void);
extern void StatusPanelTextRefresh(long pt, unsigned kind);
extern short fn_2b308(void);
extern void fn_2b67c(const char *text, unsigned flag);
extern void StatusPanelShow(void);
extern void GameScreenCancelOrPlace(void);
extern void MinimapBeginScrollInput(void);
extern void GameScreenScheduleInputRestore(void);
extern void SelectionBoxBegin(void);

/* @0x1a168 */
void GameScreenMouseUpdate(void)
{
    const char *text;
    unsigned short kind;
    int cursor;

    if (ui_input_locked == 0 && cursor_flag2_condition != 0) {
        map_cursor_flags |= 2;
    } else {
        map_cursor_flags &= 0xfd;
    }
    text = status_help_text_pending;
    kind = 0;
    if (ui_mouse_x >= status_panel_rect_x1 && ui_mouse_x <= status_panel_rect_x2 && ui_mouse_y >= status_panel_rect_y1 && ui_mouse_y <= status_panel_rect_y2) {
        if (status_help_timer == 0) {
            text = status_help_text;
            kind = status_help_kind;
        }
        ui_release_handler = StatusPanelShow;
        ui_press_handler = GameScreenCancelOrPlace;
        StatusPanelTextRefresh(*(long *)&ui_mouse_x, kind);
        MapScrollFromMouseEdges(0);
        cursor = 0;
    } else if (ui_mouse_x >= side_panel_rect_x1 && ui_mouse_x <= side_panel_rect_x2 && ui_mouse_y >= side_panel_rect_y1 && ui_mouse_y <= side_panel_rect_y2) {
        ui_release_handler = map_aux_handler;
        ui_press_handler = MinimapBeginScrollInput;
        cursor = MapScrollFromMouseEdges(0);
    } else if (ui_mouse_x >= map_view_rect[0] && ui_mouse_x <= map_view_rect[2] && ui_mouse_y >= map_view_rect[1] && ui_mouse_y <= map_view_rect[3]) {
        ui_press_handler = (void (*)(void))map_press_handler;
        if (fn_2b308() == 0 && PlaceBoxActive() == 0 && (selection_box_enable_a != 0 || selection_box_enable_b != 0)) {
            ui_release_handler = SelectionBoxBegin;
            cursor = 6;
        } else {
            ui_release_handler = (void (*)(void))map_release_handler;
            cursor = MapScrollUpdateWithoutEdges();
        }
    } else {
        ui_release_handler = GameScreenScheduleInputRestore;
        ui_press_handler = GameScreenCancelOrPlace;
        cursor = MapScrollFromMouseEdges(1);
    }
    if (ui_input_locked == 0) {
        fn_2b67c(text, kind & 0xff);
    }
    SetCursorShape((unsigned char)cursor);
}
