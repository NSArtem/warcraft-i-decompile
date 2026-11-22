/* codegen-compiler: 10.0a */
#include "mod_19470.h"

/* 0x19470: stores EAX into the saved-state seed at 0x50d7c. */
void GameSetRandomSeed(long seed)
{
    game_rng_seed = seed;
}
