/* codegen-compiler: 10.0a */
#include "mod_19470.h"

/* 0x19470: stores EAX into the saved-state seed at 0x50d7c. */
void GameSetRandomSeed(long seed)
{
    dat_50d7c = seed;
}
