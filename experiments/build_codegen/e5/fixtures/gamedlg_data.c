/* codegen-compiler: 10.0a */
/* E5: consolidate the real DefeatDialog with its canonical global storage.
 * The original ASM remains the sole physical provider after B3 verification. */
#include "gamedlg.h"
unsigned short net_play_flag = 0;
short game_mode;
#include "../../../../src/gamedlg/defeat_dialog.c"
