/* codegen-flags: -s -od -4r -zp2
 * codegen-compiler: 10.0a
 *
 * SndInstallMidi (0x26b3c), game sound layer above Miles AIL - reference C
 * (T4).  Installs the configured MIDI driver and allocates the single
 * sequence handle.  The IO block is the 24-byte AIL layout (four 16-bit
 * values, then four longs; ail_mdi_default_io 0x36b40 copies 24 bytes and
 * fills the words from the driver description) - the game only sets the four
 * words, so the rest of the block is whatever the stack held.
 *
 * Not T3: the frame-slot order of the parameters and the return-value slot
 * differs (audio.toml t3_blocker); the body is instruction for instruction.
 */
#include "audio.h"

struct SndIo {
    unsigned short io, irq, dma, drq;
    unsigned long reserved[4];
};

int SndInstallMidi(const char *path, unsigned short io, unsigned short irq,
                   unsigned short dma, unsigned short drq)
{
    struct SndIo iob;
    volatile short i;

    iob.io = io;
    iob.irq = irq;
    iob.dma = dma;
    iob.drq = drq;
    snd_hmdi = AIL_install_MDI_driver_file(path, io != 0 ? &iob : 0);
    if (snd_hmdi == 0)
        return 1;
    for (i = 0; i < 1; i++)
        if ((snd_sequences[i].hseq = AIL_allocate_sequence_handle(snd_hmdi)) == 0)
            return 1;
    snd_mdi_active = 1;
    return 0;
}
