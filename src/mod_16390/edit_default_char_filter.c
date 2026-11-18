/* codegen-compiler: 10.0a */
/* 0x16390: the default edit-control character filter (edit_char_hook). */
int EditDefaultCharFilter(int ch)
{
    ch &= 0xff;
    if (ch >= 0x20 && ch < 0x7f)
        return 1;
    return 0;
}
