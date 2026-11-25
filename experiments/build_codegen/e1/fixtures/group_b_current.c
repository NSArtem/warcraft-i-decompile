#include "playflic.h"

unsigned short *IntroOpPlaySound(unsigned short *p)
{
    SndPlay(*p++);
    return p;
}

unsigned short *IntroOpSyncSound(unsigned short *p)
{
    while (SndActiveCount()) {
        IntroTick();
        if (intro_abort)
            break;
        if (frame == flic_frames + 1) {
            if (!IntroShowFirstFrame(p))
                return 0;
        } else if (!IntroNextFrame()) {
            return 0;
        }
    }
    return p;
}

unsigned short *IntroOpWaitSound(unsigned short *p)
{
    while (SndActiveCount()) {
        if (intro_abort)
            break;
        IntroTick();
    }
    return p;
}
