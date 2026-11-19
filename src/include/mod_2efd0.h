/* mod_2efd0.h - declarations for the object at 0x2efd0..0x3024e
 * (analysis/modules.toml name "mod_2efd0"), reconstructed in src/mod_2efd0/.
 *
 * The object is two related pieces of the game screen:
 *   0x2efd0..0x2f350  the map selection layer: click-select, the drag
 *                     rectangle ("marquee") and the order packet the command
 *                     card sends (SELECT.C-shaped code),
 *   0x2f350..0x3024e  the mission-end layer: the per-mission victory/defeat
 *                     conditions and the win/lose screen that plays
 *                     win1/win2/lose1/lose2.war with the animated score.
 *
 * Names, addresses and the evidence for every claim are in
 * analysis/symbols/mod_2efd0.toml; the prose is docs/subsystems/mod_2efd0.md.
 * Layouts reused from other areas: the 0x5c-byte unit record
 * (game_2c4e0.toml), the 12-byte Event (input.toml), Bitmap/Rect/Layer
 * (graphics.toml), CheatFlags/game_mode (cmd_123f0.toml).
 */
#ifndef MOD_2EFD0_H
#define MOD_2EFD0_H

#include "game_2c4e0.h"     /* Unit, Point, Flags */
#include "graphics.h"       /* Bitmap, Rect, Layer, layers, cur_bitmap, cur_font */
#include "input.h"          /* Event */
#include "war.h"            /* GdsAlloc/GdsFree/FatalError */
#include "cmd_123f0.h"      /* cheat_flags, game_mode, scenario_race */

/* ---------------------------------------------------------------- selection */

/* The drag rectangle at 0x5a7d0.  The press stores the anchor (screen
 * pixels, from the press Event), the mouse-move callback recomputes the
 * corner that follows the cursor, and the per-frame callback converts the
 * four edges to map pixels (screen + scroll*16 - origin) before it tests the
 * units.  `visible` is what SelectionBoxDraw checks. */
typedef struct SelectionBox {
    short anchor_x, anchor_y;       /* 0x5a7d0, 0x5a7d2 */
    short min_x, min_y;             /* 0x5a7d4, 0x5a7d6 */
    short max_x, max_y;             /* 0x5a7d8, 0x5a7da */
    short w, h;                     /* 0x5a7dc, 0x5a7de */
    short visible;                  /* 0x5a7e0 */
} SelectionBox;

extern SelectionBox selection_box;          /* 0x5a7d0 */
extern unsigned short selection_local;      /* 0x5a118 */
extern unsigned short sel_mod_select_all;   /* 0x5a928 (never written: 0) */
extern unsigned short sel_mod_add;          /* 0x5a940 (never written: 0) */
extern unsigned short type_is_creature[];   /* 0x51cc0 1 for types 0..0x1f */
extern short unit_pixel_size[][2];          /* 0x51b9c {w,h} pixels per type */

/* ----------------------------------------------------------- mission end */

extern Bitmap end_screen_bm;                /* 0x5a7f0 184x112 panel */
extern long end_screen_value[13];           /* 0x5a7f8 counted-up numbers */
extern long end_screen_target[13];          /* 0x5a82c their targets */
extern void (*end_screen_action)(void);     /* 0x5a860 mission-end action */
extern unsigned short end_screen_done;      /* 0x5a864 */
extern unsigned short end_screen_ticks;     /* 0x5a866 */
extern unsigned short end_check_timer;      /* 0x5a868 */

extern Bitmap end_text_bm;                  /* 0x552f8 290x128 numbers bitmap */
extern Rect end_panel_rect;                 /* 0x55300 the 184x112 rect */
extern short end_value_step[13];            /* 0x5530c count-up step */
extern short end_value_x[13];               /* 0x55326 */
extern short end_value_y[13];               /* 0x55340 */
extern unsigned short end_sound_ids[];      /* 0x5535a SndLoadTable list */
extern unsigned short end_music_win[];      /* 0x55370 6 tracks */
extern unsigned short end_music_win2[];     /* 0x5537c */
extern unsigned short end_music_lose[];     /* 0x55388 */
extern unsigned short end_music_lose2[];    /* 0x55394 */
extern char movie_win1[];                   /* 0x552d0 "win1.war" */
extern char movie_win2[];                   /* 0x552d9 "win2.war" */
extern char movie_lose1[];                  /* 0x552e2 "lose1.war" */
extern char movie_lose2[];                  /* 0x552ec "lose2.war" */
extern Rect full_screen_rect;               /* 0x514d8 320x200 */
extern short movie_state;                   /* 0x58da4 */
extern unsigned short demo_mode;            /* 0x5152c */
extern unsigned short scenario_objective_count; /* 0x50096 */
extern unsigned short dead_men[];           /* 0x50d8e */
extern unsigned short dead_buildings[];     /* 0x50da2 */
extern unsigned long harvested_gold[];      /* 0x50dc0 */
extern unsigned long harvested_lumber[];    /* 0x50dd4 */
extern unsigned short player_building_count[]; /* 0x58e1e */
extern unsigned short player_town_hall_count[]; /* 0x58df6 */

