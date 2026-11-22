/* codegen-compiler: 10.0a */
#include "war.h"

extern const char modem_settings_filename[];
extern unsigned long modem_baud;
extern short SaveFileInExeDir(const char *name, const void *buf, unsigned size);

/* 0x1d53a..0x1d549 saves the 0xca-byte settings block beginning at modem_baud. */
void SaveModemSettings(void)
{
    SaveFileInExeDir(modem_settings_filename, &modem_baud, 0xca);
}
