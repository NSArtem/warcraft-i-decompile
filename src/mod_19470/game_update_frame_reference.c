/* codegen-compiler: 10.0a */
#include "mod_19470.h"

extern void UiEventPump(void);
extern void SndTick(void);
extern void PacketTick(void);
extern void PlaceBoxUpdate(void);
extern void ScoreUpdate(void);
extern void UnitPanelUpdate(void);
extern void AiTick(void);
extern void fn_2b824(void);
extern void fn_2d650(void);
extern void fn_2ec0c(void);
extern void LayerInvalidate(unsigned char id);
extern void ScreenUpdate(void);
extern void PaletteCyclesUpdate(void);

/* 0x197c7 tests simulation_due; 0x197cc tests packet_due inside that branch. */
void GameUpdateFrame(short simulation_due, short packet_due)
{
    fn_2d650();
    if (movie_state == 0)
        UiEventPump();
    if (simulation_due != 0) {
        if (packet_due != 0)
            PacketTick();
        AiTick();
        fn_2ec0c();
        ScoreUpdate();
    }
    fn_2b824();
    SndTick();
    UnitPanelUpdate();
    PlaceBoxUpdate();
    LayerInvalidate(0x16);
    ScreenUpdate();
    PaletteCyclesUpdate();
}
