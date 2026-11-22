/* codegen-compiler: 10.0a */
#include "mod_16390.h"

/* @0x17588 */
int EditFieldRun(Dialog *d, DialogItem *item, char *dest, const char *src, unsigned short maxlen)
{
    Rect r;
    Event ev;
    short got;
    short insert = 1;
    short running;
    short first = 1;
    unsigned short pos;
    unsigned short last;
    char *buf;

    edit_buffer = (char *)GdsAlloc(maxlen + 1);
    if (strcmp(src, str_empty_slot) == 0) {
        edit_cursor = 0;
    } else {
        strcpy(edit_buffer, src);
        edit_cursor = (short)strlen(edit_buffer);
    }
    buf = edit_buffer;
    pos = edit_cursor;
    while (pos != maxlen) {
        buf[pos] = ' ';
        pos++;
    }
    buf[pos] = 0;

    r.x = item->x - 3;
    r.y = item->y;
    r.right = *(short *)d->cb->unk0 - 1;
    r.bottom = r.y + ((Font *)cur_font)->rows - 1;
    r.w = r.right - r.x + 1;
    r.h = r.bottom - r.y + 1;

    LayerInvalidate(cursor_layer_id);
    layers[cursor_layer_id].active = 0;
    EditFieldDraw(r, 1);
    LayerInvalidate((unsigned char)d->layer);
    ScreenUpdate();
    buf = edit_buffer;
    running = 1;
    last = maxlen - 1;

    do {
        if (net_play_flag) {
            if (screen_mode) {
                NetSendLocalEvent(&ev);
                got = 1;
            } else {
                got = NetQueryRemoteEvent(&ev);
            }
        } else {
            got = EvtGet(&ev);
        }
        buf = edit_buffer;
        if (setup_quit) {
            ev.key = 0;
            break;
        }
        if (dialog_pre_event)
            dialog_pre_event();
        if (got) {
            EvtProcess(&ev);
            if (ev.type == 0x80) {
                buf = edit_buffer;
                switch ((unsigned short)ev.key) {
                case 0x5200: ev.key = '0'; break;
                case 0x4f00: ev.key = '1'; break;
                case 0x5000: ev.key = '2'; break;
                case 0x5100: ev.key = '3'; break;
                case 0x4b00: ev.key = '4'; break;
                case 0x4c00: ev.key = '5'; break;
                case 0x4d00: ev.key = '6'; break;
                case 0x4700: ev.key = '7'; break;
                case 0x4800: ev.key = '8'; break;
                case 0x4900: ev.key = '9'; break;
                }
                switch ((unsigned short)ev.key) {
                case 0x0d:
                case 0x1b:
                    running = 0;
                    break;
                case 0x4d00:
                case 0x7a00:
                    first = 0;
                    if (edit_cursor < maxlen) edit_cursor++;
                    break;
                case 0x5300:
                case 0x7f00:
                    first = 0;
                    pos = edit_cursor;
                    if (pos < maxlen) {
                        pos++;
                        while (pos < maxlen) {
                            buf[pos - 1] = buf[pos];
                            pos++;
                        }
                        buf[pos - 1] = ' ';
                    }
                    break;
                case 0x4b00:
                case 0x7900:
                    first = 0;
                    if (edit_cursor != 0) edit_cursor--;
                    break;
                case 0x4700:
                case 0x7600:
                    first = 0;
                    edit_cursor = 0;
                    break;
                case 0x4f00:
                case 0x7b00:
                    first = 0;
                    pos = last;
                    while (pos != 0 && buf[pos] == ' ') pos--;
                    if (buf[pos] != ' ') pos++;
                    edit_cursor = pos;
                    break;
                case 0x5200:
                case 0x7e00:
                    first = 0;
                    insert = (insert == 0);
                    break;
                case 0x08:
                    first = 0;
                    if (edit_cursor != 0) {
                        pos = edit_cursor;
                        while (pos < maxlen) {
                            buf[pos - 1] = buf[pos];
                            pos++;
                        }
                        buf[pos - 1] = ' ';
                        edit_cursor--;
                    }
                    break;
                default:
                    if ((ev.key >> 8) == 0 && ((int (*)(int))edit_char_hook)(ev.key & 0xff)) {
                        buf = edit_buffer;
                        /* the original keeps `first` in ecx, which the hook
                         * call leaves stale: a leading blank clears it
                         * (observed 0x17a94: test cx,cx after a blank key) */
                        if (first && ev.key == ' ')
                            first = 0;
                        if (first && ev.key != ' ') {
                            first = 0;
                            pos = 0;
                            while (pos < maxlen) {
                                buf[pos] = ' ';
                                pos++;
                            }
                            edit_cursor = 0;
                        }
                        if (edit_cursor < maxlen) {
                            if (insert && last > edit_cursor) {
                                pos = last;
                                do {
                                    buf[pos] = buf[pos - 1];
                                    pos--;
                                } while (pos > edit_cursor);
                            }
                            buf[edit_cursor] = (char)ev.key;
                            edit_cursor++;
                        }
                    }
                    break;
                }
                EditFieldDraw(r, 1);
                LayerInvalidate((unsigned char)d->layer);
            }
        }
        ScreenUpdate();
    } while (running);

    CursorLayerShow();
    DirtyRectUnion((const short *)&r);
    if (ev.key == 0x0d) {
        EditFieldDraw(r, 0);
    } else {
        draw_color = 0;
        FillRect(r.x, r.y, r.w, r.h);
    }
    LayerInvalidate((unsigned char)d->layer);
    if (ev.key == 0x0d) {
        strcpy(dest, edit_buffer);
        maxlen--;
        while (maxlen != 0 && dest[maxlen] == ' ')
            maxlen--;
        if (maxlen != 0 || dest[0] != ' ')
            maxlen++;
        dest[maxlen] = 0;
    }
    GdsFree(edit_buffer);
    return ev.key == 0x0d;
}
