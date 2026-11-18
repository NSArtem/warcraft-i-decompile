/* codegen-flags: -s -ot -ol -4r -zp2
 * REFERENCE C for the stream helpers and the save-file loader of mod_24860
 * (0x24900, 0x249f8; 0x249c8 SaveSkipStream and 0x249e0 SaveFreeImage are
 * T3 under Watcom 10.0a and built from save_skip_stream.c /
 * save_free_image.c).  Not built: each one is a near miss
 * of the OW2 backend (register choice for the 16-bit constant stores, the
 * loop/jump layout of SaveWriteBytes), verified as T4 against the original
 * with wc1.cemu, see tests/test_mod_24860.py and
 * docs/subsystems/save_format.md section 6.
 */
#include "war.h"
#include "mod_24860.h"

/* @0x249c8 SaveSkipStream: built from C (T3 under Watcom 10.0a) in src/mod_24860/save_skip_stream.c. */

/* @0x249e0 SaveFreeImage: built from C (T3 under Watcom 10.0a) in src/mod_24860/save_free_image.c. */

/* @0x24900  read the save image from the current position of `fp` to the end
 * of the file into a GdsAlloc'd buffer, then validate the header.
 *
 * Returns the validated stream position (SaveStreamValidate's result: the
 * start of the game state inside the image) or 0 on failure; a failed load
 * frees the image again.  The image is the file from the current position to
 * EOF, so its size is (file size - current position); the 0x11170 limit is the
 * largest image the loader accepts (the written image is 0x109ee bytes).
 *
 * Near miss: the two constant stores use eax/ecx where the original uses
 * edx/ecx (codegen.md V2).
 */
unsigned char *SaveLoadImage(StdFile *fp)
{
    long start;
    unsigned long size;
    void *buf;
    unsigned char *pos;

    save_reloc_state.w.mode = 0;
    start = FileTell(fp);
    FileSeek(fp, 0, 2);                 /* SEEK_END */
    save_stream_left = FileTell(fp);
    FileSeek(fp, start, 0);             /* SEEK_SET */
    size = save_stream_left - start;
    save_stream_left = size;
    if (size <= 0x11170) {
        buf = GdsAlloc(size);
        save_image = buf;
        if (FileRead(buf, size, 1, fp) == 1) {
            pos = SaveStreamValidate(buf);
            if (pos)
                return pos;
        } else {
            SaveStreamValidate(0);
        }
        GdsFree(save_image);
        save_image = 0;
    }
    return 0;
}

/* @0x249f8  write `count` bytes to the stdio stream fp.
 *
 * This is the original's own buffered writer: instead of calling fputc per
 * byte it stores the byte in the FILE buffer directly and only calls fputc
 * when the stream is line buffered (mode bit 4), the buffer has one byte
 * left, or the byte is a newline (fputc then expands it to CR LF).  Returns
 * 0 when all bytes were written, 1 when fputc reported an error (-1); the
 * caller (SaveWriteImage) treats 1 as "abort the save".
 *
 * Near miss (codegen): OW2 keeps the source pointer in edi and needs an ebp
 * frame for the buffer pointer, reloads fp->ptr, and lays the error exit out
 * inline; see docs/subsystems/save_format.md section 6.
 */
short SaveWriteBytes(const unsigned char *data, short count, StdFile *fp)
{
    int c;

    while (count != 0) {
        c = *data++;
        if ((fp->mode & 4) || (int)(fp->bufsiz - fp->cnt) <= 1) {
            c = fputc(c, fp);
        } else {
            *fp->ptr = c;
            if (c == '\n') {
                c = fputc(c, fp);
            } else {
                fp->mode |= 0x10;
                fp->cnt++;
                fp->ptr++;
                c = fp->ptr[-1];
            }
        }
        count--;
        if (c == -1)
            return 1;
    }
    return 0;
}
