/* codegen-compiler: 10.0a */
#include "mod_19470.h"
#include <time.h>

extern void PlayerStatsReset(int keep_totals);
extern int fn_19478(int);
extern void MapViewBookmarksInit(void);
extern void GameScreenInputInit(void);
extern void ModalDepthReset(void);
extern void MapCenterOnTile(short x, short y);
extern void MapFindStartTile(int *x, int *y);
extern unsigned char *MapInitBuffers(unsigned char *save_pos);
extern void SndEventsInit(int in_game);
extern void fn_1cb90(void);
extern void fn_1e7b0(int);
extern void ResetPacketId(void);
extern void PlaceBoxInit(void);
extern unsigned char *SaveReadStream(void *dst, unsigned count, unsigned char *pos);
extern void SaveFreeImage(int);
extern void ScoreInit(void);
extern void SelectionRebuildFromUnitFlags(void);
extern void AnimTableLoad(void);
extern void SndApplyOptions(const int *opts);
extern void StatusPanelInit(void);
extern void AiReset(int resume);
extern void TargetModeClear(void);
extern void fn_2b4b8(void);
extern void TerrainTablesInit(void);
extern int UnitsInitGame(int campaign);
extern void MissionStartCheck(void);
extern unsigned long ResourceBegin(unsigned short id, unsigned long *packed_len);
extern void *ResourceRead(void *dest, unsigned count);

/* 0x195ac */
void GameInitSession(unsigned char *save_pos)
{
    int y;
    int x;
    unsigned short enemy_race;
    unsigned short race;
    int unit_result;

    game_init_in_progress = 1;
    if (save_pos != 0) {
        save_pos = SaveReadStream(prefs_block, 0x14, save_pos);
        save_pos = SaveReadStream(&scenario_unit_mask, 0xbb8, save_pos);
        save_pos = SaveReadStream(&game_rng_seed, 0x200, save_pos);
        SndApplyOptions((const int *)prefs_block);
        GameSetRandomSeed(game_rng_seed);
    } else {
        minimap_redraw_state = 0;
        if (net_play_flag == 0)
            GameSetRandomSeed(demo_mode != 0 ? 1L : (long)time(0));
        if (custom_game != 0) {
            race = scenario_race;
            enemy_race = scenario_race_enemy;
            GameResolveCustomScenario();
        }
        if (ResourceBegin(scenario_number, 0) > 0xbb8UL)
            FatalError(scenario_size_error);
        ResourceRead(&scenario_unit_mask, 0);
        if (custom_game != 0) {
            scenario_race = race;
            scenario_race_enemy = enemy_race;
            scenario_music_track = (unsigned short)(fn_19478(3) % 6 + 2);
        }
    }

    cheat_flags.w &= 0xa4000000UL;
    player_visibility_mask[0] = 0x100;
    player_visibility_mask[1] = net_play_flag != 0 ? 0x200 : 0;
    TerrainTablesInit();
    AiReset((int)save_pos);
    {
        unsigned char *unit_pos;

        unit_pos = MapInitBuffers(save_pos);
        AnimTableLoad();
        fn_1cb90();
        PlayerStatsReset((int)unit_pos);
        fn_1e7b0(unit_result = UnitsInitGame((int)unit_pos));
    }
    if (unit_result != 0)
        SaveFreeImage(0);
    if (custom_game != 0 && unit_result == 0) {
        MapFindStartTile(&x, &y);
        MapCenterOnTile((short)x, (short)y);
    }
    SndEventsInit(1);
    MissionStartCheck();
    ModalDepthReset();
    fn_2b4b8();
    PlaceBoxInit();
    TargetModeClear();
    MapViewBookmarksInit();
    ScoreInit();
    GameScreenInputInit();
    StatusPanelInit();
    SelectionRebuildFromUnitFlags();
    ResetPacketId();
    game_init_in_progress = 0;
}
