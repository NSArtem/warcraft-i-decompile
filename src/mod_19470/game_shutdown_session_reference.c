/* codegen-compiler: 10.0a */
#include "mod_19470.h"

extern void StatusBarBitmapRelease(void);
extern void MapFreeBuffers(void);
extern void SndEventsInit(int in_game);
extern void fn_1ccdc(void);
extern void PlaceBoxShutdown(void);
extern void ScoreFreePanels(void);
extern void AnimTableFree(void);
extern void MusicClear(void);
extern void StatusPanelFree(void);
extern void fn_2b400(void);
extern void TerrainTablesFree(void);
extern void PaletteCyclesClear(void);

void GameShutdownSession(void)
{
    unsigned short i;

    PaletteCyclesClear();
    for (i = 0x0d; i <= 0x16; ++i)
        layers[i].state = 0;
    PlaceBoxShutdown();
    StatusBarBitmapRelease();
    fn_2b400();
    ScoreFreePanels();
    StatusPanelFree();
    fn_1ccdc();
    AnimTableFree();
    MapFreeBuffers();
    TerrainTablesFree();
    MusicClear();
    SndEventsInit(0);
}
