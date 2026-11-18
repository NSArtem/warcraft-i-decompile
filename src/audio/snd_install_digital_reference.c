/* codegen-flags: -s -od -4r -zp2
 * codegen-compiler: 10.0a
 *
 * SndInstallDigital (0x26f1c), game sound layer above Miles AIL - reference C
 * (T4).  Installs the configured digital driver, clears the four channel
 * slots and enables the digital paths.  Same 24-byte IO block and same
 * frame-slot blocker as SndInstallMidi 0x26b3c (audio.toml).
 */
#include "audio.h"

struct SndIo {
    unsigned short io, irq, dma, drq;
    unsigned long reserved[4];
};

int SndInstallDigital(const char *path, unsigned short io, unsigned short irq,
                      unsigned short dma, unsigned short drq)
{
    struct SndIo iob;
    volatile short i;

    iob.io = io;
    iob.irq = irq;
    iob.dma = dma;
    iob.drq = drq;
    snd_hdig = AIL_install_DIG_driver_file(path, io != 0 ? &iob : 0);
    if (snd_hdig == 0)
        return 1;
    for (i = 0; i < 4; i++)
        snd_channels[i].hsample = 0;
    snd_dig_active = 1;
    return 0;
}
