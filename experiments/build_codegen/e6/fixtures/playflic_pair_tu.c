/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* E6 consolidation; unchanged PLAYFLIC bodies. */
#include "playflic.h"
/* @0x22d40  Scrolling loader of the credit text: advances the credit table
 * when the line timer reaches 1, and loops while the new delay is 0. */
void IntroLoadCreditLines(void)
{
    unsigned short count = line_count;
    unsigned short idx = line_index;
    unsigned short timer = line_timer;

    if (--timer == 0) {
        do {
            const CreditLine *c;

            idx++;
            line_index = idx;
            c = &credit_lines[idx];
            timer = c->delay;
            line_timer = timer;
            if (!*c->text) {
                count = 0;
                credit_line[0] = 0;
                credit_line[1] = 0;
                credit_line[2] = 0;
                line_count = count;
                memset(frame_image + flic_height * 0x140, 0, 0xfa00 - flic_height * 0x140);
            } else {
                credit_line[count] = c->text;
                line_count = count;
                credit_line_x[count] = (0x140 - TextWidth(cur_font, c->text)) / 2;
                count++;
            }
        } while (timer == 0);
        if (timer == 0xffff)
            credits_on = 0;
    }
    line_count = count;
    line_index = idx;
    line_timer = timer;
}



/* @0x22e84  The per-frame (idle event) callback. */
void IntroFrame(void)
{
    frame_ready = 1;
    intro_tick_count++;
    if (credits_on)
        IntroLoadCreditLines();
}
