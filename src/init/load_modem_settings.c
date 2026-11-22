/* codegen-compiler: 10.0a */
#include "war.h"

extern const char modem_settings_filename[];
extern unsigned long modem_baud;

/* 0x1d51d..0x1d52e loads the 0xca-byte settings block beginning at modem_baud. */
void LoadModemSettings(void)
{
    LoadFile(modem_settings_filename, &modem_baud, 0xca, 0xca, 1);
}
