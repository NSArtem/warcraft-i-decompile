/* codegen-compiler: 10.0a */
#include "mod_1eba0_f2.h"

struct Unit;
extern void ScoreSetPage(int page); /* 0x1f005 */
extern void GameScreenInputReset(unsigned char cursor); /* 0x1f028 */
extern void IssueOrderAt(int x, int y, struct Unit *target); /* 0x1f02d–0x1f03d */

void MinimapIssueOrder(void *mouse_event)
{
    const short *event_words;
    struct {
        short x;
        short pad_x;
        short y;
        short pad_y;
    } coords;
    int x, y;

    event_words = mouse_event;
    ScoreSetPage(0);
    *(volatile short *)&coords.x = event_words[2];
    *(volatile short *)&coords.y = event_words[3];
    MinimapScreenToTile(&coords.x, &coords.y);
    GameScreenInputReset(0);
    /* Watcom/x86 dword views: each coordinate is in the high word. */
    y = *(const volatile long *)((const char *)&coords.y - 2) >> 16;
    x = *(const volatile long *)((const char *)&coords.x - 2) >> 16;
    IssueOrderAt(x, y, 0);
}
