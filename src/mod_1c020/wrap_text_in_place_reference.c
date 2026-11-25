/* codegen-compiler: 10.0a */
#include "mod_1c020.h"

extern short TextWidth(const struct Font *font, const char *s);

void WrapTextInPlace(int max_width)
{
    int count;
    int index;
    char *line;
    char *end;
    char *previous;
    unsigned char ch;
    unsigned char saved;

    count = 0;
    line = wrap_text_buffer;
    if (*line != '\0') {
        index = 0;
        do {
            while ((ch = (unsigned char)*line) != 0 && ch == ' ')
                ++line;
            end = line;
            wrapped_text_lines[index++] = line;
            ++count;
            for (;;) {
                previous = end;
                ++end;
                while (*end != '\0' && (unsigned char)*end != ' ')
                    ++end;
                saved = (unsigned char)*end;
                *end = '\0';
                if (TextWidth(cur_font, line) > max_width) {
                    *end = (char)saved;
                    *previous = '\0';
                    line = previous + 1;
                    break;
                }
                ch = saved;
                if (ch == 0) {
                    line = end;
                    break;
                }
                *end = (char)ch;
            }
        } while (*line != '\0');
    }
    if (count < 100)
        wrapped_text_lines[count] = 0;
}
