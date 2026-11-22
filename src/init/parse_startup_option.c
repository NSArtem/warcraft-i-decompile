/* codegen-compiler: 10.0a */
#include "war.h"
#include <stdlib.h>
#include <string.h>

extern short LoadConfigFile(const char *name, short alternate);
extern short alternate_config_loaded;
extern const char option_file_prefix[];
extern const char option_extra_packets_prefix[];
extern const char option_packet_speed_prefix[];
extern const char option_direct_link[];
extern unsigned short net_direct_link;
extern unsigned short net_link_speed;
extern unsigned short net_link_speed_set;
extern unsigned short net_port_base[5];
extern unsigned short net_sync_counter;

/* 0x1d645 records config status; 0x1d6c3 accepts explicit zero;
 * 0x1d710..0x1d722 clamps and converts packet speed to a zero-based value.
 */
short ParseStartupOption(const char *arg)
{
    char *end;
    const char *value_arg;
    unsigned long value;
    int cmp;
    short handled;

    if (strncmp(arg, option_file_prefix, 5) == 0) {
        alternate_config_loaded = LoadConfigFile(arg + 5, 1);
        handled = 1;
    } else {
        if (strcmp(arg, option_direct_link) == 0) {
            net_direct_link = 1;
            return 1;
        }
        cmp = strncmp(arg, option_extra_packets_prefix, 9);
        value_arg = arg + 9;
        if (cmp == 0) {
            value = strtoul(value_arg, &end, 10);
            if (value != 0) {
                net_port_base[0] = (unsigned short)value;
                net_sync_counter = (unsigned short)value;
                return 1;
            }
            if (arg[9] == '0') {
                net_port_base[0] = 0;
                net_sync_counter = 0;
                return 1;
            }
        } else if (strncmp(arg, option_packet_speed_prefix, 9) == 0) {
            value = strtoul(value_arg, &end, 10);
            if (value != 0) {
                if (value > 5UL)
                    value = 5;
                --value;
                net_link_speed_set = (unsigned short)value;
                net_link_speed = (unsigned short)value;
                return 1;
            }
        }
        handled = 0;
    }
    return handled;
}
