/* codegen-compiler: 10.0a */
#include "mod_1af20.h"
#include <string.h>

#pragma intrinsic(memcpy)

extern const char chat_prompt_prefix[6]; /* 0x1b7b3: source of the six-byte copy. */
extern short CmdProcessText(char *text, unsigned char *flags); /* 0x1b724: passes text and local flags address. */
extern void NetSendCheatFlags(unsigned long flags); /* 0x1b73c: flags in EAX. */
extern void NetSendChatText(const char *text, unsigned short len); /* 0x1b74d: text in EAX, length in EDX. */
extern void StatusBarDrawText(const char *text, unsigned char show_costs); /* 0x1b7d2: prompt in EAX, zero in EDX. */

int GameScreenHandleChatKey(void *evt)
{
    char prompt[128];
    unsigned long flags;
    unsigned char *event;
    unsigned short len;
    unsigned key;
    int ch;
    short handled;

    event = evt;
    len = ui_input_locked;
    if (len == 0) {
        if (event[8] != 0x1c) {
            ui_input_locked = len;
            return 0;
        }
        chat_input_text[0] = '_';
        len = 1;
        goto update_prompt;
    }

    key = event[8];
    if (key == 0x1c) {
        if (--len != 0) {
            chat_input_text[len] = '\0';
            flags = cheat_flags.w;
            ui_input_locked = len;
            handled = CmdProcessText(chat_input_text, (unsigned char *)&flags);
            len = ui_input_locked;
            if (handled != 0)
                NetSendCheatFlags(flags);
            else
                NetSendChatText(chat_input_text, len);
            len = 0;
        }
        goto update_prompt;
    }

    if (key == 0x0e) {
        if (len > 1) {
            --len;
            chat_input_text[len - 1] = '_';
        }
        goto update_prompt;
    }

    if (event[11] == 0) {
        ch = event[10];
        if (ch >= 0x20 && ch <= 0x7f && len < 0x1e) {
            chat_input_text[len - 1] = (char)event[10];
            chat_input_text[len] = '_';
            ++len;
        }
    }

update_prompt:
    chat_input_text[len] = '\0';
    memcpy(prompt, chat_prompt_prefix, sizeof(chat_prompt_prefix));
    ui_input_locked = len;
    strcat(prompt, chat_input_text);
    StatusBarDrawText(prompt, 0);
    len = ui_input_locked;
    ui_input_locked = len;
    return 1;
}