/* game state published by other areas */
extern unsigned short player_active_men[];      /* 0x58e28 */
extern unsigned short player_worker_count[];    /* 0x58dd8 */
extern unsigned short player_unit_cap[];        /* 0x58dec */
extern void *player_town_hall[];                /* 0x58db0 */
extern unsigned short training_count[];         /* 0x50d84 */
extern unsigned short scenario_objectives;      /* 0x50092 */
extern unsigned short scenario_race_enemy;      /* 0x5008a */
extern unsigned short player_score[];           /* 0x50e34 */
extern unsigned short player_unit_count[];      /* 0x50d98 */
extern unsigned short flic_frames;              /* 0x59446 */
extern unsigned char palette[];                 /* 0x58f20 */
extern Font alt_font;                           /* 0x59220 */
extern short ui_mouse_x, ui_mouse_y;            /* 0x59428/0x5942a */
extern short game_state;                        /* 0x59614 (high word = game_mode) */
extern unsigned short net_event_pending;        /* 0x5a11a player slot being served */
extern unsigned long dat_50074[];               /* 0x50074 per-player gold */
extern unsigned long dat_50060[];               /* 0x50060 per-player lumber */
extern short map_view_rect[];                   /* 0x51eec x0,y0,x1,y1 of the map view */
extern unsigned char palette_cycles[];          /* 0x628a0 graphics palette cycles */

/* ---------------------------------------------------------------- callees */

Unit *SelectionFirst(void);                     /* 0x25cc4 */
Unit *SelectionNext(void);                      /* 0x25c50 */
void SelectionSet(unsigned short count, Unit **list);  /* 0x262a0 */
void IssueOrderAt(short x, short y, Unit *target);     /* 0x2f0a8 (this area) */
void fn_1b9b8(Unit *u);                         /* 0x1b9b8 map cursor */
void NetSendOrder(short x, short y, Unit *u);   /* 0x21a58 */
void NetSendControlPacket(unsigned short id);   /* 0x21c20 */
int PlaceBoxActive(void);                       /* 0x22538 */
int fn_2b308(void);                             /* 0x2b308 map input blocked */
void GameScreenInputInit(void);                 /* 0x1a328 */
void fn_13dd0(unsigned char id);                /* 0x13dd0 set cursor shape */
void RectOutline(short x, short y, unsigned short w, unsigned short h);
void DrawText(short x, short y, const char *s); /* 0x31dcc */
int TextWidth(const Font *font, const char *s);  /* 0x32060 */
void LayerInvalidate(unsigned char id);         /* 0x31f70 */
void LayerAdd(Bitmap *bm, const Rect *r, unsigned short id,
              unsigned short res, void (*blit)());      /* 0x21d0c */
void ScreenUpdate(void);                        /* 0x321e8 */
void BitmapClear(unsigned char color);          /* 0x31fc0 */
void BitmapBlit(short x, short y, const Bitmap *src, const Rect *srcrect);
void BitmapBlitTransparent(short x, short y, const Bitmap *src,
                           const Rect *srcrect);
void *memset(void *dst, int c, unsigned n);     /* 0x30c50 */
void *memcpy(void *dst, const void *src, unsigned n);   /* 0x31789 */
int sprintf(char *buf, const char *fmt, ...);   /* 0x31be2 */
unsigned strlen(const char *s);                 /* 0x31d1a */
void PaletteSet(unsigned char first, unsigned short count,
                const unsigned char *rgb);      /* 0x33150 */
