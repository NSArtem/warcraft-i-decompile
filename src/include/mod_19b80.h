#ifndef MOD_19B80_H
#define MOD_19B80_H

/* mod_19b80: in-game screen input glue (0x19b80..0x1a3b6) */

/* saved map view slot: {short x; short y} (4 bytes).  3 slots at 0x50e3e.
 * 0x50e3c (dword view, x is the high word) and 0x50e40 (y field of slot 0)
 * are interior offsets of this array and have separate data entries. */
typedef struct MapBookmark {
    short x;
    short y;
} MapBookmark;

extern MapBookmark map_bookmarks[3];            /* 0x50e3e */

void MapViewRecall(unsigned short slot);        /* 0x19d68 */
void MapViewSave(unsigned short slot);          /* 0x19d8c */
void MapViewBookmarksInit(void);                /* 0x19db4 */
void StatusBarBitmapRelease(void);              /* 0x19ed0 */
void StatusHelpTextSet(const char *text);       /* 0x19f80 */
void StatusHelpTimersTick(void);                /* 0x19f94 */
void GameHotkeyDispatch(void *evt);             /* 0x19fd8 */
void UiReleaseDispatch(void);                   /* 0x1a130 */
void UiPressDispatch(void);                     /* 0x1a14c */
void GameScreenMouseUpdate(void);               /* 0x1a168 */
void GameScreenInputReset(unsigned char cursor);/* 0x1a388 */

#endif
