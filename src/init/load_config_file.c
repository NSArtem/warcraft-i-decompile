/* codegen-compiler: 10.0a */
#include "war.h"
#include <stdio.h>

extern const char config_load_error_format[];
extern unsigned char config_file_data[0x20];
extern void delay(unsigned ms);

/* 0x1d4e0 loads exactly 0x20 bytes; 0x1d4ea gates the error on alternate. */
short LoadConfigFile(const char *name, short alternate)
{
    if (LoadFile(name, config_file_data, sizeof(config_file_data), sizeof(config_file_data), (short)(alternate == 0)) == 0) {
        if (alternate != 0) {
            printf(config_load_error_format, name);
            delay(2000);
        }
        return 0;
    }
    return 1;
}
