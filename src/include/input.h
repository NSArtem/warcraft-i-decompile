/* input.h - the event queue, keyboard ISR and mouse callback of EVT.C/EVTGET.C
 * (war.exe 0x30ea0..0x31784, module "gfx_evt_vid").
 *
 * The event record is 12 bytes (see analysis/symbols/input.toml):
 *   +0 word type   (1 move, 2 L-press, 4 L-release, 8 R-press, 0x10 R-release,
 *                   0x80 key-down, 0x100 key-up, 0x400 idle/tick)
 *   +2 word sub    +4 word x   +6 word y
 *   +8 byte scancode   +9 byte modifier bits   +0xa word translated key
 *
 * The whole ISR-visible state block 0x5a880..0x5aa5e (0x1df bytes) is zeroed
 * by EvtInit and DPMI-locked, together with the ISR code region
 * 0x30ea0..0x312d8.
 */
#ifndef WC1_INPUT_H
#define WC1_INPUT_H

/* --------------------------------------------------------------- records */

typedef struct Event {
    unsigned short type;                /* +0x0 */
    unsigned short sub;                 /* +0x2 */
    unsigned short x;                   /* +0x4 */
    unsigned short y;                   /* +0x6 */
    unsigned char scan;                 /* +0x8 */
    unsigned char mods;                 /* +0x9 */
    unsigned short key;                 /* +0xa */
} Event;                                /* 12 bytes */

/* ------------------------------------------------------- event queue data */
extern Event *evt_queue;                /* 0x5a8be, GdsAlloc(evt_queue_size*12) */
extern unsigned short evt_head;         /* 0x5a8c4, write index */
extern unsigned short evt_tail;         /* 0x5a8c2, read index */
extern unsigned short evt_queue_size;   /* 0x5a8c6, ring length in events */
extern volatile unsigned short evt_count;/* 0x5a8c8, queued events */
extern unsigned short evt_mask;/* 0x5a8b4, accepted type bits */
extern Event *evt_move_pending;         /* 0x5a8ba, pending move event or 0 */

/* the four event templates (inside the ISR state block) */
extern Event evt_key;                   /* 0x5a880, KeyboardISR's template */
extern Event evt_move;                  /* 0x5a88c, type 1/sub 3 */
extern Event evt_button;                /* 0x5a898, MouseButtonEvent's */
extern Event evt_idle;                  /* 0x5a8a4, type 0x400/sub 8 */

/* mouse position: what the cursor layer draws at, and the driver's own
 * (clamped) position that MouseCallback latches */
extern short mouse_x;                   /* 0x5a8ca */
extern short mouse_y;                   /* 0x5a8cc */
extern short mouse_raw_x;               /* 0x5a8b0 */
extern short mouse_raw_y;               /* 0x5a8b2 */

/* ------------------------------------------------------- keyboard state */
extern unsigned short key_down_table[128];      /* 0x5a8d4, typematic filter */
extern unsigned char scancode_fixup_table[0x80];/* 0x5a9df, E0-prefixed codes */
extern unsigned char key_modifiers;             /* 0x5ad50 */

/* the ISR's prefix/vector scratch (inside the state block) */
extern unsigned short kbd_e0_prefix;/* 0x5a9d5, last byte was 0xE0 */
extern volatile unsigned short kbd_e1_count;/* 0x5a9d7, bytes of the pause seq */
extern unsigned short kbd_pause_flag;   /* 0x5a9be, read only (always 0) */
extern void (__far *old_int9)(void);    /* 0x5a9d9, saved IRQ1 vector */

/* idle-event clock gate: EvtGet emits one 0x400 event per 5 clock ticks */
extern unsigned long evt_last_idle;     /* 0x55434 */

/* ------------------------------------------------------------ functions */
int EvtPost(Event *ev);                          /* 0x30eb8 */
int EvtGet(Event *out);                          /* 0x31598 */
void EvtPump(void);                              /* 0x31568 */
void EvtInit(unsigned short queue_size);         /* 0x316a0 */
void EvtShutdown(void);                          /* 0x31764 */

void MouseButtonEvent(unsigned short type, unsigned short sub);  /* 0x30fa8 */
short EvtInitMouse(void);                        /* 0x314a4 */
void EvtShutdownMouse(void);                     /* 0x31538 */
void EvtHookKeyboard(void);                      /* 0x313d0 */
void EvtUnhookKeyboard(void);                    /* 0x31450 */

void DpmiLockRegion(void *addr, unsigned size);  /* 0x312f0 */
void DpmiUnlockRegion(void *addr, unsigned size);/* 0x31360 */

/* the two DPMI-locked region markers around the ISR code */
void IsrRegionStart(void);                       /* 0x30ea0 */
void IsrRegionEnd(void);                         /* 0x312d8 */

#endif
