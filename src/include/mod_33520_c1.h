#ifndef MOD_33520_C1_H
#define MOD_33520_C1_H

typedef struct { short x, y, x2, y2, w, h; } Rect;
typedef struct { short type; short pad[4]; short key; } Event;
typedef struct Bitmap { char data[24]; } Bitmap;
typedef struct { short flags; char pad[16]; } Layer;
void EvtPump(void);
int EvtGet(Event *out);
void delay(unsigned ms);
void LayerInvalidate(unsigned char id);
void BitmapBlit(short x, short y, const Bitmap *src, const Rect *srcrect);
void CursorLayerShow(void);
void EvtProcess(Event *ev);
void BitmapBlitAll(short x, short y, const Bitmap *src);
void exit(int status);
int cputs(const char *s);
void DpmiLockRegion(void *addr, unsigned size);
void _hardresume(int result);
void _harderr(int (__far *handler)());
void CriticalErrorPrompt(void);
int __far CritErrHandler(unsigned deverr, unsigned errcode, unsigned __far *devhdr);
void CritErrInstall(void);

#endif