void PaletteFadeIn(unsigned short steps);       /* 0x32e80 */
void PaletteFadeOut(unsigned short steps);      /* 0x32fb0 */
void CursorLayerShow(void);                     /* 0x32940 */
void ResourceBegin(unsigned short id, void *len);      /* 0x31870 */
void *ResourceRead(void *dest, unsigned count);        /* 0x32740 */
void ResourceReadHeaderBody(void *hdr4, void *dest);   /* 0x323e0 */
void ResourceFreeBody(void *hdr);               /* 0x21cf0 */
int FlicOpen(const char *name, void *chunk, void *image,
             unsigned first, unsigned last);    /* 0x1933c */
int FlicRewind(void);                           /* 0x193fc */
int FlicNextFrame(void);                        /* 0x19450 */
int FlicRestart(void);                          /* 0x19420 */
void FlicClose(void);                           /* 0x193dc */
void SndPlay(unsigned id);                      /* 0x26958 */
void SndStop(unsigned id);                      /* 0x269b8 */
void SndReleaseAll(void);                       /* 0x271f4 */
void SndLoadTable(const unsigned short *ids);   /* 0x267fc */
void MusicStart(unsigned track);                /* 0x26784 */
void MusicClear(void);                          /* 0x267e0 */
void UiInputInit(void);                         /* 0x18488 */
void UiEventPump(void);                         /* 0x184cc */
void EvtPump(void);                             /* 0x31568 */
void PacketTick(void);                          /* 0x21844 */
char *RankName(void);                           /* 0x255b8 */
void ScoreTickIncome(void);                     /* 0x24e90 */
void TextSetColorBase(unsigned char c);         /* 0x32030 */
int fn_19478(int id);                           /* 0x19478 LCG */
void VictoryDialog(void);                       /* 0x1aa7c */
void DefeatDialog(void);                        /* 0x1ab28 */

extern void (*status_frame_callback)(void);     /* 0x59414 */
extern void (*status_click_callback)(void);     /* 0x5941c */
extern void (*status_mouse_callback)(void *);   /* 0x5940c */
extern void (*dialog_pre_event)(void);          /* 0x59424 */
extern void (*dialog_idle)(void);               /* 0x59420 */
extern void (*event_handlers[])(Event *ev);     /* 0x59400 */
extern unsigned short map_scroll_x, map_scroll_y;  /* 0x500d0/0x500d2 */
extern Unit *unit_array;                        /* 0x59640 */
extern unsigned short *map_flags;               /* 0x5857c */

/* this object's functions (see the TOML for each address) */
void SelectionClickUnit(Unit *u);               /* 0x2efd0 */
void SelectionBoxTrack(Event *ev);              /* 0x2f0c8 */
void SelectionBoxFrame(Event *ev);              /* 0x2f15c */
void SelectionBoxBegin(Event *ev);              /* 0x2f350 */
void SelectionBoxDraw(void);                    /* 0x2f3dc */
int  ObjectiveUnitCount(void);                  /* 0x2f428 */
void EndCheckElimination(void);                 /* 0x2f4c0 */
void EndCheckObjectives(void);                  /* 0x2f540 */
void EndCheckSurvive(void);                     /* 0x2f694 */
void MissionDefeat(void);                       /* 0x2f73c */
void MissionToMenu(void);                       /* 0x2f748 */
void EndCheckDemo(void);                        /* 0x2f754 */
void MissionStartCheck(void);                   /* 0x2f788 */
void MissionEndTick(short force);                /* 0x2f7fc */
char *FormatNumber(char *buf, long value, char *out);   /* 0x2f830 */
void DrawNumberRight(short x, short y, long value);     /* 0x2f878 */
void DrawNumberCentre(short x, short y, long value);    /* 0x2f8bc */
void EndScreenInput(Event *ev);                 /* 0x2f90c */
void EndScreenTick(void);                       /* 0x2f930 */
void EndScreenDraw(void);                       /* 0x2f938 */
int  EndScreenAnimate(void);                    /* 0x2f9b4 */
void EndScreenStop(void);                       /* 0x2fa24 */
int  EndScreenSoundId(void);                    /* 0x2fa30 */
void EndScreenMovie(void *chunk, Bitmap *screen);  /* 0x2fac4 */
void EndScreen(void);                           /* 0x2fcfc */

#endif
